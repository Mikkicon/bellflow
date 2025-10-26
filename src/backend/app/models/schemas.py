from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from bson import ObjectId


# ============================================================================
# Health Check Models
# ============================================================================

class HealthResponse(BaseModel):
    status: str
    message: str
    timestamp: datetime

class DataResponse(BaseModel):
    """Response model for data endpoint."""
    id: str = Field(..., description="Document ID")
    analysis: Dict[str, Any] = Field(..., description="Analysis results as JSON object")
    news: List[str] = Field(..., description="News list")

# ============================================================================
# Scraper Models
# ============================================================================

class ScraperRequest(BaseModel):
    """Request model for scraping endpoint."""
    url: str = Field(..., description="Profile URL to scrape (e.g., https://www.threads.com/@username)")
    user_id: str = Field(..., description="User ID for browser profile isolation")
    post_limit: Optional[int] = Field(None, description="Maximum number of posts to scrape")
    time_limit: Optional[int] = Field(None, description="Maximum scraping time in seconds")
    scroll_delay: float = Field(0.75, description="Delay between scrolls in seconds", ge=0.1, le=5.0)
    headless: bool = Field(False, description="Run browser in headless mode")
    engine: Optional[Literal["playwright", "brightdata"]] = Field(
        None,
        description="Scraping engine to use. If None, auto-selects based on platform (Threads=playwright, Twitter/LinkedIn=brightdata)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://www.threads.com/@yannlecun",
                "user_id": "user1",
                "post_limit": 100,
                "time_limit": 300,
                "scroll_delay": 0.75,
                "headless": False,
                "engine": None
            }
        }

class ScraperResponse(BaseModel):
    """Response model for scraping endpoint."""
    scraped_at: str
    url: str
    platform: str
    user_id: str
    total_items: int
    post_limit: Optional[int] = None
    time_limit: Optional[int] = None
    elapsed_time: float
    selector_used: Optional[str] = None
    items: List[Dict[str, Any]]  # Generic list of dictionaries for flexibility
    error: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "scraped_at": "20251025_143022",
                "url": "https://www.threads.com/@yannlecun",
                "platform": "threads",
                "user_id": "user1",
                "total_items": 100,
                "post_limit": 100,
                "time_limit": None,
                "elapsed_time": 45.3,
                "selector_used": "div[data-pressable-container=\"true\"]",
                "items": [
                    {
                        "text": "Post text content...",
                        "link": "https://www.threads.com/@yannlecun/post/...",
                        "likes": 442,
                        "comments": 65,
                        "reposts": 24
                    }
                ],
                "error": None
            }
        }


class ScraperTaskResponse(BaseModel):
    """Response model for async scraping task."""
    task_id: str = Field(..., description="MongoDB ObjectId for polling scraping status")
    message: str = Field(default="Scraping task started", description="Status message")
    source_link: str = Field(..., description="URL being scraped")

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "507f1f77bcf86cd799439011",
                "message": "Scraping task started",
                "source_link": "https://www.threads.com/@yannlecun"
            }
        }


# ============================================================================
# Poster Models
# ============================================================================

class PostRequest(BaseModel):
    """Request model for posting endpoint."""
    user_id: str = Field(..., description="User ID for browser profile isolation")
    content: str = Field(..., description="Text content to post")
    platform: str = Field(..., description="Platform to post to (e.g., 'x', 'threads')")
    url: Optional[str] = Field(None, description="Optional URL to navigate to (if None, uses platform home)")
    headless: bool = Field(False, description="Run browser in headless mode")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user1",
                "content": "Hello from BellFlow API! This is a test post.",
                "platform": "x",
                "url": None,
                "headless": False
            }
        }


class PostResponse(BaseModel):
    """Response model for posting endpoint."""
    posted_at: str
    platform: str
    user_id: str
    success: bool
    content: str
    post_url: Optional[str] = None
    error: Optional[str] = None
    elapsed_time: float

    class Config:
        json_schema_extra = {
            "example": {
                "posted_at": "20251026_143022",
                "platform": "x",
                "user_id": "user1",
                "success": True,
                "content": "Hello from BellFlow API! This is a test post.",
                "post_url": "https://x.com/username/status/1234567890",
                "error": None,
                "elapsed_time": 8.5
            }
        }


class PostTaskResponse(BaseModel):
    """Response model for async posting task."""
    task_id: str = Field(..., description="MongoDB ObjectId for polling posting status")
    message: str = Field(default="Posting task started", description="Status message")
    platform: str = Field(..., description="Platform being posted to")

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "507f1f77bcf86cd799439011",
                "message": "Posting task started",
                "platform": "x"
            }
        }
