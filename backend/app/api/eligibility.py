from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.scheme import Scheme
from app.models.user import User
from app.models.draft import AssessmentHistory
from app.schemas.eligibility import (
    EligibilityAssessmentRequest,
    EligibilityAssessmentResponse,
    CitizenProfileInput
)
from app.services.eligibility.engine import evaluate_scheme_eligibility
from app.services.documents.pdf_generator import generate_citizen_report_pdf
from app.api.deps import get_current_user_optional, get_current_user

router = APIRouter(prefix="/eligibility", tags=["Eligibility Engine"])

@router.post("/assess", response_model=EligibilityAssessmentResponse)
def assess_eligibility(
    req: EligibilityAssessmentRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    scheme = db.query(Scheme).filter(Scheme.slug == req.scheme_slug).first()
    if not scheme:
        raise HTTPException(status_code=404, detail=f"Scheme '{req.scheme_slug}' not found.")

    profile_dict = req.profile.model_dump(exclude_unset=True)

    # If citizen is logged in and state/phone not explicitly in profile, inherit from profile
    if current_user:
        if "state" not in profile_dict and current_user.state:
            profile_dict["state"] = current_user.state

    result = evaluate_scheme_eligibility(scheme, profile_dict)
    res_dict = result.to_dict()

    # Save to history if citizen is logged in
    if current_user:
        history_item = AssessmentHistory(
            user_id=current_user.id,
            scheme_id=scheme.id,
            inputs_snapshot=profile_dict,
            status=result.status,
            assessment_result=res_dict
        )
        db.add(history_item)
        db.commit()

    return res_dict

@router.get("/history")
def get_assessment_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    records = (
        db.query(AssessmentHistory)
        .filter(AssessmentHistory.user_id == current_user.id)
        .order_by(AssessmentHistory.created_at.desc())
        .limit(20)
        .all()
    )
    history_list = []
    for r in records:
        history_list.append({
            "id": r.id,
            "scheme_id": r.scheme_id,
            "scheme_name": r.scheme.name if r.scheme else "Unknown Scheme",
            "scheme_slug": r.scheme.slug if r.scheme else "",
            "status": r.status,
            "inputs_snapshot": r.inputs_snapshot,
            "assessed_at": r.created_at.isoformat()
        })
    return history_list

@router.post("/download-report")
def download_citizen_report(
    req: EligibilityAssessmentRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    scheme = db.query(Scheme).filter(Scheme.slug == req.scheme_slug).first()
    if not scheme:
        raise HTTPException(status_code=404, detail=f"Scheme '{req.scheme_slug}' not found.")

    profile_dict = req.profile.model_dump(exclude_unset=True)
    citizen_name = current_user.full_name if current_user else "Citizen Applicant"

    result = evaluate_scheme_eligibility(scheme, profile_dict)

    pdf_bytes = generate_citizen_report_pdf(
        citizen_name=citizen_name,
        scheme_name=scheme.name,
        eligibility_status=result.status,
        summary_explanation=result.summary_explanation,
        satisfied_conditions=result.satisfied_conditions,
        unsatisfied_conditions=result.unsatisfied_conditions,
        required_documents=scheme.required_documents or [],
        official_portal_url=scheme.official_portal_url
    )

    filename = f"JanSahayak_Report_{scheme.slug}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
