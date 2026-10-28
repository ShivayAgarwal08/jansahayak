import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.core.config import settings
from app.db.session import get_db
from app.models.scheme import Scheme
from app.schemas.assistant import (
    AssistantChatRequest,
    AssistantChatResponse,
    AssistantStatusResponse,
    CitationSchema,
    MatchedSchemeSchema
)
from app.services.rag.retrieval import retrieve_grounded_passages
from app.services.ai.groq_service import (
    generate_grounded_answer,
    get_clean_groq_api_key,
    get_clean_groq_model
)
from app.services.ai.profile_extractor import (
    extract_citizen_profile,
    generate_profile_followups,
    detect_query_language,
    clean_speech_text,
    classify_profile_facts
)
from app.services.eligibility.engine import evaluate_scheme_eligibility

router = APIRouter(prefix="/assistant", tags=["Assistant & RAG"])

@router.get("/status", response_model=AssistantStatusResponse)
async def get_assistant_status(check_live: bool = False):
    """
    Check whether Groq AI is securely configured in the environment without exposing credentials.
    Pass ?check_live=true to run a live probe against Groq's models endpoint.
    """
    clean_key = get_clean_groq_api_key()
    clean_model = get_clean_groq_model()
    has_key = bool(clean_key)

    if not has_key:
        return AssistantStatusResponse(
            groq_configured=False,
            groq_model=clean_model,
            ai_provider="none",
            fallback_available=True,
            status="fallback_mode",
            available_models=None,
            provider_note="GROQ_API_KEY is not configured in environment"
        )

    if not check_live:
        return AssistantStatusResponse(
            groq_configured=True,
            groq_model=clean_model,
            ai_provider="groq",
            fallback_available=True,
            status="online",
            available_models=None,
            provider_note="Configured in environment"
        )

    # Live check if requested
    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            resp = await client.get(
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": f"Bearer {clean_key}"}
            )
            if resp.status_code == 200:
                data = resp.json()
                model_ids = [m["id"] for m in data.get("data", [])]
                return AssistantStatusResponse(
                    groq_configured=True,
                    groq_model=clean_model,
                    ai_provider="groq",
                    fallback_available=True,
                    status="online",
                    available_models=model_ids[:15],
                    provider_note=f"Verified with Groq API ({len(model_ids)} models available)"
                )
            else:
                err_text = ""
                try:
                    err_text = resp.json().get("error", {}).get("message", resp.text[:100])
                except Exception:
                    err_text = resp.text[:100]
                safe_err = err_text.replace(clean_key, "[REDACTED]")[:100]
                return AssistantStatusResponse(
                    groq_configured=True,
                    groq_model=clean_model,
                    ai_provider="none",
                    fallback_available=True,
                    status=f"provider_http_{resp.status_code}",
                    available_models=None,
                    provider_note=f"Groq returned HTTP {resp.status_code}: {safe_err}"
                )
    except Exception as e:
        return AssistantStatusResponse(
            groq_configured=True,
            groq_model=clean_model,
            ai_provider="none",
            fallback_available=True,
            status="connection_error",
            available_models=None,
            provider_note=f"Failed to reach Groq API: {type(e).__name__}"
        )

@router.post("/chat", response_model=AssistantChatResponse)
async def chat_with_assistant(
    req: AssistantChatRequest,
    db: Session = Depends(get_db)
):
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    # 1. Conversational fact extraction & privacy-preserving classification
    extracted_profile = extract_citizen_profile(query)
    
    # Merge existing conversation profile if provided (multi-turn memory)
    if req.existing_profile:
        for k, v in req.existing_profile.items():
            if extracted_profile.get(k) is None and v is not None:
                extracted_profile[k] = v

    # Classify facts strictly into confirmed, inferred, unknown, contradictory
    fact_classification = classify_profile_facts(extracted_profile, query)

    # Detect language of the query and determine response language
    detected_lang = detect_query_language(query, req.preferred_language or "en")
    response_lang = "hi" if (detected_lang in ["hi", "hi-Latn"] or (req.preferred_language and req.preferred_language.startswith("hi"))) else "en"

    # 2. Retrieve top verified passages using stopword filtering & domain intent matching
    # Multi-turn contextualization: incorporate confirmed profile facts into retrieval
    search_query = query
    context_cues = []
    if req.existing_profile:
        if req.existing_profile.get("occupation"):
            context_cues.append(str(req.existing_profile["occupation"]))
        if req.existing_profile.get("housing_type"):
            context_cues.append(str(req.existing_profile["housing_type"]))
    if extracted_profile.get("occupation"):
        context_cues.append(str(extracted_profile["occupation"]))
    if extracted_profile.get("owns_cultivable_land"):
        context_cues.append("land farmer")
    if context_cues:
        search_query = f"{query} {' '.join(context_cues)}"

    passages = retrieve_grounded_passages(
        query=search_query,
        db=db,
        limit=4,
        target_scheme_slug=req.scheme_slug
    )

    # 3. Identify relevant top schemes and evaluate deterministic eligibility
    top_scheme_slugs = list(dict.fromkeys([p.scheme_slug for p in passages]))[:3]
    
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

    # 6. Generate grounded answer via Groq LLM (or deterministic fallback if unconfigured / error)
    result = await generate_grounded_answer(
        query=query,
        passages=passages,
        preferred_language=req.preferred_language or "en",
        detected_language=detected_lang,
        response_language=response_lang,
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
            page_number=c["page_number"],
            match_reasons=c.get("match_reasons"),
            is_seeded_record=c.get("is_seeded_record", True),
            document_reference=c.get("document_reference"),
            similarity_score=c.get("similarity_score")
        )
        for c in result.get("citations", [])
    ]

    # Build structured matched schemes list (top 3)
    matched_schemes: List[MatchedSchemeSchema] = []
    match_reasons_list: List[str] = []
    for s_obj in top_schemes_objs[:3]:
        ev = next((e for e in eligibility_evaluations if e["scheme_slug"] == s_obj.slug), None)
        status_val = ev["status"] if ev else "unknown"

        # Why it fits explanation
        reasons = []
        if ev and ev.get("satisfied_conditions"):
            reasons.extend([f"{sc['criterion']}: {sc.get('citizen_value', 'Met')}" for sc in ev["satisfied_conditions"]])
        
        why_str = f"Matches your profile: {'; '.join(reasons)}" if reasons else f"Identified as highly relevant for {s_obj.name} based on official scheme guidelines."
        match_reasons_list.append(why_str)
        why_list = reasons if reasons else [f"Identified based on eligibility criteria for {s_obj.name}."]

        # Missing information
        missing_items = [
            uc.get("prompt", uc["criterion"])
            for uc in (ev.get("unknown_conditions", []) if ev else [])
        ][:3]

        matched_schemes.append(
            MatchedSchemeSchema(
                scheme_slug=s_obj.slug,
                scheme_name=s_obj.name,
                slug=s_obj.slug,
                name=s_obj.name,
                authority=s_obj.department or "Government of India",
                ministry=s_obj.department,
                benefit_summary=s_obj.benefits_summary or s_obj.summary or "",
                eligibility_status=status_val,
                why_it_fits=why_list,
                missing_information=missing_items if missing_items else [],
                official_source_url=s_obj.official_portal_url or "https://india.gov.in",
                official_url=s_obj.official_portal_url,
                action_label="Prepare Application Draft",
                action_url=f"/applications?slug={s_obj.slug}",
                action_prefill=extracted_profile
            )
        )

    # Primary overall eligibility status
    primary_status = eligibility_evaluations[0]["status"] if eligibility_evaluations else "unknown"

    # Document checklist for primary matched scheme
    primary_checklist: List[str] = []
    if top_schemes_objs and top_schemes_objs[0].required_documents:
        for doc in top_schemes_objs[0].required_documents:
            doc_name = doc.get("name") if isinstance(doc, dict) else str(doc)
            primary_checklist.append(doc_name)

    # Concrete next steps
    next_steps_list = []
    if primary_status == "eligible":
        next_steps_list = [
            "Use JanSahayak's Application Preparation tool to assemble your verified draft.",
            f"Collect the {len(primary_checklist)} required documents from the checklist.",
            f"Submit directly on the official portal ({top_schemes_objs[0].official_portal_url if top_schemes_objs else 'india.gov.in'}) or visit a CSC."
        ]
    elif primary_status == "possibly_eligible":
        next_steps_list = [
            "Provide the missing details highlighted in the follow-up prompt to confirm eligibility.",
            "Verify whether you have eligible alternative documentation for any pending criteria.",
            "Review official guidelines on the portal link provided before applying."
        ]
    else:
        next_steps_list = [
            "Review the specific unsatisfied criteria to understand why qualification was not met.",
            "Explore other welfare schemes in the catalogue matching your current profile.",
            "If you believe government records are inaccurate, consider submitting an inquiry or grievance."
        ]

    # Uncertainty disclosure
    uncertainty_statement = (
        "JanSahayak provides rule-based informational assistance and does not guarantee official sanction; "
        "final approval rests exclusively with the competent government department."
    )

    # Clean spoken audio text suitable for Web Speech API and Bhashini
    answer_raw = result.get("answer", "")
    spoken_audio_text = clean_speech_text(answer_raw)
    if len(spoken_audio_text) > 400:
        # Provide concise spoken summary
        summary_intro = f"JanSahayak identified {len(matched_schemes)} relevant scheme(s): " + ", ".join([m.name for m in matched_schemes]) + ". "
        spoken_audio_text = summary_intro + spoken_audio_text[:350].rsplit(".", 1)[0] + "."

    return AssistantChatResponse(
        # Agentic structured fields
        detected_language=detected_lang,
        response_language=response_lang,
        extracted_facts=fact_classification,
        unknown_facts=fact_classification.get("unknown", []),
        clarifying_questions=missing_criteria[:2] if missing_criteria else [],
        matched_schemes=matched_schemes,
        match_reasons=match_reasons_list,
        eligibility_status=primary_status,
        uncertainty_notes=uncertainty_statement,
        source_citations=citations,
        next_steps=next_steps_list,
        application_checklist=primary_checklist,
        response_text=answer_raw,
        speech_text=spoken_audio_text,
        # Legacy fields for backward compatibility
        answer=answer_raw,
        citations=citations,
        model=result.get("model", "rule-grounded-deterministic-fallback"),
        is_fallback=result.get("is_fallback", True),
        status=result.get("status", "fallback_grounded"),
        ai_provider=result.get("ai_provider", "none"),
        fallback_reason=result.get("fallback_reason"),
        extracted_profile=extracted_profile,
        missing_criteria=missing_criteria,
        follow_up_prompt=follow_up_prompt,
        eligibility_results=eligibility_evaluations,
        suggested_action=suggested_action
    )

@router.get("/documents")
def list_knowledge_documents(db: Session = Depends(get_db)):
    """
    List all ingested official government scheme guidelines and knowledge documents.
    """
    from app.models.document import KnowledgeDocument
    docs = db.query(KnowledgeDocument).all()
    return [
        {
            "id": d.id,
            "scheme_id": d.scheme_id,
            "scheme_slug": d.scheme.slug if d.scheme else None,
            "scheme_name": d.scheme.name if d.scheme else None,
            "title": d.title,
            "source_url": d.source_url,
            "authority": d.authority,
            "document_reference": d.document_reference,
            "doc_type": d.doc_type,
            "ocr_status": d.ocr_status,
            "total_pages": d.total_pages,
            "chunks_count": len(d.chunks),
            "retrieval_date": d.retrieval_date.isoformat() if hasattr(d.retrieval_date, "isoformat") else str(d.retrieval_date)
        }
        for d in docs
    ]

@router.get("/search-documents")
def search_documents_endpoint(
    query: str,
    db: Session = Depends(get_db),
    limit: int = 5
):
    """
    Search official document passages using hybrid semantic vector and keyword retrieval.
    """
    from app.services.rag.retrieval import search_official_documents
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    return search_official_documents(query=query.strip(), db=db, limit=limit)
