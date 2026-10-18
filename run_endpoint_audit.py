import sys
import os
import json
import httpx
from datetime import datetime

# Set up backend import path
sys.path.insert(0, os.path.abspath('backend'))
from fastapi.testclient import TestClient
from app.main import app

def run_tests_against_target(target_name, client_type='in_process', base_url=None):
    results = []
    
    print(f"\n==========================================")
    print(f"RUNNING AUDIT SUITE ON: {target_name}")
    print(f"==========================================\n")

    def execute_suite(client):
        def record(endpoint, method, scenario, expected_status, res):
            actual_status = res.status_code
            if isinstance(expected_status, list):
                passed = actual_status in expected_status
            else:
                passed = (actual_status == expected_status)
                
            try:
                body = res.json() if res.headers.get("content-type", "").startswith("application/json") else f"Bytes/Non-JSON ({len(res.content)} bytes)"
            except Exception:
                body = res.text[:200]
                
            status_label = "PASS" if passed else "FAIL"
            results.append({
                "endpoint": endpoint,
                "method": method,
                "scenario": scenario,
                "expected_status": expected_status,
                "actual_status": actual_status,
                "passed": passed,
                "evidence": str(body)[:150]
            })
            print(f"[{status_label}] {method:6} {endpoint:40} | Scenario: {scenario:35} | {actual_status} vs {expected_status}")
            return body

        # 1. Health & Root
        r = client.get("/")
        record("/", "GET", "Root welcome endpoint", 200, r)

        r = client.get("/api/health")
        record("/api/health", "GET", "Platform health check", 200, r)

        r = client.get("/api/health/db")
        record("/api/health/db", "GET", "Database connection check", 200, r)

        # 2. Public Scheme Endpoints
        r = client.get("/api/schemes")
        schemes = record("/api/schemes", "GET", "List verified schemes", 200, r)

        r = client.get("/api/schemes/categories")
        record("/api/schemes/categories", "GET", "Get scheme categories", 200, r)

        r = client.get("/api/schemes/pm-kisan")
        record("/api/schemes/{slug}", "GET", "Get PM-KISAN details", 200, r)

        r = client.get("/api/schemes/non-existent-scheme-xyz")
        record("/api/schemes/{slug}", "GET", "Non-existent scheme returns 404", 404, r)

        r = client.get("/api/schemes/compare?slugs=pm-kisan,pmay-g")
        record("/api/schemes/compare", "GET", "Compare multiple schemes", 200, r)

        # 3. Voice & Language Endpoints
        r = client.get("/api/voice/status")
        record("/api/voice/status", "GET", "Voice provider readiness status", 200, r)

        r = client.get("/api/voice/languages")
        record("/api/voice/languages", "GET", "List supported 11 Indian languages", 200, r)

        r = client.post("/api/voice/stt", json={"audio_base64": "dGVzdA==", "language_code": "hi"})
        record("/api/voice/stt", "POST", "Speech-to-text with fallback", 200, r)

        r = client.post("/api/voice/translate", json={"text": "Hello", "source_language": "en", "target_language": "hi"})
        record("/api/voice/translate", "POST", "Translation with fallback", 200, r)

        # 4. Public RAG Assistant Chat
        r = client.post("/api/assistant/chat", json={"query": "What is PM Kisan benefit amount?", "scheme_slug": "pm-kisan"})
        record("/api/assistant/chat", "POST", "Grounded AI chat with citation", 200, r)

        # 5. Public Feedback Submission
        r = client.post("/api/feedback", json={"category": "general", "message": "Audit test feedback verification"})
        record("/api/feedback", "POST", "Submit citizen feedback", [200, 201], r)

        # 6. Auth Protection Checks (Unauthorized)
        r = client.get("/api/auth/me")
        record("/api/auth/me", "GET", "Unauthenticated profile access fails", 401, r)

        r = client.get("/api/applications")
        record("/api/applications", "GET", "Unauthenticated application drafts fails", 401, r)

        r = client.get("/api/admin/schemes")
        record("/api/admin/schemes", "GET", "Unauthenticated admin endpoint fails", 401, r)

        # 7. Citizen Registration, Login & Profile Lifecycle
        test_email = f"audit_citizen_{int(datetime.now().timestamp())}@example.com"
        reg_payload = {
            "full_name": "Test Auditor Citizen",
            "email": test_email,
            "password": "AuditSecurePassword123!",
            "phone": "9812345678",
            "state": "Madhya Pradesh",
            "district": "Bhopal",
            "preferred_language": "hi"
        }
        r = client.post("/api/auth/register", json=reg_payload)
        reg_data = record("/api/auth/register", "POST", "Register new citizen account", 200, r)
        token = reg_data.get("access_token", "") if isinstance(reg_data, dict) else ""

        # Login
        login_payload = {"email": test_email, "password": "AuditSecurePassword123!"}
        r = client.post("/api/auth/login", json=login_payload)
        login_data = record("/api/auth/login", "POST", "Login with valid credentials", 200, r)

        # Prepare Auth Headers
        auth_headers = {"Authorization": f"Bearer {token}"} if token else {}

        # Profile Get
        r = client.get("/api/auth/me", headers=auth_headers)
        record("/api/auth/me", "GET", "Get authenticated citizen profile", 200, r)

        # Profile Update
        r = client.put("/api/auth/me", json={"full_name": "Auditor Updated Name", "district": "Indore"}, headers=auth_headers)
        record("/api/auth/me", "PUT", "Update citizen profile details", 200, r)

        # 8. Eligibility Assessment & PDF Report
        profile_data = {
            "age": 42,
            "gender": "male",
            "state": "Madhya Pradesh",
            "residence": "rural",
            "occupation": "farmer",
            "annual_income": 80000,
            "landholding_acres": 2.5,
            "income_tax_payer": False,
            "is_govt_employee": False
        }
        r = client.post("/api/eligibility/assess", json={"scheme_slug": "pm-kisan", "profile": profile_data}, headers=auth_headers)
        record("/api/eligibility/assess", "POST", "Evaluate eligibility with deterministic engine", 200, r)

        r = client.get("/api/eligibility/history", headers=auth_headers)
        record("/api/eligibility/history", "GET", "Fetch user assessment history", 200, r)

        r = client.post("/api/eligibility/download-report", json={"scheme_slug": "pm-kisan", "profile": profile_data}, headers=auth_headers)
        record("/api/eligibility/download-report", "POST", "Generate citizen eligibility PDF", 200, r)

        # 9. Application Preparation CRUD & PDF
        scheme_id = 1
        if isinstance(schemes, list) and len(schemes) > 0:
            scheme_id = schemes[0]["id"]

        draft_payload = {
            "scheme_id": scheme_id,
            "title": "PM Kisan Application Draft Audit",
            "applicant_details": {"name": "Auditor", "land_survey_no": "123/4"},
            "checklist_state": {"aadhaar_ready": True, "patta_ready": True},
            "notes": "Draft prepared during system verification"
        }
        r = client.post("/api/applications", json=draft_payload, headers=auth_headers)
        app_draft = record("/api/applications", "POST", "Create application draft", 201, r)
        app_draft_id = app_draft.get("id") if isinstance(app_draft, dict) else 1

        r = client.get("/api/applications", headers=auth_headers)
        record("/api/applications", "GET", "List user application drafts", 200, r)

        r = client.get(f"/api/applications/{app_draft_id}", headers=auth_headers)
        record("/api/applications/{draft_id}", "GET", "Get single application draft", 200, r)

        r = client.put(f"/api/applications/{app_draft_id}", json={"title": "Updated Draft Title"}, headers=auth_headers)
        record("/api/applications/{draft_id}", "PUT", "Update application draft", 200, r)

        r = client.get(f"/api/applications/{app_draft_id}/pdf", headers=auth_headers)
        record("/api/applications/{draft_id}/pdf", "GET", "Download application summary PDF", 200, r)

        r = client.delete(f"/api/applications/{app_draft_id}", headers=auth_headers)
        record("/api/applications/{draft_id}", "DELETE", "Delete application draft", 200, r)

        # 10. RTI Assistant CRUD & PDF
        rti_payload = {
            "public_authority": "Department of Agriculture",
            "subject": "Delay in PM-KISAN 16th Installment",
            "information_requested": "Provide official reason for installment status being under review",
            "time_period": "2025-2026",
            "applicant_name": "Test Auditor Citizen",
            "state": "Madhya Pradesh",
            "preferred_language": "en"
        }
        r = client.post("/api/rti", json=rti_payload, headers=auth_headers)
        rti_draft = record("/api/rti", "POST", "Create RTI petition draft", 201, r)
        rti_draft_id = rti_draft.get("id") if isinstance(rti_draft, dict) else 1

        r = client.get("/api/rti", headers=auth_headers)
        record("/api/rti", "GET", "List RTI drafts", 200, r)

        r = client.get(f"/api/rti/{rti_draft_id}", headers=auth_headers)
        record("/api/rti/{draft_id}", "GET", "Get single RTI draft", 200, r)

        r = client.put(f"/api/rti/{rti_draft_id}", json={"subject": "Updated RTI Subject"}, headers=auth_headers)
        record("/api/rti/{draft_id}", "PUT", "Update RTI draft", 200, r)

        r = client.get(f"/api/rti/{rti_draft_id}/pdf", headers=auth_headers)
        record("/api/rti/{draft_id}/pdf", "GET", "Download RTI petition PDF", 200, r)

        r = client.delete(f"/api/rti/{rti_draft_id}", headers=auth_headers)
        record("/api/rti/{draft_id}", "DELETE", "Delete RTI draft", 200, r)

        # 11. Grievance Assistant CRUD & PDF
        grievance_payload = {
            "department": "Revenue and Land Records",
            "category": "Land Record Verification Delay",
            "description": "Patta mutation certificate pending at Tehsil for over 6 months",
            "desired_resolution": "Immediate field inspection and mutation approval",
            "previous_complaint_ref": "REF998877",
            "applicant_name": "Test Auditor Citizen"
        }
        r = client.post("/api/grievances", json=grievance_payload, headers=auth_headers)
        grievance_draft = record("/api/grievances", "POST", "Create Grievance representation draft", 201, r)
        grievance_draft_id = grievance_draft.get("id") if isinstance(grievance_draft, dict) else 1

        r = client.get("/api/grievances", headers=auth_headers)
        record("/api/grievances", "GET", "List Grievance drafts", 200, r)

        r = client.get(f"/api/grievances/{grievance_draft_id}", headers=auth_headers)
        record("/api/grievances/{draft_id}", "GET", "Get single Grievance draft", 200, r)

        r = client.put(f"/api/grievances/{grievance_draft_id}", json={"description": "Updated Grievance Description"}, headers=auth_headers)
        record("/api/grievances/{draft_id}", "PUT", "Update Grievance draft", 200, r)

        r = client.get(f"/api/grievances/{grievance_draft_id}/pdf", headers=auth_headers)
        record("/api/grievances/{draft_id}/pdf", "GET", "Download Grievance representation PDF", 200, r)

        r = client.delete(f"/api/grievances/{grievance_draft_id}", headers=auth_headers)
        record("/api/grievances/{draft_id}", "DELETE", "Delete Grievance draft", 200, r)

        # 12. Dashboard & Saved Schemes
        r = client.post(f"/api/dashboard/saved-schemes/{scheme_id}", headers=auth_headers)
        record("/api/dashboard/saved-schemes/{scheme_id}", "POST", "Toggle bookmark scheme (Save)", 200, r)

        r = client.get("/api/dashboard/saved-schemes", headers=auth_headers)
        record("/api/dashboard/saved-schemes", "GET", "Get saved schemes", 200, r)

        r = client.get("/api/dashboard/stats", headers=auth_headers)
        record("/api/dashboard/stats", "GET", "Get citizen dashboard statistics", 200, r)

        r = client.post(f"/api/dashboard/saved-schemes/{scheme_id}", headers=auth_headers)
        record("/api/dashboard/saved-schemes/{scheme_id}", "POST", "Toggle bookmark scheme (Unsave)", 200, r)

        # 13. Admin Operations
        admin_login = client.post("/api/auth/login", json={"email": "admin@jansahayak.gov.in", "password": "JanSahayakAdmin@2026"})
        admin_data = record("/api/auth/login", "POST", "Admin authentication", 200, admin_login)
        admin_token = admin_data.get("access_token", "") if isinstance(admin_data, dict) else ""
        admin_headers = {"Authorization": f"Bearer {admin_token}"} if admin_token else {}

        r = client.get("/api/admin/schemes", headers=admin_headers)
        record("/api/admin/schemes", "GET", "Admin list all schemes", 200, r)

        r = client.put(f"/api/admin/schemes/{scheme_id}/verify", json={"verification_status": "verified", "notes": "Audited provenance verified"}, headers=admin_headers)
        record("/api/admin/schemes/{scheme_id}/verify", "PUT", "Admin update scheme verification status", 200, r)

        r = client.get("/api/admin/audit-logs", headers=admin_headers)
        record("/api/admin/audit-logs", "GET", "Admin get audit logs", 200, r)

        r = client.get("/api/admin/feedbacks", headers=admin_headers)
        record("/api/admin/feedbacks", "GET", "Admin get citizen feedbacks", 200, r)

        # 14. Citizen Account Deletion (GDPR/Privacy right)
        r = client.delete("/api/auth/me", headers=auth_headers)
        record("/api/auth/me", "DELETE", "Citizen account permanent deletion", 200, r)

        # 15. Verify citizen cannot login after deletion
        r = client.post("/api/auth/login", json=login_payload)
        record("/api/auth/login", "POST", "Deleted citizen cannot log in", 401, r)

    if client_type == 'in_process':
        with TestClient(app) as client:
            execute_suite(client)
    else:
        with httpx.Client(base_url=base_url, timeout=25.0) as client:
            execute_suite(client)

    passed_count = sum(1 for x in results if x["passed"])
    total_count = len(results)
    print(f"\nAUDIT COMPLETE FOR {target_name}: {passed_count}/{total_count} PASSED ({(passed_count/total_count)*100:.1f}%)")
    return results

if __name__ == '__main__':
    in_proc_results = run_tests_against_target("In-Process FastAPI TestClient", client_type='in_process')
    live_results = run_tests_against_target("Live Render Production Backend", client_type='live', base_url='https://jansahayak-backend-kvuq.onrender.com')

    with open('reports_audit_results.json', 'w', encoding='utf-8') as f:
        json.dump({"in_process": in_proc_results, "live": live_results}, f, indent=2)
    print("\nSaved test results to reports_audit_results.json")
