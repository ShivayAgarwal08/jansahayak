from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class CitationSchema(BaseModel):
    citation_id: int
    scheme_slug: str
    scheme_name: str
    title: str
    authority: str
    url: str
    page_number: int

class AssistantChatRequest(BaseModel):
    query: str
    scheme_slug: Optional[str] = None
    preferred_language: str = "en"

class AssistantChatResponse(BaseModel):
    answer: str
    citations: List[CitationSchema]
    model: str
    is_fallback: bool
    status: str
