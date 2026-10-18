from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.scheme import Scheme
from app.models.draft import SavedScheme, ApplicationDraft, RtiDraft, GrievanceDraft, AssessmentHistory
from app.api.deps import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Citizen Dashboard"])

@router.get("/stats")
def get_citizen_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    saved_count = db.query(SavedScheme).filter(SavedScheme.user_id == current_user.id).count()
    app_drafts_count = db.query(ApplicationDraft).filter(ApplicationDraft.user_id == current_user.id).count()
    rti_count = db.query(RtiDraft).filter(RtiDraft.user_id == current_user.id).count()
    grievance_count = db.query(GrievanceDraft).filter(GrievanceDraft.user_id == current_user.id).count()
    assessments_count = db.query(AssessmentHistory).filter(AssessmentHistory.user_id == current_user.id).count()

    # Recent assessments
    recent_assessments = (
        db.query(AssessmentHistory)
        .filter(AssessmentHistory.user_id == current_user.id)
        .order_by(AssessmentHistory.created_at.desc())
        .limit(5)
        .all()
    )
    assessments_data = []
    for a in recent_assessments:
        assessments_data.append({
            "id": a.id,
            "scheme_name": a.scheme.name if a.scheme else "Unknown Scheme",
            "scheme_slug": a.scheme.slug if a.scheme else "",
            "status": a.status,
            "assessed_at": a.created_at.isoformat()
        })

    return {
        "saved_schemes_count": saved_count,
        "application_drafts_count": app_drafts_count,
        "rti_drafts_count": rti_count,
        "grievance_drafts_count": grievance_count,
        "assessments_count": assessments_count,
        "recent_assessments": assessments_data
    }

@router.get("/saved-schemes")
def list_saved_schemes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    saved = db.query(SavedScheme).filter(SavedScheme.user_id == current_user.id).all()
    result = []
    for item in saved:
        s = item.scheme
        if s:
            result.append({
                "saved_id": item.id,
                "scheme_id": s.id,
                "slug": s.slug,
                "name": s.name,
                "name_hi": s.name_hi,
                "summary": s.summary,
                "category": s.category,
                "official_portal_url": s.official_portal_url,
                "saved_at": item.created_at.isoformat()
            })
    return result

@router.post("/saved-schemes/{scheme_id}")
def toggle_save_scheme(
    scheme_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    scheme = db.query(Scheme).filter(Scheme.id == scheme_id).first()
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found.")

    existing = (
        db.query(SavedScheme)
        .filter(SavedScheme.user_id == current_user.id, SavedScheme.scheme_id == scheme_id)
        .first()
    )
    if existing:
        db.delete(existing)
        db.commit()
        return {"saved": False, "message": "Scheme removed from saved list."}
    else:
        new_save = SavedScheme(user_id=current_user.id, scheme_id=scheme_id)
        db.add(new_save)
        db.commit()
        return {"saved": True, "message": "Scheme saved to your citizen dashboard."}
