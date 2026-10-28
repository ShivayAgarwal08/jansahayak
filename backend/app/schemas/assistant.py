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
    document_reference: Optional[str] = None
    similarity_score: Optional[float] = None

class AssistantChatRequest(BaseModel):
    query: str
    scheme_slug: Optional[str] = None
    preferred_language: str = "en"
    existing_profile: Optional[Dict[str, Any]] = None

class MatchedSchemeSchema(BaseModel):
    scheme_slug: str
    scheme_name: str
    slug: Optional[str] = None
    name: Optional[str] = None
    authority: Optional[str] = "Government of India"
    ministry: Optional[str] = None
    benefit_summary: Optional[str] = ""
    why_it_fits: List[str] = []
    missing_information: Optional[List[str]] = []
    official_source_url: Optional[str] = "https://india.gov.in"
    official_url: Optional[str] = None
    official_guideline_url: Optional[str] = None
    eligibility_status: str = "unknown"
    action_label: Optional[str] = "Prepare Application Draft"
    action_url: Optional[str] = None
    action_prefill: Optional[Dict[str, Any]] = None

class AssistantChatResponse(BaseModel):
    # Core response text & citations (backward-compatible)
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

    # Agentic structured fields (Phase 4 Specification)
    detected_language: str = "en"
    response_language: str = "en"
    extracted_facts: Dict[str, Any] = {}
    unknown_facts: List[str] = []
    clarifying_questions: List[str] = []
    matched_schemes: List[MatchedSchemeSchema] = []
    match_reasons: List[str] = []
    eligibility_status: str = "informational"
    uncertainty_notes: Optional[str] = None
    source_citations: List[CitationSchema] = []
    next_steps: List[str] = []
    application_checklist: List[str] = []
    response_text: str = ""
    speech_text: str = ""

class AssistantStatusResponse(BaseModel):
    groq_configured: bool
    groq_model: str
    ai_provider: str
    fallback_available: bool
    status: str
    available_models: Optional[List[str]] = None
    provider_note: Optional[str] = None
