
from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime, timezone
from app.db.session import Base


class ScrapeJob(Base):

# This represents one scraping request made by a user.
    
    __tablename__ = "scrape_jobs"   

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String(50), default="pending")
    user_id = Column(Integer)

    total_urls = Column(Integer, default=0)
    scraped_urls = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
