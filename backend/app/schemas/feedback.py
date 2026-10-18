from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class FeedbackCreate(BaseModel):
    category: str
    scheme_slug: Optional[str] = None
    message: str

class FeedbackResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    category: str
    scheme_slug: Optional[str] = None
    message: str
    created_at: datetime

    class Config:
        from_attributes = True
