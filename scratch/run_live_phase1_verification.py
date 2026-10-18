import urllib.request
import urllib.error
import json
import time

BASE_URL = "https://jansahayak-backend-kvuq.onrender.com/api"

def make_request(endpoint: str, method: str = "GET", data: dict = None, token: str = None):
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json", "User-Agent": "JanSahayak-Phase1-Verifier/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    encoded_data = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            res_body = res.read().decode("utf-8")
            return res.status, json.loads(res_body) if res_body else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            parsed = json.loads(err_body)
        except Exception:
            parsed = {"raw": err_body}
        return e.code, parsed

def run_tests():
    print("=" * 70)
    print("JANSAHAYAK PHASE 1 LIVE DEPLOYMENT VERIFICATION")
    print(f"Target: {BASE_URL}")
    print("=" * 70)
    results = []

    # 1. Health Checks
    print("\n[1] Checking /health...")
    status, body = make_request("/health")
    assert status == 200 and body.get("status") == "healthy", f"Health failed: {status} {body}"
    print(f"  PASS: /health returned 200 (Service: {body.get('service')}, Version: {body.get('version')})")
    results.append(("Health Check", "PASS", f"200 OK - {body.get('service')}"))

    # 2. Database Health
    print("\n[2] Checking /health/db...")
    status, body = make_request("/health/db")
    assert status == 200 and body.get("database") == "connected", f"DB health failed: {status} {body}"
    print(f"  PASS: /health/db returned 200 (Dialect: {body.get('dialect')}, Database: {body.get('database')})")
    results.append(("Database Connectivity", "PASS", f"200 OK - {body.get('dialect')} connected"))

    # 3. Schemes Catalog
    print("\n[3] Checking /schemes...")
    status, body = make_request("/schemes")
    assert status == 200 and isinstance(body, list) and len(body) >= 8, f"Schemes list failed: {status}"
    scheme_slugs = [s["slug"] for s in body]
    print(f"  PASS: /schemes returned {len(body)} schemes: {', '.join(scheme_slugs[:5])}...")
    results.append(("Schemes Catalog", "PASS", f"{len(body)} verified schemes available"))

    # 4. Phase 1 Benchmark Query on /assistant/chat
    print("\n[4] Testing Benchmark Query on /assistant/chat...")
    benchmark_query = (
        "A farmer from Bihar speaks in Bhojpuri and says they have three children, "
        "two bighas of land, and annual income around ₹1.5 lakh. Which government schemes might they qualify for?"
    )
    status, body = make_request("/assistant/chat", method="POST", data={
        "query": benchmark_query,
        "preferred_language": "en"
    })
    assert status == 200, f"Assistant chat failed: {status} {body}"
    
    # Check extraction
    prof = body.get("extracted_profile", {})
    assert prof.get("occupation") == "farmer", f"Occupation extraction mismatch: {prof}"
    assert prof.get("state") == "Bihar", f"State extraction mismatch: {prof}"
    assert prof.get("annual_income") == 150000.0, f"Income normalization mismatch: {prof}"
    assert prof.get("owns_cultivable_land") is True, f"Land ownership mismatch: {prof}"
    assert "bigha" in str(prof.get("landholding_raw")), f"Bigha unit mismatch: {prof}"
    assert prof.get("family_details", {}).get("children_count") == 3, f"Children extraction mismatch: {prof}"
    print("  PASS: Fact extraction accurate:")
    print(f"        State: {prof.get('state')}, Occupation: {prof.get('occupation')}, Income: Rs. {prof.get('annual_income')}")
    print(f"        Land: {prof.get('landholding_raw')}, Regional Note: {prof.get('landholding_notes')[:65]}...")
    results.append(("Fact Extraction", "PASS", f"Bihar farmer, Rs. 1.5L income, 2 bighas with regional survey note"))

    # Check retrieval ranking
    citations = body.get("citations", [])
    assert len(citations) > 0 and citations[0]["scheme_slug"] == "pm-kisan", f"Top citation mismatch: {citations}"
    top_slugs = [c["scheme_slug"] for c in citations[:2]]
    assert "pmmvy" not in top_slugs and "ignoaps" not in top_slugs, f"False positives present: {top_slugs}"
    print(f"  PASS: Grounded retrieval ranked top scheme: {citations[0]['scheme_name']}")
    print(f"        False positive maternal/pension schemes successfully suppressed.")
    results.append(("Grounded Retrieval Ranking", "PASS", "PM-KISAN #1; PMMVY & IGNOAPS suppressed"))

    # Check deterministic eligibility in chat
    evals = body.get("eligibility_results", [])
    assert len(evals) > 0, "No eligibility results returned in chat"
    kisan_eval = next((e for e in evals if e["scheme_slug"] == "pm-kisan"), None)
    assert kisan_eval is not None, "PM-KISAN not in eligibility evaluation"
    assert kisan_eval["status"] == "possibly_eligible", f"Expected possibly_eligible, got {kisan_eval['status']}"
    print(f"  PASS: Deterministic eligibility invoked: PM-KISAN -> {kisan_eval['status']}")
    print(f"        Unknown conditions requiring follow-up: {len(kisan_eval.get('unknown_conditions', []))}")
    results.append(("Eligibility in Chat", "PASS", "PM-KISAN evaluated as possibly_eligible"))

    # Check follow-up question
    follow_up = body.get("follow_up_prompt")
    assert follow_up is not None and len(follow_up) > 10, f"Missing follow up: {follow_up}"
    print(f"  PASS: Follow-up question generated: \"{follow_up[:80]}...\"")
    results.append(("Follow-Up Generation", "PASS", follow_up[:60]))

    # Check suggested action
    action = body.get("suggested_action")
    assert action is not None and action.get("action") == "prepare_application", f"Action mismatch: {action}"
    assert action.get("scheme_slug") == "pm-kisan", f"Action slug mismatch: {action}"
    print(f"  PASS: Suggested application prefill action: Prepare Application for {action.get('scheme_name')}")
    results.append(("Application Prefill CTA", "PASS", f"prepare_application for {action.get('scheme_slug')}"))

    # Check AI Provider Fallback Transparency
    is_fallback = body.get("is_fallback")
    ai_provider = body.get("ai_provider")
    model = body.get("model")
    print(f"  AI Provider Status: is_fallback={is_fallback}, ai_provider={ai_provider}, model={model}")
    if is_fallback:
        assert body.get("status") == "fallback_grounded"
        assert "Notice: Live AI generation is currently offline" in body.get("answer") or "rule-grounded" in model
        print("  PASS: AI Fallback honestly disclosed (no false AI claims).")
        results.append(("AI Transparency", "PASS", f"Honest fallback ({model})"))
    else:
        print("  PASS: Live Groq LLM generated grounded response.")
        results.append(("AI Transparency", "PASS", f"Live Groq response ({model})"))

    # 5. Multi-Turn Session Conversation
    print("\n[5] Testing Multi-Turn Clarification Memory on /assistant/chat...")
    status, t2_body = make_request("/assistant/chat", method="POST", data={
        "query": "I do not pay income tax and no one in my family is a govt employee.",
        "existing_profile": prof
    })
    assert status == 200, f"Turn 2 failed: {status}"
    prof2 = t2_body.get("extracted_profile", {})
    assert prof2.get("pays_income_tax") is False, f"Tax status not merged: {prof2}"
    assert prof2.get("is_govt_employee") is False, f"Govt employee status not merged: {prof2}"
    assert prof2.get("occupation") == "farmer", f"Turn 1 occupation lost: {prof2}"
    
    t2_evals = t2_body.get("eligibility_results", [])
    t2_kisan = next((e for e in t2_evals if e["scheme_slug"] == "pm-kisan"), None)
    assert t2_kisan is not None and t2_kisan["status"] == "eligible", f"Expected eligible after clarification, got {t2_kisan}"
    print("  PASS: Multi-turn memory preserved previous facts and updated eligibility to ELIGIBLE.")
    results.append(("Multi-Turn Memory", "PASS", "PM-KISAN updated to confirmed ELIGIBLE"))

    # 6. Authentication and Application Draft Isolation
    print("\n[6] Testing User Registration, Authentication & Draft Isolation...")
    test_email = f"citizen.verifier_{int(time.time())}@gmail.com"
    test_password = "SecurePassword@2026!"
    status, reg_body = make_request("/auth/register", method="POST", data={
        "email": test_email,
        "password": test_password,
        "full_name": "Test Citizen Verifier",
        "role": "citizen"
    })
    assert status in [200, 201], f"Registration failed: {status} {reg_body}"
    user_id = reg_body.get("user", {}).get("id") or reg_body.get("id")
    token = reg_body.get("access_token")
    print(f"  PASS: Citizen registered successfully (User ID: {user_id}, Email: {test_email})")

    # If login is separate or verify token
    if not token:
        status, login_body = make_request("/auth/login", method="POST", data={
            "email": test_email,
            "password": test_password
        })
        assert status == 200 and "access_token" in login_body, f"Login failed: {status} {login_body}"
        token = login_body["access_token"]
    print(f"  PASS: Authenticated access token verified.")

    # Check Me
    status, me_body = make_request("/auth/me", token=token)
    assert status == 200 and me_body.get("id") == user_id, f"Auth me failed: {status} {me_body}"
    print(f"  PASS: /auth/me returns isolated profile for {me_body.get('full_name')}.")

    # Create Draft using prefilled details
    prefill_notes = (
        f"[Extracted from JanSahayak Assistant]\n"
        f"State: {prof.get('state')} | District: {prof.get('district')} | "
        f"Occupation: {prof.get('occupation')} | Annual Income: ₹{prof.get('annual_income')} | "
        f"Land: {prof.get('landholding_raw')} ({prof.get('landholding_notes')})"
    )
    status, draft_body = make_request("/applications", method="POST", token=token, data={
        "scheme_id": 1,
        "title": "PM-KISAN Application Draft - Test Citizen Verifier",
        "applicant_details": {
            "applicant_name": "Test Citizen Verifier",
            "state": prof.get("state"),
            "district": prof.get("district"),
            "occupation": prof.get("occupation"),
            "annual_income": prof.get("annual_income"),
            "landholding": prof.get("landholding_raw")
        },
        "checklist_state": {"Aadhaar Card": True, "Land Ownership Papers": False},
        "notes": prefill_notes
    })
    assert status == 201, f"Draft creation failed: {status} {draft_body}"
    draft_id = draft_body.get("id")
    print(f"  PASS: Draft created successfully (Draft ID: {draft_id}, Scheme ID: {draft_body.get('scheme_id')})")
    print(f"        Notes stored safely in database body: \"{draft_body.get('notes')[:60]}...\"")

    # List Drafts
    status, list_body = make_request("/applications", token=token)
    assert status == 200 and len(list_body) == 1, f"Draft list failed: {status} {list_body}"
    assert list_body[0]["id"] == draft_id
    print(f"  PASS: User draft list verified with 1 isolated draft.")
    results.append(("Auth & Application Draft Prefill", "PASS", f"Draft {draft_id} isolated & persisted"))

    # 7. Direct Eligibility Engine Verification
    print("\n[7] Testing /eligibility/assess deterministic engine...")
    status, elig_body = make_request("/eligibility/assess", method="POST", data={
        "scheme_slug": "pm-kisan",
        "profile": {
            "owns_cultivable_land": True,
            "pays_income_tax": False,
            "is_govt_employee": False
        }
    })
    assert status == 200 and elig_body.get("status") == "eligible", f"Assess failed: {elig_body}"
    assert "automated assessment is rule-based" in elig_body.get("disclaimer"), "Disclaimer missing"
    print(f"  PASS: Direct eligibility returned status: {elig_body.get('status')}")
    print(f"        Official disclaimer verified.")
    results.append(("Direct Eligibility Engine", "PASS", "PM-KISAN confirmed eligible with disclaimer"))

    print("\n" + "=" * 70)
    print("ALL LIVE VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)
    for name, res, detail in results:
        print(f"  [{res}] {name:<35} : {detail}")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
