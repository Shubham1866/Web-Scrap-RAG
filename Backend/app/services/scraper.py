import httpx
import asyncio
import hashlib


sem = asyncio.Semaphore(10)


# ✅ Fetch single URL
async def fetch(client, url):
    async with sem:
        try:
            res = await client.get(url, timeout=10)

            if res.status_code != 200:
                print(f"❌ Failed: {url} | Status: {res.status_code}")
                return url, None, None, None

            # Track final URL after redirects
            final_url = str(res.url)
            content_hash = hashlib.md5(res.text.encode("utf-8")).hexdigest()

            print(f"✅ Success: {url} -> Final: {final_url} | Hash: {content_hash}")
            return url, res.text, final_url, content_hash

        except Exception as e:
            print(f"❌ Error: {url} | {e}")
            return url, None, None, None


# ✅ Scrape multiple URLs with page-level deduplication
async def scrape(urls):
    timeout = httpx.Timeout(30.0)
    async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
        tasks = [fetch(client, u) for u in urls]
        results = await asyncio.gather(*tasks)

    seen_final_urls = set()
    seen_hashes = set()
    unique_pages = []
    duplicates = []

    for original_url, html, final_url, content_hash in results:
        if not html:
            continue

        # Deduplicate by final URL (catches HTTP redirects)
        if final_url in seen_final_urls:
            duplicates.append({
                "original_url": original_url,
                "final_url": final_url,
                "reason": "final_url_duplicate",
                "duplicate_of": None
            })
            print(f"🔄 Duplicate (redirect): {original_url} -> {final_url}")
            continue

        # Deduplicate by content hash (catches identical content)
        if content_hash in seen_hashes:
            duplicates.append({
                "original_url": original_url,
                "final_url": final_url,
                "reason": "content_hash_duplicate",
                "content_hash": content_hash
            })
            print(f"📄 Duplicate (content): {original_url} | Hash: {content_hash}")
            continue

        seen_final_urls.add(final_url)
        seen_hashes.add(content_hash)
        unique_pages.append((original_url, html))

    print(f"\n📊 Deduplication Stats:")
    print(f"   Total fetched: {len([r for r in results if r[1]])}")
    print(f"   Unique pages: {len(unique_pages)}")
    print(f"   Duplicates removed: {len(duplicates)}")

    return {
        "unique_pages": unique_pages,
        "duplicate_count": len(duplicates),
        "duplicates": duplicates
    }
