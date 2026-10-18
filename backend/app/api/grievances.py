from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.draft import GrievanceDraft
from app.models.user import User
from app.schemas.draft import GrievanceDraftCreate, GrievanceDraftUpdate, GrievanceDraftResponse
from app.api.deps import get_current_user
from app.services.documents.pdf_generator import generate_grievance_petition_pdf

router = APIRouter(prefix="/grievances", tags=["Grievance Assistant"])

@router.get("", response_model=List[GrievanceDraftResponse])
def list_grievance_drafts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(GrievanceDraft).filter(GrievanceDraft.user_id == current_user.id).all()

@router.post("", response_model=GrievanceDraftResponse, status_code=status.HTTP_201_CREATED)
def create_grievance_draft(
    draft_in: GrievanceDraftCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    draft = GrievanceDraft(
        user_id=current_user.id,
        department=draft_in.department.strip(),
        category=draft_in.category.strip(),
        description=draft_in.description.strip(),
        previous_complaint_ref=draft_in.previous_complaint_ref.strip() if draft_in.previous_complaint_ref else None,
        desired_resolution=draft_in.desired_resolution.strip(),
        applicant_name=draft_in.applicant_name.strip(),
        status="draft"
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft

@router.get("/{draft_id}", response_model=GrievanceDraftResponse)
def get_grievance_draft(
    draft_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    draft = db.query(GrievanceDraft).filter(GrievanceDraft.id == draft_id, GrievanceDraft.user_id == current_user.id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Grievance draft not found or unauthorized.")
    return draft

@router.put("/{draft_id}", response_model=GrievanceDraftResponse)
def update_grievance_draft(
    draft_id: int,
    draft_update: GrievanceDraftUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    draft = db.query(GrievanceDraft).filter(GrievanceDraft.id == draft_id, GrievanceDraft.user_id == current_user.id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Grievance draft not found or unauthorized.")

    if draft_update.department is not None:
        draft.department = draft_update.department.strip()
    if draft_update.category is not None:
        draft.category = draft_update.category.strip()
    if draft_update.description is not None:
        draft.description = draft_update.description.strip()
    if draft_update.previous_complaint_ref is not None:
        draft.previous_complaint_ref = draft_update.previous_complaint_ref.strip()
    if draft_update.desired_resolution is not None:
        draft.desired_resolution = draft_update.desired_resolution.strip()
    if draft_update.applicant_name is not None:
        draft.applicant_name = draft_update.applicant_name.strip()
    if draft_update.status is not None:
        draft.status = draft_update.status

    db.commit()
    db.refresh(draft)
    return draft

@router.delete("/{draft_id}")
def delete_grievance_draft(
    draft_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    draft = db.query(GrievanceDraft).filter(GrievanceDraft.id == draft_id, GrievanceDraft.user_id == current_user.id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Grievance draft not found or unauthorized.")

    db.delete(draft)
    db.commit()
    return {"message": "Grievance draft deleted successfully."}

@router.get("/{draft_id}/pdf")
def download_grievance_pdf(
    draft_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    draft = db.query(GrievanceDraft).filter(GrievanceDraft.id == draft_id, GrievanceDraft.user_id == current_user.id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Grievance draft not found or unauthorized.")

    pdf_bytes = generate_grievance_petition_pdf(
        applicant_name=draft.applicant_name,
        department=draft.department,
        category=draft.category,
        description=draft.description,
        previous_ref=draft.previous_complaint_ref or "",
        desired_resolution=draft.desired_resolution
    )

    filename = f"Grievance_Petition_{draft.id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
