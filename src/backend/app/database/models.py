from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic models."""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


class BaseDocument(BaseModel):
    """Base document model for MongoDB collections."""

    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z"
            }
        }

class RawDataDocument(BaseDocument):
    """Raw data document model for storing scraped or collected data."""

    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when the data was collected")
    source_link: str = Field(..., min_length=1, max_length=2000, description="URL or link to the source data")
    status: str = Field(default="retriver:processing", description="Processing status of the data")
    raw_data: str = Field(default="", description="The actual raw data content as a string")
    analysis: str = Field(default="", description="Result of running analyzer on raw_data: suggested posts + metrics and suggestions")
    events: str = Field(default="[]", description="Reasoning of analysis")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "timestamp": "2023-01-01T12:00:00Z",
                "source_link": "https://example.com/data-source",
                "status": "retriver:processing",
                "raw_data": "This is the raw data content"
            }
        }