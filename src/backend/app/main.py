from dotenv import load_dotenv
import os
import signal
import sys

# Load environment variables from .env file
# This must be done before importing any modules that read env vars
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from app.routers import tasks, scraper, data
from app.models.schemas import HealthResponse
from app.database import connect_database, disconnect_database
from app.scraper.session_manager import SessionManager


# Signal handler for graceful shutdown
def signal_handler(sig, frame):
    """
    Handle SIGINT (Ctrl+C) and SIGTERM signals for graceful shutdown.

    This ensures that all browser sessions are properly closed and
    profile data is saved before the application exits.
    """
    print("\n\n🛑 Received shutdown signal, cleaning up...")

    try:
        SessionManager.cleanup_all_sessions()
    except Exception as e:
        print(f"Error during session cleanup: {e}")

    try:
        disconnect_database()
        print("Database disconnected successfully")
    except Exception as e:
        print(f"Database disconnection error: {e}")

    print("👋 Goodbye!\n")
    sys.exit(0)


# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


# Create FastAPI instance
app = FastAPI(
    title="BellFlow API",
    description="A simple FastAPI application for the BellFlow project",
    version="1.0.0"
)

# Database connection events
@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup."""
    try:
        if connect_database():
            print("Database connected successfully")
        else:
            print("Failed to connect to database")
    except Exception as e:
        print(f"Database connection error: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection and cleanup browser sessions on shutdown."""
    # Clean up active browser sessions first to ensure data is saved
    try:
        SessionManager.cleanup_all_sessions()
    except Exception as e:
        print(f"Session cleanup error: {e}")

    # Then disconnect database
    try:
        disconnect_database()
        print("Database disconnected successfully")
    except Exception as e:
        print(f"Database disconnection error: {e}")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tasks.router, prefix="/v1", tags=["tasks"])
app.include_router(scraper.router, prefix="/v1", tags=["scraper"])
app.include_router(data.router, prefix="/v1", tags=["data"])


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
