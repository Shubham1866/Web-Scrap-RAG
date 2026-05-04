from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.session import engine, Base

# Import routers
from app.api.auth import router as auth
from app.api.scrape import router as scrape

# Run below before running the app for the first time to create DB tables:

# ALTER TABLE scrape_jobs ADD COLUMN total_urls INT DEFAULT 0;
# ALTER TABLE scrape_jobs ADD COLUMN scraped_urls INT DEFAULT 0;
# ALTER TABLE scrape_jobs ADD COLUMN error_message TEXT;


# -------------------------------
# Create DB Tables
# -------------------------------
Base.metadata.create_all(bind=engine)


# -------------------------------
# Initialize FastAPI App
# -------------------------------
app = FastAPI(
    title="RAG Web Scraping API",
    description="Scrape websites + build knowledge base + chat with data",
    version="1.0.0"
)


# -------------------------------
# CORS (for frontend - React/Vite)
# -------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ change in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------
# Include Routers
# -------------------------------
app.include_router(auth, prefix="/api/auth", tags=["Auth"])
app.include_router(scrape, prefix="/api", tags=["Scrape"])


# -------------------------------
# Root Endpoint
# -------------------------------
@app.get("/")
def root():
    return {
        "message": "RAG Web Scraping API is running 🚀"
    }


# -------------------------------
# Health Check (important for deployment)
# -------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}