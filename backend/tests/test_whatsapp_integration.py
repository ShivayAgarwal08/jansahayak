import json
import hmac
import hashlib
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.services.whatsapp.security import verify_signature
from app.services.whatsapp.service import whatsapp_service
from app.core.config import settings

client = TestClient(app)

def test_whatsapp_status_endpoint():
    resp = client.get("/api/whatsapp/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "provider" in data
    assert "configured" in data
    assert "status" in data
    assert "live_messaging_available" in data

def test_webhook_verification_handshake_success():
    verify_token = settings.WHATSAPP_VERIFY_TOKEN or "jansahayak_wa_verify_2026"
    resp = client.get(
        "/api/whatsapp/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": verify_token,
            "hub.challenge": "987654321"
        }
    )
    assert resp.status_code == 200
    assert resp.text == "987654321"

def test_webhook_verification_handshake_invalid_token():
    resp = client.get(
        "/api/whatsapp/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong_unauthorized_token",
            "hub.challenge": "987654321"
        }
    )
    assert resp.status_code == 403

def test_signature_verification_security():
    secret = "meta_test_secret_12345"
    payload = b'{"test": "payload_body"}'

    # 1. Valid signature
    sig = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    assert verify_signature(payload, f"sha256={sig}", secret) is True

    # 2. Tampered payload
    tampered = b'{"test": "tampered_payload_body"}'
    assert verify_signature(tampered, f"sha256={sig}", secret) is False

    # 3. Missing or malformed header
    assert verify_signature(payload, None, secret) is False
    assert verify_signature(payload, "invalid_format", secret) is False

def test_inbound_text_message_processing_and_citations():
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "WHATSAPP_ACC_01",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {"display_phone_number": "15550234567", "phone_number_id": "123456789"},
                    "contacts": [{"profile": {"name": "Suresh"}, "wa_id": "919876543210"}],
                    "messages": [{
                        "from": "919876543210",
                        "id": "wamid.TEST_UNIQUE_MSG_001",
                        "timestamp": "1710000000",
                        "text": {"body": "I am a small farmer in Bihar with 2 bigha land. Am I eligible for PM-KISAN?"},
                        "type": "text"
                    }]
                },
                "field": "messages"
            }]
        }]
    }

    # Mock the outbound send so we don't attempt real network call
    with patch.object(whatsapp_service, "send_whatsapp_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"success": True, "status": "mocked_sent"}
        
        resp = client.post("/api/whatsapp/webhook", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["result"]["processed_count"] == 1
        assert data["result"]["details"][0]["status"] == "processed"
        
        # Verify outbound message was called with formatted WhatsApp citations
        assert mock_send.called
        sent_phone = mock_send.call_args[1]["to_phone"]
        sent_text = mock_send.call_args[1]["text"]
        assert sent_phone == "919876543210"
        assert "*जनसहायक (JanSahayak) Civic Assistant*" in sent_text
        assert "Official Government Sources:" in sent_text
        assert "https://pmkisan.gov.in" in sent_text

def test_message_idempotency_duplicate_ignored():
    dup_id = "wamid.TEST_IDEMPOTENCY_MSG_999"
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "WHATSAPP_ACC_01",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {"display_phone_number": "15550234567", "phone_number_id": "123456789"},
                    "messages": [{
                        "from": "919876543210",
                        "id": dup_id,
                        "timestamp": "1710000000",
                        "text": {"body": "First message submission"},
                        "type": "text"
                    }]
                },
                "field": "messages"
            }]
        }]
    }

    with patch.object(whatsapp_service, "send_whatsapp_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"success": True}
        # First send: processed
        resp1 = client.post("/api/whatsapp/webhook", json=payload)
        assert resp1.status_code == 200
        assert resp1.json()["result"]["details"][0]["status"] == "processed"

        # Second send with identical message ID: recognized as duplicate & discarded
        resp2 = client.post("/api/whatsapp/webhook", json=payload)
        assert resp2.status_code == 200
        assert resp2.json()["result"]["details"][0]["status"] == "duplicate_ignored"

def test_inbound_audio_message_advisory():
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "WHATSAPP_ACC_01",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "messages": [{
                        "from": "919876543210",
                        "id": "wamid.TEST_AUDIO_MSG_111",
                        "timestamp": "1710000000",
                        "type": "audio",
                        "audio": {"id": "audio_file_id_123"}
                    }]
                },
                "field": "messages"
            }]
        }]
    }

    with patch.object(whatsapp_service, "send_whatsapp_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"success": True}
        resp = client.post("/api/whatsapp/webhook", json=payload)
        assert resp.status_code == 200
        assert resp.json()["result"]["details"][0]["status"] == "audio_advisory_sent"
        sent_text = mock_send.call_args[1]["text"]
        assert "audio message" in sent_text.lower()
        assert "text" in sent_text.lower()

def test_inbound_unsupported_media_advisory():
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "WHATSAPP_ACC_01",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "messages": [{
                        "from": "919876543210",
                        "id": "wamid.TEST_STICKER_MSG_222",
                        "timestamp": "1710000000",
                        "type": "sticker",
                        "sticker": {"id": "sticker_123"}
                    }]
                },
                "field": "messages"
            }]
        }]
    }

    with patch.object(whatsapp_service, "send_whatsapp_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"success": True}
        resp = client.post("/api/whatsapp/webhook", json=payload)
        assert resp.status_code == 200
        assert resp.json()["result"]["details"][0]["status"] == "unsupported_media_advisory_sent"
