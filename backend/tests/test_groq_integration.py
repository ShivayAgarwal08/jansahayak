import pytest
import os
import httpx
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.config import settings
from app.db.session import Base, get_db
from app.db.seed_data import seed_database
from app.services.rag.retrieval import retrieve_grounded_passages, Passage
from app.services.ai.groq_service import generate_grounded_answer
from app.models.scheme import Scheme

# SQLite in-memory test database
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

class MockPassage:
    def __init__(self, slug, name, title, authority, url, content):
        self.scheme_slug = slug
        self.scheme_name = name
        self.title = title
        self.authority = authority
        self.url = url
        self.content = content
        self.page_number = 1
        self.match_reasons = ["Matched test criteria"]
        self.is_seeded_record = True

# 1. Official Model Configuration Verification
def test_groq_configured_model():
    assert settings.GROQ_MODEL == "llama-3.3-70b-versatile"
    assert "llama-3.3" in settings.GROQ_MODEL

# 2. Secure Key Access
def test_groq_secure_key_access():
    # Verify that key configuration can be inspected as a boolean without printing/logging value
    has_key = bool(settings.GROQ_API_KEY and settings.GROQ_API_KEY.strip())
    assert isinstance(has_key, bool)
    # The repr or str of settings must not be directly printed to public logs

# 3. Status Endpoint when Unconfigured
def test_assistant_status_unconfigured():
    with patch("app.core.config.settings.GROQ_API_KEY", ""):
        res = client.get("/api/assistant/status")
        assert res.status_code == 200
        data = res.json()
        assert data["groq_configured"] is False
        assert data["status"] == "fallback_mode"
        assert data["ai_provider"] == "none"
        assert data["groq_model"] == "llama-3.3-70b-versatile"
        assert "api_key" not in data

# 4. Status Endpoint when Configured
def test_assistant_status_configured():
    with patch("app.core.config.settings.GROQ_API_KEY", "gsk_mock_secret_key_12345"):
        res = client.get("/api/assistant/status")
        assert res.status_code == 200
        data = res.json()
        assert data["groq_configured"] is True
        assert data["status"] == "online"
        assert data["ai_provider"] == "groq"
        assert "api_key" not in data
        assert "gsk_" not in str(data)

# 5. Successful Groq AI Inference (Mocked)
@pytest.mark.asyncio
async def test_groq_successful_inference_mock():
    mock_groq_response = {
        "id": "chatcmpl-test-123",
        "object": "chat.completion",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": (
                        "Based on verified government records, as a farmer in Bihar with 2 bighas of land, "
                        "you qualify for PM-KISAN which provides ₹6,000 annually. [Passage 1]"
                    )
                },
                "finish_reason": "stop"
            }
        ]
    }
    
    passages = [
        MockPassage("pm-kisan", "PM-KISAN", "PM-KISAN Guidelines", "Dept of Agriculture", "https://pmkisan.gov.in", "Financial benefit: ₹6,000 per year")
    ]
    
    with patch("app.core.config.settings.GROQ_API_KEY", "gsk_test_key_5678"):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = AsyncMock(status_code=200, json=lambda: mock_groq_response)
            
            result = await generate_grounded_answer(
                query="I am a farmer from Bihar with 2 bighas of land. Do I qualify?",
                passages=passages,
                preferred_language="en",
                extracted_profile={"state": "Bihar", "occupation": "farmer", "annual_income": 150000.0},
                eligibility_evaluations=[{"scheme_slug": "pm-kisan", "scheme_name": "PM-KISAN", "status": "eligible", "summary_explanation": "All criteria met"}],
                follow_up_prompt=None
            )
            
            assert result["is_fallback"] is False
            assert result["status"] == "success"
            assert result["ai_provider"] == "groq"
            assert result["fallback_reason"] is None
            assert result["model"] == "llama-3.3-70b-versatile"
            assert "PM-KISAN which provides ₹6,000" in result["answer"]
            assert len(result["citations"]) == 1

# 6. Groq Provider Timeout Error Handling
@pytest.mark.asyncio
async def test_groq_timeout_error_handling():
    passages = [
        MockPassage("pm-kisan", "PM-KISAN", "PM-KISAN Guidelines", "Dept of Agriculture", "https://pmkisan.gov.in", "Financial benefit: ₹6,000 per year")
    ]
    with patch("app.core.config.settings.GROQ_API_KEY", "gsk_test_key_5678"):
        with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Read timed out")):
            result = await generate_grounded_answer(
                query="Tell me about PM-KISAN",
                passages=passages,
                preferred_language="en"
            )
            assert result["is_fallback"] is True
            assert result["status"] == "fallback_grounded"
            assert result["ai_provider"] == "none"
            assert result["fallback_reason"] == "provider_timeout"
            assert "Live AI service timed out" in result["answer"]

# 7. Groq Provider HTTP 401 Unauthorized Handling (Invalid Key)
@pytest.mark.asyncio
async def test_groq_401_invalid_key_handling():
    passages = [
        MockPassage("pm-kisan", "PM-KISAN", "PM-KISAN Guidelines", "Dept of Agriculture", "https://pmkisan.gov.in", "Financial benefit: ₹6,000 per year")
    ]
    mock_err_res = AsyncMock(status_code=401, text='{"error": {"message": "Invalid API Key"}}')
    with patch("app.core.config.settings.GROQ_API_KEY", "gsk_invalid_key"):
        with patch("httpx.AsyncClient.post", return_value=mock_err_res):
            result = await generate_grounded_answer(
                query="Tell me about PM-KISAN",
                passages=passages,
                preferred_language="en"
            )
            assert result["is_fallback"] is True
            assert result["status"] == "fallback_grounded"
            assert result["fallback_reason"] == "provider_http_401"
            assert "provider_http_401" in result["answer"]
            # Sensitive key must not be in answer
            assert "gsk_invalid_key" not in result["answer"]

# 8. Groq Provider HTTP 429 Rate Limit Handling
@pytest.mark.asyncio
async def test_groq_429_rate_limit_handling():
    passages = [
        MockPassage("pm-kisan", "PM-KISAN", "PM-KISAN Guidelines", "Dept of Agriculture", "https://pmkisan.gov.in", "Financial benefit: ₹6,000 per year")
    ]
    mock_err_res = AsyncMock(status_code=429, text='{"error": {"message": "Rate limit reached"}}')
    with patch("app.core.config.settings.GROQ_API_KEY", "gsk_valid_key"):
        with patch("httpx.AsyncClient.post", return_value=mock_err_res):
            result = await generate_grounded_answer(
                query="Tell me about PM-KISAN",
                passages=passages,
                preferred_language="en"
            )
            assert result["is_fallback"] is True
            assert result["status"] == "fallback_grounded"
            assert result["fallback_reason"] == "provider_http_429"

# 9. End-to-End Chat Endpoint with Mocked Groq Success
def test_e2e_chat_with_mocked_groq():
    mock_groq_response = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "You are eligible for PM-KISAN based on verified land records. [Passage 1]"
                }
            }
        ]
    }
    with patch("app.core.config.settings.GROQ_API_KEY", "gsk_test_token_123"):
        with patch("httpx.AsyncClient.post", return_value=AsyncMock(status_code=200, json=lambda: mock_groq_response)):
            res = client.post("/api/assistant/chat", json={
                "query": "I am a farmer in Bihar with 2 bighas of land and no govt job."
            })
            assert res.status_code == 200
            data = res.json()
            assert data["is_fallback"] is False
            assert data["ai_provider"] == "groq"
            assert data["model"] == "llama-3.3-70b-versatile"
            assert "eligible for PM-KISAN" in data["answer"]
            assert data["extracted_profile"]["occupation"] == "farmer"
            assert data["extracted_profile"]["state"] == "Bihar"

# 10. Optional Real Production/Live Smoke Test
@pytest.mark.asyncio
async def test_live_groq_api_smoke_test_when_key_present():
    key = os.environ.get("GROQ_API_KEY")
    if not key or not key.strip():
        pytest.skip("GROQ_API_KEY is not configured in local environment; skipping live provider test.")
    
    # Real live call to api.groq.com
    async with httpx.AsyncClient(timeout=15.0) as http_client:
        response = await http_client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {key.strip()}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "user", "content": "Respond with the word 'VERIFIED' only."}
                ],
                "max_tokens": 10
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["choices"]) > 0
