from dotenv import load_dotenv
import os

# Load environment variables from .env file
# This must be done before importing any modules that read env vars
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from app.routers import sample, scraper
from app.models.schemas import HealthResponse

# Create FastAPI instance
app = FastAPI(
    title="BellFlow API",
    description="A simple FastAPI application for the BellFlow project",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(sample.router, prefix="/api", tags=["items"])
app.include_router(scraper.router, prefix="/v1", tags=["scraper"])


@app.get("/", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint to verify the API is running.
    """
    return HealthResponse(
        status="healthy",
        message="BellFlow API is running successfully!",
        timestamp=datetime.now()
    )


@app.get("/health", response_model=HealthResponse)
async def health():
    """
    Alternative health check endpoint.
    """
    return HealthResponse(
        status="healthy",
        message="API is operational",
        timestamp=datetime.now()
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
