import httpx
import asyncio
import traceback
from app.models.scrape import ScrapeJob
from app.db.session import SessionLocal
from app.services.sitemap_parser import SitemapScraper


sem = asyncio.Semaphore(10)


# ✅ Fetch single URL
async def fetch(client, url):
    async with sem:
        try:
            res = await client.get(url, timeout=10)

            if res.status_code != 200:
                print(f"❌ Failed: {url} | Status: {res.status_code}")
                return url, None

            print(f"✅ Success: {url}")
            return url, res.text

        except Exception as e:
            print(f"❌ Error: {url} | {e}")
            return url, None


# ✅ Scrape multiple URLs
async def scrape(urls):
    async with httpx.AsyncClient(follow_redirects=True) as client:
        tasks = [fetch(client, u) for u in urls]
        results = await asyncio.gather(*tasks)

    # return only successful pages
    return [(u, h) for u, h in results if h]


# ✅ DB session
def get_db():
    return SessionLocal()


# ✅ MAIN SCRAPER
async def run_scraper(job_id: int, sitemap_url: str):
    db = get_db()

    try:
        job = db.query(ScrapeJob).filter(ScrapeJob.id == job_id).first()

        if not job:
            print("❌ Job not found")
            return

        # ✅ Step 1: Start
        job.status = "running"
        db.commit()

        print("🔍 Parsing sitemap:", sitemap_url)

        scraper = SitemapScraper()
        urls = await scraper.parse_sitemap(sitemap_url)

        print(f"✅ Total URLs found: {len(urls)}")

        if not urls:
            raise Exception("No URLs found in sitemap")

        job.total_urls = len(urls)
        db.commit()

        # ✅ Step 2: Scrape ALL URLs at once
        results = await scrape(urls)

        # ✅ Step 3: Update progress
        job.scraped_urls = len(results)
        db.commit()

        print(f"✅ Successfully scraped: {len(results)} URLs")

        # ✅ OPTIONAL: Save debug file
        with open(f"scraped_job_{job_id}.txt", "w", encoding="utf-8") as f:
            for url, html in results:
                f.write(f"URL: {url}\n")
                f.write(html[:1000])  # limit content
                f.write("\n\n" + "="*50 + "\n\n")

        # ✅ Step 4: Complete
        job.status = "completed"
        db.commit()

    except Exception as e:
        error_text = traceback.format_exc()

        job.status = "failed"
        job.error_message = error_text  # make sure column exists
        db.commit()

        print("🔥 FULL ERROR:\n", error_text)

    finally:
        db.close()