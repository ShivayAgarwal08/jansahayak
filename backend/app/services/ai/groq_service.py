import httpx
import logging
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.services.rag.retrieval import Passage

logger = logging.getLogger("jansahayak.ai.groq")

SYSTEM_PROMPT = """You are JanSahayak's Citizen Welfare AI Assistant, an empathetic, accurate, and trustworthy guide for Indian government welfare schemes.

CRITICAL CONSTRAINTS:
1. Base your answer EXCLUSIVELY on the verified government evidence provided inside <VERIFIED_GOVERNMENT_EVIDENCE> and deterministic evaluation inside <DETERMINISTIC_ELIGIBILITY_EVALUATION>.
2. DO NOT hallucinate, invent schemes, eligibility criteria, subsidy amounts, deadlines, or application procedures.
3. If deterministic eligibility results are provided, report them faithfully. Do not alter 'eligible', 'possibly_eligible', or 'ineligible' conclusions.
4. If essential citizen details are missing, include the suggested follow-up question so the citizen can clarify.
5. Always mention the issuing department, the official portal URL, and cite [Passage N] tags with page numbers if available.
6. Distinguish sourced facts, missing information, and uncertainty. DO NOT mark someone eligible merely because their income or occupation sounds suitable.
7. If no adequate official evidence is available in <VERIFIED_GOVERNMENT_EVIDENCE>, clearly indicate that official evidence is insufficient and direct the citizen to official portals.
8. Provide clear, empathetic, citizen-friendly explanations in simple language.
"""

def get_clean_groq_api_key() -> Optional[str]:
    raw = settings.GROQ_API_KEY
    if not raw or not raw.strip():
        return None
    cleaned = raw.strip().strip('"').strip("'")
    if cleaned.lower().startswith("bearer "):
        cleaned = cleaned[7:].strip()
    return cleaned if cleaned else None

def get_clean_groq_model() -> str:
    raw = settings.GROQ_MODEL
    if not raw or not raw.strip():
        return "llama-3.3-70b-versatile"
    cleaned = raw.strip().strip('"').strip("'")
    return cleaned if cleaned else "llama-3.3-70b-versatile"

def extract_safe_error_message(response: Any, api_key: Optional[str]) -> str:
    err_text = ""
    try:
        json_fn = getattr(response, "json", None)
        if callable(json_fn):
            raw_data = json_fn()
            if hasattr(raw_data, "close") and callable(raw_data.close):
                raw_data.close()
                data = {}
            else:
                data = raw_data
            if isinstance(data, dict):
                err_text = data.get("error", {}).get("message", "")
    except Exception:
        pass
    if not err_text:
        raw_text = getattr(response, "text", "")
        err_text = raw_text if isinstance(raw_text, str) else ""
    if api_key and err_text:
        err_text = err_text.replace(api_key, "[REDACTED]")
    return err_text[:120].strip()

async def generate_grounded_answer(
    query: str,
    passages: List[Passage],
    preferred_language: str = "en",
    extracted_profile: Optional[Dict[str, Any]] = None,
    eligibility_evaluations: Optional[List[Dict[str, Any]]] = None,
    follow_up_prompt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate an answer grounded strictly in verified passages and deterministic eligibility results.
    Uses Groq API (llama-3.3-70b-versatile) when credentials are configured.
    Falls back honestly and safely to deterministic rule synthesis when AI is unavailable or encounters errors.
    Never exposes API credentials in logs, exceptions, or responses.
    """
    evidence_blocks = []
    citations = []
    
    for idx, p in enumerate(passages):
        doc_ref = f"Document Reference: {p.document_reference}\n" if getattr(p, "document_reference", None) else ""
        corpus_type = "Official Guidelines Document" if not getattr(p, "is_seeded_record", True) else "Verified Scheme Definition"
        page_str = f"Page {p.page_number}" if getattr(p, "page_number", 1) > 0 else "Guidelines Overview"
        evidence_blocks.append(
            f"[Passage {idx+1} ({page_str})]\n"
            f"Scheme: {p.scheme_name}\n"
            f"Document Title: {p.title}\n"
            f"Issuing Authority: {p.authority}\n"
            f"{doc_ref}"
            f"Official URL: {p.url}\n"
            f"Source Record Type: {corpus_type}\n"
            f"Match Reasons: {', '.join(p.match_reasons) if p.match_reasons else 'General Catalog'}\n"
            f"Official Text Content:\n{p.content}\n"
        )
        citations.append({
            "citation_id": idx + 1,
            "scheme_slug": p.scheme_slug,
            "scheme_name": p.scheme_name,
            "title": p.title,
            "authority": p.authority,
            "url": p.url,
            "page_number": p.page_number,
            "match_reasons": p.match_reasons,
            "is_seeded_record": p.is_seeded_record,
            "document_reference": getattr(p, "document_reference", None),
            "similarity_score": getattr(p, "similarity_score", None)
        })
        
    evidence_text = "\n---\n".join(evidence_blocks) if evidence_blocks else "NO ADEQUATE OFFICIAL EVIDENCE FOUND."

    # Format profile block for context
    profile_summary = []
    if extracted_profile:
        for k, v in extracted_profile.items():
            if v is not None and v != {}:
                profile_summary.append(f"- {k.replace('_', ' ').title()}: {v}")
    profile_text = "\n".join(profile_summary) if profile_summary else "No confirmed facts yet."

    # Format deterministic eligibility evaluation block
    eval_summary = []
    if eligibility_evaluations:
        for ev in eligibility_evaluations:
            status_label = ev.get("status", "unknown").upper()
            eval_summary.append(
                f"- Scheme: {ev.get('scheme_name')} ({ev.get('scheme_slug')})\n"
                f"  Status: {status_label}\n"
                f"  Summary: {ev.get('summary_explanation')}\n"
                f"  Satisfied: {len(ev.get('satisfied_conditions', []))} conditions\n"
                f"  Missing/Unknown: {len(ev.get('unknown_conditions', []))} conditions\n"
                f"  Unsatisfied: {len(ev.get('unsatisfied_conditions', []))} conditions"
            )
    eval_text = "\n".join(eval_summary) if eval_summary else "No scheme evaluation completed."

    user_message = (
        f"<VERIFIED_GOVERNMENT_EVIDENCE>\n"
        f"{evidence_text}\n"
        f"</VERIFIED_GOVERNMENT_EVIDENCE>\n\n"
        f"<CITIZEN_EXTRACTED_PROFILE>\n"
        f"{profile_text}\n"
        f"</CITIZEN_EXTRACTED_PROFILE>\n\n"
        f"<DETERMINISTIC_ELIGIBILITY_EVALUATION>\n"
        f"{eval_text}\n"
        f"</DETERMINISTIC_ELIGIBILITY_EVALUATION>\n\n"
        f"Citizen Query: {query}\n"
        f"Preferred Language: {preferred_language}\n"
        + (f"Suggested Follow-Up: {follow_up_prompt}\n" if follow_up_prompt else "")
        + "Provide a grounded, citizen-first answer based strictly on the above evidence."
    )

    fallback_reason = "unconfigured"
    safe_err = ""

    # 1. Attempt Groq API if configured
    clean_key = get_clean_groq_api_key()
    configured_model = get_clean_groq_model()

    if clean_key:
        candidate_models = [configured_model]
        for fb in [
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "qwen/qwen3.8-27b",
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant"
        ]:
            if fb not in candidate_models:
                candidate_models.append(fb)

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                for model_candidate in candidate_models:
                    response = await client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {clean_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": model_candidate,
                            "messages": [
                                {"role": "system", "content": SYSTEM_PROMPT},
                                {"role": "user", "content": user_message}
                            ],
                            "temperature": 0.2,
                            "max_tokens": 900
                        }
                    )
                    if response.status_code == 200:
                        data = response.json()
                        answer_text = data["choices"][0]["message"]["content"]
                        # Strip thinking tags if returned by reasoning models
                        if "<think>" in answer_text and "</think>" in answer_text:
                            parts = answer_text.split("</think>", 1)
                            if len(parts) > 1 and parts[1].strip():
                                answer_text = parts[1].strip()
                        return {
                            "answer": answer_text,
                            "citations": citations,
                            "model": model_candidate,
                            "is_fallback": False,
                            "status": "success",
                            "ai_provider": "groq",
                            "fallback_reason": None
                        }
                    elif response.status_code in [400, 404]:
                        safe_err = extract_safe_error_message(response, clean_key)
                        logger.warning(
                            f"Groq API returned HTTP {response.status_code} for model '{model_candidate}': {safe_err}. Trying fallback candidate..."
                        )
                        fallback_reason = f"provider_http_{response.status_code}"
                        continue
                    else:
                        fallback_reason = f"provider_http_{response.status_code}"
                        safe_err = extract_safe_error_message(response, clean_key)
                        logger.warning(
                            f"Groq API returned HTTP {response.status_code}: {safe_err}. Falling back to deterministic rule synthesis."
                        )
                        break
        except httpx.TimeoutException:
            fallback_reason = "provider_timeout"
            logger.warning("Groq API request timed out after 20.0s. Falling back to deterministic rule synthesis.")
        except httpx.ConnectError:
            fallback_reason = "provider_connect_error"
            logger.warning("Could not connect to Groq API. Falling back to deterministic rule synthesis.")
        except Exception as e:
            fallback_reason = f"provider_exception_{type(e).__name__}"
            logger.warning(f"Groq API call encountered {type(e).__name__}: {str(e)[:150]}. Falling back to deterministic rule synthesis.")

    # 2. Deterministic Non-Hallucinatory Fallback
    # Transparently inform citizen that AI is in offline/fallback mode and present exact rule synthesis
    if fallback_reason == "unconfigured":
        notice_line = "> ℹ️ **Notice: Live AI generation is currently offline (API key unconfigured). JanSahayak is displaying verified deterministic rule records.**\n"
    elif fallback_reason == "provider_timeout":
        notice_line = "> ⚠️ **Notice: Live AI service timed out. JanSahayak has safely engaged verified deterministic rule records.**\n"
    elif safe_err:
        notice_line = f"> ⚠️ **Notice: Live AI provider encountered a temporary error ({fallback_reason}: {safe_err}). JanSahayak has safely engaged verified deterministic rule records.**\n"
    else:
        notice_line = f"> ⚠️ **Notice: Live AI provider encountered a temporary error ({fallback_reason}). JanSahayak has safely engaged verified deterministic rule records.**\n"

    lines = [notice_line]

    if eligibility_evaluations:
        lines.append("### 📋 Scheme Eligibility Assessment")
        for ev in eligibility_evaluations:
            badge = "✅ ELIGIBLE" if ev['status'] == "eligible" else ("⚠️ POTENTIALLY ELIGIBLE" if ev['status'] == "possibly_eligible" else "❌ INELIGIBLE")
            lines.append(f"#### {ev['scheme_name']} — {badge}")
            lines.append(f"{ev['summary_explanation']}\n")

            if ev.get("satisfied_conditions"):
                lines.append("**Satisfied Conditions:**")
                for sc in ev["satisfied_conditions"]:
                    lines.append(f"- ✓ **{sc['criterion']}**: {sc.get('citizen_value', 'Met')}")

            if ev.get("unknown_conditions"):
                lines.append("\n**Information Needed to Confirm:**")
                for uc in ev["unknown_conditions"]:
                    lines.append(f"- ❓ {uc.get('prompt', uc['criterion'])}")

            if ev.get("unsatisfied_conditions"):
                lines.append("\n**Unsatisfied Criteria:**")
                for unc in ev["unsatisfied_conditions"]:
                    lines.append(f"- ✗ **{unc['criterion']}**: {unc.get('reason', 'Not met')}")

            lines.append(f"\n🔗 **Official Portal**: [{ev['official_sources'][0]['url']}]({ev['official_sources'][0]['url']})\n")

    elif passages:
        top = passages[0]
        lines.append(f"### 📋 Information from Verified Records: {top.scheme_name}")
        lines.append(top.content)
        lines.append(f"\n🔗 **Official Government Portal**: [{top.url}]({top.url})\n")
    else:
        lines.append("We could not find matching verified government scheme guidelines for your query.")
        lines.append("Please visit [india.gov.in](https://www.india.gov.in) to browse national schemes.")

    if follow_up_prompt:
        lines.append(f"\n---\n**💬 Next Question for You:**\n{follow_up_prompt}")

    lines.append("\n*Note: JanSahayak provides rule-based guidance and never guarantees official benefits. Final approval rests with the issuing government authority.*")

    fallback_text = "\n".join(lines)

    return {
        "answer": fallback_text,
        "citations": citations,
        "model": "rule-grounded-deterministic-fallback",
        "is_fallback": True,
        "status": "fallback_grounded",
        "ai_provider": "none",
        "fallback_reason": fallback_reason
    }
