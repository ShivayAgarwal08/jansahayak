from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.draft import RtiDraft
from app.models.user import User
from app.schemas.draft import RtiDraftCreate, RtiDraftUpdate, RtiDraftResponse
from app.api.deps import get_current_user
from app.services.documents.pdf_generator import generate_rti_petition_pdf

router = APIRouter(prefix="/rti", tags=["RTI Assistant"])

@router.get("", response_model=List[RtiDraftResponse])
def list_rti_drafts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(RtiDraft).filter(RtiDraft.user_id == current_user.id).all()

@router.post("", response_model=RtiDraftResponse, status_code=status.HTTP_201_CREATED)
def create_rti_draft(
    draft_in: RtiDraftCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    draft = RtiDraft(
        user_id=current_user.id,
        public_authority=draft_in.public_authority.strip(),
        subject=draft_in.subject.strip(),
        information_requested=draft_in.information_requested.strip(),
        time_period=draft_in.time_period.strip() if draft_in.time_period else None,
        applicant_name=draft_in.applicant_name.strip(),
        state=draft_in.state.strip(),
        preferred_language=draft_in.preferred_language,
        status="draft"
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft

@router.get("/{draft_id}", response_model=RtiDraftResponse)
def get_rti_draft(
    draft_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    draft = db.query(RtiDraft).filter(RtiDraft.id == draft_id, RtiDraft.user_id == current_user.id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="RTI draft not found or unauthorized.")
    return draft

@router.put("/{draft_id}", response_model=RtiDraftResponse)
def update_rti_draft(
    draft_id: int,
    draft_update: RtiDraftUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    draft = db.query(RtiDraft).filter(RtiDraft.id == draft_id, RtiDraft.user_id == current_user.id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="RTI draft not found or unauthorized.")

    if draft_update.public_authority is not None:
        draft.public_authority = draft_update.public_authority.strip()
    if draft_update.subject is not None:
        draft.subject = draft_update.subject.strip()
    if draft_update.information_requested is not None:
        draft.information_requested = draft_update.information_requested.strip()
    if draft_update.time_period is not None:
        draft.time_period = draft_update.time_period.strip()
    if draft_update.applicant_name is not None:
        draft.applicant_name = draft_update.applicant_name.strip()
    if draft_update.state is not None:
        draft.state = draft_update.state.strip()
    if draft_update.preferred_language is not None:
        draft.preferred_language = draft_update.preferred_language
    if draft_update.status is not None:
        draft.status = draft_update.status

    db.commit()
    db.refresh(draft)
    return draft

@router.delete("/{draft_id}")
def delete_rti_draft(
    draft_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    draft = db.query(RtiDraft).filter(RtiDraft.id == draft_id, RtiDraft.user_id == current_user.id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="RTI draft not found or unauthorized.")

    db.delete(draft)
    db.commit()
    return {"message": "RTI draft deleted successfully."}

@router.get("/{draft_id}/pdf")
def download_rti_pdf(
    draft_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    draft = db.query(RtiDraft).filter(RtiDraft.id == draft_id, RtiDraft.user_id == current_user.id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="RTI draft not found or unauthorized.")

    pdf_bytes = generate_rti_petition_pdf(
        applicant_name=draft.applicant_name,
        public_authority=draft.public_authority,
        subject=draft.subject,
        information_requested=draft.information_requested,
        time_period=draft.time_period or "",
        state=draft.state
    )

    filename = f"RTI_Petition_{draft.id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
