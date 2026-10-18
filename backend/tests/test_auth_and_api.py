import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.session import Base, get_db
from app.db.seed_data import seed_database
from app.services.documents.pdf_generator import (
    generate_citizen_report_pdf,
    generate_rti_petition_pdf,
    generate_grievance_petition_pdf
)

from sqlalchemy.pool import StaticPool

# Test SQLite in-memory database with StaticPool to share connection across calls
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Initialize database schema and seeds
Base.metadata.create_all(bind=engine)
db = TestingSessionLocal()
seed_database(db)
db.close()

client = TestClient(app)

def test_health_endpoints():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

    res_db = client.get("/api/health/db")
    assert res_db.status_code == 200
    assert res_db.json()["status"] == "healthy"

def test_schemes_list_and_detail():
    res = client.get("/api/schemes")
    assert res.status_code == 200
    schemes = res.json()
    assert len(schemes) >= 5

    pm_kisan = next(s for s in schemes if s["slug"] == "pm-kisan")
    assert pm_kisan["name"] == "PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)"

    detail_res = client.get("/api/schemes/pm-kisan")
    assert detail_res.status_code == 200
    data = detail_res.json()
    assert "eligibility_rules" in data
    assert "sources" in data
    assert len(data["sources"]) > 0

def test_user_registration_and_login():
    reg_payload = {
        "full_name": "Ramesh Kumar",
        "email": "ramesh.kumar@example.com",
        "password": "SecurePassword123!",
        "phone": "9876543210",
        "state": "Uttar Pradesh",
        "preferred_language": "hi"
    }
    res = client.post("/api/auth/register", json=reg_payload)
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "ramesh.kumar@example.com"
    token = data["access_token"]

    # Login check
    login_res = client.post("/api/auth/login", json={
        "email": "ramesh.kumar@example.com",
        "password": "SecurePassword123!"
    })
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()

    # /api/auth/me check
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["full_name"] == "Ramesh Kumar"

def test_citizen_data_isolation():
    # User A registers
    res_a = client.post("/api/auth/register", json={
        "full_name": "Citizen A",
        "email": "citizena@example.com",
        "password": "PasswordA123!"
    })
    token_a = res_a.json()["access_token"]

    # User B registers
    res_b = client.post("/api/auth/register", json={
        "full_name": "Citizen B",
        "email": "citizenb@example.com",
        "password": "PasswordB123!"
    })
    token_b = res_b.json()["access_token"]

    # User A creates an application draft
    draft_res = client.post(
        "/api/applications",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "scheme_id": 1,
            "title": "Citizen A PM-KISAN Prep",
            "applicant_details": {"land_acres": 2.5},
            "checklist_state": {"aadhaar": True}
        }
    )
    assert draft_res.status_code == 201
    draft_id = draft_res.json()["id"]

    # User A can view their draft
    view_a = client.get(f"/api/applications/{draft_id}", headers={"Authorization": f"Bearer {token_a}"})
    assert view_a.status_code == 200
    assert view_a.json()["title"] == "Citizen A PM-KISAN Prep"

    # User B MUST NOT be able to view, update, or delete User A's draft (Data Isolation check)
    view_b = client.get(f"/api/applications/{draft_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert view_b.status_code == 404

    update_b = client.put(
        f"/api/applications/{draft_id}",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"title": "Hacked Title"}
    )
    assert update_b.status_code == 404

    delete_b = client.delete(f"/api/applications/{draft_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert delete_b.status_code == 404

    # User A can download the PDF, but User B gets 404
    pdf_a = client.get(f"/api/applications/{draft_id}/pdf", headers={"Authorization": f"Bearer {token_a}"})
    assert pdf_a.status_code == 200
    assert pdf_a.content.startswith(b"%PDF")

    pdf_b = client.get(f"/api/applications/{draft_id}/pdf", headers={"Authorization": f"Bearer {token_b}"})
    assert pdf_b.status_code == 404

def test_pdf_generators():
    report_pdf = generate_citizen_report_pdf(
        citizen_name="Anita Devi",
        scheme_name="PMAY-G",
        eligibility_status="eligible",
        summary_explanation="Qualified under rural housing criteria",
        satisfied_conditions=[{"criterion": "Rural", "citizen_value": "Rural", "official_rule": "Must be rural"}],
        unsatisfied_conditions=[],
        required_documents=[{"name": "Aadhaar", "alternatives": []}],
        official_portal_url="https://pmayg.nic.in"
    )
    assert report_pdf.startswith(b"%PDF")

    rti_pdf = generate_rti_petition_pdf(
        applicant_name="Suresh Patel",
        public_authority="Ministry of Rural Development",
        subject="Status of PMAY-G Installment",
        information_requested="Details of delayed installment release",
        time_period="2025-2026",
        state="Madhya Pradesh"
    )
    assert rti_pdf.startswith(b"%PDF")

    grievance_pdf = generate_grievance_petition_pdf(
        applicant_name="Sunita Sharma",
        department="Department of Health",
        category="Ayushman Card Generation Delay",
        description="Application pending at CSC for 4 weeks",
        previous_ref="TKN12345",
        desired_resolution="Expedited approval and card issuance"
    )
    assert grievance_pdf.startswith(b"%PDF")

def test_email_validation_enforced():
    # Attempt registration with invalid email format
    invalid_payload = {
        "full_name": "Test User",
        "email": "not-an-email-address",
        "password": "ValidPassword123!"
    }
    res = client.post("/api/auth/register", json=invalid_payload)
    assert res.status_code == 422  # Pydantic validation error

def test_assistant_chat_fallback():
    # Test chat assistant with no external keys configured
    res = client.post("/api/assistant/chat", json={
        "query": "How to get PM Kisan ₹6000 installment?",
        "scheme_slug": "pm-kisan"
    })
    assert res.status_code == 200
    data = res.json()
    assert "answer" in data
    assert "citations" in data
    assert len(data["citations"]) > 0

def test_voice_status():
    res = client.get("/api/voice/status")
    assert res.status_code == 200
    data = res.json()
    assert "provider" in data
    assert "browser_speech_fallback_supported" in data
    assert data["browser_speech_fallback_supported"] is True

