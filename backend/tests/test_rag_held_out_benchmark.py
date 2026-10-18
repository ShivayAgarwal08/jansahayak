"""
JanSahayak 40-Query Held-Out Retrieval Benchmark Test Suite
Covers 7 distinct realistic scenarios:
- Indirect Descriptions without Scheme Names
- Hinglish Natural Phrasing
- Misspellings & Phonetic Typos
- Traditional Occupations & Crafts
- Ambiguous Cross-Scheme Requests
- Out-of-Scope / Unrelated Queries (Abstention)
- Adversarial Fake Schemes (Abstention)
"""
import pytest
from app.db.session import SessionLocal
from app.services.rag.retrieval import retrieve_grounded_passages

HELD_OUT_BENCHMARK = [
    # Category 1: Indirect Descriptions without Scheme Names (8 queries)
    {"id": "H01", "cat": "indirect", "query": "I cultivate 3 acres of paddy field and need financial support for purchasing seasonal seeds.", "exp": "pm-kisan"},
    {"id": "H02", "cat": "indirect", "query": "My family lives in a dilapidated mud hut in our village panchayat and the roof leaks during monsoon.", "exp": "pmay-g"},
    {"id": "H03", "cat": "indirect", "query": "My 73 year old mother needs gallbladder surgery at a private empanelled hospital.", "exp": "ayushman-bharat-pmjay"},
    {"id": "H04", "cat": "indirect", "query": "A 21 year old rural woman is pregnant with her first baby and attending anganwadi checkups.", "exp": "pmmvy"},
    {"id": "H05", "cat": "indirect", "query": "An 82 year old destitute widow living in extreme poverty needs monthly financial sustenance.", "exp": "ignoaps"},
    {"id": "H06", "cat": "indirect", "query": "I want to deposit monthly savings for my 3 year old daughter to fund her university fees later.", "exp": "sukanya-samriddhi-yojana"},
    {"id": "H07", "cat": "indirect", "query": "Selling roasted corn on a wooden cart by the roadside, need money to restock inventory.", "exp": "pm-svanidhi"},
    {"id": "H08", "cat": "indirect", "query": "Traditional village carpenter making wooden cots and doors with hand tools seeking grant for modern electric saw.", "exp": "pm-vishwakarma"},

    # Category 2: Hinglish & Transliterated Natural Phrasing (8 queries)
    {"id": "H09", "cat": "hinglish", "query": "khet me kheti karne ke liye sarkar se saal ka 6000 rupaye kaise milta hai?", "exp": "pm-kisan"},
    {"id": "H10", "cat": "hinglish", "query": "gaon me kachha ghar hai pakka makan banane ke liye aavedan kaise kare?", "exp": "pmay-g"},
    {"id": "H11", "cat": "hinglish", "query": "hospital me 5 lakh tak ka free ilaj karane ke liye golden card kaise banta hai?", "exp": "ayushman-bharat-pmjay"},
    {"id": "H12", "cat": "hinglish", "query": "garbhavati mahila ko pehle bacche ke janm par 5000 ki rashi kab milti hai?", "exp": "pmmvy"},
    {"id": "H13", "cat": "hinglish", "query": "meri dadi ki umar 65 saal hai aur hum bpl parivar se hain unki vridha pension kaise chalu hogi?", "exp": "ignoaps"},
    {"id": "H14", "cat": "hinglish", "query": "chhoti beti ke naam par post office me khata kholna hai kitna byaj milta hai?", "exp": "sukanya-samriddhi-yojana"},
    {"id": "H15", "cat": "hinglish", "query": "sadak kinare phal bechta hu bina guarantee 10000 ka loan chahiye", "exp": "pm-svanidhi"},
    {"id": "H16", "cat": "hinglish", "query": "hum lohar hain lohe ka auzar banate hain vishwakarma scheme me training stipend aur toolkit milega?", "exp": "pm-vishwakarma"},

    # Category 3: Misspellings and Phonetic Typos (6 queries)
    {"id": "H17", "cat": "typo", "query": "pm kisaan samman nidhy land record verification khatauni", "exp": "pm-kisan"},
    {"id": "H18", "cat": "typo", "query": "pradhan mantri aawas yojana gramin kutcha makaan list", "exp": "pmay-g"},
    {"id": "H19", "cat": "typo", "query": "aayushman bhart pmjaay card eligibility 70 years", "exp": "ayushman-bharat-pmjay"},
    {"id": "H20", "cat": "typo", "query": "matru vandana pmmvi scheme first chid 5000", "exp": "pmmvy"},
    {"id": "H21", "cat": "typo", "query": "sukanya samridhi beti age ten years document", "exp": "sukanya-samriddhi-yojana"},
    {"id": "H22", "cat": "typo", "query": "pm svanidi thela hawker certficate of vending", "exp": "pm-svanidhi"},

    # Category 4: Traditional Occupations & Crafts (6 queries)
    {"id": "H23", "cat": "occupation", "query": "Sculptor carving stone statues and idols by hand seeking assistance for purchasing diamond chisels", "exp": "pm-vishwakarma"},
    {"id": "H24", "cat": "occupation", "query": "Goldsmith repairing gold and silver ornaments in small rural bazaar wanting loan for workspace", "exp": "pm-vishwakarma"},
    {"id": "H25", "cat": "occupation", "query": "Traditional cobbler repairing leather shoes on footpath footpath worker", "exp": "pm-vishwakarma", "alt": "pm-svanidhi"},
    {"id": "H26", "cat": "occupation", "query": "Tea stall vendor running small chai thela near railway station seeking working capital", "exp": "pm-svanidhi"},
    {"id": "H27", "cat": "occupation", "query": "Tenant cultivator farming on leased land without registered ownership deed in patta records", "exp": "pm-kisan"},
    {"id": "H28", "cat": "occupation", "query": "Barber cutting hair in small village shop applying for modern grooming equipment", "exp": "pm-vishwakarma"},

    # Category 5: Ambiguous / Cross-Scheme Requests (4 queries)
    {"id": "H29", "cat": "ambiguous", "query": "Central government monetary aid for rural poor families with elderly persons", "schemes": ["ignoaps", "pmay-g"]},
    {"id": "H30", "cat": "ambiguous", "query": "Government financial grants and DBT transfers for women welfare", "schemes": ["pmmvy", "sukanya-samriddhi-yojana"]},
    {"id": "H31", "cat": "ambiguous", "query": "Collateral-free low-interest loan for urban self-employed worker", "schemes": ["pm-svanidhi", "pm-vishwakarma"]},
    {"id": "H32", "cat": "ambiguous", "query": "Health treatment and financial security for senior citizens aged above 60", "schemes": ["ayushman-bharat-pmjay", "ignoaps"]},

    # Category 6: Out-of-Scope / Unrelated Queries (Should return 0 passages / Abstain) (4 queries)
    {"id": "H33", "cat": "unrelated", "query": "What is the live score in the India vs Australia cricket match?", "expected_count": 0},
    {"id": "H34", "cat": "unrelated", "query": "Recipe for chocolate chip cookies with butter and vanilla", "expected_count": 0},
    {"id": "H35", "cat": "unrelated", "query": "How to debug a NullPointerException in Java programming?", "expected_count": 0},
    {"id": "H36", "cat": "unrelated", "query": "Flight ticket booking from New Delhi to London Heathrow", "expected_count": 0},

    # Category 7: Adversarial / Fake Scheme Inventions (Should return 0 passages / Abstain) (4 queries)
    {"id": "H37", "cat": "fake", "query": "Pradhan Mantri Free Smartphone and Gold iPhone Scheme 2026 application form", "expected_count": 0},
    {"id": "H38", "cat": "fake", "query": "Central Government 10 Lakh Free Cash Giveaway Lottery Yojana online registration", "expected_count": 0},
    {"id": "H39", "cat": "fake", "query": "PM Free Luxury Helicopter Transport Scheme for private citizens", "expected_count": 0},
    {"id": "H40", "cat": "fake", "query": "Pradhan Mantri Bitcoin and Cryptocurrency Double Profit Scheme", "expected_count": 0}
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

def test_held_out_benchmark_40_queries(db_session):
    """
    Evaluate 40 realistic held-out queries covering indirect descriptions, Hinglish,
    typos, crafts, ambiguous queries, and adversarial / out-of-scope abstention.
    """
    total_scheme_queries = 0
    top1_correct = 0
    top3_correct = 0

    total_abstention_queries = 0
    correct_abstentions = 0

    for item in HELD_OUT_BENCHMARK:
        cat = item["cat"]
        query = item["query"]
        passages = retrieve_grounded_passages(query=query, db=db_session, limit=3)
        slugs = [p.scheme_slug for p in passages]

        if cat in ["unrelated", "fake"]:
            total_abstention_queries += 1
            if len(passages) == 0:
                correct_abstentions += 1
        elif cat == "ambiguous":
            total_scheme_queries += 1
            exp_schemes = item["schemes"]
            if any(s in slugs[:1] for s in exp_schemes):
                top1_correct += 1
            if any(s in slugs for s in exp_schemes):
                top3_correct += 1
        else:
            total_scheme_queries += 1
            exp_scheme = item["exp"]
            alt_scheme = item.get("alt")
            if slugs and (slugs[0] == exp_scheme or (alt_scheme and slugs[0] == alt_scheme)):
                top1_correct += 1
            if exp_scheme in slugs or (alt_scheme and alt_scheme in slugs):
                top3_correct += 1

    scheme_top1_rate = (top1_correct / total_scheme_queries) * 100
    scheme_top3_rate = (top3_correct / total_scheme_queries) * 100
    abstention_rate = (correct_abstentions / total_abstention_queries) * 100

    assert scheme_top1_rate == 100.0, f"Expected 100% Top-1, got {scheme_top1_rate}%"
    assert scheme_top3_rate == 100.0, f"Expected 100% Top-3, got {scheme_top3_rate}%"
    assert abstention_rate == 100.0, f"Expected 100% true negative abstention, got {abstention_rate}%"
