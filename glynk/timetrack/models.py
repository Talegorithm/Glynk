from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TagCreate(BaseModel):
    name: str
    color: str = "#6B7280"

class TagUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    sort_order: Optional[int] = None

class TagResponse(BaseModel):
    id: str
    name: str
    color: str
    sort_order: int
    created_at: datetime

class TagReorderItem(BaseModel):
    id: str
    sort_order: int

class TagReorderRequest(BaseModel):
    items: list[TagReorderItem]

class SessionCreate(BaseModel):
    pass # Currently no body needed to start

class SessionStop(BaseModel):
    end_time: Optional[datetime] = None # Allow client to pass end time for offline sync, otherwise use server time

class SessionNoteUpdate(BaseModel):
    note: str

class SessionResponse(BaseModel):
    id: str
    tag_id: str
    start_time: datetime
    end_time: Optional[datetime]
    note: Optional[str]
    created_at: datetime
