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
