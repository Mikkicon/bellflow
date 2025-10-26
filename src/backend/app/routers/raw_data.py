from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError
from datetime import datetime
from bson import ObjectId

from ..database.connector import get_collection
from ..database.models import RawDataDocument
from ..models.schemas import (
    RawDataCreate,
    RawDataUpdate,
    RawDataResponse,
    RawDataListResponse
)

router = APIRouter(prefix="/raw-data", tags=["raw-data"])


def doc_to_response(doc: Dict[str, Any]) -> RawDataResponse:
    """Convert MongoDB document to RawDataResponse by converting _id to id string."""
    doc["id"] = str(doc.pop("_id"))
    return RawDataResponse(**doc)


def get_raw_data_collection() -> Collection:
    """Get the raw_data collection."""
    collection = get_collection("raw_data")
    if not collection:
        raise HTTPException(status_code=500, detail="Database connection failed")
    return collection


@router.post("/", response_model=RawDataResponse, status_code=201)
async def create_raw_data(
    raw_data: RawDataCreate,
    collection: Collection = Depends(get_raw_data_collection)
):
    """Create a new raw data entry."""
    try:
        # Create RawDataDocument instance
        document = RawDataDocument(**raw_data.dict())

        # Convert to dict for MongoDB insertion
        doc_dict = document.dict(by_alias=True)

        # Insert document
        result = collection.insert_one(doc_dict)

        # Fetch the created document
        created_doc = collection.find_one({"_id": result.inserted_id})
        if not created_doc:
            raise HTTPException(status_code=500, detail="Failed to retrieve created document")

        return doc_to_response(created_doc)

    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Document with this ID already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create raw data: {str(e)}")


@router.post("/init", response_model=RawDataResponse, status_code=201)
async def initialize_scraping(
    source_link: str = Query(..., description="URL to scrape"),
    collection: Collection = Depends(get_raw_data_collection)
):
    """
    Initialize a new scraping job.

    Creates a raw data entry with status="processing" for the given source link.
    This endpoint is used to create a job record before scraping begins.
    """
    try:
        # Create RawDataDocument instance
        document = RawDataDocument(
            timestamp=datetime.utcnow(),
            source_link=source_link,
            status="processing",
            raw_data="",
            error=None
        )

        # Convert to dict for MongoDB insertion
        doc_dict = document.dict(by_alias=True)

        # Insert document
        result = collection.insert_one(doc_dict)

        # Fetch the created document
        created_doc = collection.find_one({"_id": result.inserted_id})
        if not created_doc:
            raise HTTPException(status_code=500, detail="Failed to retrieve created document")

        return doc_to_response(created_doc)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize scraping: {str(e)}")


@router.get("/{raw_data_id}", response_model=RawDataResponse)
async def get_raw_data(
    raw_data_id: str,
    collection: Collection = Depends(get_raw_data_collection)
):
    """Get a specific raw data entry by ID."""
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(raw_data_id):
            raise HTTPException(status_code=400, detail="Invalid ID format")

        # Find document
        document = collection.find_one({"_id": ObjectId(raw_data_id)})
        if not document:
            raise HTTPException(status_code=404, detail="Raw data not found")

        return doc_to_response(document)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve raw data: {str(e)}")


@router.get("/{raw_data_id}/poll", response_model=RawDataResponse)
async def poll_raw_data(
    raw_data_id: str,
    collection: Collection = Depends(get_raw_data_collection)
):
    """
    Poll a specific raw data entry for status updates.

    This endpoint is identical to the GET endpoint but provides clearer intent
    for polling operations. Use this for checking scraping job progress.
    """
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(raw_data_id):
            raise HTTPException(status_code=400, detail="Invalid ID format")

        # Find document
        document = collection.find_one({"_id": ObjectId(raw_data_id)})
        if not document:
            raise HTTPException(status_code=404, detail="Raw data not found")

        return doc_to_response(document)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to poll raw data: {str(e)}")


@router.get("/", response_model=RawDataListResponse)
async def list_raw_data(
    skip: int = Query(0, ge=0, description="Number of documents to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of documents to return"),
    link_filter: Optional[str] = Query(None, description="Filter by source_link containing this string"),
    collection: Collection = Depends(get_raw_data_collection)
):
    """List raw data entries with optional filtering and pagination."""
    try:
        # Build filter query
        filter_query = {}
        if link_filter:
            filter_query["source_link"] = {"$regex": link_filter, "$options": "i"}

        # Get total count
        total_count = collection.count_documents(filter_query)

        # Get documents with pagination
        cursor = collection.find(filter_query).skip(skip).limit(limit).sort("created_at", -1)
        documents = list(cursor)

        # Convert to response format
        raw_data_list = [doc_to_response(doc.copy()) for doc in documents]

        return RawDataListResponse(
            items=raw_data_list,
            total=total_count,
            skip=skip,
            limit=limit
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list raw data: {str(e)}")


@router.put("/{raw_data_id}", response_model=RawDataResponse)
async def update_raw_data(
    raw_data_id: str,
    raw_data_update: RawDataUpdate,
    collection: Collection = Depends(get_raw_data_collection)
):
    """Update a raw data entry."""
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(raw_data_id):
            raise HTTPException(status_code=400, detail="Invalid ID format")

        # Check if document exists
        existing_doc = collection.find_one({"_id": ObjectId(raw_data_id)})
        if not existing_doc:
            raise HTTPException(status_code=404, detail="Raw data not found")

        # Prepare update data (only non-None fields)
        update_data = raw_data_update.dict(exclude_unset=True)

        # Always update the updated_at timestamp
        update_data["updated_at"] = datetime.utcnow()

        # Update document
        result = collection.update_one(
            {"_id": ObjectId(raw_data_id)},
            {"$set": update_data}
        )

        if result.modified_count == 0 and len(update_data) > 1:
            # Only raise error if there was actual data to update (beyond updated_at)
            raise HTTPException(status_code=500, detail="Failed to update document")

        # Fetch updated document
        updated_doc = collection.find_one({"_id": ObjectId(raw_data_id)})
        return doc_to_response(updated_doc)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update raw data: {str(e)}")


@router.delete("/{raw_data_id}")
async def delete_raw_data(
    raw_data_id: str,
    collection: Collection = Depends(get_raw_data_collection)
):
    """Delete a raw data entry."""
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(raw_data_id):
            raise HTTPException(status_code=400, detail="Invalid ID format")

        # Check if document exists
        existing_doc = collection.find_one({"_id": ObjectId(raw_data_id)})
        if not existing_doc:
            raise HTTPException(status_code=404, detail="Raw data not found")

        # Delete document
        result = collection.delete_one({"_id": ObjectId(raw_data_id)})

        if result.deleted_count == 0:
            raise HTTPException(status_code=500, detail="Failed to delete document")

        return {"message": "Raw data deleted successfully", "id": raw_data_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete raw data: {str(e)}")


@router.get("/stats/summary")
async def get_raw_data_stats(
    collection: Collection = Depends(get_raw_data_collection)
):
    """Get statistics about the raw_data collection."""
    try:
        # Get collection stats
        total_documents = collection.count_documents({})

        # Get unique source_links count
        unique_links = len(collection.distinct("source_link"))

        # Get date range
        date_pipeline = [
            {
                "$group": {
                    "_id": None,
                    "earliest": {"$min": "$created_at"},
                    "latest": {"$max": "$created_at"}
                }
            }
        ]
        date_stats = list(collection.aggregate(date_pipeline))

        # Get recent activity (last 24 hours)
        from datetime import timedelta
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_count = collection.count_documents({"created_at": {"$gte": yesterday}})

        return {
            "total_documents": total_documents,
            "unique_links": unique_links,
            "recent_entries_24h": recent_count,
            "date_range": date_stats[0] if date_stats else None
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get raw data stats: {str(e)}")
