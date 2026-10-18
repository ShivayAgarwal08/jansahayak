from typing import Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.feedback import Feedback
from app.models.user import User
from app.schemas.feedback import FeedbackCreate, FeedbackResponse
from app.api.deps import get_current_user_optional

router = APIRouter(prefix="/feedback", tags=["Feedback & Error Reports"])

@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def submit_feedback(
    feedback_in: FeedbackCreate,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    feedback = Feedback(
        user_id=current_user.id if current_user else None,
        category=feedback_in.category,
        scheme_slug=feedback_in.scheme_slug,
        message=feedback_in.message.strip()
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback
