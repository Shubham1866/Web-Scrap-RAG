import httpx
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, urlunparse


class SitemapScraper:
    def __init__(self, sitemap_url: str, max_urls: int = None):
        self.sitemap_url = sitemap_url
        self.max_urls = max_urls  # None means check ALL URLs
        self.base_domain = urlparse(sitemap_url).netloc
        self.visited = set()

    # -------------------------------
    # Normalize URL (remove duplicates)
    # -------------------------------
    def normalize_url(self, url: str) -> str:
        parsed = urlparse(url)

        # remove query params & fragments
        clean = parsed._replace(query="", fragment="")

        url = urlunparse(clean)

        # remove trailing slash
        return url.rstrip("/")

    # -------------------------------
    # URL Filtering Rules
    # -------------------------------
    def is_valid_url(self, url: str) -> bool:
        try:
            parsed = urlparse(url)

            # ❌ Skip external domains
            if parsed.netloc != self.base_domain:
                return False

            path = url.lower()

            # ❌ Skip auth pages
            if any(k in path for k in [
                "login", "signin", "signup", "register",
                "account", "cart", "checkout"
            ]):
                return False

            # ❌ Skip useless/legal pages
            # if any(k in path for k in [
            #     "privacy", "terms", "policy", "cookies"
            # ]):
            #     return False

            # ❌ Skip file types
            if path.endswith((
                ".pdf", ".jpg", ".jpeg", ".png",
                ".gif", ".zip", ".rar"
            )):
                return False

            return True

        except Exception:
            return False

    # -------------------------------
    # Check if page is alive and error-free
    # -------------------------------
    async def is_page_alive(self, url: str) -> bool:
        try:
            timeout = httpx.Timeout(30.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                res = await client.get(url, follow_redirects=True, timeout=timeout)

            if res.status_code != 200:
                return False

            # Check if page contains PHP errors
            html_lower = res.text.lower()
            php_error_indicators = [
                "php error",
                "notice:",
                "warning:",
                "fatal error",
                "parse error",
                "syntax error",
                "undefined variable",
                "severity: notice",
                "severity: warning"
            ]

            for indicator in php_error_indicators:
                if indicator in html_lower:
                    return False

            return True

        except Exception:
            return False


    # -------------------------------
    # Parse Sitemap Recursively
    # -------------------------------
    async def parse_sitemap(self, url: str, collected: set):
        # Skip if max_urls is set and we've reached the limit
        if self.max_urls is not None and len(collected) >= self.max_urls:
            return

        try:
            timeout = httpx.Timeout(30.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                res = await client.get(url, timeout=timeout)

            if res.status_code != 200:
                return

            root = ET.fromstring(res.text)

            # 🔁 Handle sitemap index
            if root.tag.endswith("sitemapindex"):
                for sm in root.findall(".//{*}loc"):
                    await self.parse_sitemap(sm.text, collected)

            # 📄 Handle urlset
            elif root.tag.endswith("urlset"):
                for loc in root.findall(".//{*}loc"):
                    raw_url = loc.text
                    norm_url = self.normalize_url(raw_url)

                    if norm_url in self.visited:
                        continue

                    self.visited.add(norm_url)

                    if not self.is_valid_url(norm_url):
                        continue

                    # Only check limit if max_urls is set
                    if self.max_urls is not None and len(collected) >= self.max_urls:
                        break

                    collected.add(norm_url)

        except Exception:
            return

    # -------------------------------
    # Get URLs with detailed status for debugging
    # -------------------------------
    async def get_urls_with_status(self):
        """
        Returns a dict with categorized URLs:
        - valid_alive: URLs that are valid and accessible (200)
        - valid_broken: URLs that are valid but not accessible (non-200 or timeout)
        """
        collected = set()
        await self.parse_sitemap(self.sitemap_url, collected)
        
        # First, collect ALL valid URLs (don't limit yet)
        all_valid_urls = list(collected)
        
        valid_alive = []
        valid_broken = []
        
        # Now check ALL of them for status (not just max_urls)
        for url in all_valid_urls:
            if await self.is_page_alive(url):
                valid_alive.append(url)
            else:
                valid_broken.append(url)
        
        # Only limit the alive ones for scraping
        allowed_to_scrape = valid_alive[:self.max_urls]
        
        return {
            "valid_alive": allowed_to_scrape,
            "valid_broken": valid_broken
        }


