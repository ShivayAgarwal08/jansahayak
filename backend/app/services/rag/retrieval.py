import re
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.scheme import Scheme

from app.models.document import KnowledgeDocument, DocumentChunk
from app.services.rag.embeddings import generate_embedding, compute_cosine_similarity

# Comprehensive stopwords to prevent generic numbers and conversational filler from polluting search
STOPWORDS = {
    # English grammar & conversational fillers
    "a", "about", "above", "after", "again", "all", "am", "an", "and", "any", "are", "around",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but",
    "by", "can", "did", "do", "does", "doing", "down", "during", "each", "few", "for", "from",
    "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself", "him",
    "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just",
    "me", "more", "most", "my", "myself", "no", "nor", "not", "now", "of", "off", "on", "once",
    "only", "or", "other", "our", "ours", "ourselves", "out", "over", "own", "same", "say", "says",
    "she", "should", "so", "some", "speaks", "such", "than", "that", "the", "their", "theirs",
    "them", "themselves", "then", "there", "these", "they", "this", "those", "through", "to",
    "too", "under", "until", "up", "very", "was", "we", "were", "what", "when", "where", "which",
    "while", "who", "whom", "why", "will", "with", "would", "you", "your", "yours", "yourself",
    # Generic numbers and quantities (MUST NOT match maternity or old age schemes)
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "first", "second",
    "third", "double", "triple",
    # Generic conversational filler words (intent words like eligible/benefit/apply/exclusion are preserved!)
    "government", "govt", "scheme", "schemes", "help", "please", "know", "information", "details",
    "might", "annual", "yearly", "monthly", "per"
}

# Sub-Intent definitions for high-precision ranking
QUERY_INTENTS = {
    "eligibility": {
        "query_keywords": ["eligible", "eligibility", "qualify", "qualification", "criteria", "who can", "who gets", "who is eligible", "condition", "conditions", "requirement", "requirements"],
        "chunk_keywords": ["eligibility", "objective", "scope", "beneficiary", "beneficiaries", "entitlement", "target", "identification", "criteria"],
        "boost": 18.0,
        "reason": "Matched eligibility and qualification intent"
    },
    "exclusions": {
        "query_keywords": ["exclusion", "exclusions", "disqualified", "disqualification", "ineligible", "not eligible", "barred", "cannot apply", "tax payer", "taxpayer", "income tax", "govt employee", "government employee"],
        "chunk_keywords": ["exclusion", "exclusions", "disqualified", "disqualification", "ineligible", "not eligible", "mandatory ineligibility", "automatic exclusion", "higher economic status"],
        "boost": 26.0,
        "reason": "Matched exclusion and disqualification criteria"
    },
    "benefits": {
        "query_keywords": ["benefit", "benefits", "assistance", "money", "rupees", "amount", "cash", "subsidy", "installment", "installments", "financial", "pension", "scale", "payout", "cost", "coverage", "grant"],
        "chunk_keywords": ["benefit", "financial assistance", "installment", "pension", "allowance", "dbt", "cash", "unit assistance", "scale", "package", "rate"],
        "boost": 20.0,
        "reason": "Matched financial benefit and assistance structure"
    },
    "documents_application": {
        "query_keywords": ["apply", "applying", "application", "document", "documents", "paperwork", "portal", "registration", "register", "process", "where to apply", "how to apply", "online", "procedure", "csc", "aadhaar"],
        "chunk_keywords": ["verification", "portal", "documents", "registration", "grievance", "how to apply", "procedure", "csc", "redressal", "aadhaar", "mandatory", "records"],
        "boost": 20.0,
        "reason": "Matched application procedure and document verification intent"
    }
}

# Domain Intent Mappings with high-precision keywords
DOMAIN_INTENTS = {
    "pm-kisan": {
        "keywords": {"farmer", "farmers", "farming", "kisan", "krishi", "land", "landholding", "cultivable", "cultivator", "bigha", "bighas", "acre", "acres", "agriculture", "agricultural", "pm-kisan", "pmkisan"},
        "boost": 25,
        "reason": "Matched agricultural & farmer landholding criteria"
    },
    "pmay-g": {
        "keywords": {"housing", "house", "shelter", "kutcha", "pucca", "dilapidated", "awas", "gramin", "houseless", "roof", "room", "rural housing", "pmay", "pmay-g", "pmayg", "awas yojana"},
        "boost": 25,
        "reason": "Matched rural housing & dwelling condition criteria"
    },
    "ayushman-bharat-pmjay": {
        "keywords": {"health", "hospital", "hospitalization", "medical", "treatment", "doctor", "illness", "surgery", "ayushman", "golden card", "5 lakh", "pmjay", "pm-jay", "healthcare"},
        "boost": 25,
        "reason": "Matched health & secondary/tertiary hospital coverage criteria"
    },
    "pmmvy": {
        "keywords": {"pregnant", "pregnancy", "maternity", "lactating", "delivery", "infant", "mother", "matru", "vandana", "first child", "institutional delivery", "pmmvy"},
        "boost": 25,
        "reason": "Matched maternal health & pregnancy assistance criteria"
    },
    "ignoaps": {
        "keywords": {"pension", "elderly", "senior", "senior citizen", "old age", "vridha", "60 years", "old", "destitute pension", "ignoaps", "nsap"},
        "boost": 25,
        "reason": "Matched senior citizen social security pension criteria"
    },
    "sukanya-samriddhi-yojana": {
        "keywords": {"girl child", "daughter", "sukanya", "samriddhi", "girl", "beti", "under 10", "child education", "ssy"},
        "boost": 25,
        "reason": "Matched girl child savings & education welfare criteria"
    },
    "pm-svanidhi": {
        "keywords": {"vendor", "street vendor", "hawker", "thela", "rehri", "svanidhi", "micro credit", "working capital", "footpath", "pm-svanidhi"},
        "boost": 25,
        "reason": "Matched urban street vendor micro-credit criteria"
    },
    "pm-vishwakarma": {
        "keywords": {"artisan", "vishwakarma", "carpenter", "blacksmith", "goldsmith", "potter", "mason", "tailor", "barber", "craftsperson", "traditional craft", "tool kit", "pm-vishwakarma"},
        "boost": 25,
        "reason": "Matched traditional family artisan & craftsperson trade criteria"
    }
}

class Passage:
    def __init__(
        self,
        scheme_slug: str,
        scheme_name: str,
        title: str,
        authority: str,
        url: str,
        content: str,
        page_number: int = 1,
        match_reasons: Optional[List[str]] = None,
        is_seeded_record: bool = True,
        document_reference: Optional[str] = None,
        similarity_score: Optional[float] = None
    ):
        self.scheme_slug = scheme_slug
        self.scheme_name = scheme_name
        self.title = title
        self.authority = authority
        self.url = url
        self.content = content
        self.page_number = page_number
        self.match_reasons = match_reasons or []
        self.is_seeded_record = is_seeded_record
        self.document_reference = document_reference
        self.similarity_score = similarity_score

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scheme_slug": self.scheme_slug,
            "scheme_name": self.scheme_name,
            "title": self.title,
            "authority": self.authority,
            "url": self.url,
            "content": self.content,
            "page_number": self.page_number,
            "match_reasons": self.match_reasons,
            "is_seeded_record": self.is_seeded_record,
            "document_reference": self.document_reference,
            "similarity_score": self.similarity_score
        }

def build_scheme_passages(scheme: Scheme) -> List[Passage]:
    """
    Extract structured chunks from verified scheme records.
    Explicitly tags records as verified seed records with official portal URLs.
    """
    passages = []
    
    # 1. Overview & Benefits chunk
    overview_text = (
        f"Scheme: {scheme.name} ({scheme.name_hi or ''})\n"
        f"Department: {scheme.department}\n"
        f"Scope: {scheme.scope.capitalize()}\n"
        f"Overview: {scheme.summary}\n"
        f"Financial/Welfare Benefits: {scheme.benefits_summary}\n"
        f"Official Portal: {scheme.official_portal_url}\n"
        f"Verification Source: Verified Record (Last audited: {scheme.last_verified_at.strftime('%Y-%m-%d') if hasattr(scheme.last_verified_at, 'strftime') else str(scheme.last_verified_at)})"
    )
    passages.append(Passage(
        scheme_slug=scheme.slug,
        scheme_name=scheme.name,
        title=f"{scheme.name} - Overview & Benefits",
        authority=scheme.department,
        url=scheme.official_portal_url,
        content=overview_text,
        page_number=1,
        is_seeded_record=True
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
        page_number=2,
        is_seeded_record=True
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
        page_number=3,
        is_seeded_record=True
    ))

    return passages

def retrieve_grounded_passages(
    query: str,
    db: Session,
    limit: int = 4,
    target_scheme_slug: Optional[str] = None
) -> List[Passage]:
    """
    Search and retrieve the most relevant verified scheme passages for a user query.
    First performs hybrid semantic vector search over ingested official DocumentChunk records.
    If no document chunks are present in DB, falls back gracefully to structured scheme definitions.
    Prevents false-positive ranking of maternal or pension schemes due to generic numbers.
    """
    # Tokenize and filter stopwords
    raw_tokens = re.findall(r"\w+", query.lower())
    meaningful_tokens = [w for w in raw_tokens if len(w) > 2 and w not in STOPWORDS]

    # Detect domain intents in user query
    matched_domains: Dict[str, List[str]] = {}
    query_str_lower = query.lower()
    for slug, intent_data in DOMAIN_INTENTS.items():
        matched_kws = [kw for kw in intent_data["keywords"] if re.search(rf"\b{re.escape(kw)}\b", query_str_lower)]
        if matched_kws:
            matched_domains[slug] = matched_kws

    has_other_domain = any(slug != "pm-kisan" for slug in matched_domains.keys())
    is_agri_query = ("pm-kisan" in matched_domains or any(w in query_str_lower for w in ["farmer", "kisan", "cultivator", "bigha", "land"])) and not has_other_domain

    # 1. Attempt vector search over ingested official DocumentChunk records
    db_chunks = []
    try:
        chunk_q = db.query(DocumentChunk)
        if hasattr(chunk_q, "join"):
            chunk_q = chunk_q.join(KnowledgeDocument, DocumentChunk.document_id == KnowledgeDocument.id)\
                .join(Scheme, KnowledgeDocument.scheme_id == Scheme.id)\
                .filter(Scheme.verification_status == "verified")
            if target_scheme_slug:
                chunk_q = chunk_q.filter(Scheme.slug == target_scheme_slug)
            
            # Retrieve chunks with related document and scheme
            raw_results = chunk_q.all()
            for item in raw_results:
                if isinstance(item, DocumentChunk):
                    # Chunks loaded via relationship
                    doc = item.document
                    scheme = doc.scheme if doc else None
                    if doc and scheme:
                        db_chunks.append((item, doc, scheme))
                elif isinstance(item, (tuple, list)) and len(item) == 3:
                    db_chunks.append(item)
    except Exception:
        db_chunks = []

    if db_chunks:
        query_vec = generate_embedding(query)
        scored_chunks: List[Tuple[float, Passage]] = []

        for chunk, doc, scheme in db_chunks:
            # Vector cosine similarity
            vec_sim = compute_cosine_similarity(query_vec, chunk.embedding) if chunk.embedding else 0.0
            score = vec_sim * 30.0
            reasons = [f"Semantic vector match ({vec_sim:.2f})"]

            # Domain intent boost
            if scheme.slug in matched_domains:
                intent = DOMAIN_INTENTS[scheme.slug]
                score += intent["boost"]
                reasons.append(f"{intent['reason']} (matched: {', '.join(matched_domains[scheme.slug])})")

            # Sub-intent boost (eligibility vs exclusions vs benefits vs application)
            content_lower = chunk.content.lower()
            section_lower = (chunk.section_title or "").lower()
            for intent_name, intent_data in QUERY_INTENTS.items():
                if any(qk in query_str_lower for qk in intent_data["query_keywords"]):
                    title_hits = [bk for bk in intent_data["chunk_keywords"] if bk in section_lower]
                    content_hits = [bk for bk in intent_data["chunk_keywords"] if bk in content_lower]
                    if title_hits:
                        score += intent_data["boost"]
                        reasons.append(f"{intent_data['reason']} in section title '{chunk.section_title}'")
                    elif content_hits:
                        score += intent_data["boost"] * 0.6
                        reasons.append(f"{intent_data['reason']} in official guideline text")

            # Keyword and section matching
            token_hits = 0
            for t in meaningful_tokens:
                if t in content_lower or (chunk.keywords and t in chunk.keywords):
                    score += 4.0
                    token_hits += 1
                if t in section_lower:
                    score += 6.0
                    token_hits += 1

            if token_hits > 0:
                reasons.append(f"Matched {token_hits} civic query keywords in official guideline text")

            # Negative penalty for irrelevant categories on specific agricultural queries
            if is_agri_query:
                if scheme.slug == "pmmvy" and "pmmvy" not in matched_domains:
                    score = -100.0
                elif scheme.slug == "ignoaps" and "ignoaps" not in matched_domains:
                    score = -100.0

            if score > 5.0 or (vec_sim > 0.35 and score > 0):
                passage = Passage(
                    scheme_slug=scheme.slug,
                    scheme_name=scheme.name,
                    title=f"{doc.title} - {chunk.section_title or f'Page {chunk.page_number}'}",
                    authority=doc.authority,
                    url=doc.source_url,
                    content=chunk.content,
                    page_number=chunk.page_number,
                    match_reasons=reasons,
                    is_seeded_record=False,
                    document_reference=doc.document_reference,
                    similarity_score=round(vec_sim, 3)
                )
                scored_chunks.append((score, passage))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        results = [item[1] for item in scored_chunks[:limit]]
        if results:
            return results

    # 2. Fallback to structured scheme definitions if document chunks are empty or no matches found
    schemes = db.query(Scheme).filter(Scheme.verification_status == "verified").all()
    if target_scheme_slug:
        schemes = [s for s in schemes if s.slug == target_scheme_slug] or schemes

    all_passages: List[Passage] = []
    for s in schemes:
        all_passages.extend(build_scheme_passages(s))

    scored_passages: List[Tuple[int, Passage]] = []

    for p in all_passages:
        score = 0
        reasons: List[str] = []
        text = f"{p.scheme_name} {p.title} {p.content}".lower()

        if p.scheme_slug in matched_domains:
            intent = DOMAIN_INTENTS[p.scheme_slug]
            score += intent["boost"]
            reasons.append(f"{intent['reason']} (matched: {', '.join(matched_domains[p.scheme_slug])})")

        token_hits = 0
        for token in meaningful_tokens:
            if token in p.scheme_slug:
                score += 8
                token_hits += 1
            elif token in p.scheme_name.lower():
                score += 6
                token_hits += 1
            elif token in p.title.lower():
                score += 4
                token_hits += 1
            else:
                count = text.count(token)
                if count > 0:
                    score += min(count, 3)
                    token_hits += 1

        if token_hits > 0 and not reasons:
            reasons.append("Matched relevant scheme keywords in official verified documentation")

        if is_agri_query:
            if p.scheme_slug == "pmmvy" and "pmmvy" not in matched_domains:
                score = -100
            elif p.scheme_slug == "ignoaps" and "ignoaps" not in matched_domains:
                score = -100

        if score > 0:
            p.match_reasons = reasons
            scored_passages.append((score, p))

    scored_passages.sort(key=lambda x: x[0], reverse=True)
    results = [item[1] for item in scored_passages[:limit]]

    if not results:
        results = all_passages[:limit]

    return results

def search_official_documents(
    query: str,
    db: Session,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Search official document chunks via hybrid vector and keyword retrieval.
    Returns structured results with source URLs, page numbers, and similarity metrics.
    """
    passages = retrieve_grounded_passages(query=query, db=db, limit=limit)
    return [p.to_dict() for p in passages]
