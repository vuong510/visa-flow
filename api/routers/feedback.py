from typing import Optional
from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db.session import get_db
from db.models import Feedback

router = APIRouter()


class FeedbackCreate(BaseModel):
    client_id: str = Field(..., max_length=64)
    message: str = Field(..., min_length=1)
    application_id: Optional[int] = None
    session_id: Optional[str] = Field(None, max_length=36)
    screen: Optional[str] = Field(None, max_length=50)

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("message must not be empty or whitespace-only")
        return v


def _serialize(fb: Feedback) -> dict:
    return {
        "id": fb.id,
        "application_id": fb.application_id,
        "session_id": fb.session_id,
        "screen": fb.screen,
        "message": fb.message,
        "client_id": fb.client_id,
        "created_at": fb.created_at.isoformat() if fb.created_at else None,
    }


@router.post("/feedback", status_code=201)
def create_feedback(body: FeedbackCreate, response: Response, db: Session = Depends(get_db)):
    existing = db.query(Feedback).filter(Feedback.client_id == body.client_id).first()
    if existing:
        # Idempotent retry: server already has this client_id — return existing record, no new row.
        response.status_code = 200
        return _serialize(existing)

    fb = Feedback(
        application_id=body.application_id,
        session_id=body.session_id,
        screen=body.screen,
        message=body.message,
        client_id=body.client_id,
    )
    db.add(fb)
    try:
        db.commit()
    except IntegrityError:
        # Lost the race: another request with the same client_id committed first.
        # Roll back this failed insert and fall back to the idempotent-retry path.
        db.rollback()
        existing = db.query(Feedback).filter(Feedback.client_id == body.client_id).first()
        if existing:
            response.status_code = 200
            return _serialize(existing)
        raise
    db.refresh(fb)
    return _serialize(fb)
