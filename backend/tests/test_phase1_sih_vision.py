import pytest
import os
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.session import Base, get_db
from app.db.seed_data import seed_database
from app.services.ai.profile_extractor import (
    extract_citizen_profile,
    normalize_indian_currency,
    parse_landholding,
    generate_profile_followups
)
from app.services.rag.retrieval import retrieve_grounded_passages
from app.services.ai.groq_service import generate_grounded_answer
from app.services.eligibility.engine import evaluate_scheme_eligibility

# ---------------------------------------------------------
# Test DB Setup for Endpoint Testing
# ---------------------------------------------------------
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

Base.metadata.create_all(bind=test_engine)
init_db = TestingSessionLocal()
seed_database(init_db)
init_db.close()

client = TestClient(app)

class MockDbScheme:
    def __init__(self, slug, name, department, rules, exclusions=None, states=None):
        self.id = 1
        self.slug = slug
        self.name = name
        self.name_hi = name
        self.summary = f"Summary of {name}"
        self.summary_hi = f"Summary of {name}"
        self.scope = "central"
        self.applicable_states = states or ["ALL"]
        self.department = department
        self.category = "welfare"
        self.beneficiary_types = ["farmers" if "kisan" in slug else "citizens"]
        self.benefits_summary = f"Benefits for {name}"
        self.eligibility_rules = rules
        self.exclusions = exclusions or []
        self.required_documents = [{"name": "Aadhaar Card", "mandatory": True, "alternatives": []}]
        self.application_steps = ["Visit portal", "Submit form"]
        self.official_portal_url = f"https://{slug}.gov.in"
        self.verification_status = "verified"
        self.last_verified_at = "2026-03-01"
        self.sources = []

class MockQuery:
    def __init__(self, items):
        self.items = items
    def filter(self, *args, **kwargs):
        return self
    def all(self):
        return self.items

class MockSession:
    def __init__(self, schemes):
        self._schemes = schemes
    def query(self, model):
        return MockQuery(self._schemes)

# 1. Test Indian Currency Normalization
def test_indian_currency_normalization():
    assert normalize_indian_currency("annual income around ₹1.5 lakh") == 150000.0
    assert normalize_indian_currency("earns 1.5 lakhs per year") == 150000.0
    assert normalize_indian_currency("income of 2 lac") == 200000.0
    assert normalize_indian_currency("earning 50k monthly") == 50000.0
    assert normalize_indian_currency("salary 50 thousand") == 50000.0
    assert normalize_indian_currency("income ₹1,50,000") == 150000.0
    assert normalize_indian_currency("no income mentioned") is None

# 2. Test Landholding & Regional Bigha Handling
def test_bigha_handling_bihar():
    owns, raw, acres, notes = parse_landholding("two bighas of land", "Bihar")
    assert owns is True
    assert "2" in raw and "bigha" in raw
    assert "In Bihar, 1 pucca bigha is ~0.62 acres" in notes
    assert "survey definitions vary" in notes

def test_bigha_handling_unknown_state():
    owns, raw, acres, notes = parse_landholding("have three bighas", None)
    assert owns is True
    assert "3" in raw and "bigha" in raw
    assert acres is None
    assert "State location required" in notes

def test_landless_citizen():
    owns, raw, acres, notes = parse_landholding("I am a landless laborer without land", "Bihar")
    assert owns is False
    assert raw == "0"

# 3. Test Full Benchmark Query Extraction
def test_benchmark_bihar_farmer_extraction():
    query = (
        "A farmer from Bihar speaks in Bhojpuri and says they have three children, "
        "two bighas of land, and annual income around ₹1.5 lakh. Which government schemes might they qualify for?"
    )
    profile = extract_citizen_profile(query)
    
    assert profile["occupation"] == "farmer"
    assert profile["state"] == "Bihar"
    assert profile["annual_income"] == 150000.0
    assert profile["owns_cultivable_land"] is True
    assert "2" in profile["landholding_raw"] and "bigha" in profile["landholding_raw"]
    assert profile["family_details"].get("children_count") == 3
    assert profile["is_govt_employee"] is None
    assert profile["pays_income_tax"] is None
    assert profile["is_bpl"] is None

# 4. Test Scheme Retrieval Ranking for Benchmark Query
def test_benchmark_retrieval_ranking():
    kisan = MockDbScheme("pm-kisan", "PM-KISAN", "Ministry of Agriculture", {"landholding_required": True})
    pmmvy = MockDbScheme("pmmvy", "PMMVY (Matru Vandana)", "Ministry of Women & Child Development", {"first_child": True})
    ignoaps = MockDbScheme("ignoaps", "IGNOAPS (Old Age Pension)", "Ministry of Rural Development", {"min_age": 60})
    pmay = MockDbScheme("pmay-g", "PMAY-G (Gramin Awas)", "Ministry of Rural Development", {"kutcha_house": True})

    db = MockSession([kisan, pmmvy, ignoaps, pmay])
    query = (
        "A farmer from Bihar speaks in Bhojpuri and says they have three children, "
        "two bighas of land, and annual income around ₹1.5 lakh. Which government schemes might they qualify for?"
    )
    passages = retrieve_grounded_passages(query, db, limit=4)
    top_slugs = [p.scheme_slug for p in passages]

    assert passages[0].scheme_slug == "pm-kisan"
    assert "pmmvy" not in top_slugs[:2]
    assert "ignoaps" not in top_slugs[:2]

# 5. Test Missing Criteria & Follow-Up Generation
def test_missing_criteria_follow_up():
    profile = {
        "state": "Bihar",
        "occupation": "farmer",
        "owns_cultivable_land": True,
        "annual_income": 150000.0,
        "is_govt_employee": None,
        "pays_income_tax": None
    }
    missing, prompt = generate_profile_followups(profile, ["pm-kisan"])
    assert len(missing) >= 2
    assert prompt is not None
    assert "income tax" in prompt.lower() or "government" in prompt.lower()

# 6. Test Deterministic Eligibility Evaluation with Extracted Profile
def test_eligibility_evaluation_with_profile():
    kisan = MockDbScheme("pm-kisan", "PM-KISAN", "Ministry of Agriculture", {
        "is_govt_employee": False,
        "income_tax_payer": False,
        "landholding_required": True
    })
    profile_partial = {
        "state": "Bihar",
        "occupation": "farmer",
        "owns_cultivable_land": True,
        "is_govt_employee": None,
        "pays_income_tax": None
    }
    res = evaluate_scheme_eligibility(kisan, profile_partial)
    assert res.status == "possibly_eligible"
    assert len(res.unknown_conditions) > 0

    profile_full = {
        "state": "Bihar",
        "occupation": "farmer",
        "owns_cultivable_land": True,
        "is_govt_employee": False,
        "pays_income_tax": False
    }
    res_full = evaluate_scheme_eligibility(kisan, profile_full)
    assert res_full.status == "eligible"
    assert len(res_full.unsatisfied_conditions) == 0

# 7. Test AI Provider: Fallback when GROQ_API_KEY is not set
@pytest.mark.asyncio
async def test_groq_fallback_when_unconfigured():
    with patch("app.core.config.settings.GROQ_API_KEY", ""):
        kisan = MockDbScheme("pm-kisan", "PM-KISAN", "Ministry of Agriculture", {})
        db = MockSession([kisan])
        passages = retrieve_grounded_passages("farmer PM-KISAN support", db, limit=1)

        result = await generate_grounded_answer(
            query="Tell me about PM-KISAN",
            passages=passages,
            preferred_language="en"
        )
        assert result["is_fallback"] is True
        assert result["status"] == "fallback_grounded"
        assert result["ai_provider"] == "none"
        assert "Notice: Live AI generation is currently offline" in result["answer"]

# 8. Test AI Provider: Mocked Groq success
@pytest.mark.asyncio
async def test_groq_success_mock():
    mock_response = {
        "choices": [
            {
                "message": {
                    "content": "PM-KISAN provides ₹6,000 yearly in 3 equal installments to landholding farmer families. [Passage 1]"
                }
            }
        ]
    }
    with patch("app.core.config.settings.GROQ_API_KEY", "gsk_test_mock_key_12345"):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = AsyncMock(status_code=200, json=lambda: mock_response)
            kisan = MockDbScheme("pm-kisan", "PM-KISAN", "Ministry of Agriculture", {})
            db = MockSession([kisan])
            passages = retrieve_grounded_passages("PM-KISAN", db, limit=1)

            result = await generate_grounded_answer(
                query="Tell me about PM-KISAN",
                passages=passages,
                preferred_language="en"
            )
            assert result["is_fallback"] is False
            assert result["status"] == "success"
            assert result["ai_provider"] == "groq"
            assert "PM-KISAN provides ₹6,000" in result["answer"]

# 9. End-to-End Endpoint Test: Benchmark Citizen Query
def test_e2e_assistant_chat_benchmark_query():
    query = (
        "A farmer from Bihar speaks in Bhojpuri and says they have three children, "
        "two bighas of land, and annual income around ₹1.5 lakh. Which government schemes might they qualify for?"
    )
    res = client.post("/api/assistant/chat", json={"query": query, "preferred_language": "en"})
    assert res.status_code == 200
    data = res.json()

    # Fact extraction verified
    prof = data["extracted_profile"]
    assert prof["occupation"] == "farmer"
    assert prof["state"] == "Bihar"
    assert prof["annual_income"] == 150000.0
    assert prof["owns_cultivable_land"] is True
    assert "bigha" in prof["landholding_raw"]

    # Retrieval ranking verified
    assert data["citations"][0]["scheme_slug"] == "pm-kisan"
    assert not any(c["scheme_slug"] in ["pmmvy", "ignoaps"] for c in data["citations"][:2])

    # Eligibility evaluation verified
    evals = data["eligibility_results"]
    assert len(evals) > 0
    kisan_eval = next(e for e in evals if e["scheme_slug"] == "pm-kisan")
    assert kisan_eval["status"] == "possibly_eligible"  # Needs tax & govt employee confirmation

    # Follow-up prompt verified
    assert data["follow_up_prompt"] is not None
    assert "income tax" in data["follow_up_prompt"].lower() or "government" in data["follow_up_prompt"].lower()

    # Application prefill action verified
    action = data["suggested_action"]
    assert action is not None
    assert action["action"] == "prepare_application"
    assert action["scheme_slug"] == "pm-kisan"
    assert action["prefill_data"]["state"] == "Bihar"
    assert action["prefill_data"]["annual_income"] == 150000.0

# 10. Multi-Turn Conversation Memory Test
def test_e2e_assistant_multi_turn_memory():
    # Turn 1
    t1_res = client.post("/api/assistant/chat", json={
        "query": "I am a farmer in Bihar with 2 bighas of land and annual income around ₹1.5 lakh."
    })
    t1_data = t1_res.json()
    profile_t1 = t1_data["extracted_profile"]

    # Turn 2: User answers follow-up about income tax and government employment
    t2_res = client.post("/api/assistant/chat", json={
        "query": "I do not pay income tax and no one in my family is a govt employee.",
        "existing_profile": profile_t1
    })
    t2_data = t2_res.json()
    profile_t2 = t2_data["extracted_profile"]

    # Check merged facts
    assert profile_t2["occupation"] == "farmer"
    assert profile_t2["state"] == "Bihar"
    assert profile_t2["annual_income"] == 150000.0
    assert profile_t2["pays_income_tax"] is False
    assert profile_t2["is_govt_employee"] is False

    # Check that PM-KISAN is now officially CONFIRMED ELIGIBLE!
    evals = t2_data["eligibility_results"]
    kisan_eval = next(e for e in evals if e["scheme_slug"] == "pm-kisan")
    assert kisan_eval["status"] == "eligible"
    assert len(kisan_eval["unsatisfied_conditions"]) == 0

# 11. Optional Live Groq Smoke Test (only runs if GROQ_API_KEY is present in env)
@pytest.mark.asyncio
async def test_live_groq_smoke_test_if_configured():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        pytest.skip("GROQ_API_KEY is not configured in local environment; skipping live smoke test.")
    
    kisan = MockDbScheme("pm-kisan", "PM-KISAN", "Ministry of Agriculture", {})
    db = MockSession([kisan])
    passages = retrieve_grounded_passages("PM-KISAN farmer support", db, limit=1)

    result = await generate_grounded_answer(
        query="What is the benefit under PM-KISAN?",
        passages=passages,
        preferred_language="en"
    )
    assert result["is_fallback"] is False
    assert result["status"] == "success"
    assert result["ai_provider"] == "groq"
    assert len(result["answer"]) > 50
