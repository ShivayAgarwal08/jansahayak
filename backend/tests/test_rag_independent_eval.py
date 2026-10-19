"""
JanSahayak Independent RAG Retrieval Benchmark Test Suite
This benchmark was constructed independently from the domain intent dictionary
and scam indicator keyword lists to evaluate genuine out-of-vocabulary generalization.

Includes:
- Category 1: Indirect descriptions & uncommon wording (8 queries)
- Category 2: Natural Hinglish & conversational phrasing (8 queries)
- Category 3: Phonetic typos of varying severity, including regressions (6 queries)
- Category 4: Cross-scheme overlapping benefits (3 queries)
- Category 5: Ambiguous & incomplete citizen situations (2 queries)
- Category 6: Fabricated schemes & unanchored scams (4 queries) - must abstain
- Category 7: Out-of-scope / unrelated inquiries (4 queries) - must abstain
"""
import pytest
from app.db.session import SessionLocal
from app.services.rag.retrieval import retrieve_grounded_passages

INDEPENDENT_EVAL_SET = [
    # Category 1: Indirect Descriptions & Uncommon Wording (8 queries)
    {"id": "IND_01", "cat": "indirect", "query": "We cultivate leased boro paddy in seasonal wetlands and need seed purchase aid", "exp": "pm-kisan"},
    {"id": "IND_02", "cat": "indirect", "query": "Crumbling thatching and cracked mud walls in our flood-prone hamlet need replacement with concrete", "exp": "pmay-g"},
    {"id": "IND_03", "cat": "indirect", "query": "My octogenarian father requires cataract extraction and intraocular lens implantation at a registered clinic", "exp": "ayushman-bharat-pmjay"},
    {"id": "IND_04", "cat": "indirect", "query": "First-time expecting rural mother attending regular nutrition counseling at community balwadi", "exp": "pmmvy"},
    {"id": "IND_05", "cat": "indirect", "query": "Elderly infirm person living without familial support or livelihood earnings in village ward", "exp": "ignoaps"},
    {"id": "IND_06", "cat": "indirect", "query": "Setting aside recurring monthly savings for our 4-year-old girl child's future collegiate tuition", "exp": "sukanya-samriddhi-yojana"},
    {"id": "IND_07", "cat": "indirect", "query": "Pushcart operator vending roasted peanuts on station road seeking working inventory funds", "exp": "pm-svanidhi"},
    {"id": "IND_08", "cat": "indirect", "query": "Handloom weaver crafting cotton stoles and traditional furnishings seeking equipment voucher", "exp": "pm-vishwakarma"},

    # Category 2: Natural Hinglish & Conversational Transliteration (8 queries)
    {"id": "IND_09", "cat": "hinglish", "query": "kheti kisani ka kam karte hain zameen ke kagaz par saalana sahayata kaise milegi", "exp": "pm-kisan"},
    {"id": "IND_10", "cat": "hinglish", "query": "mitti ki jhopdi girne wali hai pakke chhat wale aawas ke liye gram pradhan se kaise mile", "exp": "pmay-g"},
    {"id": "IND_11", "cat": "hinglish", "query": "bade aspataal me bina paise diye surgery aur admit hone ke liye sarkar ka card", "exp": "ayushman-bharat-pmjay"},
    {"id": "IND_12", "cat": "hinglish", "query": "pehli baar maa banne wali aurat ko anganbadi se kist me milne wali sahayata", "exp": "pmmvy"},
    {"id": "IND_13", "cat": "hinglish", "query": "sath baras se upar ke vriddh vyakti jinke pas aamadani ka sadhan nahi hai unki pension", "exp": "ignoaps"},
    {"id": "IND_14", "cat": "hinglish", "query": "nanhi gudiya ke bhavishya ke liye dakghar me jama karne par kitna munafa milega", "exp": "sukanya-samriddhi-yojana"},
    {"id": "IND_15", "cat": "hinglish", "query": "footpath par sabji lagate hain dukan badhane ke liye chhota karz chahiye bina girvi", "exp": "pm-svanidhi"},
    {"id": "IND_16", "cat": "hinglish", "query": "mitti ke bartan aur matke banane wale karigar ko auzar khareedne ka grant", "exp": "pm-vishwakarma"},

    # Category 3: Phonetic Typos of Varying Severity (6 queries - includes Priority 1 regressions)
    {"id": "IND_17", "cat": "typo", "query": "pardon muntri kishaan samann nidhy do hazaar", "exp": "pm-kisan"},
    {"id": "IND_18", "cat": "typo", "query": "ayusman bhrat rogoya bima 500000", "exp": "ayushman-bharat-pmjay"},
    {"id": "IND_19", "cat": "typo", "query": "sukanya samrithi post offce beti yojna", "exp": "sukanya-samriddhi-yojana"},
    {"id": "IND_20", "cat": "typo", "query": "pm swanidi vander thela karj", "exp": "pm-svanidhi"},
    {"id": "IND_21", "cat": "typo", "query": "mathru vandhana garbhvati maa sahayata", "exp": "pmmvy"},
    {"id": "IND_22", "cat": "typo", "query": "pradhan mantry aawash gramin suchi", "exp": "pmay-g"},

    # Category 4: Overlapping Benefits & Cross-Scheme Queries (3 queries)
    {"id": "IND_23", "cat": "cross_scheme", "query": "Financial loan or grant for a rural self-employed woman doing home-based dressmaking", "schemes": ["pm-vishwakarma", "pm-svanidhi"]},
    {"id": "IND_24", "cat": "cross_scheme", "query": "Government sustenance and healthcare coverage for poor senior citizens", "schemes": ["ignoaps", "ayushman-bharat-pmjay"]},
    {"id": "IND_25", "cat": "cross_scheme", "query": "Direct benefit transfer for low income expectant mothers in village", "schemes": ["pmmvy", "pmay-g"]},

    # Category 5: Ambiguous & Incomplete Citizen Situations (2 queries)
    {"id": "IND_26", "cat": "ambiguous", "query": "What welfare programs exist for families living below poverty threshold?", "schemes": ["ignoaps", "pmay-g", "ayushman-bharat-pmjay"]},
    {"id": "IND_27", "cat": "ambiguous", "query": "Credit facility for self-employed traditional worker without bank collateral", "schemes": ["pm-svanidhi", "pm-vishwakarma"]},

    # Category 6: Fabricated Schemes & Unanchored Scams (4 queries - Must Abstain)
    {"id": "IND_28", "cat": "fake", "query": "Pradhan Mantri Free Electric Tesla Car Distribution Scheme 2026", "expected_count": 0},
    {"id": "IND_29", "cat": "fake", "query": "Free Diamond Necklace and Gold Jewelry Scheme for newly married brides", "expected_count": 0},
    {"id": "IND_30", "cat": "fake", "query": "Central Government 50 Lakh Free Cash Jackpot Scheme application", "expected_count": 0},
    {"id": "IND_31", "cat": "fake", "query": "PM Free Solar Powered Private Jet Scheme registration", "expected_count": 0},

    # Category 7: Out-of-Scope / Off-Topic Inquiries (4 queries - Must Abstain)
    {"id": "IND_32", "cat": "unrelated", "query": "How to configure WireGuard VPN on Ubuntu 24.04 server", "expected_count": 0},
    {"id": "IND_33", "cat": "unrelated", "query": "Best traditional ramen restaurants in downtown Osaka", "expected_count": 0},
    {"id": "IND_34", "cat": "unrelated", "query": "Current exchange rate between US Dollars and Swiss Francs", "expected_count": 0},
    {"id": "IND_35", "cat": "unrelated", "query": "Tips for training an energetic golden retriever puppy", "expected_count": 0}
]

@pytest.fixture(scope="module")
def db_session():
    from app.db.session import engine
    from app.db.migrations import ensure_schema_compatibility
    from app.db.seed_data import seed_database
    from app.services.rag.seed_corpus import seed_official_documents_corpus
    
    ensure_schema_compatibility(engine)
    db = SessionLocal()
    seed_database(db)
    seed_official_documents_corpus(db)
    yield db
    db.close()

def test_independent_eval_benchmark_35_queries(db_session):
    """
    Run the 35-query independent evaluation suite.
    Measures Top-1 accuracy, Top-3 recall, false-positive rate, false-negative rate,
    and abstention quality.
    """
    total_scheme_queries = 0
    top1_correct = 0
    top3_correct = 0

    total_abstention_queries = 0
    correct_abstentions = 0
    false_positives = 0
    false_negatives = 0

    results_log = []

    for item in INDEPENDENT_EVAL_SET:
        cat = item["cat"]
        query = item["query"]
        passages = retrieve_grounded_passages(query=query, db=db_session, limit=3)
        slugs = [p.scheme_slug for p in passages]

        if cat in ["fake", "unrelated"]:
            total_abstention_queries += 1
            if len(passages) == 0:
                correct_abstentions += 1
                status = "PASS_ABSTAIN"
            else:
                false_positives += 1
                status = f"FAIL_FP({slugs})"
        elif cat in ["cross_scheme", "ambiguous"]:
            total_scheme_queries += 1
            exp_schemes = item["schemes"]
            matched_top1 = bool(slugs and slugs[0] in exp_schemes)
            matched_top3 = any(s in exp_schemes for s in slugs)
            if matched_top1:
                top1_correct += 1
            if matched_top3:
                top3_correct += 1
            else:
                false_negatives += 1
            status = f"TOP1={matched_top1}, TOP3={matched_top3}"
        else:
            total_scheme_queries += 1
            exp_scheme = item["exp"]
            matched_top1 = bool(slugs and slugs[0] == exp_scheme)
            matched_top3 = bool(exp_scheme in slugs)
            if matched_top1:
                top1_correct += 1
            if matched_top3:
                top3_correct += 1
            else:
                false_negatives += 1
            status = f"TOP1={matched_top1}, TOP3={matched_top3} (retrieved: {slugs[:1]})"

        results_log.append(f"[{item['id']}] {cat:12s} | {status} | Query: {query[:50]}")

    top1_rate = (top1_correct / total_scheme_queries) * 100
    top3_rate = (top3_correct / total_scheme_queries) * 100
    abstention_rate = (correct_abstentions / total_abstention_queries) * 100
    fp_rate = (false_positives / total_abstention_queries) * 100
    fn_rate = (false_negatives / total_scheme_queries) * 100

    print("\n" + "=" * 60)
    print("INDEPENDENT EVALUATION RESULTS (N=35)")
    print("=" * 60)
    for r in results_log:
        print(r)
    print("-" * 60)
    print(f"Scheme Queries (N={total_scheme_queries}):")
    print(f"  Top-1 Accuracy:     {top1_correct}/{total_scheme_queries} ({top1_rate:.1f}%)")
    print(f"  Top-3 Recall:       {top3_correct}/{total_scheme_queries} ({top3_rate:.1f}%)")
    print(f"  False-Negative Rate:{false_negatives}/{total_scheme_queries} ({fn_rate:.1f}%)")
    print(f"Abstention Queries (N={total_abstention_queries}):")
    print(f"  Abstention Quality: {correct_abstentions}/{total_abstention_queries} ({abstention_rate:.1f}%)")
    print(f"  False-Positive Rate:{false_positives}/{total_abstention_queries} ({fp_rate:.1f}%)")
    print("=" * 60)

    # Assertions
    assert top1_rate >= 85.0, f"Expected >=85% Top-1 accuracy, got {top1_rate:.1f}%"
    assert top3_rate >= 85.0, f"Expected >=85% Top-3 recall, got {top3_rate:.1f}%"
    assert abstention_rate == 100.0, f"Expected 100% true negative abstention, got {abstention_rate:.1f}%"
    assert fp_rate == 0.0, f"Expected 0% false positive rate on off-topic/fake queries, got {fp_rate:.1f}%"

def test_regression_two_known_phonetic_typos(db_session):
    """
    Priority 1 explicit regression test for the two previously failing queries:
    1. 'pardon muntri kishaan samann nidhy do hazaar' -> PM-KISAN
    2. 'ayusman bhrat rogoya bima 500000' -> Ayushman Bharat PM-JAY
    """
    # 1. PM-KISAN phonetic failure
    q1 = "pardon muntri kishaan samann nidhy do hazaar"
    p1 = retrieve_grounded_passages(query=q1, db=db_session, limit=3)
    assert len(p1) > 0, f"Query 1 failed to retrieve any passages: {q1}"
    assert p1[0].scheme_slug == "pm-kisan", f"Query 1 Top-1 was {p1[0].scheme_slug}, expected pm-kisan"

    # 2. Ayushman Bharat PM-JAY phonetic failure
    q2 = "ayusman bhrat rogoya bima 500000"
    p2 = retrieve_grounded_passages(query=q2, db=db_session, limit=3)
    assert len(p2) > 0, f"Query 2 failed to retrieve any passages: {q2}"
    assert p2[0].scheme_slug == "ayushman-bharat-pmjay", f"Query 2 Top-1 was {p2[0].scheme_slug}, expected ayushman-bharat-pmjay"
