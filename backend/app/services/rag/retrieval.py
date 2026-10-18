import re
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.scheme import Scheme

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
    # Generic civic / question words
    "qualify", "qualification", "eligible", "eligibility", "government", "govt", "scheme", "schemes",
    "welfare", "apply", "applying", "help", "please", "know", "information", "details", "might",
    "annual", "yearly", "monthly", "per", "amount", "rupees", "rs", "inr", "lakh", "lakhs"
}

# Domain Intent Mappings with high-precision keywords
DOMAIN_INTENTS = {
    "pm-kisan": {
        "keywords": {"farmer", "farmers", "farming", "kisan", "krishi", "land", "landholding", "cultivable", "cultivator", "bigha", "bighas", "acre", "acres", "agriculture", "agricultural"},
        "boost": 25,
        "reason": "Matched agricultural & farmer landholding criteria"
    },
    "pmay-g": {
        "keywords": {"housing", "house", "shelter", "kutcha", "pucca", "dilapidated", "awas", "gramin", "houseless", "roof", "room", "rural housing"},
        "boost": 25,
        "reason": "Matched rural housing & dwelling condition criteria"
    },
    "ayushman-bharat-pmjay": {
        "keywords": {"health", "hospital", "hospitalization", "medical", "treatment", "doctor", "illness", "surgery", "ayushman", "golden card", "5 lakh", "pmjay", "healthcare"},
        "boost": 25,
        "reason": "Matched health & secondary/tertiary hospital coverage criteria"
    },
    "pmmvy": {
        "keywords": {"pregnant", "pregnancy", "maternity", "lactating", "delivery", "infant", "mother", "matru", "vandana", "first child", "institutional delivery"},
        "boost": 25,
        "reason": "Matched maternal health & pregnancy assistance criteria"
    },
    "ignoaps": {
        "keywords": {"pension", "elderly", "senior", "senior citizen", "old age", "vridha", "60 years", "old", "destitute pension"},
        "boost": 25,
        "reason": "Matched senior citizen social security pension criteria"
    },
    "sukanya-samriddhi-yojana": {
        "keywords": {"girl child", "daughter", "sukanya", "samriddhi", "girl", "beti", "under 10", "child education"},
        "boost": 25,
        "reason": "Matched girl child savings & education welfare criteria"
    },
    "pm-svanidhi": {
        "keywords": {"vendor", "street vendor", "hawker", "thela", "rehri", "svanidhi", "micro credit", "working capital", "footpath"},
        "boost": 25,
        "reason": "Matched urban street vendor micro-credit criteria"
    },
    "pm-vishwakarma": {
        "keywords": {"artisan", "vishwakarma", "carpenter", "blacksmith", "goldsmith", "potter", "mason", "tailor", "barber", "craftsperson", "traditional craft", "tool kit"},
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
        is_seeded_record: bool = True
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
            "is_seeded_record": self.is_seeded_record
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
    Applies stopword filtering, domain intent matching, and specific criteria weighting.
    Prevents false-positive ranking of maternal or pension schemes due to generic numbers.
    """
    schemes = db.query(Scheme).filter(Scheme.verification_status == "verified").all()
    if target_scheme_slug:
        schemes = [s for s in schemes if s.slug == target_scheme_slug] or schemes

    all_passages: List[Passage] = []
    for s in schemes:
        all_passages.extend(build_scheme_passages(s))

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

    scored: List[Tuple[int, Passage]] = []

    for p in all_passages:
        score = 0
        reasons: List[str] = []
        text = f"{p.scheme_name} {p.title} {p.content}".lower()

        # 1. Domain Intent Score
        if p.scheme_slug in matched_domains:
            intent = DOMAIN_INTENTS[p.scheme_slug]
            score += intent["boost"]
            reasons.append(f"{intent['reason']} (matched: {', '.join(matched_domains[p.scheme_slug])})")

        # 2. Token Matching (filtered)
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

        # 3. Penalize maternal or old-age schemes if the query is explicitly about farmers/agriculture
        # and has NO maternity/senior keywords
        is_agri_query = "pm-kisan" in matched_domains or any(w in query_str_lower for w in ["farmer", "kisan", "cultivator", "bigha", "land"])
        if is_agri_query:
            if p.scheme_slug == "pmmvy" and "pmmvy" not in matched_domains:
                score = -100  # Disqualify from agricultural results
            elif p.scheme_slug == "ignoaps" and "ignoaps" not in matched_domains:
                score = -100  # Disqualify from agricultural results

        if score > 0:
            p.match_reasons = reasons
            scored.append((score, p))

    # Sort descending by relevance score
    scored.sort(key=lambda x: x[0], reverse=True)
    results = [item[1] for item in scored[:limit]]

    # Fallback to general schemes if nothing scored > 0
    if not results:
        results = all_passages[:limit]

    return results
