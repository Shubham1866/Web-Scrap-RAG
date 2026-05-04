from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
import os
import asyncio
from datetime import datetime, timezone

from app.schemas.scrape import ScrapeRequest
from app.db.session import get_db
from app.models.scrape import ScrapeJob
from app.core.dependencies import get_current_user

from app.services.sitemap_parser import SitemapScraper
from app.services.scraper import scrape
from app.services.extractor import extract_clean_main_content
from app.services.chunker import chunk
from app.services.embedder import embed
from app.services.vector_store import store


router = APIRouter(tags=["Scrape"])


# -------------------------------
# Debug: Save deduplication results
# -------------------------------
def save_deduplication_results(job_id: int, sitemap_url: str, dedup_data: dict):
    """Save deduplication stats and duplicate URLs to a text file"""
    debug_dir = "debug_output"
    os.makedirs(debug_dir, exist_ok=True)
    
    filename = f"{debug_dir}/job_{job_id}_deduplication.txt"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"Sitemap URL: {sitemap_url}\n")
        f.write(f"Unique Pages: {len(dedup_data.get('unique_pages', []))}\n")
        f.write(f"Duplicates Removed: {dedup_data.get('duplicate_count', 0)}\n")
        f.write("=" * 80 + "\n\n")
        
        if dedup_data.get("duplicates"):
            f.write("DUPLICATE PAGES REMOVED:\n")
            f.write("-" * 40 + "\n")
            for dup in dedup_data["duplicates"]:
                reason = dup.get("reason", "unknown")
                original = dup.get("original_url", "")
                final = dup.get("final_url", "")
                if reason == "final_url_duplicate":
                    f.write(f"🔄 Redirect Duplicate: {original}\n")
                    f.write(f"   Resolved to: {final}\n")
                else:
                    f.write(f"📄 Content Duplicate: {original}\n")
                    f.write(f"   Hash: {dup.get('content_hash', '')}\n")
                f.write("\n")
        else:
            f.write("No duplicate pages found.\n")
    
    print(f"📄 Deduplication results saved to: {filename}")


# -------------------------------
# Debug: Save extracted content to file (without footer)
# -------------------------------
def save_extracted_content(job_id: int, sitemap_url: str, pages: list):
    """Save extracted content from each URL to a text file (footer already stripped)"""
    debug_dir = "debug_output"
    os.makedirs(debug_dir, exist_ok=True)
    
    filename = f"{debug_dir}/job_{job_id}_extracted_content.txt"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"Sitemap URL: {sitemap_url}\n")
        f.write(f"Total Pages Scraped: {len(pages)}\n")
        f.write("=" * 80 + "\n\n")
        
        for url, html in pages:
            # Extract main content only (footer already stripped by extract())
            page_data = extract_clean_main_content(html, url)
            main_content = page_data['content']
            
            f.write(f"URL: {url}\n")
            f.write(f"Title: {page_data['metadata'].get('title', 'N/A')}\n")
            f.write(f"Content Length: {len(main_content)} characters\n")
            f.write("-" * 40 + "\n")
            f.write(main_content)
            f.write("\n\n" + "=" * 80 + "\n\n")
    
    print(f"📄 Extracted content saved to: {filename}")


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
    job.updated_at = datetime.now(timezone.utc)
    db.commit()

    try:
        # 1. Initialize sitemap scraper (auto-detect all URLs from sitemap)
        scraper = SitemapScraper(req.sitemap_url, max_urls=None)
        
        # 2. Get ALL URLs with status (valid+alive vs valid+broken) - with timeout
        url_status = await asyncio.wait_for(scraper.get_urls_with_status(), timeout=300)

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
        job.updated_at = datetime.now(timezone.utc)
        db.commit()

        # 3. Save URL filtering results for debugging
        save_url_filtering_results(job_id, req.sitemap_url, urls, broken_urls)

        # 4. Scrape pages with deduplication
        scrape_result = await scrape(urls)
        pages = scrape_result["unique_pages"]
        duplicate_count = scrape_result["duplicate_count"]

        # Save deduplication results for debugging
        save_deduplication_results(job_id, req.sitemap_url, scrape_result)

        all_chunks = []
        metadatas = []

        # Extract clean main content from all pages (footer already stripped)
        for url, html in pages:
            page_data = extract_clean_main_content(html, url)
            clean_content = page_data['content']
            
            if len(clean_content) < 200:
                continue

            chunks = chunk(clean_content)
            all_chunks.extend(chunks)
            page_meta = {
                'job_id': str(job_id), 
                'type': 'page', 
                'url': url, 
                'title': page_data['metadata'].get('title', '')
            }
            metadatas.extend([page_meta for _ in chunks])

        # Save extracted content for debugging
        save_extracted_content(job_id, req.sitemap_url, pages)

        if not all_chunks:
            job.status = "failed"
            job.error_message = "No content extracted from pages"
            db.commit()
            return

        # 8. Embed
        vectors = embed(all_chunks)

        # 9. Store with metadata in ChromaDB
        store(vectors, all_chunks, metadatas)

        job.scraped_urls = len(pages)
        job.status = "completed"
        job.updated_at = datetime.now(timezone.utc)

    except asyncio.TimeoutError:
        job.status = "failed"
        job.error_message = "Job timeout (5min on sitemap parsing)"
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
