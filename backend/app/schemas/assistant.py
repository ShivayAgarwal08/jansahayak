from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, model_validator

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
    # Canonical agentic fields
    scheme_slug: str
    scheme_name: str
    authority: Optional[str] = "Government of India"
    benefit_summary: Optional[str] = ""
    why_it_fits: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    official_source_url: Optional[str] = None
    official_guideline_url: Optional[str] = None
    eligibility_status: str = "unknown"
    action_label: Optional[str] = "Prepare Application Draft"
    action_url: Optional[str] = None
    action_prefill: Optional[Dict[str, Any]] = None

    # Backward-compatibility alias fields
    slug: Optional[str] = None
    name: Optional[str] = None
    ministry: Optional[str] = None
    official_url: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def sync_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # slug <-> scheme_slug
            if "scheme_slug" not in data and "slug" in data:
                data["scheme_slug"] = data["slug"]
            elif "slug" not in data and "scheme_slug" in data:
                data["slug"] = data["scheme_slug"]

            # name <-> scheme_name
            if "scheme_name" not in data and "name" in data:
                data["scheme_name"] = data["name"]
            elif "name" not in data and "scheme_name" in data:
                data["name"] = data["scheme_name"]

            # ministry <-> authority
            if "authority" not in data and "ministry" in data:
                data["authority"] = data["ministry"]
            elif "ministry" not in data and "authority" in data:
                data["ministry"] = data["authority"]

            # official_url <-> official_source_url
            if "official_source_url" not in data and "official_url" in data:
                data["official_source_url"] = data["official_url"]
            elif "official_url" not in data and "official_source_url" in data:
                data["official_url"] = data["official_source_url"]
        return data

    def model_post_init(self, __context: Any) -> None:
        if self.slug is None:
            self.slug = self.scheme_slug
        if self.name is None:
            self.name = self.scheme_name
        if self.ministry is None and self.authority:
            self.ministry = self.authority
        if self.official_url is None and self.official_source_url:
            self.official_url = self.official_source_url

class AssistantChatResponse(BaseModel):
    # Core response text & citations (backward-compatible)
    answer: str
    citations: List[CitationSchema] = Field(default_factory=list)
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
    extracted_facts: Dict[str, Any] = Field(default_factory=dict)
    unknown_facts: List[str] = Field(default_factory=list)
    clarifying_questions: List[str] = Field(default_factory=list)
    matched_schemes: List[MatchedSchemeSchema] = Field(default_factory=list)
    match_reasons: List[str] = Field(default_factory=list)
    eligibility_status: str = "informational"
    uncertainty_notes: Optional[str] = None
    source_citations: List[CitationSchema] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    application_checklist: List[str] = Field(default_factory=list)
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
