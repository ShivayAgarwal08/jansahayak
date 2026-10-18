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
    match_reasons: Optional[List[str]] = None
    is_seeded_record: Optional[bool] = True

class AssistantChatRequest(BaseModel):
    query: str
    scheme_slug: Optional[str] = None
    preferred_language: str = "en"
    existing_profile: Optional[Dict[str, Any]] = None

class AssistantChatResponse(BaseModel):
    answer: str
    citations: List[CitationSchema]
    model: str
    is_fallback: bool
    status: str
    ai_provider: Optional[str] = "none"
    fallback_reason: Optional[str] = None
    extracted_profile: Optional[Dict[str, Any]] = None
    missing_criteria: Optional[List[str]] = None
    follow_up_prompt: Optional[str] = None
    eligibility_results: Optional[List[Dict[str, Any]]] = None
    suggested_action: Optional[Dict[str, Any]] = None

class AssistantStatusResponse(BaseModel):
    groq_configured: bool
    groq_model: str
    ai_provider: str
    fallback_available: bool
    status: str
    available_models: Optional[List[str]] = None
    provider_note: Optional[str] = None
