from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any

from glynk.api.auth import get_current_user
from glynk.timetrack.models import (
    TagCreate, TagUpdate, TagResponse, TagReorderRequest,
    SessionCreate, SessionStop, SessionNoteUpdate, SessionResponse
)
from glynk.timetrack.db import TimetrackStore

router = APIRouter(tags=["Timetrack"])

def get_store() -> TimetrackStore:
    return TimetrackStore()

# --- Tags ---

@router.get("/timetrack/tags", response_model=List[TagResponse])
async def list_tags(user: dict = Depends(get_current_user), store: TimetrackStore = Depends(get_store)):
    return store.list_tags(user['entity_id'])

@router.post("/timetrack/tags", response_model=TagResponse)
async def create_tag(req: TagCreate, user: dict = Depends(get_current_user), store: TimetrackStore = Depends(get_store)):
    return store.create_tag(user['entity_id'], req.name, req.color)

@router.put("/timetrack/tags/reorder")
async def reorder_tags(req: TagReorderRequest, user: dict = Depends(get_current_user), store: TimetrackStore = Depends(get_store)):
    items = [{"id": item.id, "sort_order": item.sort_order} for item in req.items]
    store.reorder_tags(user['entity_id'], items)
    return {"success": True}

@router.put("/timetrack/tags/{tag_id}", response_model=TagResponse)
async def update_tag(tag_id: str, req: TagUpdate, user: dict = Depends(get_current_user), store: TimetrackStore = Depends(get_store)):
    tag = store.update_tag(tag_id, user['entity_id'], **req.model_dump(exclude_unset=True))
    if not tag:
        raise HTTPException(404, "Tag not found")
    return tag

@router.delete("/timetrack/tags/{tag_id}")
async def delete_tag(tag_id: str, user: dict = Depends(get_current_user), store: TimetrackStore = Depends(get_store)):
    store.delete_tag(tag_id, user['entity_id'])
    return {"success": True}

# --- Sessions ---

@router.get("/timetrack/sessions/active", response_model=List[SessionResponse])
async def get_active_sessions(user: dict = Depends(get_current_user), store: TimetrackStore = Depends(get_store)):
    return store.get_active_sessions(user['entity_id'])

@router.post("/timetrack/sessions/{tag_id}/start", response_model=SessionResponse)
async def start_session(tag_id: str, single_mode: bool = Query(False), user: dict = Depends(get_current_user), store: TimetrackStore = Depends(get_store)):
    return store.start_session(user['entity_id'], tag_id, single_mode)

@router.post("/timetrack/sessions/{session_id}/stop", response_model=SessionResponse)
async def stop_session(session_id: str, req: SessionStop, user: dict = Depends(get_current_user), store: TimetrackStore = Depends(get_store)):
    session = store.stop_session(session_id, user['entity_id'], req.end_time)
    if not session:
        raise HTTPException(404, "Session not found")
    return session

@router.put("/timetrack/sessions/{session_id}/note", response_model=SessionResponse)
async def update_session_note(session_id: str, req: SessionNoteUpdate, user: dict = Depends(get_current_user), store: TimetrackStore = Depends(get_store)):
    session = store.update_session_note(session_id, user['entity_id'], req.note)
    if not session:
        raise HTTPException(404, "Session not found")
    return session

from pydantic import BaseModel
class PastSessionRequest(BaseModel):
    tag_id: str
    duration_mins: int
    note: str

@router.post("/timetrack/sessions/past", response_model=SessionResponse)
async def add_past_session(req: PastSessionRequest, user: dict = Depends(get_current_user), store: TimetrackStore = Depends(get_store)):
    return store.add_past_session(user['entity_id'], req.tag_id, req.duration_mins, req.note)

@router.get("/timetrack/stats")
async def get_stats(
    start_dt: str = Query(None), 
    end_dt: str = Query(None), 
    user: dict = Depends(get_current_user), 
    store: TimetrackStore = Depends(get_store)
):
    # Returns raw sessions with tag details. Frontend will aggregate.
    return store.get_stats(user['entity_id'], start_dt, end_dt)

@router.get("/timetrack/stats/today")
async def get_today_stats(user: dict = Depends(get_current_user), store: TimetrackStore = Depends(get_store)):
    return store.get_today_stats(user['entity_id'])
