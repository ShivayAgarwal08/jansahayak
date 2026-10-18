from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel

# Application Draft Schemas
class ApplicationDraftCreate(BaseModel):
    scheme_id: int
    title: str
    applicant_details: Dict[str, Any] = {}
    checklist_state: Dict[str, Any] = {}
    notes: Optional[str] = None

class ApplicationDraftUpdate(BaseModel):
    title: Optional[str] = None
    applicant_details: Optional[Dict[str, Any]] = None
    checklist_state: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class ApplicationDraftResponse(BaseModel):
    id: int
    user_id: int
    scheme_id: int
    title: str
    applicant_details: Dict[str, Any]
    checklist_state: Dict[str, Any]
    status: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# RTI Draft Schemas
class RtiDraftCreate(BaseModel):
    public_authority: str
    subject: str
    information_requested: str
    time_period: Optional[str] = None
    applicant_name: str
    state: str
    preferred_language: str = "en"

class RtiDraftUpdate(BaseModel):
    public_authority: Optional[str] = None
    subject: Optional[str] = None
    information_requested: Optional[str] = None
    time_period: Optional[str] = None
    applicant_name: Optional[str] = None
    state: Optional[str] = None
    preferred_language: Optional[str] = None
    status: Optional[str] = None

class RtiDraftResponse(BaseModel):
    id: int
    user_id: int
    public_authority: str
    subject: str
    information_requested: str
    time_period: Optional[str] = None
    applicant_name: str
    state: str
    preferred_language: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Grievance Draft Schemas
class GrievanceDraftCreate(BaseModel):
    department: str
    category: str
    description: str
    previous_complaint_ref: Optional[str] = None
    desired_resolution: str
    applicant_name: str

class GrievanceDraftUpdate(BaseModel):
    department: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    previous_complaint_ref: Optional[str] = None
    desired_resolution: Optional[str] = None
    applicant_name: Optional[str] = None
    status: Optional[str] = None

class GrievanceDraftResponse(BaseModel):
    id: int
    user_id: int
    department: str
    category: str
    description: str
    previous_complaint_ref: Optional[str] = None
    desired_resolution: str
    applicant_name: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
