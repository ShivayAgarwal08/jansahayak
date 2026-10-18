from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class CitizenProfileInput(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    occupation: Optional[str] = None
    annual_income: Optional[float] = None
    owns_cultivable_land: Optional[bool] = None
    landholding_acres: Optional[float] = None
    housing_type: Optional[str] = None  # "pucca", "kutcha", "houseless"
    area_type: Optional[str] = None  # "rural", "urban"
    is_bpl: Optional[bool] = None
    is_govt_employee: Optional[bool] = None
    pays_income_tax: Optional[bool] = None
    is_pregnant_or_lactating: Optional[bool] = None
    has_girl_child_under_10: Optional[bool] = None
    girl_child_age: Optional[int] = None
    is_street_vendor: Optional[bool] = None
    is_traditional_artisan: Optional[bool] = None

class EligibilityAssessmentRequest(BaseModel):
    scheme_slug: str
    profile: CitizenProfileInput

class ConditionEvaluation(BaseModel):
    criterion: str
    official_rule: Optional[str] = None
    citizen_value: Optional[Any] = None
    reason: Optional[str] = None

class UnknownCondition(BaseModel):
    criterion: str
    prompt: str

class OfficialSourceRef(BaseModel):
    title: str
    url: str
    authority: Optional[str] = None

class EligibilityAssessmentResponse(BaseModel):
    scheme_id: int
    scheme_slug: str
    scheme_name: str
    status: str  # "eligible", "possibly_eligible", "ineligible"
    summary_explanation: str
    satisfied_conditions: List[Dict[str, Any]]
    unsatisfied_conditions: List[Dict[str, Any]]
    unknown_conditions: List[Dict[str, Any]]
    applicable_exclusions: List[str]
    official_sources: List[Dict[str, Any]]
    next_steps: List[str]
    assessed_at: str
    disclaimer: str
