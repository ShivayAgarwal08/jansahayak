from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.scheme import Scheme, SchemeSource
from app.models.feedback import AuditLog, Feedback
from app.models.user import User
from app.schemas.scheme import SchemeDetailSchema
from app.api.deps import get_current_admin

router = APIRouter(prefix="/admin", tags=["Administrator & Verification Operations"])

class SchemeStatusUpdate(BaseModel):
    verification_status: str  # "verified", "under_review", "deprecated"
    official_portal_url: Optional[str] = None
    notes: Optional[str] = None

@router.get("/schemes", response_model=List[SchemeDetailSchema])
def admin_list_all_schemes(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    return db.query(Scheme).all()

@router.put("/schemes/{scheme_id}/verify", response_model=SchemeDetailSchema)
def admin_update_scheme_verification(
    scheme_id: int,
    update_in: SchemeStatusUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    scheme = db.query(Scheme).filter(Scheme.id == scheme_id).first()
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found.")

    old_status = scheme.verification_status
    scheme.verification_status = update_in.verification_status
    scheme.last_verified_at = datetime.now(timezone.utc)
    if update_in.official_portal_url:
        scheme.official_portal_url = update_in.official_portal_url.strip()

    # Record Audit Log
    audit = AuditLog(
        admin_id=admin.id,
        action="update_scheme_verification",
        target_type="scheme",
        target_id=str(scheme.id),
        details={
            "scheme_slug": scheme.slug,
            "old_status": old_status,
            "new_status": scheme.verification_status,
            "notes": update_in.notes
        }
    )
    db.add(audit)
    db.commit()
    db.refresh(scheme)
    return scheme

@router.get("/audit-logs")
def admin_get_audit_logs(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(50).all()
    return logs

@router.get("/feedbacks")
def admin_get_feedbacks(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    return db.query(Feedback).order_by(Feedback.created_at.desc()).limit(50).all()
