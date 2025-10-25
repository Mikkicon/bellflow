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




class ItemDocument(BaseDocument):
    """Item document model for the existing items functionality."""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: float = Field(..., gt=0)
    is_available: bool = Field(default=True)
    category: Optional[str] = Field(None, max_length=50)
    tags: List[str] = Field(default_factory=list)
    stock_quantity: int = Field(default=0, ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Sample Item",
                "description": "A sample item description",
                "price": 29.99,
                "is_available": True,
                "category": "Electronics",
                "tags": ["new", "featured"],
                "stock_quantity": 10
            }
        }


class OrderDocument(BaseDocument):
    """Order document model."""

    user_id: PyObjectId = Field(...)
    items: List[Dict[str, Any]] = Field(...)  # List of item_id and quantity
    total_amount: float = Field(..., gt=0)
    status: str = Field(default="pending", pattern="^(pending|confirmed|shipped|delivered|cancelled)$")
    shipping_address: Dict[str, Any] = Field(...)
    payment_method: str = Field(..., max_length=50)
    notes: Optional[str] = Field(None, max_length=500)

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "507f1f77bcf86cd799439011",
                "items": [
                    {"item_id": "507f1f77bcf86cd799439012", "quantity": 2},
                    {"item_id": "507f1f77bcf86cd799439013", "quantity": 1}
                ],
                "total_amount": 59.98,
                "status": "pending",
                "shipping_address": {
                    "street": "123 Main St",
                    "city": "Anytown",
                    "state": "CA",
                    "zip_code": "12345",
                    "country": "USA"
                },
                "payment_method": "credit_card",
                "notes": "Please deliver after 5 PM"
            }
        }


class RawDataDocument(BaseDocument):
    """Raw data document model for storing scraped or collected data."""

    id: str = Field(..., description="Unique identifier for the raw data entry")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when the data was collected")
    source_link: str = Field(..., min_length=1, max_length=2000, description="URL or link to the source data")
    status: str = Field(default="processing", description="Processing status of the data")
    raw_data: str = Field(default="", description="The actual raw data content as a string")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2023-01-01T12:00:00Z",
                "source_link": "https://example.com/data-source",
                "status": "processing",
                "raw_data": "This is the raw data content"
            }
        }


class DatabaseStats(BaseModel):
    """Database statistics model."""

    total_collections: int
    total_documents: int
    database_size: int
    collections: Dict[str, Dict[str, Any]]
    server_info: Dict[str, Any]

    class Config:
        json_schema_extra = {
            "example": {
                "total_collections": 3,
                "total_documents": 150,
                "database_size": 1024000,
                "collections": {
                    "users": {"count": 50, "size": 512000},
                    "items": {"count": 75, "size": 256000},
                    "orders": {"count": 25, "size": 256000}
                },
                "server_info": {
                    "version": "4.4.0",
                    "uptime": 86400
                }
            }
        }
