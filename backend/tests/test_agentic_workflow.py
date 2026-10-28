import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import get_db
from app.models.scheme import Scheme
from app.services.ai.profile_extractor import (
    extract_citizen_profile,
    classify_profile_facts,
    detect_profile_contradictions,
    detect_query_language,
    clean_speech_text,
    generate_profile_followups
)
from app.services.eligibility.engine import evaluate_scheme_eligibility
from app.db.seed_data import seed_database
from app.services.rag.seed_corpus import seed_official_documents_corpus

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="module", autouse=True)
def ensure_db_seeded():
    db = next(get_db())
    try:
        seed_database(db)
        seed_official_documents_corpus(db)
    finally:
        db.close()

# -------------------------------------------------------------------------
# 1. Fact Classification & Privacy Protection Tests
# -------------------------------------------------------------------------

def test_fact_classification_and_sensitive_privacy():
    raw_query = "I am a farmer from Bihar with 2 acres of land and my annual income is ₹1.5 lakh."
    profile = extract_citizen_profile(raw_query)
    classified = classify_profile_facts(profile, raw_query)

    confirmed = classified["confirmed"]
    inferred = classified["inferred"]
    contradictions = classified["contradictions"]

    # Explicit facts must be confirmed
    assert confirmed.get("occupation") == "farmer"
    assert confirmed.get("state") == "Bihar"
    assert confirmed.get("annual_income") == 150000.0
    assert confirmed.get("owns_cultivable_land") is True
    assert confirmed.get("landholding_acres") == 2.0

    # Sensitive attributes MUST NOT be guessed or inferred
    assert "caste" not in confirmed
    assert "caste" not in inferred
    assert "religion" not in confirmed
    assert "religion" not in inferred
    assert "disability" not in confirmed
    assert "disability" not in inferred

    # No contradictions
    assert len(contradictions) == 0

def test_contradiction_detection():
    # Contradiction: 0 land but reporting 3 acres
    conflicted_profile = {
        "owns_cultivable_land": False,
        "landholding_acres": 3.0,
        "annual_income": 2000000.0,
        "pays_income_tax": False,
        "age": 12,
        "is_govt_employee": True
    }
    contradictions = detect_profile_contradictions(conflicted_profile)
    assert len(contradictions) >= 2
    # Land conflict flagged
    assert any("cultivable land" in c.lower() for c in contradictions)
    # Income/Tax conflict flagged
    assert any("income" in c.lower() and "tax" in c.lower() for c in contradictions)
    # Child age vs govt employee flagged
    assert any("government employee" in c.lower() for c in contradictions)

# -------------------------------------------------------------------------
# 2. Language Detection & Speech Normalization Tests
# -------------------------------------------------------------------------

def test_language_detection():
    # Devanagari Hindi
    hi_query = "मुझे किसान योजना के बारे में जानकारी चाहिए"
    assert detect_query_language(hi_query) == "hi"

    # Hinglish / Romanized Hindi
    hinglish_query = "kisan samman nidhi ka paisa kaise milega"
    assert detect_query_language(hinglish_query) == "hi-Latn"

    # Standard English
    en_query = "What is the annual financial support under PM-KISAN?"
    assert detect_query_language(en_query) == "en"

def test_clean_speech_text():
    markdown_text = (
        "### 📋 Scheme Eligibility Assessment\n\n"
        "#### PM-KISAN — ✅ ELIGIBLE\n\n"
        "Based on your profile, you satisfy all criteria. "
        "Visit [pmkisan.gov.in](https://pmkisan.gov.in) to register.\n\n"
        "- ✓ **Landholding**: 2 acres\n"
        "- ✓ **Tax Status**: Non-Taxpayer"
    )
    clean_audio = clean_speech_text(markdown_text)

    # Markdown hashes, brackets, links, and bullets must be completely stripped
    assert "###" not in clean_audio
    assert "[" not in clean_audio
    assert "]" not in clean_audio
    assert "https://" not in clean_audio
    assert "**" not in clean_audio
    assert "- ✓" not in clean_audio
    assert "Based on your profile" in clean_audio
    assert "pmkisan.gov.in" in clean_audio

# -------------------------------------------------------------------------
# 3. New Scheme Deterministic Evaluation Tests (Phase 5)
# -------------------------------------------------------------------------

def test_atal_pension_yojana_evaluation():
    db = next(get_db())
    try:
        apy = db.query(Scheme).filter(Scheme.slug == "atal-pension-yojana").first()
        assert apy is not None, "Atal Pension Yojana must be present in database"

        # Eligible profile: age 28, non-taxpayer
        eligible_profile = {"age": 28, "pays_income_tax": False}
        res_eligible = evaluate_scheme_eligibility(apy, eligible_profile)
        assert res_eligible.status == "eligible"
        assert any(sc["criterion"] == "Age Qualification" for sc in res_eligible.satisfied_conditions)

        # Ineligible profile: age 45 (outside 18-40 window)
        ineligible_profile = {"age": 45, "pays_income_tax": False}
        res_ineligible = evaluate_scheme_eligibility(apy, ineligible_profile)
        assert res_ineligible.status == "ineligible"
        assert any(unc["criterion"] == "Age Qualification" for unc in res_ineligible.unsatisfied_conditions)

        # Ineligible profile: income tax payer
        taxpayer_profile = {"age": 30, "pays_income_tax": True}
        res_taxpayer = evaluate_scheme_eligibility(apy, taxpayer_profile)
        assert res_taxpayer.status == "ineligible"
        assert any(unc["criterion"] == "Non-Taxpayer Rule" for unc in res_taxpayer.unsatisfied_conditions)
    finally:
        db.close()

def test_pm_jeevan_jyoti_bima_evaluation():
    db = next(get_db())
    try:
        pmjjby = db.query(Scheme).filter(Scheme.slug == "pm-jeevan-jyoti-bima").first()
        assert pmjjby is not None, "PMJJBY must be present in database"

        # Eligible profile: age 35
        eligible_profile = {"age": 35}
        res_eligible = evaluate_scheme_eligibility(pmjjby, eligible_profile)
        assert res_eligible.status == "eligible"

        # Ineligible profile: age 58 (max age 50)
        ineligible_profile = {"age": 58}
        res_ineligible = evaluate_scheme_eligibility(pmjjby, ineligible_profile)
        assert res_ineligible.status == "ineligible"
    finally:
        db.close()

def test_pm_yasasvi_evaluation():
    db = next(get_db())
    try:
        yasasvi = db.query(Scheme).filter(Scheme.slug == "pm-yasasvi").first()
        assert yasasvi is not None, "PM-YASASVI must be present in database"

        # Eligible: student with annual income <= 2.5 lakh
        eligible_profile = {"occupation": "student", "annual_income": 180000.0}
        res_eligible = evaluate_scheme_eligibility(yasasvi, eligible_profile)
        assert res_eligible.status == "eligible"

        # Ineligible: student with income > 2.5 lakh
        ineligible_profile = {"occupation": "student", "annual_income": 400000.0}
        res_ineligible = evaluate_scheme_eligibility(yasasvi, ineligible_profile)
        assert res_ineligible.status == "ineligible"
    finally:
        db.close()

# -------------------------------------------------------------------------
# 4. End-to-End Agentic Chat Endpoint Structured Contract Test
# -------------------------------------------------------------------------

def test_chat_endpoint_agentic_contract(client):
    payload = {
        "query": "I am a farmer from Bihar with 2 acres of land and my annual income is around 1.5 lakh. Which schemes can I get?",
        "preferred_language": "en"
    }
    response = client.post("/api/assistant/chat", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Agentic Contract Assertions
    assert "detected_language" in data
    assert data["detected_language"] in ["en", "hi-Latn"]
    assert "response_language" in data
    assert "extracted_facts" in data
    assert "matched_schemes" in data
    assert isinstance(data["matched_schemes"], list)
    assert len(data["matched_schemes"]) > 0

    # Top scheme should be PM-KISAN
    top_scheme = data["matched_schemes"][0]
    assert top_scheme["slug"] == "pm-kisan"
    assert "why_it_fits" in top_scheme
    assert top_scheme["official_url"] == "https://pmkisan.gov.in"
    assert top_scheme["action_label"] == "Prepare Application Draft"
    assert "/applications?slug=pm-kisan" in top_scheme["action_url"]

    # Check next steps and checklist
    assert "next_steps" in data
    assert isinstance(data["next_steps"], list)
    assert len(data["next_steps"]) >= 2
    assert "application_checklist" in data
    assert isinstance(data["application_checklist"], list)

    # Clean spoken audio text
    assert "speech_text" in data
    assert data["speech_text"] is not None
    assert "[" not in data["speech_text"]
    assert "http" not in data["speech_text"]

    # Uncertainty disclosure
    assert "uncertainty_notes" in data
    assert "does not guarantee" in data["uncertainty_notes"].lower()

def test_chat_endpoint_hindi_language_preservation(client):
    # Query in Hindi Devanagari
    payload = {
        "query": "मैं बिहार का एक किसान हूँ, मेरे पास दो बीघा जमीन है। मुझे कौन सी योजना मिलेगी?",
        "preferred_language": "hi"
    }
    response = client.post("/api/assistant/chat", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["detected_language"] == "hi"
    assert data["response_language"] == "hi"
    assert len(data["matched_schemes"]) > 0
    assert data["matched_schemes"][0]["slug"] == "pm-kisan"
    assert data["matched_schemes"][0]["scheme_slug"] == "pm-kisan"


def test_chat_endpoint_empty_matched_schemes_on_fabricated_query(client):
    # Fabricated / ungrounded query with no matched scheme
    payload = {
        "query": "Tesla electric car distribution lottery scheme free gold voucher",
        "preferred_language": "en"
    }
    response = client.post("/api/assistant/chat", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "matched_schemes" in data
    assert isinstance(data["matched_schemes"], list)
    assert len(data["matched_schemes"]) == 0
    # Clean speech summary handles empty matched schemes gracefully
    assert "speech_text" in data
    assert "JanSahayak identified 0" not in data["speech_text"]
    # Legacy fields contract
    assert "answer" in data
    assert "citations" in data
    assert "extracted_profile" in data
    assert "eligibility_results" in data
def test_matched_scheme_serialization_canonical_and_aliases(client):
    payload = {
        "query": "What are the benefits and guidelines of PM-KISAN for farmers?",
        "preferred_language": "en"
    }
    response = client.post("/api/assistant/chat", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert len(data["matched_schemes"]) > 0
    scheme = data["matched_schemes"][0]

    # Canonical agentic fields
    assert "scheme_slug" in scheme
    assert scheme["scheme_slug"] == "pm-kisan"
    assert "scheme_name" in scheme
    assert "PM-KISAN" in scheme["scheme_name"] or "Pradhan Mantri Kisan" in scheme["scheme_name"]
    assert "authority" in scheme
    assert "why_it_fits" in scheme
    assert isinstance(scheme["why_it_fits"], list)
    assert "official_source_url" in scheme
    assert "action_label" in scheme
    assert scheme["action_label"] == "Prepare Application Draft"
    assert "action_url" in scheme
    assert "/applications?slug=pm-kisan" in scheme["action_url"]

    # Backward compatibility aliases
    assert "slug" in scheme
    assert scheme["slug"] == scheme["scheme_slug"]
    assert "name" in scheme
    assert scheme["name"] == scheme["scheme_name"]
    assert "ministry" in scheme
    assert "official_url" in scheme
    assert scheme["official_url"] == scheme["official_source_url"]

    # Legacy contract fields preserved on root response
    assert "answer" in data
    assert "citations" in data
    assert "extracted_profile" in data
    assert "eligibility_results" in data
