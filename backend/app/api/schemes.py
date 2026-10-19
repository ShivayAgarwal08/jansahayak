from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.db.session import get_db
from app.models.scheme import Scheme
from app.schemas.scheme import SchemeSummarySchema, SchemeDetailSchema

router = APIRouter(prefix="/schemes", tags=["Schemes"])

@router.get("", response_model=List[SchemeSummarySchema])
def list_schemes(
    category: Optional[str] = None,
    state: Optional[str] = None,
    scope: Optional[str] = None,
    beneficiary: Optional[str] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Scheme).filter(Scheme.verification_status != "deprecated")

    if category and category != "all":
        query = query.filter(Scheme.category == category)

    if scope and scope != "all":
        query = query.filter(Scheme.scope == scope)

    if q:
        search_term = f"%{q.lower().strip()}%"
        query = query.filter(
            or_(
                Scheme.name.ilike(search_term),
                Scheme.name_hi.ilike(search_term),
                Scheme.summary.ilike(search_term),
                Scheme.department.ilike(search_term),
                Scheme.slug.ilike(search_term)
            )
        )

    schemes = query.all()

    # Fallback to RAG phonetic matching if standard substring search yields no results
    if not schemes and q and q.strip():
        try:
            from app.services.rag.retrieval import retrieve_grounded_passages
            passages = retrieve_grounded_passages(q.strip(), db, limit=3)
            matched_slugs = []
            for p in passages:
                if p.scheme_slug and p.scheme_slug not in matched_slugs:
                    matched_slugs.append(p.scheme_slug)
            if matched_slugs:
                fallback_query = db.query(Scheme).filter(
                    Scheme.verification_status != "deprecated",
                    Scheme.slug.in_(matched_slugs)
                )
                if category and category != "all":
                    fallback_query = fallback_query.filter(Scheme.category == category)
                if scope and scope != "all":
                    fallback_query = fallback_query.filter(Scheme.scope == scope)
                fallback_schemes = fallback_query.all()
                # Maintain rank ordering from retrieval
                slug_order = {slug: idx for idx, slug in enumerate(matched_slugs)}
                schemes = sorted(fallback_schemes, key=lambda s: slug_order.get(s.slug, 999))
        except Exception:
            pass

    # In-memory filter for JSON fields if state or beneficiary specified
    if state and state != "ALL":
        schemes = [
            s for s in schemes 
            if "ALL" in (s.applicable_states or []) or state in (s.applicable_states or [])
        ]

    if beneficiary and beneficiary != "all":
        schemes = [
            s for s in schemes
            if any(beneficiary.lower() in b.lower() for b in (s.beneficiary_types or []))
        ]

    return schemes

@router.get("/categories")
def list_categories(db: Session = Depends(get_db)):
    schemes = db.query(Scheme).filter(Scheme.verification_status != "deprecated").all()
    categories_dict = {
        "agriculture": {"id": "agriculture", "name": "Agriculture & Farmers", "count": 0, "icon": "Sprout"},
        "housing": {"id": "housing", "name": "Housing & Shelter", "count": 0, "icon": "Home"},
        "health": {"id": "health", "name": "Health & Medical", "count": 0, "icon": "HeartPulse"},
        "women_children": {"id": "women_children", "name": "Women & Children", "count": 0, "icon": "Users"},
        "social_security": {"id": "social_security", "name": "Social Security & Pension", "count": 0, "icon": "ShieldCheck"},
        "employment": {"id": "employment", "name": "Livelihoods & Self-Employment", "count": 0, "icon": "Briefcase"},
        "education": {"id": "education", "name": "Education & Students", "count": 0, "icon": "GraduationCap"}
    }
    for s in schemes:
        if s.category in categories_dict:
            categories_dict[s.category]["count"] += 1

    return list(categories_dict.values())

@router.get("/compare", response_model=List[SchemeDetailSchema])
def compare_schemes(slugs: str = Query(..., description="Comma-separated list of scheme slugs"), db: Session = Depends(get_db)):
    slug_list = [s.strip() for s in slugs.split(",") if s.strip()]
    if len(slug_list) < 2 or len(slug_list) > 4:
        raise HTTPException(
            status_code=400,
            detail="Please provide between 2 and 4 scheme slugs to compare."
        )

    schemes = db.query(Scheme).filter(Scheme.slug.in_(slug_list)).all()
    if not schemes:
        raise HTTPException(status_code=404, detail="No matching schemes found for comparison.")

    return schemes

@router.get("/{slug}", response_model=SchemeDetailSchema)
def get_scheme_detail(slug: str, db: Session = Depends(get_db)):
    scheme = db.query(Scheme).filter(Scheme.slug == slug).first()
    if not scheme:
        raise HTTPException(status_code=404, detail=f"Scheme '{slug}' not found.")
    return scheme
