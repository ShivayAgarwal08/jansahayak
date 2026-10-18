import re
from typing import Dict, Any, List, Optional, Tuple

# Standard list of Indian States and Union Territories (case-insensitive lookup)
INDIAN_STATES = {
    "andhra pradesh": "Andhra Pradesh",
    "arunachal pradesh": "Arunachal Pradesh",
    "assam": "Assam",
    "bihar": "Bihar",
    "chhattisgarh": "Chhattisgarh",
    "goa": "Goa",
    "gujarat": "Gujarat",
    "haryana": "Haryana",
    "himachal pradesh": "Himachal Pradesh",
    "jharkhand": "Jharkhand",
    "karnataka": "Karnataka",
    "kerala": "Kerala",
    "madhya pradesh": "Madhya Pradesh",
    "maharashtra": "Maharashtra",
    "manipur": "Manipur",
    "meghalaya": "Meghalaya",
    "mizoram": "Mizoram",
    "nagaland": "Nagaland",
    "odisha": "Odisha",
    "punjab": "Punjab",
    "rajasthan": "Rajasthan",
    "sikkim": "Sikkim",
    "tamil nadu": "Tamil Nadu",
    "telangana": "Telangana",
    "tripura": "Tripura",
    "uttar pradesh": "Uttar Pradesh",
    "uttarakhand": "Uttarakhand",
    "west bengal": "West Bengal",
    "delhi": "Delhi",
    "jammu and kashmir": "Jammu & Kashmir",
    "ladakh": "Ladakh",
    "puducherry": "Puducherry",
    "chandigarh": "Chandigarh"
}

# Number words mapping for simple counts
WORD_TO_NUM = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "ek": 1, "do": 2, "teen": 3, "char": 4, "paanch": 5
}

def normalize_indian_currency(text: str) -> Optional[float]:
    """
    Extract and normalize Indian currency expressions to integer/float rupees.
    Examples:
      - '₹1.5 lakh' -> 150000.0
      - '1.5 lakhs' -> 150000.0
      - '1.5 lac' -> 150000.0
      - '50k' -> 50000.0
      - '50 thousand' -> 50000.0
      - '2 crore' -> 20000000.0
      - 'Rs. 1,50,000' -> 150000.0
      - '150000' -> 150000.0
    """
    # 1. Lakh / Lac pattern: e.g., ₹1.5 lakh, 1.5 lakhs, 2 lac, 2.5 lacs
    lakh_match = re.search(r'(?:₹|rs\.?|inr)?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:lakh|lakhs|lac|lacs)\b', text, re.IGNORECASE)
    if lakh_match:
        val = float(lakh_match.group(1))
        return val * 100_000.0

    # 2. Crore pattern: e.g., ₹2 crore, 1.2 crores
    crore_match = re.search(r'(?:₹|rs\.?|inr)?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:crore|crores|cr)\b', text, re.IGNORECASE)
    if crore_match:
        val = float(crore_match.group(1))
        return val * 10_000_000.0

    # 3. Thousand / K pattern: e.g., 50k, 50 thousand, ₹50 thousand
    thousand_match = re.search(r'(?:₹|rs\.?|inr)?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:thousand|k)\b', text, re.IGNORECASE)
    if thousand_match:
        val = float(thousand_match.group(1))
        return val * 1_000.0

    # 4. Explicit formatted number: e.g., ₹1,50,000 or Rs. 150000 or income around 150000
    income_context_match = re.search(r'(?:income|earning|salary|around|of)\s*(?:of|is|around|approx|approximately)?\s*(?:₹|rs\.?|inr)?\s*([0-9]{1,3}(?:,[0-9]{2,3})*(?:\.[0-9]+)?|[0-9]{4,9})\b', text, re.IGNORECASE)
    if income_context_match:
        num_str = income_context_match.group(1).replace(',', '')
        try:
            return float(num_str)
        except ValueError:
            pass

    # 5. Direct rupee symbol match: e.g., ₹150000
    rupee_match = re.search(r'₹\s*([0-9]{1,3}(?:,[0-9]{2,3})*(?:\.[0-9]+)?|[0-9]{4,9})', text)
    if rupee_match:
        num_str = rupee_match.group(1).replace(',', '')
        try:
            return float(num_str)
        except ValueError:
            pass

    return None

def parse_landholding(text: str, state: Optional[str]) -> Tuple[Optional[bool], Optional[str], Optional[float], Optional[str]]:
    """
    Parse landholding mentions without silent/erroneous standard conversions.
    Returns:
      (owns_cultivable_land, landholding_raw, landholding_acres, notes)
    """
    # Check if user says landless / no land
    if re.search(r'\b(?:no\s+land|landless|without\s+land|bhoomiheen)\b', text, re.IGNORECASE):
        return (False, "0", 0.0, "Citizen reported having no land.")

    # Match bigha pattern: e.g. "two bighas of land", "2 bigha", "3 bighas"
    bigha_match = re.search(r'(\d+(?:\.\d+)?|one|two|three|four|five|six|seven|eight|nine|ten)\s*(?:bigha|bighas|beegha)\b', text, re.IGNORECASE)
    if bigha_match:
        raw_qty = bigha_match.group(1).lower()
        qty = WORD_TO_NUM.get(raw_qty, None)
        if qty is None:
            try:
                qty = float(raw_qty)
            except ValueError:
                qty = 1.0

        raw_str = f"{qty} bigha(s)"
        
        # Regional conversion note
        if state and state.lower() == "bihar":
            # In Bihar, 1 pucca bigha is conventionally ~27,225 sq ft (~0.625 acres / ~0.253 ha),
            # but kaccha bighas vary by district.
            note = f"Reported {qty} bighas in Bihar. In Bihar, 1 pucca bigha is ~0.62 acres (~0.25 ha), but local district survey definitions vary. Unit preserved without silent standard conversion."
            # Do NOT set a hard acres figure without verification, but provide estimated acres for calculation only
            est_acres = round(qty * 0.625, 2)
            return (True, raw_str, est_acres, note)
        elif state and state.lower() in ["uttar pradesh", "up"]:
            note = f"Reported {qty} bighas in Uttar Pradesh. Standard pucca bigha is ~0.625 acres, but kaccha bigha (~0.208 acres) is also common. Unit preserved."
            est_acres = round(qty * 0.625, 2)
            return (True, raw_str, est_acres, note)
        elif state:
            note = f"Reported {qty} bighas in {state}. Regional conversion factors vary significantly by state/district. Unit preserved."
            return (True, raw_str, None, note)
        else:
            note = f"Reported {qty} bighas. Bigha is a regional unit varying between 0.2 and 0.8 acres depending on the state. State location required for accurate land conversion."
            return (True, raw_str, None, note)

    # Match acre pattern: e.g. "2 acres", "1.5 acre"
    acre_match = re.search(r'(\d+(?:\.\d+)?|one|two|three|four|five|six|seven|eight|nine|ten)\s*(?:acre|acres|ekad)\b', text, re.IGNORECASE)
    if acre_match:
        raw_qty = acre_match.group(1).lower()
        qty = WORD_TO_NUM.get(raw_qty, None)
        if qty is None:
            try:
                qty = float(raw_qty)
            except ValueError:
                qty = 1.0
        return (True, f"{qty} acre(s)", float(qty), f"Confirmed {qty} acre(s).")

    # Match hectare pattern: e.g. "1.5 hectare", "2 ha"
    ha_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:hectare|hectares|ha)\b', text, re.IGNORECASE)
    if ha_match:
        qty = float(ha_match.group(1))
        acres = round(qty * 2.471, 2)
        return (True, f"{qty} hectare(s)", acres, f"{qty} hectare(s) equivalent to approx {acres} acres.")

    # General land ownership mention: "own land", "have land", "agricultural land"
    if re.search(r'\b(?:own\s+land|has\s+land|have\s+land|farmer\s+with\s+land|cultivable\s+land)\b', text, re.IGNORECASE):
        return (True, "Landholding mentioned (size unstated)", None, "Citizen owns land, but exact acreage was not specified.")

    return (None, None, None, None)

def extract_citizen_profile(text: str) -> Dict[str, Any]:
    """
    Extract structured facts explicitly provided by the citizen in natural language.
    Does NOT invent unstated information. Unstated fields are returned as None.
    """
    profile: Dict[str, Any] = {
        "state": None,
        "district": None,
        "occupation": None,
        "age": None,
        "gender": None,
        "annual_income": None,
        "owns_cultivable_land": None,
        "landholding_raw": None,
        "landholding_acres": None,
        "landholding_notes": None,
        "family_details": {},
        "housing_type": None,
        "area_type": None,
        "is_bpl": None,
        "is_govt_employee": None,
        "pays_income_tax": None,
        "is_pregnant_or_lactating": None,
        "has_girl_child_under_10": None,
        "girl_child_age": None,
        "is_street_vendor": None,
        "is_traditional_artisan": None,
    }

    # 1. State extraction
    text_lower = text.lower()
    for state_key, state_name in INDIAN_STATES.items():
        # Match as whole phrase
        if re.search(rf'\b{re.escape(state_key)}\b', text_lower):
            profile["state"] = state_name
            break

    # 2. Occupation extraction
    if re.search(r'\b(?:farmer|kisan|cultivator|agriculture|farming)\b', text_lower):
        profile["occupation"] = "farmer"
    elif re.search(r'\b(?:street\s+vendor|vendor|hawker|thela|rehri)\b', text_lower):
        profile["occupation"] = "street vendor"
        profile["is_street_vendor"] = True
    elif re.search(r'\b(?:carpenter|potter|blacksmith|goldsmith|mason|tailor|barber|artisan|craftsperson|vishwakarma)\b', text_lower):
        profile["occupation"] = "artisan"
        profile["is_traditional_artisan"] = True
    elif re.search(r'\b(?:laborer|labourer|daily\s+wage|mazdoor|worker)\b', text_lower):
        profile["occupation"] = "daily wage laborer"
    elif re.search(r'\b(?:student)\b', text_lower):
        profile["occupation"] = "student"
    elif re.search(r'\b(?:unemployed|berozgar)\b', text_lower):
        profile["occupation"] = "unemployed"

    # 3. Landholding & regional conversion
    owns_land, land_raw, land_acres, land_notes = parse_landholding(text, profile["state"])
    profile["owns_cultivable_land"] = owns_land
    profile["landholding_raw"] = land_raw
    profile["landholding_acres"] = land_acres
    profile["landholding_notes"] = land_notes

    # If occupation is farmer and owns_land is True, confirm
    if profile["occupation"] == "farmer" and profile["owns_cultivable_land"] is None:
        # User is farmer, but hasn't explicitly stated land ownership
        pass

    # 4. Income extraction & normalization
    income = normalize_indian_currency(text)
    if income is not None:
        profile["annual_income"] = income

    # 5. Age extraction
    age_match = re.search(r'\b(?:age\s*(?:is|of)?\s*([0-9]{1,2})|([0-9]{1,2})\s*(?:years?\s*old|yr|yrs|sal|saal))\b', text_lower)
    if age_match:
        val = age_match.group(1) or age_match.group(2)
        try:
            profile["age"] = int(val)
        except ValueError:
            pass

    # 6. Gender extraction
    if re.search(r'\b(?:woman|female|mother|pregnant|lactating|mahila|aurat)\b', text_lower):
        profile["gender"] = "female"
    elif re.search(r'\b(?:man|male|purush|aadmi)\b', text_lower):
        profile["gender"] = "male"

    # 7. Family details: children, daughters
    children_match = re.search(r'(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s*(?:children|kids|bachhe|santane)\b', text_lower)
    if children_match:
        qty_str = children_match.group(1)
        count = WORD_TO_NUM.get(qty_str, None)
        if count is None:
            try:
                count = int(qty_str)
            except ValueError:
                count = 1
        profile["family_details"]["children_count"] = count

    # Girl child check
    girl_match = re.search(r'(\d+|one|two)?\s*(?:girl\s*child|daughter|beti|ladki)\b', text_lower)
    if girl_match:
        profile["has_girl_child_under_10"] = True
        # Check girl child age if mentioned: e.g. "daughter of 5 years", "daughter aged 4"
        girl_age_match = re.search(r'(?:daughter|girl|beti)\s*(?:of|aged|is)?\s*([0-9]{1,2})', text_lower)
        if girl_age_match:
            try:
                profile["girl_child_age"] = int(girl_age_match.group(1))
            except ValueError:
                pass

    # 8. Housing type & area
    if re.search(r'\b(?:kutcha|kaccha|thatched|mud\s+house|dilapidated|houseless|no\s+house)\b', text_lower):
        profile["housing_type"] = "kutcha"
    elif re.search(r'\b(?:pucca|pukka|concrete\s+house)\b', text_lower):
        profile["housing_type"] = "pucca"

    if re.search(r'\b(?:rural|village|gram|panchayat|dehat)\b', text_lower):
        profile["area_type"] = "rural"
    elif re.search(r'\b(?:urban|city|municipality|town|nagar)\b', text_lower):
        profile["area_type"] = "urban"

    # 9. BPL / Ration card
    if re.search(r'\b(?:bpl|below\s+poverty\s+line|antyodaya|ration\s+card|nfsa)\b', text_lower):
        profile["is_bpl"] = True

    # 10. Tax and Govt Employee disqualifiers (Check negation FIRST to avoid false positives)
    if re.search(r'\b(?:do\s+not\s+pay\s+(?:income\s+)?tax|does\s+not\s+pay\s+(?:income\s+)?tax|don\'?t\s+pay\s+(?:income\s+)?tax|no\s+income\s+tax|not\s+(?:an?\s+)?income\s+tax\s+payee|non-taxpayer|no\s+tax)\b', text_lower):
        profile["pays_income_tax"] = False
    elif re.search(r'\b(?:pays?\s+income\s+tax|taxpayer|income\s+tax\s+payee)\b', text_lower):
        profile["pays_income_tax"] = True

    if re.search(r'\b(?:not\s+(?:a\s+)?govt\s+employee|not\s+in\s+govt|no\s+one\s+.*is\s+a\s+govt\s+employee|no\s+govt\s+job|neither\s+.*govt|private|unorganized)\b', text_lower):
        profile["is_govt_employee"] = False
    elif re.search(r'\b(?:govt\s+employee|government\s+servant|sarkari\s+naukri)\b', text_lower):
        profile["is_govt_employee"] = True

    return profile

def generate_profile_followups(profile: Dict[str, Any], relevant_schemes: List[str]) -> Tuple[List[str], Optional[str]]:
    """
    Identify missing facts essential to confirm eligibility for relevant schemes and generate a focused follow-up prompt.
    """
    missing_criteria = []

    # If farmer / PM-KISAN is relevant
    if "pm-kisan" in relevant_schemes or profile.get("occupation") == "farmer":
        if profile.get("owns_cultivable_land") is None:
            missing_criteria.append("Do you own cultivable agricultural land registered in your revenue records?")
        if profile.get("pays_income_tax") is None:
            missing_criteria.append("Did you or anyone in your household pay income tax in the last financial year?")
        if profile.get("is_govt_employee") is None:
            missing_criteria.append("Are you or a family member a regular government/PSU employee?")

    # If rural housing / PMAY-G is relevant
    if "pmay-g" in relevant_schemes:
        if profile.get("housing_type") is None:
            missing_criteria.append("What type of dwelling do you currently reside in (kutcha house, houseless, or pucca house)?")
        if profile.get("area_type") is None:
            missing_criteria.append("Do you reside in a rural Gram Panchayat area?")

    # If PM-JAY is relevant
    if "ayushman-bharat-pmjay" in relevant_schemes:
        if profile.get("age") is None and profile.get("is_bpl") is None:
            missing_criteria.append("What is your age, and does your family hold an eligible BPL/Antyodaya ration card?")

    # General missing state
    if profile.get("state") is None:
        missing_criteria.append("Which state or union territory do you reside in?")

    follow_up_prompt = None
    if missing_criteria:
        # Pick the top 2 most urgent questions to avoid overwhelming the citizen
        top_questions = missing_criteria[:2]
        follow_up_prompt = (
            "To confirm your eligibility under official scheme criteria, could you please clarify: "
            + " ".join(top_questions)
        )

    return missing_criteria, follow_up_prompt
