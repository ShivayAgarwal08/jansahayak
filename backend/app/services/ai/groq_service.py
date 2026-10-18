import httpx
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.services.rag.retrieval import Passage

SYSTEM_PROMPT = """You are JanSahayak's Citizen Welfare AI Assistant, an empathetic, accurate, and trustworthy guide for Indian government welfare schemes.

CRITICAL CONSTRAINTS:
1. Base your answer EXCLUSIVELY on the verified government evidence provided inside <VERIFIED_GOVERNMENT_EVIDENCE> and deterministic evaluation inside <DETERMINISTIC_ELIGIBILITY_EVALUATION>.
2. DO NOT hallucinate, invent schemes, eligibility criteria, subsidy amounts, deadlines, or application procedures.
3. If deterministic eligibility results are provided, report them faithfully. Do not alter 'eligible', 'possibly_eligible', or 'ineligible' conclusions.
4. If essential citizen details are missing, include the suggested follow-up question so the citizen can clarify.
5. Always mention the issuing department, the official portal URL, and cite [Passage N] tags.
6. Provide clear, empathetic, citizen-friendly explanations in simple language.
"""

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
    Falls back honestly and safely to deterministic rule synthesis when AI is unavailable.
    """
    evidence_blocks = []
    citations = []
    
    for idx, p in enumerate(passages):
        evidence_blocks.append(
            f"[Passage {idx+1}]\n"
            f"Scheme: {p.scheme_name}\n"
            f"Title: {p.title}\n"
            f"Issuing Authority: {p.authority}\n"
            f"Official URL: {p.url}\n"
            f"Verified Seed Record: {p.is_seeded_record}\n"
            f"Match Reasons: {', '.join(p.match_reasons) if p.match_reasons else 'General Catalog'}\n"
            f"Content Details:\n{p.content}\n"
        )
        citations.append({
            "citation_id": idx + 1,
            "scheme_slug": p.scheme_slug,
            "scheme_name": p.scheme_name,
            "title": p.title,
            "authority": p.authority,
            "url": p.url,
            "page_number": p.page_number
        })
        
    evidence_text = "\n---\n".join(evidence_blocks)

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

    # 1. Attempt Groq API if configured
    if settings.GROQ_API_KEY and settings.GROQ_API_KEY.strip():
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.GROQ_API_KEY.strip()}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": settings.GROQ_MODEL,
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
                    return {
                        "answer": answer_text,
                        "citations": citations,
                        "model": settings.GROQ_MODEL,
                        "is_fallback": False,
                        "status": "success",
                        "ai_provider": "groq"
                    }
        except Exception:
            # Fall through to deterministic fallback if Groq API fails or times out
            pass

    # 2. Deterministic Non-Hallucinatory Fallback
    # Transparently inform citizen that AI is in offline/fallback mode and present exact rule synthesis
    lines = [
        "> ℹ️ **Notice: Live AI generation is currently offline (API key unconfigured or provider unreachable). JanSahayak is displaying verified deterministic rule records.**\n"
    ]

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
        "ai_provider": "none"
    }
