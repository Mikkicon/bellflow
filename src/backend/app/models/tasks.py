from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Event(BaseModel):
    id: int
    name: str
    status: str
    message: str
    timestamp: datetime

class Task(BaseModel):
    id: str
    request_id: str # this is our main request id
    name: str
    message: str
    status: str
    timestamp: datetime
    events: list[Event]