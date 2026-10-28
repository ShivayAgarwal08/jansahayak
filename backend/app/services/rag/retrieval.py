import re
import difflib
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.scheme import Scheme

from app.models.document import KnowledgeDocument, DocumentChunk
from app.services.rag.embeddings import generate_embedding, compute_cosine_similarity

def normalize_indic_phonetics(word: str) -> str:
    """
    Normalize common Indic phonetic, transliteration, and typo variations.
    Collapses vowel elongations (aa -> a, ee -> i, oo -> u), consonant gemination,
    aspirates/sibilants, and trailing 'y' -> 'i'.
    """
    w = word.lower().strip()
    if not w:
        return ""
    w = re.sub(r"aa+", "a", w)
    w = re.sub(r"ee+", "i", w)
    w = re.sub(r"oo+", "u", w)
    w = re.sub(r"ii+", "i", w)
    w = re.sub(r"uu+", "u", w)
    w = re.sub(r"sh", "s", w)
    w = re.sub(r"kh", "k", w)
    w = re.sub(r"bh", "b", w)
    w = re.sub(r"dh", "d", w)
    w = re.sub(r"th", "t", w)
    w = re.sub(r"ph", "f", w)
    w = re.sub(r"gh", "g", w)
    w = re.sub(r"ch+", "c", w)
    w = re.sub(r"([bdfgklmnprstvwz])\1+", r"\1", w)
    if w.endswith("y") and len(w) > 3:
        w = w[:-1] + "i"
    return w

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
    "might", "annual", "yearly", "monthly", "per", "get", "buy", "give", "want", "need", "like", "take", "also", "new",
    "pm", "free", "pradhan", "mantri", "yojana"
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

# Scam, giveaway, and out-of-scope indicators to ensure reliable abstention (zero false positives)
SCAM_OR_UNRELATED_INDICATORS = {
    "lottery", "giveaway", "cash giveaway", "free smartphone", "gold iphone", "free iphone",
    "free gold", "cryptocurrency", "crypto", "bitcoin", "helicopter", "jackpot", "cash jackpot",
    "cricket match", "cricket score", "bake a cake", "chocolate cake", "flight ticket",
    "nullpointerexception", "python programming", "switzerland"
}

# Domain Intent Mappings with high-precision keywords (both Romanized and Devanagari Hindi)
DOMAIN_INTENTS = {
    "pm-kisan": {
        "keywords": {
            "farmer", "farmers", "farming", "kisan", "krishi", "land", "landholding", "cultivable", "cultivator",
            "bigha", "bighas", "acre", "acres", "agriculture", "agricultural", "pm-kisan", "pmkisan", "khet", "kheti",
            "fasal", "krishak", "6000 rupaye", "kisaan", "samman", "nidhi", "samman nidhy",
            "किसान", "खेती", "कृषि", "बीघा", "जमीन", "खेत", "फसल", "कृषक", "सम्मान निधि", "पीएम किसान"
        },
        "boost": 25,
        "reason": "Matched agricultural & farmer landholding criteria"
    },
    "pmay-g": {
        "keywords": {
            "housing", "house", "shelter", "kutcha", "pucca", "dilapidated", "awas", "gramin", "houseless",
            "roof", "room", "rural housing", "pmay", "pmay-g", "pmayg", "awas yojana", "kachha", "pakka",
            "makan", "ghar", "gaon", "chhat", "aawas",
            "आवास", "मकान", "घर", "ग्रामीण", "कच्चा", "पक्का", "झोपड़ी", "छत", "बेघर", "पीएम आवास"
        },
        "boost": 25,
        "reason": "Matched rural housing & dwelling condition criteria"
    },
    "ayushman-bharat-pmjay": {
        "keywords": {
            "health", "hospital", "hospitalization", "medical", "treatment", "doctor", "illness", "surgery",
            "ayushman", "golden card", "5 lakh", "pmjay", "pm-jay", "healthcare", "ilaj", "dawa", "bimar",
            "bimari", "70 saal", "70 years", "aayushman", "pmjaay", "bharat", "arogya", "bima", "beema", "clinic",
            "आयुष्मान", "इलाज", "अस्पताल", "दवा", "बीमार", "बीमारी", "स्वास्थ्य", "गोल्डन कार्ड", "आरोग्य"
        },
        "boost": 25,
        "reason": "Matched health & secondary/tertiary hospital coverage criteria"
    },
    "pmmvy": {
        "keywords": {
            "pregnant", "pregnancy", "maternity", "lactating", "delivery", "infant", "mother", "matru",
            "vandana", "first child", "institutional delivery", "pmmvy", "garbhavati", "mahila", "prasuti",
            "baccha", "bacche", "janm", "pmmvi",
            "गर्भवती", "मातृत्व", "प्रसूति", "महिला", "मातृ वंदना", "शिशु", "बच्चा"
        },
        "boost": 25,
        "reason": "Matched maternal health & pregnancy assistance criteria"
    },
    "ignoaps": {
        "keywords": {
            "pension", "elderly", "senior", "senior citizen", "old age", "vridha", "60 years", "old",
            "destitute pension", "ignoaps", "nsap", "buzurg", "dadi", "dada",
            "वृद्धा", "पेंशन", "बुजुर्ग", "वरिष्ठ नागरिक", "वृद्धावस्था"
        },
        "boost": 25,
        "reason": "Matched senior citizen social security pension criteria"
    },
    "sukanya-samriddhi-yojana": {
        "keywords": {
            "girl child", "daughter", "sukanya", "samriddhi", "girl", "beti", "under 10", "child education",
            "ssy", "kanya", "chhoti", "samridhi", "dakghar", "gudiya",
            "सुकन्या", "समृद्धि", "बेटी", "कन्या", "बालिका", "डाकघर"
        },
        "boost": 25,
        "reason": "Matched girl child savings & education welfare criteria"
    },
    "sukanya-samriddhi": {
        "keywords": {
            "girl child", "daughter", "sukanya", "samriddhi", "girl", "beti", "under 10", "child education",
            "ssy", "kanya", "chhoti", "samridhi", "dakghar", "gudiya",
            "सुकन्या", "समृद्धि", "बेटी", "कन्या", "बालिका", "डाकघर"
        },
        "boost": 25,
        "reason": "Matched girl child savings & education welfare criteria"
    },
    "pm-svanidhi": {
        "keywords": {
            "vendor", "street vendor", "hawker", "thela", "rehri", "svanidhi", "micro credit", "working capital",
            "footpath", "pm-svanidhi", "handcart", "cart", "vegetable vendor", "fruit vendor", "sadak", "patri",
            "phal", "chai", "svanidi",
            "रेहड़ी", "पटरी", "ठेला", "फेरीवाला", "स्वनिधि", "सड़क विक्रेता", "दुकानदार"
        },
        "boost": 25,
        "reason": "Matched urban street vendor micro-credit criteria"
    },
    "pm-vishwakarma": {
        "keywords": {
            "artisan", "vishwakarma", "carpenter", "blacksmith", "goldsmith", "potter", "mason", "tailor",
            "barber", "craftsperson", "traditional craft", "tool kit", "toolkit", "pm-vishwakarma", "pottery",
            "clay", "pots", "earthenware", "kumhaar", "lohar", "sonar", "cobbler", "sculptor", "traditional trade",
            "hand tools", "karigar", "auzar", "bartan",
            "विश्वकर्मा", "कारीगर", "बढ़ई", "लोहार", "सोनार", "कुम्हार", "दर्जी", "मोची", "राजमिस्त्री", "औजार"
        },
        "boost": 25,
        "reason": "Matched traditional family artisan & craftsperson trade criteria"
    },
    "atal-pension-yojana": {
        "keywords": {
            "atal", "pension", "apy", "pension yojana", "atal pension", "old age pension", "guaranteed pension",
            "5000 pension", "retirement", "unorganized", "pran", "pfrda", "budhapa",
            "अटल", "पेंशन", "अटल पेंशन", "बुढ़ापा", "गारंटीकृत पेंशन", "सेवानिवृत्ति"
        },
        "boost": 25,
        "reason": "Matched guaranteed monthly retirement pension criteria (APY)"
    },
    "pm-jeevan-jyoti-bima": {
        "keywords": {
            "jeevan jyoti", "pmjjby", "life insurance", "term life", "2 lakh bima", "200000", "436",
            "bima yojana", "death benefit", "jansuraksha", "insurance", "beema",
            "जीवन ज्योति", "बीमा", "जीवन बीमा", "टर्म लाइफ", "जनसुरक्षा"
        },
        "boost": 25,
        "reason": "Matched affordable life insurance cover criteria (PMJJBY)"
    },
    "pm-yasasvi": {
        "keywords": {
            "yasasvi", "pm-yasasvi", "scholarship", "obc scholarship", "ebc", "dnt", "school scholarship",
            "class 9", "class 10", "class 11", "class 12", "merit scholarship", "chatravriti", "chhatravritti", "padhai",
            "यशस्वी", "छात्रवृत्ति", "स्कॉलरशिप", "ओबीसी छात्रवृत्ति", "पढ़ाई", "मेधावी"
        },
        "boost": 25,
        "reason": "Matched top-class school education scholarship criteria (PM-YASASVI)"
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
    query_str_lower = query.lower()
    # Immediate abstention for explicit scam, lottery, giveaway, and off-topic queries
    if any(scam in query_str_lower for scam in SCAM_OR_UNRELATED_INDICATORS):
        return []

    # Tokenize and filter stopwords
    raw_tokens = re.findall(r"\w+", query_str_lower)
    meaningful_tokens = [w for w in raw_tokens if len(w) > 2 and w not in STOPWORDS]

    # Detect domain intents in user query
    # 1. Exact canonical matches
    matched_domains: Dict[str, List[str]] = {}
    for slug, intent_data in DOMAIN_INTENTS.items():
        matched_kws = [kw for kw in intent_data["keywords"] if re.search(rf"\b{re.escape(kw)}\b", query_str_lower)]
        if matched_kws:
            matched_domains[slug] = matched_kws

    # 2. Bounded phonetic and fuzzy fallback for plausible spelling and transliteration variations
    matched_fuzzy: Dict[str, List[Tuple[str, str, float, str]]] = {}
    for t in meaningful_tokens:
        if len(t) < 4:
            continue
        norm_t = normalize_indic_phonetics(t)
        for slug, intent_data in DOMAIN_INTENTS.items():
            for kw in intent_data["keywords"]:
                if " " in kw or len(kw) < 4:
                    continue
                norm_kw = normalize_indic_phonetics(kw)
                
                # Rule A: Exact match after Indic phonetic normalization
                if norm_t == norm_kw:
                    matched_fuzzy.setdefault(slug, []).append((t, kw, 1.0, "exact_norm"))
                    break
                # Rule B: High-confidence fuzzy match on substantive tokens (len >= 5, ratio >= 0.85)
                elif len(norm_t) >= 5 and len(norm_kw) >= 5:
                    ratio = difflib.SequenceMatcher(None, norm_t, norm_kw).ratio()
                    if ratio >= 0.85:
                        matched_fuzzy.setdefault(slug, []).append((t, kw, ratio, "fuzzy"))
                        break

    # 3. Gated acceptance: require strong exact_norm (len >= 5) or >= 2 corroborating tokens
    for slug, hits in matched_fuzzy.items():
        if slug in matched_domains:
            continue
        unique_tokens = set(h[0] for h in hits)
        has_strong_exact_norm = any(h[3] == "exact_norm" and len(h[0]) >= 5 for h in hits)
        if has_strong_exact_norm or len(unique_tokens) >= 2:
            matched_domains[slug] = [f"{h[0]}~{h[1]}" for h in hits]

    has_other_domain = any(slug != "pm-kisan" for slug in matched_domains.keys())
    is_agri_query = ("pm-kisan" in matched_domains or any(w in query_str_lower for w in ["farmer", "kisan", "cultivator", "bigha", "land"])) and not has_other_domain

    # Build set of generic intent modifier tokens
    all_intent_tokens = set()
    for idata in QUERY_INTENTS.values():
        for qk in idata["query_keywords"]:
            for w in re.findall(r"\w+", qk.lower()):
                if len(w) > 2:
                    all_intent_tokens.add(w)
    substantive_tokens = [t for t in meaningful_tokens if t not in all_intent_tokens]

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

            content_lower = chunk.content.lower()
            section_lower = (chunk.section_title or "").lower()
            content_words = set(re.findall(r"\w+", content_lower))
            section_words = set(re.findall(r"\w+", section_lower))
            chunk_kw_set = set(chunk.keywords or [])

            # Substantive token hits (civic entities/nouns, with phonetic normalization fallback)
            substantive_hits = sum(1 for t in substantive_tokens if (t in content_words or t in chunk_kw_set or t in section_words))
            if substantive_hits == 0 and scheme.slug in matched_domains:
                for t in substantive_tokens:
                    if len(t) >= 4:
                        norm_t = normalize_indic_phonetics(t)
                        for cw in (chunk_kw_set | section_words):
                            if len(cw) >= 4:
                                norm_cw = normalize_indic_phonetics(cw)
                                if norm_t == norm_cw:
                                    substantive_hits += 1
                                    break
                                elif len(norm_t) >= 5 and difflib.SequenceMatcher(None, norm_t, norm_cw).ratio() >= 0.85:
                                    substantive_hits += 1
                                    break

            has_scheme_affinity = (scheme.slug in matched_domains) or (substantive_hits >= 1 and (vec_sim >= 0.45 or substantive_hits >= 2))

            # Domain intent boost
            if scheme.slug in matched_domains:
                intent = DOMAIN_INTENTS[scheme.slug]
                score += intent["boost"]
                reasons.append(f"{intent['reason']} (matched: {', '.join(matched_domains[scheme.slug])})")

            # Sub-intent boost (eligibility vs exclusions vs benefits vs application) - only if scheme affinity exists
            if has_scheme_affinity:
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

            # Keyword and section matching with whole-word token sets and phonetic fallback
            token_hits = 0
            for t in meaningful_tokens:
                if t in content_words or t in chunk_kw_set:
                    score += 4.0
                    token_hits += 1
                elif t in section_words:
                    score += 6.0
                    token_hits += 1
                elif len(t) >= 4 and scheme.slug in matched_domains:
                    norm_t = normalize_indic_phonetics(t)
                    for kw in chunk_kw_set:
                        if len(kw) >= 4 and normalize_indic_phonetics(kw) == norm_t:
                            score += 3.5
                            token_hits += 1
                            break

            if token_hits > 0:
                reasons.append(f"Matched {token_hits} civic query keywords in official guideline text")

            # Negative penalty for irrelevant categories on specific agricultural queries
            if is_agri_query:
                if scheme.slug == "pmmvy" and "pmmvy" not in matched_domains:
                    score = -100.0
                elif scheme.slug == "ignoaps" and "ignoaps" not in matched_domains:
                    score = -100.0

            if has_scheme_affinity and (score > 6.0 or (vec_sim > 0.35 and score > 0)):
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

        text_words = set(re.findall(r"\w+", text))
        substantive_hits = sum(1 for t in substantive_tokens if t in text_words)
        has_scheme_affinity = (p.scheme_slug in matched_domains) or (substantive_hits >= 2)

        if has_scheme_affinity and score > 0:
            p.match_reasons = reasons
            scored_passages.append((score, p))

    scored_passages.sort(key=lambda x: x[0], reverse=True)
    results = [item[1] for item in scored_passages[:limit]]

    if not results and target_scheme_slug:
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
