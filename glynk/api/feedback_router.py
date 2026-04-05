"""
反馈 API

POST /feedback   提交 Agent 反馈
"""
from uuid import uuid4
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from glynk.api.auth import get_current_user
from glynk.storage.postgres import PostgresStore

router = APIRouter(tags=["feedback"])


class FeedbackResult(BaseModel):
    result_id: str
    presented: bool = False
    clicked_through: bool = False
    agent_summary: str | None = None


class FeedbackRequest(BaseModel):
    query_id: str
    results: list[FeedbackResult]


@router.post("/feedback")
async def submit_feedback(req: FeedbackRequest, user: dict = Depends(get_current_user)):
    """提交反馈"""
    db = PostgresStore.get_instance()

    try:
        for result in req.results:
            feedback_id = f"fb-{uuid4().hex[:12]}"
            db.create_feedback(
                feedback_id=feedback_id,
                query_id=req.query_id,
                result_id=result.result_id,
                presented=result.presented,
                clicked_through=result.clicked_through,
                agent_summary=result.agent_summary,
            )
    except Exception as e:
        raise HTTPException(400, f"Feedback submission failed: {e}")

    return {"ok": True, "count": len(req.results)}
