import httpx
from typing import Dict, Any, List, Optional
from app.core.config import settings

SUPPORTED_LANGUAGES = [
    {"code": "en", "name": "English", "native": "English", "script": "Latn"},
    {"code": "hi", "name": "Hindi", "native": "हिन्दी", "script": "Deva"},
    {"code": "bn", "name": "Bengali", "native": "বাংলা", "script": "Beng"},
    {"code": "ta", "name": "Tamil", "native": "தமிழ்", "script": "Taml"},
    {"code": "te", "name": "Telugu", "native": "తెలుగు", "script": "Telu"},
    {"code": "mr", "name": "Marathi", "native": "मराठी", "script": "Deva"},
    {"code": "gu", "name": "Gujarati", "native": "ગુજરાતી", "script": "Gujr"},
    {"code": "kn", "name": "Kannada", "native": "ಕನ್ನಡ", "script": "Knda"},
    {"code": "ml", "name": "Malayalam", "native": "മലയാളം", "script": "Mlym"},
    {"code": "pa", "name": "Punjabi", "native": "ਪੰਜਾਬੀ", "script": "Guru"},
    {"code": "or", "name": "Odia", "native": "ଓଡ଼ିଆ", "script": "Orya"}
]

class BhashiniService:
    def __init__(self):
        self.user_id = settings.BHASHINI_USER_ID
        self.api_key = settings.BHASHINI_API_KEY
        self.pipeline_endpoint = settings.BHASHINI_PIPELINE_ENDPOINT

    def get_supported_languages(self) -> List[Dict[str, str]]:
        return SUPPORTED_LANGUAGES

    def get_status(self) -> Dict[str, Any]:
        """
        Check if Bhashini credentials are configured.
        """
        is_configured = bool(self.user_id and self.api_key)
        return {
            "provider": "Bhashini (National Language Translation Mission)",
            "configured": is_configured,
            "status": "ready" if is_configured else "awaiting_credentials",
            "supported_languages_count": len(SUPPORTED_LANGUAGES),
            "browser_speech_fallback_supported": True,
            "message": (
                "Bhashini API is configured for speech and translation."
                if is_configured
                else "Bhashini credentials are pending configuration. Browser Web Speech and text inputs are active as default fallbacks."
            )
        }

    async def speech_to_text(self, audio_content_base64: str, language_code: str) -> Dict[str, Any]:
        """
        Perform Automatic Speech Recognition (ASR) via Bhashini API.
        """
        if not self.user_id or not self.api_key:
            return {
                "success": False,
                "text": "",
                "error": "Bhashini credentials are not configured on this server.",
                "use_browser_speech": True
            }

        try:
            payload = {
                "pipelineTasks": [
                    {
                        "taskType": "asr",
                        "config": {
                            "language": {"sourceLanguage": language_code},
                            "audioFormat": "wav"
                        }
                    }
                ],
                "inputData": {
                    "audio": [{"audioContent": audio_content_base64}]
                }
            }

            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    self.pipeline_endpoint,
                    headers={
                        "userID": self.user_id,
                        "ulcaApiKey": self.api_key,
                        "Content-Type": "application/json"
                    },
                    json=payload
                )
                if response.status_code == 200:
                    data = response.json()
                    recognized_text = data["pipelineResponse"][0]["output"][0]["source"]
                    return {
                        "success": True,
                        "text": recognized_text,
                        "language": language_code,
                        "provider": "bhashini",
                        "is_bhashini_live": True
                    }
                else:
                    return {
                        "success": False,
                        "text": "",
                        "error": f"Bhashini ASR returned HTTP {response.status_code}",
                        "use_browser_speech": True,
                        "provider": "bhashini_error"
                    }
        except Exception as e:
            return {
                "success": False,
                "text": "",
                "error": f"ASR connection error: {str(e)}",
                "use_browser_speech": True,
                "provider": "bhashini_error"
            }

    async def text_to_speech(
        self,
        text: str,
        language_code: str,
        gender: str = "female"
    ) -> Dict[str, Any]:
        """
        Perform Text-to-Speech (TTS) via Bhashini API.
        Returns base64 encoded audio or honest fallback recommendation.
        """
        if not self.user_id or not self.api_key:
            return {
                "success": False,
                "audio_base64": "",
                "error": "Bhashini credentials are not configured on this server.",
                "use_browser_speech": True,
                "provider": "browser_fallback"
            }

        try:
            payload = {
                "pipelineTasks": [
                    {
                        "taskType": "tts",
                        "config": {
                            "language": {"sourceLanguage": language_code},
                            "gender": gender,
                            "samplingRate": 8000
                        }
                    }
                ],
                "inputData": {
                    "input": [{"source": text}]
                }
            }

            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    self.pipeline_endpoint,
                    headers={
                        "userID": self.user_id,
                        "ulcaApiKey": self.api_key,
                        "Content-Type": "application/json"
                    },
                    json=payload
                )
                if response.status_code == 200:
                    data = response.json()
                    audio_content = data["pipelineResponse"][0]["audio"][0]["audioContent"]
                    return {
                        "success": True,
                        "audio_base64": audio_content,
                        "language": language_code,
                        "provider": "bhashini",
                        "is_bhashini_live": True
                    }
                else:
                    return {
                        "success": False,
                        "audio_base64": "",
                        "error": f"Bhashini TTS returned HTTP {response.status_code}",
                        "use_browser_speech": True,
                        "provider": "bhashini_error"
                    }
        except Exception as e:
            return {
                "success": False,
                "audio_base64": "",
                "error": f"TTS connection error: {str(e)}",
                "use_browser_speech": True,
                "provider": "bhashini_error"
            }

    async def translate_text(self, text: str, source_lang: str, target_lang: str) -> Dict[str, Any]:
        """
        Perform Neural Machine Translation (NMT) via Bhashini.
        """
        if source_lang == target_lang:
            return {"success": True, "translated_text": text}

        if not self.user_id or not self.api_key:
            return {
                "success": False,
                "translated_text": text,
                "error": "Bhashini credentials pending configuration."
            }

        try:
            payload = {
                "pipelineTasks": [
                    {
                        "taskType": "translation",
                        "config": {
                            "language": {
                                "sourceLanguage": source_lang,
                                "targetLanguage": target_lang
                            }
                        }
                    }
                ],
                "inputData": {
                    "input": [{"source": text}]
                }
            }

            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    self.pipeline_endpoint,
                    headers={
                        "userID": self.user_id,
                        "ulcaApiKey": self.api_key,
                        "Content-Type": "application/json"
                    },
                    json=payload
                )
                if response.status_code == 200:
                    data = response.json()
                    translated = data["pipelineResponse"][0]["output"][0]["target"]
                    return {
                        "success": True,
                        "translated_text": translated,
                        "source_lang": source_lang,
                        "target_lang": target_lang
                    }
                else:
                    return {
                        "success": False,
                        "translated_text": text,
                        "error": f"Translation failed with status {response.status_code}"
                    }
        except Exception as e:
            return {
                "success": False,
                "translated_text": text,
                "error": str(e)
            }

bhashini_service = BhashiniService()
