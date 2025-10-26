from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserRequest(BaseModel):
    id: int
    name: str
    status: str
    message: str
    timestamp: datetime