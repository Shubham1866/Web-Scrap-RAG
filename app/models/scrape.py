
from sqlalchemy import Column, Integer, String, Text
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