import hmac
import hashlib
import logging
from typing import Optional

logger = logging.getLogger("jansahayak.whatsapp.security")

def verify_signature(
    payload_bytes: bytes,
    signature_header: Optional[str],
    app_secret: Optional[str]
) -> bool:
    """
    Verify Meta WhatsApp Cloud API webhook signature (HMAC-SHA256).
    Header format: 'sha256=<hex_digest>'
    Uses hmac.compare_digest to prevent timing attacks.
    """
    if not app_secret:
        # If no secret is configured on server, log warning and allow for dev/mock mode
        logger.warning("WHATSAPP_APP_SECRET is not configured. Webhook signature verification bypassed.")
        return True

    if not signature_header:
        logger.warning("Missing X-Hub-Signature-256 header in incoming WhatsApp webhook.")
        return False

    if not signature_header.startswith("sha256="):
        logger.warning(f"Invalid signature header format: {signature_header[:15]}")
        return False

    expected_signature = signature_header[7:].strip()
    
    computed_signature = hmac.new(
        key=app_secret.encode("utf-8"),
        msg=payload_bytes,
        digestmod=hashlib.sha256
    ).hexdigest()

    is_valid = hmac.compare_digest(computed_signature, expected_signature)
    if not is_valid:
        logger.warning("Webhook signature mismatch. Possible tampering or invalid secret.")
    return is_valid
