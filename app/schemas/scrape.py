from pydantic import BaseModel, HttpUrl


class ScrapeRequest(BaseModel):
    sitemap_url: str
    # max_pages is auto-calculated from sitemap count
    