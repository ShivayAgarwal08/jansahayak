import json
import logging
from typing import Optional
from fastapi import APIRouter, Request, Response, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.config import settings
from app.services.whatsapp.security import verify_signature
from app.services.whatsapp.service import whatsapp_service

logger = logging.getLogger("jansahayak.whatsapp.api")

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp Cloud API"])

@router.get("/status")
def get_whatsapp_status():
    """
    Check Meta WhatsApp Cloud API integration status.
    """
    return whatsapp_service.get_status()

@router.get("/webhook")
def verify_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token")
):
    """
    Meta Webhook Verification Handshake (GET).
    Validates hub.mode == 'subscribe' and hub.verify_token against configured secret.
    """
    challenge = whatsapp_service.verify_webhook_mode(
        mode=hub_mode,
        token=hub_verify_token,
        challenge=hub_challenge
    )
    if challenge is not None:
        logger.info("WhatsApp webhook challenge verified successfully.")
        return Response(content=str(challenge), media_type="text/plain")

    logger.warning(f"WhatsApp webhook verification failed for mode '{hub_mode}' and token '{hub_verify_token}'")
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Verification token mismatch or invalid subscription mode."
    )

@router.post("/webhook")
async def handle_whatsapp_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Meta Webhook Inbound Message Handler (POST).
    Verifies HMAC-SHA256 signature, parses incoming messages, executes grounded RAG
    and eligibility evaluation, and sends response back to citizen.
    """
    # 1. Read raw body bytes for cryptographic signature check
    body_bytes = await request.body()
    signature_header = request.headers.get("X-Hub-Signature-256")

    # 2. Cryptographic signature verification
    if settings.WHATSAPP_APP_SECRET:
        is_valid = verify_signature(
            payload_bytes=body_bytes,
            signature_header=signature_header,
            app_secret=settings.WHATSAPP_APP_SECRET
        )
        if not is_valid:
            logger.warning("Rejected WhatsApp webhook due to invalid HMAC-SHA256 signature.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid webhook signature."
            )

    # 3. Parse JSON payload
    try:
        payload = json.loads(body_bytes.decode("utf-8"))
    except Exception as e:
        logger.error(f"Malformed JSON in WhatsApp webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Malformed JSON body."
        )

    # 4. Process payload through JanSahayak welfare assistant pipeline
    try:
        result = await whatsapp_service.process_incoming_payload(payload=payload, db=db)
        return {"status": "ok", "result": result}
    except Exception as e:
        logger.error(f"Error processing WhatsApp message payload: {e}")
        # Always return HTTP 200 to Meta to acknowledge receipt and prevent webhook retry spam
        return {"status": "error_handled", "detail": str(e)}
