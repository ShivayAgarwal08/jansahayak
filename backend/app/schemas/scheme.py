from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class SchemeSourceSchema(BaseModel):
    id: int
    source_title: str
    source_url: str
    issuing_authority: str
    document_reference: Optional[str] = None
    verified_at: datetime

    class Config:
        from_attributes = True

class SchemeSummarySchema(BaseModel):
    id: int
    slug: str
    name: str
    name_hi: Optional[str] = None
    summary: str
    summary_hi: Optional[str] = None
    department: str
    scope: str
    applicable_states: List[str]
    category: str
    beneficiary_types: List[str]
    benefits_summary: str
    official_portal_url: str
    verification_status: str
    last_verified_at: datetime

    class Config:
        from_attributes = True

class SchemeDetailSchema(SchemeSummarySchema):
    eligibility_rules: Dict[str, Any]
    exclusions: List[str]
    required_documents: List[Dict[str, Any]]
    application_steps: List[str]
    sources: List[SchemeSourceSchema] = []

    class Config:
        from_attributes = True

class SchemeComparisonSchema(BaseModel):
    schemes: List[SchemeDetailSchema]
