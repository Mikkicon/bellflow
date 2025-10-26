from fastapi import APIRouter, HTTPException
from bson import ObjectId
import json
from app.database import get_collection
from app.models.schemas import DataResponse

# Create router instance
router = APIRouter()


@router.get("/data/{id}", response_model=DataResponse)
async def get_data_by_id(id: str):
    """
    Get a single document from the raw_data collection by ID.
    
    Args:
        id: MongoDB ObjectId as string
        
    Returns:
        DataResponse: Document containing id and analysis fields
        
    Raises:
        HTTPException: If ID is invalid, document not found, or analysis is null
    """
    try:
        # Validate ObjectId format
        if not ObjectId.is_valid(id):
            raise HTTPException(status_code=400, detail=f"Invalid ObjectId format: {id}")

        # Get the raw_data collection
        collection = get_collection("raw_data")
        if collection is None:
            raise HTTPException(status_code=500, detail="Database not connected")

        # Convert string ID to ObjectId
        object_id = ObjectId(id)

        # Query the document
        document = collection.find_one({"_id": object_id})

        if document is None:
            raise HTTPException(status_code=404, detail=f"Document with id {id} not found")

        # Check if analysis field exists and is not null/empty
        analysis_str = document.get("analysis")
        if not analysis_str or analysis_str.strip() == "":
            raise HTTPException(status_code=400, detail="Analysis field is null or empty")

        # Parse the JSON string to object
        try:
            analysis_obj = json.loads(analysis_str)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Analysis field contains invalid JSON: {str(e)}")

        # Return only id and analysis fields
        return DataResponse(
            id=str(document["_id"]),
            analysis=analysis_obj
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle any other unexpected errors
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
