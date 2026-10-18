from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.draft import ApplicationDraft
from app.models.scheme import Scheme
from app.models.user import User
from app.schemas.draft import (
    ApplicationDraftCreate,
    ApplicationDraftUpdate,
    ApplicationDraftResponse
)
from app.api.deps import get_current_user
from app.services.documents.pdf_generator import generate_citizen_report_pdf

router = APIRouter(prefix="/applications", tags=["Application Preparation"])

@router.get("", response_model=List[ApplicationDraftResponse])
def list_application_drafts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(ApplicationDraft).filter(ApplicationDraft.user_id == current_user.id).all()

@router.post("", response_model=ApplicationDraftResponse, status_code=status.HTTP_201_CREATED)
def create_application_draft(
    draft_in: ApplicationDraftCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    scheme = db.query(Scheme).filter(Scheme.id == draft_in.scheme_id).first()
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found.")

    draft = ApplicationDraft(
        user_id=current_user.id,
        scheme_id=scheme.id,
        title=draft_in.title.strip(),
        applicant_details=draft_in.applicant_details,
        checklist_state=draft_in.checklist_state,
        status="draft",
        notes=draft_in.notes
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft

@router.get("/{draft_id}", response_model=ApplicationDraftResponse)
def get_application_draft(
    draft_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    draft = (
        db.query(ApplicationDraft)
        .filter(ApplicationDraft.id == draft_id, ApplicationDraft.user_id == current_user.id)
        .first()
    )
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found or access unauthorized.")
    return draft

@router.put("/{draft_id}", response_model=ApplicationDraftResponse)
def update_application_draft(
    draft_id: int,
    draft_update: ApplicationDraftUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    draft = (
        db.query(ApplicationDraft)
        .filter(ApplicationDraft.id == draft_id, ApplicationDraft.user_id == current_user.id)
        .first()
    )
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found or access unauthorized.")

    if draft_update.title is not None:
        draft.title = draft_update.title.strip()
    if draft_update.applicant_details is not None:
        draft.applicant_details = draft_update.applicant_details
    if draft_update.checklist_state is not None:
        draft.checklist_state = draft_update.checklist_state
    if draft_update.status is not None:
        draft.status = draft_update.status
    if draft_update.notes is not None:
        draft.notes = draft_update.notes

    db.commit()
    db.refresh(draft)
    return draft

@router.delete("/{draft_id}")
def delete_application_draft(
    draft_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    draft = (
        db.query(ApplicationDraft)
        .filter(ApplicationDraft.id == draft_id, ApplicationDraft.user_id == current_user.id)
        .first()
    )
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found or access unauthorized.")

    db.delete(draft)
    db.commit()
    return {"message": "Draft deleted successfully."}

@router.get("/{draft_id}/pdf")
def download_application_pdf(
    draft_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    draft = (
        db.query(ApplicationDraft)
        .filter(ApplicationDraft.id == draft_id, ApplicationDraft.user_id == current_user.id)
        .first()
    )
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found or access unauthorized.")

    scheme = draft.scheme
    applicant_name = draft.applicant_details.get("full_name") or current_user.full_name

    pdf_bytes = generate_citizen_report_pdf(
        citizen_name=applicant_name,
        scheme_name=scheme.name,
        eligibility_status="Prepared Draft",
        summary_explanation=f"Application preparation checklist for {scheme.name}. Notes: {draft.notes or 'None'}",
        satisfied_conditions=[],
        unsatisfied_conditions=[],
        required_documents=scheme.required_documents or [],
        official_portal_url=scheme.official_portal_url
    )

    filename = f"Application_Prep_{draft.id}_{scheme.slug}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
