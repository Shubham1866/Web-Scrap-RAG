from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
import os

from app.schemas.scrape import ScrapeRequest
from app.db.session import get_db
from app.models.scrape import ScrapeJob
from app.core.dependencies import get_current_user

from app.services.sitemap_parser import SitemapScraper
from app.services.scraper import scrape
from app.services.extractor import extract_with_footer
from app.services.chunker import chunk
from app.services.embedder import embed
from app.services.vector_store import store

router = APIRouter(tags=["Scrape"])

# Store footer content globally (extracted once per job)
_job_footer_content = {}


# -------------------------------
# Debug: Save extracted content to file (without footer)
# -------------------------------
def save_extracted_content(job_id: int, sitemap_url: str, pages: list):
    """Save extracted content from each URL to a text file (footer saved separately)"""
    debug_dir = "debug_output"
    os.makedirs(debug_dir, exist_ok=True)
    
    filename = f"{debug_dir}/job_{job_id}_extracted_content.txt"
    footer_filename = f"{debug_dir}/job_{job_id}_footer.txt"
    
    footer_saved = False
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"Sitemap URL: {sitemap_url}\n")
        f.write(f"Total Pages Scraped: {len(pages)}\n")
        f.write("=" * 80 + "\n\n")
        
        for url, html in pages:
            # Extract main content and footer separately
            main_content, footer_content = extract_with_footer(html)
            
            f.write(f"URL: {url}\n")
            f.write(f"Content Length: {len(main_content)} characters\n")
            f.write("-" * 40 + "\n")
            f.write(main_content)
            f.write("\n\n" + "=" * 80 + "\n\n")
            
            # Save footer only once
            if footer_content and not footer_saved:
                with open(footer_filename, "w", encoding="utf-8") as ff:
                    ff.write(f"Footer Content (saved once for job {job_id})\n")
                    ff.write("=" * 80 + "\n\n")
                    ff.write(footer_content)
                _job_footer_content[job_id] = footer_content
                footer_saved = True
    
    print(f"📄 Extracted content saved to: {filename}")
    if footer_saved:
        print(f"📄 Footer content saved to: {footer_filename}")


# -------------------------------
# Debug: Save URL filtering results
# -------------------------------
def save_url_filtering_results(job_id: int, sitemap_url: str, allowed_urls: list, broken_urls: list):
    """Save allowed and broken URLs to a text file"""
    debug_dir = "debug_output"
    os.makedirs(debug_dir, exist_ok=True)
    
    filename = f"{debug_dir}/job_{job_id}_url_filtering.txt"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"Sitemap URL: {sitemap_url}\n")
        f.write(f"Valid & Accessible URLs: {len(allowed_urls)}\n")
        f.write(f"Valid but Broken (non-200): {len(broken_urls)}\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("ALLOWED URLs (will be scraped):\n")
        f.write("-" * 40 + "\n")
        for url in allowed_urls:
            f.write(f"✓ {url}\n")
        
        f.write("\n" + "=" * 80 + "\n\n")
        f.write("BROKEN URLs (returned non-200 or timed out):\n")
        f.write("-" * 40 + "\n")
        for url in broken_urls:
            f.write(f"✗ {url}\n")
    
    print(f"📄 URL filtering results saved to: {filename}")


# -------------------------------
# Background Job
# -------------------------------
async def run(job_id, req, db: Session):
    job = db.query(ScrapeJob).filter(ScrapeJob.id == job_id).first()
    job.status = "processing"
    db.commit()

    try:
        # 1. Initialize sitemap scraper (auto-detect all URLs from sitemap)
        scraper = SitemapScraper(req.sitemap_url, max_urls=None)
        
        # 2. Get ALL URLs with status (valid+alive vs valid+broken)
        url_status = await scraper.get_urls_with_status()
        
        all_valid_urls = url_status["valid_alive"] + url_status["valid_broken"]
        urls = url_status["valid_alive"]
        broken_urls = url_status["valid_broken"]

        if not all_valid_urls:
            job.status = "failed"
            job.error_message = "No valid URLs found in sitemap"
            db.commit()
            return

        # Set total URLs found in sitemap
        job.total_urls = len(all_valid_urls)
        db.commit()

        # 3. Save URL filtering results for debugging
        save_url_filtering_results(job_id, req.sitemap_url, urls, broken_urls)

        # 4. Scrape pages
        pages = await scrape(urls)

        all_chunks = []

        # 5. Extract + chunk (only main content, skip footer)
        for url, html in pages:
            main_content, _ = extract_with_footer(html)

            if len(main_content) < 200:
                continue

            chunks = chunk(main_content)
            all_chunks.extend(chunks)

        # 7. Save extracted content for debugging
        save_extracted_content(job_id, req.sitemap_url, pages)

        if not all_chunks:
            job.status = "failed"
            job.error_message = "No content extracted from pages"
            db.commit()
            return

        # 8. Embed
        vectors = embed(all_chunks)

        # 9. Store
        store(vectors, all_chunks)

        job.scraped_urls = len(pages)
        job.status = "completed"

    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)

    db.commit()


# -------------------------------
# API Endpoint
# -------------------------------
@router.post("/scrape")
async def start_scrape(
    req: ScrapeRequest,
    bg: BackgroundTasks,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    job = ScrapeJob(user_id=user.id, status="pending")

    db.add(job)
    db.commit()
    db.refresh(job)

    bg.add_task(run, job.id, req, db)

    return {
        "message": "Scraping started",
        "job_id": job.id
    }