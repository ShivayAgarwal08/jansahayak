from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.db.session import get_db
from app.models.scheme import Scheme
from app.schemas.assistant import AssistantChatRequest, AssistantChatResponse, CitationSchema
from app.services.rag.retrieval import retrieve_grounded_passages
from app.services.ai.groq_service import generate_grounded_answer
from app.services.ai.profile_extractor import extract_citizen_profile, generate_profile_followups
from app.services.eligibility.engine import evaluate_scheme_eligibility

router = APIRouter(prefix="/assistant", tags=["Assistant & RAG"])

@router.post("/chat", response_model=AssistantChatResponse)
async def chat_with_assistant(
    req: AssistantChatRequest,
    db: Session = Depends(get_db)
):
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    # 1. Conversational fact extraction
    extracted_profile = extract_citizen_profile(query)
    
    # Merge existing conversation profile if provided (multi-turn memory)
    if req.existing_profile:
        for k, v in req.existing_profile.items():
            if extracted_profile.get(k) is None and v is not None:
                extracted_profile[k] = v

    # 2. Retrieve top verified passages using stopword filtering & domain intent matching
    passages = retrieve_grounded_passages(
        query=query,
        db=db,
        limit=4,
        target_scheme_slug=req.scheme_slug
    )

    # 3. Identify relevant top schemes and evaluate deterministic eligibility
    top_scheme_slugs = list(dict.fromkeys([p.scheme_slug for p in passages]))[:2]
    
    eligibility_evaluations: List[Dict[str, Any]] = []
    top_schemes_objs: List[Scheme] = []
    if top_scheme_slugs:
        schemes_in_db = db.query(Scheme).filter(Scheme.slug.in_(top_scheme_slugs)).all()
        schemes_map = {s.slug: s for s in schemes_in_db}
        for slug in top_scheme_slugs:
            if slug in schemes_map:
                s_obj = schemes_map[slug]
                top_schemes_objs.append(s_obj)
                eval_res = evaluate_scheme_eligibility(s_obj, extracted_profile)
                eligibility_evaluations.append(eval_res.to_dict())

    # 4. Generate missing criteria & focused follow-up prompt
    missing_criteria, follow_up_prompt = generate_profile_followups(extracted_profile, top_scheme_slugs)

    # 5. Connect to application drafts: construct suggested prefill action if eligible or potentially eligible
    suggested_action = None
    if eligibility_evaluations:
        primary_eval = eligibility_evaluations[0]
        if primary_eval["status"] in ["eligible", "possibly_eligible"]:
            suggested_action = {
                "action": "prepare_application",
                "scheme_slug": primary_eval["scheme_slug"],
                "scheme_name": primary_eval["scheme_name"],
                "status": primary_eval["status"],
                "prefill_data": {
                    "state": extracted_profile.get("state"),
                    "district": extracted_profile.get("district"),
                    "occupation": extracted_profile.get("occupation"),
                    "annual_income": extracted_profile.get("annual_income"),
                    "landholding_raw": extracted_profile.get("landholding_raw"),
                    "landholding_acres": extracted_profile.get("landholding_acres"),
                    "housing_type": extracted_profile.get("housing_type"),
                    "area_type": extracted_profile.get("area_type")
                }
            }

    # 6. Generate grounded answer via Groq LLM (or deterministic fallback if unconfigured)
    result = await generate_grounded_answer(
        query=query,
        passages=passages,
        preferred_language=req.preferred_language,
        extracted_profile=extracted_profile,
        eligibility_evaluations=eligibility_evaluations,
        follow_up_prompt=follow_up_prompt
    )

    # Convert citations to CitationSchema
    citations = [
        CitationSchema(
            citation_id=c["citation_id"],
            scheme_slug=c["scheme_slug"],
            scheme_name=c["scheme_name"],
            title=c["title"],
            authority=c["authority"],
            url=c["url"],
            page_number=c["page_number"]
        )
        for c in result.get("citations", [])
    ]

    return AssistantChatResponse(
        answer=result.get("answer", ""),
        citations=citations,
        model=result.get("model", "rule-grounded-deterministic-fallback"),
        is_fallback=result.get("is_fallback", True),
        status=result.get("status", "fallback_grounded"),
        ai_provider=result.get("ai_provider", "none"),
        extracted_profile=extracted_profile,
        missing_criteria=missing_criteria,
        follow_up_prompt=follow_up_prompt,
        eligibility_results=eligibility_evaluations,
        suggested_action=suggested_action
    )
