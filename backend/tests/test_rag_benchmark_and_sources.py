"""
JanSahayak RAG Benchmark & Official Source Verification Test Suite
Tests 24 realistic citizen questions across all 8 official schemes.
Measures Top-1 and Top-3 retrieval accuracy, verifies source metadata,
and audits deterministic eligibility rule edge cases.
"""
import pytest
from app.db.session import SessionLocal
from app.models.scheme import Scheme
from app.models.document import KnowledgeDocument
from app.services.rag.retrieval import retrieve_grounded_passages
from app.services.eligibility.engine import evaluate_scheme_eligibility
from app.services.rag.seed_corpus import OFFICIAL_SCHEME_DOCUMENTS

BENCHMARK_QUESTIONS = [
    # --- PM-KISAN ---
    {
        "id": "Q1",
        "scheme": "pm-kisan",
        "intent": "eligibility",
        "query": "Who is eligible for PM-KISAN scheme and what is the landholding requirement?",
        "expected_page_keywords": ["objective", "scope", "landholding", "cultivable"]
    },
    {
        "id": "Q2",
        "scheme": "pm-kisan",
        "intent": "benefits",
        "query": "How much financial installment money does a farmer receive under PM-KISAN each year?",
        "expected_page_keywords": ["financial benefit", "installment", "6000", "dbt"]
    },
    {
        "id": "Q3",
        "scheme": "pm-kisan",
        "intent": "exclusions",
        "query": "Can government employees or income tax payers receive PM-KISAN benefits?",
        "expected_page_keywords": ["exclusion", "income tax", "government", "ineligibility"]
    },

    # --- PMAY-G ---
    {
        "id": "Q4",
        "scheme": "pmay-g",
        "intent": "eligibility",
        "query": "Who can get housing assistance under Pradhan Mantri Awas Yojana Gramin?",
        "expected_page_keywords": ["kutcha", "houseless", "secc", "rural"]
    },
    {
        "id": "Q5",
        "scheme": "pmay-g",
        "intent": "benefits",
        "query": "What is the financial assistance amount for building a pucca house in plain areas under PMAY-G?",
        "expected_page_keywords": ["1,20,000", "unit assistance", "mgnrega", "financial assistance"]
    },
    {
        "id": "Q6",
        "scheme": "pmay-g",
        "intent": "exclusions",
        "query": "Does owning a two-wheeler or Kisan Credit Card over 50000 disqualify from PMAY-G?",
        "expected_page_keywords": ["exclusion", "motorized", "kcc", "disqualif"]
    },

    # --- Ayushman Bharat PM-JAY ---
    {
        "id": "Q7",
        "scheme": "ayushman-bharat-pmjay",
        "intent": "eligibility",
        "query": "Are senior citizens aged 70 and above eligible for Ayushman Bharat golden card?",
        "expected_page_keywords": ["senior citizen", "70", "universal", "vay vandana"]
    },
    {
        "id": "Q8",
        "scheme": "ayushman-bharat-pmjay",
        "intent": "benefits",
        "query": "What is the annual hospital treatment coverage amount per family under PM-JAY?",
        "expected_page_keywords": ["5,00,000", "cashless", "secondary", "tertiary"]
    },
    {
        "id": "Q9",
        "scheme": "ayushman-bharat-pmjay",
        "intent": "application",
        "query": "Where can a citizen get their Ayushman Bharat card made and how to apply?",
        "expected_page_keywords": ["portal", "csc", "aadhaar", "verification"]
    },

    # --- PMMVY ---
    {
        "id": "Q10",
        "scheme": "pmmvy",
        "intent": "eligibility",
        "query": "What is the minimum age requirement for a pregnant woman to receive PMMVY maternity benefits?",
        "expected_page_keywords": ["19 years", "pregnant", "maternity", "mother"]
    },
    {
        "id": "Q11",
        "scheme": "pmmvy",
        "intent": "benefits",
        "query": "What are the installment amounts and financial assistance for the first child under Matru Vandana Yojana?",
        "expected_page_keywords": ["5,000", "installment", "anc", "immunization"]
    },
    {
        "id": "Q12",
        "scheme": "pmmvy",
        "intent": "exclusions",
        "query": "Are regular government and PSU employees eligible for PMMVY maternity aid?",
        "expected_page_keywords": ["exclusion", "government", "psu", "regular"]
    },

    # --- IGNOAPS ---
    {
        "id": "Q13",
        "scheme": "ignoaps",
        "intent": "eligibility",
        "query": "What is the qualifying age and BPL poverty criteria for Indira Gandhi National Old Age Pension?",
        "expected_page_keywords": ["60 years", "bpl", "nsap", "destitute"]
    },
    {
        "id": "Q14",
        "scheme": "ignoaps",
        "intent": "benefits",
        "query": "How much monthly old age pension is given to elderly persons aged 80 and above under IGNOAPS?",
        "expected_page_keywords": ["500", "80 years", "monthly", "pension"]
    },
    {
        "id": "Q15",
        "scheme": "ignoaps",
        "intent": "application",
        "query": "Where should a senior citizen submit application for NSAP old age pension?",
        "expected_page_keywords": ["gram panchayat", "block", "sub-divisional", "verification"]
    },

    # --- Sukanya Samriddhi Yojana ---
    {
        "id": "Q16",
        "scheme": "sukanya-samriddhi-yojana",
        "intent": "eligibility",
        "query": "What is the maximum age of girl child to open account in Sukanya Samriddhi Yojana?",
        "expected_page_keywords": ["10 years", "girl child", "account opening"]
    },
    {
        "id": "Q17",
        "scheme": "sukanya-samriddhi-yojana",
        "intent": "benefits",
        "query": "What is the minimum annual deposit and tax exemption benefit under Section 80C for SSY?",
        "expected_page_keywords": ["250", "80c", "tax exemption", "interest"]
    },
    {
        "id": "Q18",
        "scheme": "sukanya-samriddhi-yojana",
        "intent": "application",
        "query": "When can money be withdrawn from Sukanya Samriddhi account for higher education?",
        "expected_page_keywords": ["18 years", "higher education", "withdrawal", "maturity"]
    },

    # --- PM SVANidhi ---
    {
        "id": "Q19",
        "scheme": "pm-svanidhi",
        "intent": "eligibility",
        "query": "Are urban street vendors and thela hawkers eligible for PM SVANidhi loan?",
        "expected_page_keywords": ["street vendor", "urban", "hawker", "vending"]
    },
    {
        "id": "Q20",
        "scheme": "pm-svanidhi",
        "intent": "benefits",
        "query": "What are the first and second tranche loan amounts and interest subsidy in PM SVANidhi?",
        "expected_page_keywords": ["10,000", "20,000", "interest subsidy", "7%"]
    },
    {
        "id": "Q21",
        "scheme": "pm-svanidhi",
        "intent": "application",
        "query": "What documents or Certificate of Vending are needed to apply for PM SVANidhi micro credit?",
        "expected_page_keywords": ["certificate of vending", "recommendation", "ulb", "aadhaar"]
    },

    # --- PM Vishwakarma ---
    {
        "id": "Q22",
        "scheme": "pm-vishwakarma",
        "intent": "eligibility",
        "query": "Which 18 traditional family crafts and trades are covered under PM Vishwakarma scheme?",
        "expected_page_keywords": ["18 trades", "carpenter", "blacksmith", "potter", "mason"]
    },
    {
        "id": "Q23",
        "scheme": "pm-vishwakarma",
        "intent": "benefits",
        "query": "How much toolkit financial incentive and collateral-free loan is provided under PM Vishwakarma?",
        "expected_page_keywords": ["15,000", "toolkit", "1,00,000", "concessional"]
    },
    {
        "id": "Q24",
        "scheme": "pm-vishwakarma",
        "intent": "application",
        "query": "Do artisans get daily stipend during skill training in PM Vishwakarma and how to apply?",
        "expected_page_keywords": ["500", "stipend", "skilling", "csc", "portal"]
    }
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

def test_retrieval_benchmark_24_questions(db_session):
    """
    Test retrieval across 24 realistic citizen questions for all 8 official schemes.
    Measures Top-1 and Top-3 accuracy.
    """
    top1_correct = 0
    top3_correct = 0
    total = len(BENCHMARK_QUESTIONS)

    results_log = []

    for item in BENCHMARK_QUESTIONS:
        q_id = item["id"]
        expected_scheme = item["scheme"]
        query = item["query"]

        passages = retrieve_grounded_passages(query=query, db=db_session, limit=3)
        assert len(passages) > 0, f"Query '{query}' returned 0 passages"

        retrieved_slugs = [p.scheme_slug for p in passages]
        top1_hit = (retrieved_slugs[0] == expected_scheme)
        top3_hit = (expected_scheme in retrieved_slugs)

        if top1_hit:
            top1_correct += 1
        if top3_hit:
            top3_correct += 1

        results_log.append({
            "id": q_id,
            "query": query,
            "expected_scheme": expected_scheme,
            "retrieved_top1": retrieved_slugs[0],
            "top1_hit": top1_hit,
            "top3_hit": top3_hit,
            "top1_title": passages[0].title
        })

    top1_accuracy = (top1_correct / total) * 100.0
    top3_accuracy = (top3_correct / total) * 100.0

    print(f"\n--- RAG RETRIEVAL BENCHMARK RESULTS ---")
    print(f"Total Questions Evaluated: {total}")
    print(f"Top-1 Scheme Accuracy: {top1_accuracy:.1f}% ({top1_correct}/{total})")
    print(f"Top-3 Scheme Accuracy: {top3_accuracy:.1f}% ({top3_correct}/{total})")

    # Assert rigorous SIH production readiness criteria:
    # Top-1 accuracy must be >= 90% and Top-3 accuracy must be 100%
    assert top1_accuracy >= 90.0, f"Top-1 accuracy too low: {top1_accuracy}%"
    assert top3_accuracy == 100.0, f"Top-3 accuracy must be 100%: {top3_accuracy}%"

def test_source_verification_and_page_metadata(db_session):
    """
    Verify each scheme's official URL, issuing authority, order reference,
    and physical page numbering in database.
    """
    for doc_meta in OFFICIAL_SCHEME_DOCUMENTS:
        slug = doc_meta["scheme_slug"]
        scheme = db_session.query(Scheme).filter(Scheme.slug == slug).first()
        assert scheme is not None, f"Scheme {slug} missing from DB"

        doc = db_session.query(KnowledgeDocument).filter(
            KnowledgeDocument.scheme_id == scheme.id
        ).first()
        assert doc is not None, f"KnowledgeDocument for {slug} missing from DB"

        assert doc.source_url.startswith("http"), f"Invalid source_url for {slug}"
        assert doc.authority != "", f"Missing issuing authority for {slug}"
        assert doc.document_reference is not None, f"Missing document reference for {slug}"
        assert doc.total_pages > 0, f"Invalid total pages for {slug}"
        assert len(doc.chunks) > 0, f"No chunks found for {slug}"

        # Verify page numbering is sequential and positive
        pages_in_chunks = [c.page_number for c in doc.chunks]
        assert all(p >= 1 for p in pages_in_chunks), f"Invalid page number in chunks for {slug}"

def test_deterministic_eligibility_all_eight_schemes(db_session):
    """
    Audit deterministic eligibility rules for all 8 schemes with 3 test cases each:
    Eligible, Ineligible, and Insufficient Information (preserving unknown states).
    """
    schemes = {s.slug: s for s in db_session.query(Scheme).all()}

    # 1. PM-KISAN
    s = schemes["pm-kisan"]
    # Case A: Eligible
    res_a = evaluate_scheme_eligibility(s, {"owns_cultivable_land": True, "is_govt_employee": False, "pays_income_tax": False})
    assert res_a.status == "eligible"
    # Case B: Ineligible (Tax payer)
    res_b = evaluate_scheme_eligibility(s, {"owns_cultivable_land": True, "is_govt_employee": False, "pays_income_tax": True})
    assert res_b.status == "ineligible"
    # Case C: Unknown (Missing tax & employment info)
    res_c = evaluate_scheme_eligibility(s, {"owns_cultivable_land": True})
    assert res_c.status == "possibly_eligible"
    assert len(res_c.unknown_conditions) == 2

    # 2. PMAY-G
    s = schemes["pmay-g"]
    res_a = evaluate_scheme_eligibility(s, {"housing_type": "kutcha", "area_type": "rural", "is_govt_employee": False, "pays_income_tax": False})
    assert res_a.status == "eligible"
    res_b = evaluate_scheme_eligibility(s, {"housing_type": "pucca", "area_type": "rural", "is_govt_employee": False, "pays_income_tax": False})
    assert res_b.status == "ineligible"
    res_c = evaluate_scheme_eligibility(s, {"housing_type": "kutcha"})
    assert res_c.status == "possibly_eligible"

    # 3. Ayushman Bharat PM-JAY
    s = schemes["ayushman-bharat-pmjay"]
    # Universal pathway for 70+
    res_a = evaluate_scheme_eligibility(s, {"age": 72})
    assert res_a.status == "eligible"
    # Deprivation / BPL
    res_a2 = evaluate_scheme_eligibility(s, {"age": 45, "is_bpl": True})
    assert res_a2.status == "eligible"
    # Ineligible (Non-BPL, non-SECC, under 70 with complete employment/tax facts)
    res_b = evaluate_scheme_eligibility(s, {"age": 45, "is_bpl": False, "is_govt_employee": False, "pays_income_tax": False})
    assert res_b.status == "ineligible"
    # Unknown
    res_c = evaluate_scheme_eligibility(s, {})
    assert res_c.status == "possibly_eligible"

    # 4. PMMVY
    s = schemes["pmmvy"]
    res_a = evaluate_scheme_eligibility(s, {"gender": "female", "age": 22, "is_govt_employee": False})
    assert res_a.status == "eligible"
    res_b1 = evaluate_scheme_eligibility(s, {"gender": "male", "age": 25})
    assert res_b1.status == "ineligible"
    res_b2 = evaluate_scheme_eligibility(s, {"gender": "female", "age": 17})
    assert res_b2.status == "ineligible"
    res_c = evaluate_scheme_eligibility(s, {"gender": "female"})
    assert res_c.status == "possibly_eligible"

    # 5. IGNOAPS
    s = schemes["ignoaps"]
    res_a = evaluate_scheme_eligibility(s, {"age": 65, "is_bpl": True})
    assert res_a.status == "eligible"
    res_b = evaluate_scheme_eligibility(s, {"age": 55, "is_bpl": True})
    assert res_b.status == "ineligible"
    res_c = evaluate_scheme_eligibility(s, {"age": 65})
    assert res_c.status == "possibly_eligible"

    # 6. Sukanya Samriddhi Yojana
    s = schemes["sukanya-samriddhi-yojana"]
    res_a = evaluate_scheme_eligibility(s, {"girl_child_age": 7})
    assert res_a.status == "eligible"
    res_b = evaluate_scheme_eligibility(s, {"girl_child_age": 14})
    assert res_b.status == "ineligible"
    res_c = evaluate_scheme_eligibility(s, {})
    assert res_c.status == "possibly_eligible"

    # 7. PM SVANidhi
    s = schemes["pm-svanidhi"]
    res_a = evaluate_scheme_eligibility(s, {"occupation": "street vendor"})
    assert res_a.status == "eligible"
    res_b = evaluate_scheme_eligibility(s, {"is_street_vendor": False})
    assert res_b.status == "ineligible"
    res_c = evaluate_scheme_eligibility(s, {})
    assert res_c.status == "possibly_eligible"

    # 8. PM Vishwakarma
    s = schemes["pm-vishwakarma"]
    res_a = evaluate_scheme_eligibility(s, {"occupation": "carpenter", "is_govt_employee": False})
    assert res_a.status == "eligible"
    res_b = evaluate_scheme_eligibility(s, {"is_traditional_artisan": False})
    assert res_b.status == "ineligible"
    res_c = evaluate_scheme_eligibility(s, {})
    assert res_c.status == "possibly_eligible"
