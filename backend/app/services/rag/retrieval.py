import re
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.scheme import Scheme

class Passage:
    def __init__(self, scheme_slug: str, scheme_name: str, title: str, authority: str, url: str, content: str, page_number: int = 1):
        self.scheme_slug = scheme_slug
        self.scheme_name = scheme_name
        self.title = title
        self.authority = authority
        self.url = url
        self.content = content
        self.page_number = page_number

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scheme_slug": self.scheme_slug,
            "scheme_name": self.scheme_name,
            "title": self.title,
            "authority": self.authority,
            "url": self.url,
            "content": self.content,
            "page_number": self.page_number
        }

def build_scheme_passages(scheme: Scheme) -> List[Passage]:
    """
    Extract structured chunks from verified scheme records.
    """
    passages = []
    
    # 1. Overview & Benefits chunk
    overview_text = (
        f"Scheme: {scheme.name} ({scheme.name_hi or ''})\n"
        f"Department: {scheme.department}\n"
        f"Scope: {scheme.scope.capitalize()}\n"
        f"Overview: {scheme.summary}\n"
        f"Financial/Welfare Benefits: {scheme.benefits_summary}\n"
        f"Official Portal: {scheme.official_portal_url}"
    )
    passages.append(Passage(
        scheme_slug=scheme.slug,
        scheme_name=scheme.name,
        title=f"{scheme.name} - Overview & Benefits",
        authority=scheme.department,
        url=scheme.official_portal_url,
        content=overview_text,
        page_number=1
    ))

    # 2. Eligibility & Exclusions chunk
    exclusions_str = "\n- ".join(scheme.exclusions or ["None specified"])
    rules_text = (
        f"Scheme: {scheme.name}\n"
        f"Target Beneficiaries: {', '.join(scheme.beneficiary_types or [])}\n"
        f"Eligibility Criteria: {scheme.eligibility_rules}\n"
        f"Official Exclusions / Disqualifications:\n- {exclusions_str}"
    )
    passages.append(Passage(
        scheme_slug=scheme.slug,
        scheme_name=scheme.name,
        title=f"{scheme.name} - Eligibility & Exclusions",
        authority=scheme.department,
        url=scheme.official_portal_url,
        content=rules_text,
        page_number=2
    ))

    # 3. Documents & Application Steps chunk
    docs_list = []
    for doc in (scheme.required_documents or []):
        alt = f" (Accepted Alternatives: {', '.join(doc.get('alternatives', []))})" if doc.get('alternatives') else ""
        docs_list.append(f"{doc.get('name')}{alt}")
    docs_str = "\n- ".join(docs_list)

    steps_str = "\n".join([f"{idx+1}. {step}" for idx, step in enumerate(scheme.application_steps or [])])
    doc_steps_text = (
        f"Scheme: {scheme.name}\n"
        f"Mandatory & Supporting Documents:\n- {docs_str}\n\n"
        f"Official Application Procedure:\n{steps_str}\n"
        f"Official Submission Portal: {scheme.official_portal_url}"
    )
    passages.append(Passage(
        scheme_slug=scheme.slug,
        scheme_name=scheme.name,
        title=f"{scheme.name} - Documents & How to Apply",
        authority=scheme.department,
        url=scheme.official_portal_url,
        content=doc_steps_text,
        page_number=3
    ))

    return passages

def retrieve_grounded_passages(query: str, db: Session, limit: int = 4) -> List[Passage]:
    """
    Search and retrieve the most relevant verified scheme passages for a user query.
    Extracts terms and computes keyword relevance scoring across all verified schemes.
    """
    schemes = db.query(Scheme).filter(Scheme.verification_status == "verified").all()
    all_passages: List[Passage] = []
    for s in schemes:
        all_passages.extend(build_scheme_passages(s))

    query_tokens = [w.lower() for w in re.findall(r"\w+", query) if len(w) > 2]
    if not query_tokens:
        return all_passages[:limit]

    scored = []
    for p in all_passages:
        text = f"{p.scheme_name} {p.title} {p.content}".lower()
        score = 0
        for token in query_tokens:
            if token in p.scheme_slug:
                score += 5
            if token in p.scheme_name.lower():
                score += 4
            if token in p.title.lower():
                score += 3
            count = text.count(token)
            score += min(count, 5)
        
        if score > 0:
            scored.append((score, p))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = [item[1] for item in scored[:limit]]
    
    # If no keyword match found, return top general schemes
    if not results:
        results = all_passages[:limit]
        
    return results
