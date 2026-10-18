import logging
import httpx
from typing import Dict, Any, List, Optional, Set
from collections import deque
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.scheme import Scheme
from app.services.ai.profile_extractor import extract_citizen_profile
from app.services.rag.retrieval import retrieve_grounded_passages
from app.services.eligibility.engine import evaluate_scheme_eligibility
from app.services.ai.groq_service import generate_grounded_answer

logger = logging.getLogger("jansahayak.whatsapp.service")

class WhatsAppService:
    def __init__(self):
        self.verify_token = settings.WHATSAPP_VERIFY_TOKEN
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.app_secret = settings.WHATSAPP_APP_SECRET
        self.api_url = settings.WHATSAPP_API_URL.rstrip("/")
        
        # In-memory LRU idempotency cache (keeps up to 10,000 recent message IDs)
        self._processed_msg_ids: Set[str] = set()
        self._msg_id_queue: deque = deque(maxlen=10000)

    def is_configured(self) -> bool:
        """Check whether minimum WhatsApp credentials are present."""
        return bool(self.verify_token and self.access_token and self.phone_number_id)

    def get_status(self) -> Dict[str, Any]:
        """Return WhatsApp integration status without exposing credentials."""
        configured = self.is_configured()
        return {
            "provider": "Meta WhatsApp Cloud API",
            "configured": configured,
            "status": "ready" if configured else "awaiting_credentials",
            "verify_token_configured": bool(self.verify_token),
            "access_token_configured": bool(self.access_token),
            "phone_number_id_configured": bool(self.phone_number_id),
            "app_secret_configured": bool(self.app_secret),
            "live_messaging_available": configured,
            "message": (
                "WhatsApp Cloud API webhook and messaging active."
                if configured
                else "WhatsApp Cloud API credentials pending configuration on server. Webhook validation and mocked responses active."
            )
        }

    def verify_webhook_mode(self, mode: Optional[str], token: Optional[str], challenge: Optional[str]) -> Optional[int]:
        """
        Validate Meta webhook verification challenge (GET request).
        """
        if mode == "subscribe" and token == (self.verify_token or "jansahayak_wa_verify_2026"):
            try:
                return int(challenge) if challenge else None
            except ValueError:
                return None
        return None

    def is_duplicate_message(self, message_id: str) -> bool:
        """Check if message_id was already processed (Idempotency)."""
        if message_id in self._processed_msg_ids:
            return True
        self._processed_msg_ids.add(message_id)
        self._msg_id_queue.append(message_id)
        if len(self._processed_msg_ids) > len(self._msg_id_queue):
            self._processed_msg_ids = set(self._msg_id_queue)
        return False

    async def send_whatsapp_message(self, to_phone: str, text: str) -> Dict[str, Any]:
        """
        Send an outbound text message via Meta WhatsApp Cloud API.
        """
        if not self.access_token or not self.phone_number_id:
            logger.info(f"[Mocked WhatsApp] Would send to {to_phone}: {text[:80]}...")
            return {
                "success": False,
                "status": "blocked_missing_credentials",
                "recipient": to_phone,
                "message": "WHATSAPP_ACCESS_TOKEN or WHATSAPP_PHONE_NUMBER_ID not configured."
            }

        url = f"{self.api_url}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_phone,
            "type": "text",
            "text": {"preview_url": True, "body": text}
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code in (200, 201):
                    return {"success": True, "response": resp.json()}
                else:
                    logger.error(f"WhatsApp API HTTP {resp.status_code}: {resp.text}")
                    return {
                        "success": False,
                        "status": "provider_error",
                        "status_code": resp.status_code,
                        "error": resp.text
                    }
        except Exception as e:
            logger.error(f"WhatsApp API connection error: {e}")
            return {"success": False, "status": "connection_error", "error": str(e)}

    def format_for_whatsapp(
        self,
        ai_reply: str,
        citations: List[Any],
        extracted_profile: Dict[str, Any],
        eligibility_results: List[Dict[str, Any]]
    ) -> str:
        """
        Format JanSahayak assistant output cleanly for WhatsApp readability.
        Uses WhatsApp formatting: *bold*, _italics_, and bullets.
        """
        parts = []
        parts.append("🇮🇳 *जनसहायक (JanSahayak) Civic Assistant*\n")

        # Clean AI reply (convert Markdown headers to WhatsApp bold)
        clean_reply = ai_reply.replace("### ", "*").replace("## ", "*").replace("# ", "*")
        parts.append(clean_reply.strip())

        # Citations block
        if citations:
            parts.append("\n\n📚 *Official Government Sources:*")
            for idx, c in enumerate(citations[:3], 1):
                if isinstance(c, dict):
                    name = c.get("scheme_name", "Scheme")
                    url = c.get("url", "")
                    page = c.get("page_number", 1)
                    ref = c.get("document_reference", "")
                else:
                    name = getattr(c, "scheme_name", "Scheme")
                    url = getattr(c, "url", "")
                    page = getattr(c, "page_number", 1)
                    ref = getattr(c, "document_reference", "") or ""
                ref_str = f" [Ref: {ref}]" if ref else ""
                parts.append(f"{idx}. *{name}* (Page {page}){ref_str}\n   🔗 {url}")

        parts.append("\n\n_Note: JanSahayak provides evidence-based civic guidance. Always verify on official .gov.in portals._")
        return "\n".join(parts)

    async def process_incoming_payload(self, payload: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """
        Process Meta WhatsApp webhook event payload.
        Connects incoming citizen messages to profile extraction, grounded RAG,
        deterministic eligibility evaluation, and Groq assistant synthesis.
        """
        entries = payload.get("entry", [])
        if not entries:
            return {"status": "no_entries"}

        results = []

        for entry in entries:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])

                for msg in messages:
                    msg_id = msg.get("id")
                    from_phone = msg.get("from")
                    msg_type = msg.get("type")

                    if not msg_id or not from_phone:
                        continue

                    # Idempotency check
                    if self.is_duplicate_message(msg_id):
                        logger.info(f"Discarding duplicate WhatsApp message {msg_id}")
                        results.append({"message_id": msg_id, "status": "duplicate_ignored"})
                        continue

                    # 1. Text Message Handling
                    if msg_type == "text":
                        text_body = msg.get("text", {}).get("body", "").strip()
                        if not text_body:
                            continue

                        # Extract citizen profile
                        extracted_profile = extract_citizen_profile(text_body)

                        # Grounded RAG retrieval
                        passages = retrieve_grounded_passages(query=text_body, db=db, limit=4)

                        # Deterministic eligibility evaluation
                        top_scheme_slugs = list(dict.fromkeys([p.scheme_slug for p in passages]))[:2]
                        eligibility_evals: List[Dict[str, Any]] = []
                        if top_scheme_slugs:
                            schemes_in_db = db.query(Scheme).filter(Scheme.slug.in_(top_scheme_slugs)).all()
                            schemes_map = {s.slug: s for s in schemes_in_db}
                            for slug in top_scheme_slugs:
                                if slug in schemes_map:
                                    eval_res = evaluate_scheme_eligibility(schemes_map[slug], extracted_profile)
                                    eligibility_evals.append(eval_res.to_dict())

                        # Groq synthesis
                        ai_result = await generate_grounded_answer(
                            query=text_body,
                            passages=passages,
                            preferred_language="en",
                            extracted_profile=extracted_profile,
                            eligibility_evaluations=eligibility_evals,
                            follow_up_prompt=None
                        )

                        wa_reply = self.format_for_whatsapp(
                            ai_reply=ai_result.get("answer", ""),
                            citations=passages,
                            extracted_profile=extracted_profile,
                            eligibility_results=eligibility_evals
                        )

                        # Send outbound reply
                        send_res = await self.send_whatsapp_message(to_phone=from_phone, text=wa_reply)
                        results.append({
                            "message_id": msg_id,
                            "type": "text",
                            "status": "processed",
                            "delivery": send_res
                        })

                    # 2. Audio Message Handling
                    elif msg_type == "audio":
                        reply_text = (
                            "🇮🇳 *JanSahayak Voice Assistant*\n\n"
                            "We received your audio message. WhatsApp voice processing via Bhashini ASR "
                            "requires active server credentials. Please send your query as a text message, "
                            "or use the multilingual voice interface on our portal:\n"
                            "🌐 https://jansahayak-two.vercel.app/assistant"
                        )
                        send_res = await self.send_whatsapp_message(to_phone=from_phone, text=reply_text)
                        results.append({
                            "message_id": msg_id,
                            "type": "audio",
                            "status": "audio_advisory_sent",
                            "delivery": send_res
                        })

                    # 3. Unsupported Media Handling
                    else:
                        reply_text = (
                            f"🇮🇳 *JanSahayak Civic Support*\n\n"
                            f"We received your message of type '{msg_type}'. "
                            "Currently JanSahayak supports scheme eligibility and guidance via text messages. "
                            "Please describe your query (e.g., occupation, state, landholding, income) in text."
                        )
                        send_res = await self.send_whatsapp_message(to_phone=from_phone, text=reply_text)
                        results.append({
                            "message_id": msg_id,
                            "type": msg_type,
                            "status": "unsupported_media_advisory_sent",
                            "delivery": send_res
                        })

        return {"status": "success", "processed_count": len(results), "details": results}

whatsapp_service = WhatsAppService()
