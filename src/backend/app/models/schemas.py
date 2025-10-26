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
# Raw Data Models
# ============================================================================

class RawDataCreate(BaseModel):
    """
    Request model for creating raw data entries.

    Used when initializing a new scraping job in the database.
    """
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when the data was collected")
    source_link: str = Field(..., min_length=1, max_length=2000, description="URL or link to the source data")
    status: str = Field(default="processing", description="Processing status of the data (processing, completed, failed)")
    raw_data: str = Field(default="", description="JSON string of scraped posts (full ScraperResponse)")
    error: Optional[str] = Field(None, description="Error message if scraping failed")


class RawDataUpdate(BaseModel):
    """
    Request model for updating raw data entries.

    All fields are optional to support partial updates. Used to update
    scraping status and populate results after scraping completes.
    """
    timestamp: Optional[datetime] = None
    source_link: Optional[str] = Field(None, min_length=1, max_length=2000)
    status: Optional[str] = None
    raw_data: Optional[str] = None
    error: Optional[str] = None


class RawDataResponse(BaseModel):
    """
    Response model for raw data queries.

    Includes all fields from RawDataDocument plus MongoDB metadata.
    The id field is the MongoDB ObjectId converted to string.
    """
    id: str = Field(..., description="MongoDB document ID (ObjectId as string)")
    timestamp: datetime = Field(..., description="Timestamp when the data was collected")
    source_link: str = Field(..., description="URL or link to the source data")
    status: str = Field(..., description="Processing status of the data (processing, completed, failed)")
    raw_data: str = Field(..., description="JSON string of scraped posts (full ScraperResponse)")
    error: Optional[str] = Field(None, description="Error message if scraping failed")
    created_at: datetime = Field(..., description="Timestamp when document was created in database")
    updated_at: datetime = Field(..., description="Timestamp when document was last updated")

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


class RawDataListResponse(BaseModel):
    """
    Response model for paginated raw data list queries.

    Used by list endpoints to return multiple raw data entries with pagination metadata.
    """
    items: List[RawDataResponse]
    total: int
    skip: int
    limit: int
