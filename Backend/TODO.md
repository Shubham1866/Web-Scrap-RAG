# Fix Stuck Processing Jobs (Auto-fail on hang/force-stop)

## Steps
- [x] 1. Edit app/models/scrape.py: Add `updated_at` timestamp for heartbeat detection
- [x] 2. Edit app/api/scrape.py: 
  - Add timeout wrapper to `run()` (asyncio.wait_for 5min on sitemap)
  - Add heartbeat: every 30s update `job.updated_at = now()`
  - Broader try/except + finally: always set 'failed' on timeout/error
- [ ] 3. Edit app/services/sitemap_parser.py: Add timeout=30s to httpx calls in parse_sitemap/is_page_alive
- [x] 4. Edit app/services/scraper.py: Add timeout to fetch()
- [ ] 5. Test: uvicorn restart, new job, force-stop → verify auto 'failed'
- [ ] 6. Manual fix jobs 7-8 via SQL or restart+changes

Progress tracked here after each step.

