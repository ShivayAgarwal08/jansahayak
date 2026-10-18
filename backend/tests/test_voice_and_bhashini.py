import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.services.bhashini.bhashini_service import bhashini_service, SUPPORTED_LANGUAGES

client = TestClient(app)

def test_voice_status_endpoint():
    resp = client.get("/api/voice/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "provider" in data
    assert "configured" in data
    assert "status" in data
    assert "supported_languages_count" in data
    assert data["supported_languages_count"] == len(SUPPORTED_LANGUAGES)

def test_supported_languages_schedule_8():
    resp = client.get("/api/voice/languages")
    assert resp.status_code == 200
    languages = resp.json()
    codes = [l["code"] for l in languages]
    assert "hi" in codes
    assert "en" in codes
    assert "bn" in codes
    assert "ta" in codes
    assert "te" in codes
    # Verify Bhojpuri is NOT claimed as a standard verified language
    assert "bho" not in codes

@pytest.mark.asyncio
async def test_stt_unconfigured_graceful_fallback():
    # When Bhashini credentials are None, ASR returns graceful browser fallback
    with patch.object(bhashini_service, "user_id", None), \
         patch.object(bhashini_service, "api_key", None):
        res = await bhashini_service.speech_to_text(audio_content_base64="dGVzdGF1ZGlv", language_code="hi")
        assert res["success"] is False
        assert res["use_browser_speech"] is True
        assert "not configured" in res["error"]

from unittest.mock import patch, AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_stt_mocked_success():
    with patch.object(bhashini_service, "user_id", "mock_user"), \
         patch.object(bhashini_service, "api_key", "mock_key"):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "pipelineResponse": [
                {
                    "taskType": "asr",
                    "output": [{"source": "मैं बिहार का एक छोटा किसान हूँ"}]
                }
            ]
        }
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
            res = await bhashini_service.speech_to_text(audio_content_base64="dGVzdGF1ZGlv", language_code="hi")
            assert res["success"] is True
            assert res["text"] == "मैं बिहार का एक छोटा किसान हूँ"
            assert res["language"] == "hi"
            assert res["provider"] == "bhashini"

@pytest.mark.asyncio
async def test_tts_unconfigured_graceful_fallback():
    with patch.object(bhashini_service, "user_id", None), \
         patch.object(bhashini_service, "api_key", None):
        res = await bhashini_service.text_to_speech(text="नमस्ते किसान", language_code="hi")
        assert res["success"] is False
        assert res["use_browser_speech"] is True
        assert "not configured" in res["error"]

@pytest.mark.asyncio
async def test_tts_mocked_success():
    with patch.object(bhashini_service, "user_id", "mock_user"), \
         patch.object(bhashini_service, "api_key", "mock_key"):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "pipelineResponse": [
                {
                    "taskType": "tts",
                    "audio": [{"audioContent": "bW9ja2VkX2F1ZGlvX2Jhc2U2NA=="}]
                }
            ]
        }
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
            res = await bhashini_service.text_to_speech(text="नमस्ते किसान", language_code="hi")
            assert res["success"] is True
            assert res["audio_base64"] == "bW9ja2VkX2F1ZGlvX2Jhc2U2NA=="
            assert res["language"] == "hi"

def test_api_tts_endpoint():
    resp = client.post("/api/voice/tts", json={"text": "Hello citizen", "language_code": "en"})
    assert resp.status_code == 200
    data = resp.json()
    assert "success" in data
    assert "use_browser_speech" in data

def test_api_translate_identity():
    resp = client.post(
        "/api/voice/translate",
        json={"text": "Same language test", "source_language": "en", "target_language": "en"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["translated_text"] == "Same language test"
