from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime
from app.models.tasks import Event, Task
from app.database import get_collection
from app.database.models import RawDataDocument
from bson import ObjectId
import json
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Create router instance
router = APIRouter()

def create_retriever_task(doc: dict, status: str) -> Task:
    """Create a 'Data Retrieving' task."""
    return Task(
        id=f"retriever-{doc.get('_id')}",
        request_id=str(doc.get('_id')),
        name="Data Retrieving",
        message="Retrieve and process raw data from source",
        status=status,
        timestamp=doc.get("timestamp", datetime.utcnow()),
        events=[]
    )

def create_analyzer_task(doc: dict, status: str) -> Task:
    """Create a 'Data Analysis' task with parsed events."""
    events = []
    if doc.get("events"):
        try:
            events_data = json.loads(doc["events"]) if isinstance(doc["events"], str) else doc["events"]
            if isinstance(events_data, list):
                for i, event in enumerate(events_data):
                    if isinstance(event, dict):
                        events.append(Event(
                            id=event.get("id", i + 1),
                            name=event.get("name", f"Step {i + 1}"),
                            status=event.get("status", "info"),
                            message=event.get("text", ""),
                            timestamp=datetime.fromisoformat(event.get("timestamp", doc.get("timestamp", datetime.utcnow()).isoformat()))
                        ))
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse events for document {doc.get('_id')}: {e}")
            events = []

    return Task(
        id=f"analyzer-{doc.get('_id')}",
        request_id=str(doc.get('_id')),
        name="Data Analysis",
        #message=doc.get("analysis", "Analyze retrieved data for insights"),
        message="Analyze retrieved data for insights",
        status=status,
        timestamp=doc.get("timestamp", datetime.utcnow()),
        events=events
    )

# for test request_id=68fd8be2ce8b5274df9cac9d
@router.get("/tasks/{request_id}", response_model=List[Task])
async def get_tasks_by_request_id(request_id: str):
    """
    Get tasks based on the raw_data document status.

    Args:
        request_id: The MongoDB ObjectId of the raw_data document
        
    Returns:
        List[Task]: List of tasks based on pipeline stage
        - Retriever stages: 1 task ("Data Retrieving")
        - Analyzer stages: 2 tasks ("Data Retrieving" mocked + "Data Analysis")
    """
    try:
        # Validate ObjectId format
        try:
            object_id = ObjectId(request_id)
        except Exception:
            raise HTTPException(status_code=400, detail=f"Invalid ObjectId format: {request_id}")

        # Get the raw_data collection
        collection = get_collection("raw_data")
        if collection is None:
            raise HTTPException(status_code=500, detail="Database not connected")

        # Query for document by MongoDB _id
        doc = collection.find_one({"_id": object_id})
        if not doc:
            raise HTTPException(status_code=404, detail=f"No document found with ID: {request_id}")

        # Get status and determine task generation logic
        status = doc.get("status", "")
        tasks = []

        if status.startswith("analyzer:"):
            # Analyzer stage: return mocked retriever task + analyzer task
            analyzer_status = status.split(":")[1]
            tasks.append(create_retriever_task(doc, "completed"))
            tasks.append(create_analyzer_task(doc, analyzer_status))
        elif status.startswith("retriever:"):
            # Retriever stage: return only retriever task
            retriever_status = status.split(":")[1]
            tasks.append(create_retriever_task(doc, retriever_status))
        else:
            # Unknown status: default to retriever processing
            logger.warning(f"Unknown status '{status}' for document {request_id}, defaulting to retriever:processing")
            tasks.append(create_retriever_task(doc, "processing"))

        return tasks

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving tasks for ID {request_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
