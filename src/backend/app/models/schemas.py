from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============================================================================
# Item Models
# ============================================================================

class ItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    is_available: bool = True


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    is_available: Optional[bool] = None


class Item(ItemBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    status: str
    message: str
    timestamp: datetime


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

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://www.threads.com/@yannlecun",
                "user_id": "user1",
                "post_limit": 100,
                "time_limit": 300,
                "scroll_delay": 0.75,
                "headless": False
            }
        }


class PostData(BaseModel):
    """Individual post data."""
    text: str
    link: Optional[str] = None
    likes: Optional[int] = None
    comments: Optional[int] = None
    reposts: Optional[int] = None
    date_posted: Optional[str] = None
    views: Optional[int] = None


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
    items: List[PostData]
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


class JobResponse(BaseModel):
    """Response model for async scraping job."""
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Job status: pending, running, completed, failed")
    platform: str = Field(..., description="Platform name")
    url: str = Field(..., description="Profile URL being scraped")
    user_id: str = Field(..., description="User identifier")
    created_at: str = Field(..., description="Job creation timestamp")
    message: str = Field(..., description="Status message")

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "status": "running",
                "platform": "twitter",
                "url": "https://twitter.com/elonmusk",
                "user_id": "user1",
                "created_at": "2025-10-25T14:30:22.123Z",
                "message": "Scraping job submitted to Bright Data"
            }
        }


class JobStatusResponse(BaseModel):
    """Response model for job status check."""
    job_id: str
    status: str
    platform: str
    url: str
    user_id: str
    created_at: str
    updated_at: str
    progress: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "status": "completed",
                "platform": "twitter",
                "url": "https://twitter.com/elonmusk",
                "user_id": "user1",
                "created_at": "2025-10-25T14:30:22.123Z",
                "updated_at": "2025-10-25T14:32:45.678Z",
                "progress": {"message": "Scraping completed"},
                "error": None
            }
        }
