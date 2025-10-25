from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from bson import ObjectId


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


# Raw Data Schemas
class RawDataBase(BaseModel):
    id: str = Field(..., description="Unique identifier for the raw data entry")
    timestamp: datetime = Field(..., description="Timestamp when the data was collected")
    source_link: str = Field(..., min_length=1, max_length=2000, description="URL or link to the source data")
    status: str = Field(default="processing", description="Processing status of the data")
    raw_data: str = Field(default="", description="The actual raw data content as a string")


class RawDataCreate(RawDataBase):
    """Schema for creating raw data entries."""
    pass


class RawDataUpdate(BaseModel):
    """Schema for updating raw data entries."""
    source_link: Optional[str] = Field(None, min_length=1, max_length=2000)
    status: Optional[str] = None
    raw_data: Optional[str] = None
    timestamp: Optional[datetime] = None


class RawDataResponse(RawDataBase):
    """Schema for raw data responses."""
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


class RawDataListResponse(BaseModel):
    """Schema for paginated raw data list responses."""
    items: List[RawDataResponse]
    total: int
    skip: int
    limit: int


