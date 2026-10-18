from typing import Dict, Any, List
from datetime import datetime, timezone

class EligibilityAssessmentResult:
    def __init__(
        self,
        scheme_id: int,
        scheme_slug: str,
        scheme_name: str,
        status: str,  # "eligible" | "possibly_eligible" | "ineligible"
        summary_explanation: str,
        satisfied_conditions: List[Dict[str, Any]],
        unsatisfied_conditions: List[Dict[str, Any]],
        unknown_conditions: List[Dict[str, Any]],
        applicable_exclusions: List[str],
        official_sources: List[Dict[str, str]],
        next_steps: List[str]
    ):
        self.scheme_id = scheme_id
        self.scheme_slug = scheme_slug
        self.scheme_name = scheme_name
        self.status = status
        self.summary_explanation = summary_explanation
        self.satisfied_conditions = satisfied_conditions
        self.unsatisfied_conditions = unsatisfied_conditions
        self.unknown_conditions = unknown_conditions
        self.applicable_exclusions = applicable_exclusions
        self.official_sources = official_sources
        self.next_steps = next_steps
        self.assessed_at = datetime.now(timezone.utc).isoformat()
        self.disclaimer = (
            "This automated assessment is rule-based informational guidance and does not "
            "constitute official sanction, approval, or guarantee of welfare benefits by "
            "the issuing government department."
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scheme_id": self.scheme_id,
            "scheme_slug": self.scheme_slug,
            "scheme_name": self.scheme_name,
            "status": self.status,
            "summary_explanation": self.summary_explanation,
            "satisfied_conditions": self.satisfied_conditions,
            "unsatisfied_conditions": self.unsatisfied_conditions,
            "unknown_conditions": self.unknown_conditions,
            "applicable_exclusions": self.applicable_exclusions,
            "official_sources": self.official_sources,
            "next_steps": self.next_steps,
            "assessed_at": self.assessed_at,
            "disclaimer": self.disclaimer
        }

def evaluate_scheme_eligibility(scheme: Any, profile: Dict[str, Any]) -> EligibilityAssessmentResult:
    """
    Deterministic rules engine evaluating citizen profile against official scheme criteria.
    Pure Python, non-hallucinatory evaluation.
    """
    rules = scheme.eligibility_rules or {}
    slug = scheme.slug
    name = scheme.name
    scheme_id = scheme.id

    satisfied = []
    unsatisfied = []
    unknown = []

    # 1. State / Scope Evaluation
    if scheme.scope == "state" and "ALL" not in (scheme.applicable_states or []):
        citizen_state = profile.get("state")
        if citizen_state:
            if citizen_state in scheme.applicable_states:
                satisfied.append({
                    "criterion": "State Residency",
                    "official_rule": f"Must reside in: {', '.join(scheme.applicable_states)}",
                    "citizen_value": citizen_state
                })
            else:
                unsatisfied.append({
                    "criterion": "State Residency",
                    "official_rule": f"Must reside in: {', '.join(scheme.applicable_states)}",
                    "citizen_value": citizen_state,
                    "reason": f"Citizen state '{citizen_state}' is not within eligible states for this state scheme."
                })
        else:
            unknown.append({
                "criterion": "State Residency",
                "prompt": "Please specify your state of residence to confirm geographic qualification."
            })

    # 2. General Exclusions Check: Government Employment & Income Tax Payee
    is_govt_emp = profile.get("is_govt_employee")
    pays_tax = profile.get("pays_income_tax")

    # If scheme excludes government employees
    if rules.get("is_govt_employee") is False:
        if is_govt_emp is True:
            unsatisfied.append({
                "criterion": "Non-Government Employee Exclusion",
                "official_rule": "Regular government employees/officers are disqualified under official guidelines.",
                "citizen_value": "Government Employee",
                "reason": "Official rules strictly exclude regular government and PSU employees."
            })
        elif is_govt_emp is False:
            satisfied.append({
                "criterion": "Non-Government Employee Status",
                "official_rule": "Must not be a regular government/PSU employee.",
                "citizen_value": "Non-Government Employee"
            })
        else:
            unknown.append({
                "criterion": "Employment Status",
                "prompt": "Are you or your family members regular government/PSU employees?"
            })

    # If scheme excludes income tax payers
    if rules.get("income_tax_payer") is False:
        if pays_tax is True:
            unsatisfied.append({
                "criterion": "Income Tax Payee Exclusion",
                "official_rule": "Persons who paid income tax in last assessment year are disqualified.",
                "citizen_value": "Income Tax Payer",
                "reason": "Official rules exclude income tax payees from this welfare benefit."
            })
        elif pays_tax is False:
            satisfied.append({
                "criterion": "Income Tax Status",
                "official_rule": "Must not be an income tax payee in the last assessment year.",
                "citizen_value": "Non-Taxpayer"
            })
        else:
            unknown.append({
                "criterion": "Tax Status",
                "prompt": "Did you or your family pay income tax in the last assessment year?"
            })

    # 3. Scheme-Specific Evaluation Rules

    # --- PM-KISAN ---
    if slug == "pm-kisan":
        # Cultivable Land
        owns_land = profile.get("owns_cultivable_land")
        if owns_land is True:
            satisfied.append({
                "criterion": "Landholding",
                "official_rule": "Must own cultivable agricultural land in applicant's name.",
                "citizen_value": "Owns cultivable land"
            })
        elif owns_land is False:
            unsatisfied.append({
                "criterion": "Landholding",
                "official_rule": "Must own cultivable agricultural land in applicant's name.",
                "citizen_value": "Does not own land",
                "reason": "PM-KISAN is exclusively for landholding farmer families with cultivable land in revenue records."
            })
        else:
            unknown.append({
                "criterion": "Landholding",
                "prompt": "Do you own cultivable agricultural land registered in your name?"
            })

    # --- PMAY-G ---
    elif slug == "pmay-g":
        housing_status = profile.get("housing_type")
        if housing_status:
            if housing_status in ["kutcha", "houseless", "dilapidated"]:
                satisfied.append({
                    "criterion": "Housing Condition",
                    "official_rule": "Houseless or living in kutcha/dilapidated house.",
                    "citizen_value": housing_status
                })
            else:
                unsatisfied.append({
                    "criterion": "Housing Condition",
                    "official_rule": "Must not already own a pucca house anywhere in India.",
                    "citizen_value": housing_status,
                    "reason": "Families possessing a pucca house are ineligible under PMAY-G guidelines."
                })
        else:
            unknown.append({
                "criterion": "Housing Condition",
                "prompt": "What is your current dwelling type (houseless, kutcha house, or pucca house)?"
            })

        area = profile.get("area_type")
        if area:
            if area.lower() == "rural":
                satisfied.append({
                    "criterion": "Rural Location",
                    "official_rule": "Location must be in a rural area (Gram Panchayat).",
                    "citizen_value": "Rural"
                })
            else:
                unsatisfied.append({
                    "criterion": "Rural Location",
                    "official_rule": "PMAY-G specifically applies to rural Gram Panchayat areas (urban areas covered under PMAY-U).",
                    "citizen_value": area,
                    "reason": "PMAY-G is designated specifically for rural areas."
                })
        else:
            unknown.append({
                "criterion": "Area Type",
                "prompt": "Do you reside in a rural area (Gram Panchayat) or urban municipality?"
            })

    # --- Ayushman Bharat PM-JAY ---
    elif slug == "ayushman-bharat-pmjay":
        age = profile.get("age")
        is_secc_or_bpl = profile.get("is_bpl") or profile.get("is_secc_eligible")
        
        # Universal pathway for 70+
        if age is not None and age >= 70:
            satisfied.append({
                "criterion": "Senior Citizen Universal Coverage",
                "official_rule": "All senior citizens aged 70 and above qualify under universal PM-JAY expansion.",
                "citizen_value": f"Age {age} (70+ Universal Pathway)"
            })
        elif is_secc_or_bpl is True:
            satisfied.append({
                "criterion": "Socio-Economic Eligibility",
                "official_rule": "Identified as deprived/vulnerable under SECC 2011 / State NFSA list.",
                "citizen_value": "BPL / Vulnerable Beneficiary"
            })
        elif is_secc_or_bpl is False and (age is not None and age < 70):
            unsatisfied.append({
                "criterion": "Deprivation Criteria",
                "official_rule": "Must be listed in SECC 2011 / state target list, or be 70+ years of age.",
                "citizen_value": f"Age {age}, Non-BPL",
                "reason": "Standard PM-JAY requires SECC deprivation listing unless applicant is 70 years or older."
            })
        else:
            unknown.append({
                "criterion": "Health Card Qualification",
                "prompt": "Are you 70+ years of age or does your household hold an eligible BPL/Antyodaya ration card?"
            })

    # --- PMMVY ---
    elif slug == "pmmvy":
        gender = profile.get("gender")
        if gender:
            if gender.lower() == "female":
                satisfied.append({
                    "criterion": "Beneficiary Gender",
                    "official_rule": "Pregnant women and lactating mothers.",
                    "citizen_value": "Female"
                })
            else:
                unsatisfied.append({
                    "criterion": "Beneficiary Gender",
                    "official_rule": "Exclusively for pregnant women and lactating mothers.",
                    "citizen_value": gender,
                    "reason": "PMMVY is an exclusive maternity support scheme for women."
                })
        else:
            unknown.append({
                "criterion": "Beneficiary Gender",
                "prompt": "Please confirm gender (scheme is designated for pregnant women/mothers)."
            })

        age = profile.get("age")
        if age is not None:
            if age >= 19:
                satisfied.append({
                    "criterion": "Minimum Age",
                    "official_rule": "Mother must be 19 years of age or older at pregnancy.",
                    "citizen_value": f"Age {age}"
                })
            else:
                unsatisfied.append({
                    "criterion": "Minimum Age",
                    "official_rule": "Mother must be at least 19 years old at pregnancy.",
                    "citizen_value": f"Age {age}",
                    "reason": "Official PMMVY rules require the mother to be at least 19 years old."
                })
        else:
            unknown.append({
                "criterion": "Mother's Age",
                "prompt": "What is the mother's age?"
            })

    # --- IGNOAPS ---
    elif slug == "ignoaps":
        age = profile.get("age")
        if age is not None:
            if age >= 60:
                satisfied.append({
                    "criterion": "Senior Citizen Age",
                    "official_rule": "Applicant must be 60 years of age or above.",
                    "citizen_value": f"Age {age}"
                })
            else:
                unsatisfied.append({
                    "criterion": "Senior Citizen Age",
                    "official_rule": "Applicant must be 60 years of age or above.",
                    "citizen_value": f"Age {age}",
                    "reason": f"Applicant age ({age}) is below the required 60-year pension threshold."
                })
        else:
            unknown.append({
                "criterion": "Age Requirement",
                "prompt": "Please specify the applicant's age (minimum 60 years required)."
            })

        is_bpl = profile.get("is_bpl")
        if is_bpl is True:
            satisfied.append({
                "criterion": "BPL Category",
                "official_rule": "Household must belong to Below Poverty Line (BPL) category.",
                "citizen_value": "BPL household"
            })
        elif is_bpl is False:
            unsatisfied.append({
                "criterion": "BPL Category",
                "official_rule": "Applicant household must be registered under Below Poverty Line (BPL).",
                "citizen_value": "Non-BPL",
                "reason": "IGNOAPS is legally restricted to verified BPL households under NSAP rules."
            })
        else:
            unknown.append({
                "criterion": "BPL Category",
                "prompt": "Does the applicant's family belong to the Below Poverty Line (BPL) list?"
            })

    # --- Sukanya Samriddhi Yojana ---
    elif slug == "sukanya-samriddhi-yojana":
        girl_age = profile.get("girl_child_age")
        has_girl = profile.get("has_girl_child_under_10")
        if girl_age is not None:
            if girl_age <= 10:
                satisfied.append({
                    "criterion": "Girl Child Age",
                    "official_rule": "Account must be opened before girl child turns 10 years old.",
                    "citizen_value": f"Age {girl_age}"
                })
            else:
                unsatisfied.append({
                    "criterion": "Girl Child Age",
                    "official_rule": "Girl child must be 10 years of age or younger.",
                    "citizen_value": f"Age {girl_age}",
                    "reason": f"Child age ({girl_age}) exceeds statutory maximum 10-year limit for new accounts."
                })
        elif has_girl is True:
            satisfied.append({
                "criterion": "Girl Child Presence",
                "official_rule": "Family has girl child under 10 years of age.",
                "citizen_value": "Yes"
            })
        elif has_girl is False:
            unsatisfied.append({
                "criterion": "Girl Child Presence",
                "official_rule": "Designated exclusively for girl children under 10 years old.",
                "citizen_value": "No",
                "reason": "SSY is specifically designated for girl children up to age 10."
            })
        else:
            unknown.append({
                "criterion": "Girl Child Age",
                "prompt": "Do you have a girl child aged 10 years or younger in your family?"
            })

    # --- PM SVANidhi ---
    elif slug == "pm-svanidhi":
        occ = profile.get("occupation", "").lower()
        is_vendor = ("vendor" in occ) or ("street" in occ) or ("hawker" in occ) or profile.get("is_street_vendor")
        if is_vendor:
            satisfied.append({
                "criterion": "Vending Occupation",
                "official_rule": "Must be engaged in street vending / hawking in urban/peri-urban areas.",
                "citizen_value": "Street Vendor / Hawker"
            })
        elif profile.get("is_street_vendor") is False:
            unsatisfied.append({
                "criterion": "Vending Occupation",
                "official_rule": "Exclusively for urban and peri-urban street vendors.",
                "citizen_value": occ or "Other",
                "reason": "PM SVANidhi is a specialized credit line specifically for street vendors."
            })
        else:
            unknown.append({
                "criterion": "Street Vending Activity",
                "prompt": "Are you actively engaged as a street vendor, hawker, or roadside seller?"
            })

    # --- PM Vishwakarma ---
    elif slug == "pm-vishwakarma":
        is_artisan = profile.get("is_traditional_artisan") or profile.get("occupation", "").lower() in [
            "carpenter", "blacksmith", "goldsmith", "potter", "cobbler", "mason", "tailor", "barber", "artisan"
        ]
        if is_artisan:
            satisfied.append({
                "criterion": "Artisan / Craftsperson Trade",
                "official_rule": "Must work in one of the 18 eligible traditional family crafts.",
                "citizen_value": "Eligible Artisan Trade"
            })
        elif profile.get("is_traditional_artisan") is False:
            unsatisfied.append({
                "criterion": "Artisan / Craftsperson Trade",
                "official_rule": "Exclusively for artisans and craftspeople in 18 notified trades.",
                "citizen_value": "Non-Artisan",
                "reason": "Scheme is targeted specifically at traditional family-based craftspeople."
            })
        else:
            unknown.append({
                "criterion": "Traditional Craft Engagement",
                "prompt": "Do you practice one of the 18 traditional crafts (e.g., carpentry, blacksmithing, pottery, masonry, tailoring)?"
            })

    # Determine overall status
    if len(unsatisfied) > 0:
        status = "ineligible"
        summary = (
            f"Based on the verified official rules for {name}, you currently appear ineligible "
            f"because {len(unsatisfied)} condition(s) were not satisfied."
        )
    elif len(unknown) > 0:
        status = "possibly_eligible"
        summary = (
            f"You appear potentially eligible for {name}, but {len(unknown)} item(s) "
            "require additional information before qualification can be confirmed."
        )
    else:
        status = "eligible"
        summary = (
            f"Based on your provided details, you appear eligible under the verified rules for {name}. "
            f"All {len(satisfied)} evaluated criteria were satisfied."
        )

    # Next actionable steps
    next_steps = []
    if status == "eligible":
        next_steps = [
            "Review the verified document checklist to ensure all records are ready.",
            "Use JanSahayak's Application Preparation tool to generate a draft application.",
            f"Submit through the official government portal: {scheme.official_portal_url}"
        ]
    elif status == "possibly_eligible":
        next_steps = [
            "Provide the missing details in the questionnaire above to complete the assessment.",
            "Check acceptable alternative documents if certain primary papers are missing.",
            "Consult the official scheme guidelines link below."
        ]
    else:
        next_steps = [
            "Review the specific unsatisfied criteria listed above.",
            "Explore alternative welfare schemes in the catalogue that match your current profile.",
            "If you believe government records about your status are incorrect, consider filing an RTI or grievance."
        ]

    # Official sources
    sources = []
    for s in (scheme.sources or []):
        sources.append({
            "title": s.source_title,
            "url": s.source_url,
            "authority": s.issuing_authority
        })
    if not sources and scheme.official_portal_url:
        sources.append({
            "title": "Official Scheme Portal",
            "url": scheme.official_portal_url,
            "authority": scheme.department
        })

    return EligibilityAssessmentResult(
        scheme_id=scheme_id,
        scheme_slug=slug,
        scheme_name=name,
        status=status,
        summary_explanation=summary,
        satisfied_conditions=satisfied,
        unsatisfied_conditions=unsatisfied,
        unknown_conditions=unknown,
        applicable_exclusions=scheme.exclusions or [],
        official_sources=sources,
        next_steps=next_steps
    )
