from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime
from app.models.tasks import Event, Task
import uuid

# Create router instance
router = APIRouter()

@router.get("/tasks/{id}", response_model=List[Task])
async def status(id: str):
    return get_mock_tasks(id)

def get_mock_tasks(id: str) -> list[Task]:
    """Return a list of 2 mock Task objects."""
    
    # Create mock events for the first task
    events_1 = [
        Event(
            id=1,
            name="reasoning 1",
            status="info",
            message="Task initialization completed",
            timestamp=datetime(2024, 1, 15, 10, 30, 0)
        ),
        Event(
            id=2,
            name="reasoning 2",
            status="success",
            message="Task completed successfully",
            timestamp=datetime(2024, 1, 15, 10, 45, 0)
        )
    ]
    
    # Create mock tasks
    mock_tasks = [
        Task(
            id="task-001",
            request_id="4489028f-ab79-4765-b256-ce7d343ba453",
            name="Data Retriving",
            message="Process customer data for analytics",
            status="completed",
            timestamp=datetime(2024, 1, 15, 10, 45, 0),
            events=[]
        ),
        Task(
            id="task-002",
            request_id="4489028f-ab79-4765-b256-ce7d343ba453",
            name="Data Analysis",
            message="",
            status="pending",
            timestamp=datetime(2024, 1, 15, 10, 45, 0),
            events=events_1
        )
    ]
    
    return mock_tasks