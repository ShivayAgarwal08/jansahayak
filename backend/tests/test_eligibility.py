import pytest
from app.services.eligibility.engine import evaluate_scheme_eligibility

class MockScheme:
    def __init__(self, slug, name, rules, exclusions=None, states=None):
        self.id = 1
        self.slug = slug
        self.name = name
        self.scope = "central"
        self.applicable_states = states or ["ALL"]
        self.department = "Test Ministry"
        self.beneficiary_types = ["general"]
        self.eligibility_rules = rules
        self.exclusions = exclusions or []
        self.official_portal_url = "https://example.gov.in"
        self.sources = []

def test_pm_kisan_eligible():
    scheme = MockScheme(
        slug="pm-kisan",
        name="PM-KISAN",
        rules={"min_age": 18, "landholding_required": True, "income_tax_payer": False, "is_govt_employee": False}
    )
    profile = {
        "owns_cultivable_land": True,
        "is_govt_employee": False,
        "pays_income_tax": False
    }
    result = evaluate_scheme_eligibility(scheme, profile)
    assert result.status == "eligible"
    assert len(result.satisfied_conditions) >= 3
    assert len(result.unsatisfied_conditions) == 0

def test_pm_kisan_ineligible_due_to_tax():
    scheme = MockScheme(
        slug="pm-kisan",
        name="PM-KISAN",
        rules={"min_age": 18, "landholding_required": True, "income_tax_payer": False, "is_govt_employee": False}
    )
    profile = {
        "owns_cultivable_land": True,
        "is_govt_employee": False,
        "pays_income_tax": True  # Disqualifying!
    }
    result = evaluate_scheme_eligibility(scheme, profile)
    assert result.status == "ineligible"
    assert any("Income Tax" in c["criterion"] for c in result.unsatisfied_conditions)

def test_pm_kisan_unknown_missing_land():
    scheme = MockScheme(
        slug="pm-kisan",
        name="PM-KISAN",
        rules={"min_age": 18, "landholding_required": True, "income_tax_payer": False, "is_govt_employee": False}
    )
    profile = {
        "is_govt_employee": False,
        "pays_income_tax": False
        # land not specified
    }
    result = evaluate_scheme_eligibility(scheme, profile)
    assert result.status == "possibly_eligible"
    assert len(result.unknown_conditions) > 0

def test_ignoaps_age_boundary():
    scheme = MockScheme(
        slug="ignoaps",
        name="IGNOAPS",
        rules={"min_age": 60, "bpl_household": True}
    )
    # Underage: 59 years
    profile_under = {"age": 59, "is_bpl": True}
    res_under = evaluate_scheme_eligibility(scheme, profile_under)
    assert res_under.status == "ineligible"

    # Eligible: 60 years
    profile_60 = {"age": 60, "is_bpl": True}
    res_60 = evaluate_scheme_eligibility(scheme, profile_60)
    assert res_60.status == "eligible"

def test_contradictory_user_facts_prevent_silent_eligibility():
    """Verify that contradictory user facts cannot silently pass as eligible."""
    pm_kisan = MockScheme(
        slug="pm-kisan",
        name="PM-KISAN",
        rules={"min_age": 18, "landholding_required": True, "income_tax_payer": False, "is_govt_employee": False}
    )
    # Contradiction: says does not own cultivable land, but claims to be landholding farmer
    contradictory_profile = {
        "owns_cultivable_land": False,
        "is_landholding_farmer": True,
        "is_govt_employee": False,
        "pays_income_tax": False
    }
    res = evaluate_scheme_eligibility(pm_kisan, contradictory_profile)
    assert res.status in ["ineligible", "possibly_eligible"]
    assert res.status != "eligible"
    assert any("Consistency" in u.get("criterion", "") for u in res.unknown_conditions)

    # Housing contradiction: owns pucca house but claims houseless
    pmay_g = MockScheme(
        slug="pmay-g",
        name="PMAY-G",
        rules={"housing_status": ["houseless", "kutcha_house"], "owns_pucca_house": False}
    )
    contradictory_housing = {
        "owns_pucca_house": True,
        "housing_status": "houseless",
        "is_govt_employee": False
    }
    res_housing = evaluate_scheme_eligibility(pmay_g, contradictory_housing)
    assert res_housing.status in ["ineligible", "possibly_eligible"]
    assert res_housing.status != "eligible"

def test_statutory_boundaries_and_cutoffs():
    """Verify exact statutory cutoffs across schemes."""
    # 1. PMMVY: age 18 (ineligible) vs 19 (eligible)
    pmmvy = MockScheme(
        slug="pmmvy",
        name="PMMVY",
        rules={"min_age": 19, "gender": "female", "is_pregnant_or_lactating": True, "is_regular_govt_employee": False}
    )
    res_18 = evaluate_scheme_eligibility(pmmvy, {"age": 18, "gender": "female", "is_pregnant_or_lactating": True, "is_regular_govt_employee": False})
    res_19 = evaluate_scheme_eligibility(pmmvy, {"age": 19, "gender": "female", "is_pregnant_or_lactating": True, "is_regular_govt_employee": False})
    assert res_18.status == "ineligible"
    assert res_19.status == "eligible"

    # 2. SSY: age 10 (eligible) vs 11 (ineligible)
    ssy = MockScheme(
        slug="sukanya-samriddhi-yojana",
        name="SSY",
        rules={"gender": "female", "max_age_years": 10}
    )
    res_10 = evaluate_scheme_eligibility(ssy, {"girl_child_age": 10, "gender": "female"})
    res_11 = evaluate_scheme_eligibility(ssy, {"girl_child_age": 11, "gender": "female"})
    assert res_10.status == "eligible"
    assert res_11.status == "ineligible"

def test_disclaimer_and_no_official_decision_guarantee():
    """Verify that every assessment includes the mandatory non-official advisory disclaimer."""
    scheme = MockScheme(slug="test", name="Test Scheme", rules={})
    res = evaluate_scheme_eligibility(scheme, {})
    assert "does not constitute official sanction" in res.disclaimer
    assert "rule-based informational guidance" in res.disclaimer
