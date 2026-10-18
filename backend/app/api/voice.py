from pydantic import BaseModel
from fastapi import APIRouter
from app.services.bhashini.bhashini_service import bhashini_service

router = APIRouter(prefix="/voice", tags=["Voice & Bhashini"])

class STTRequest(BaseModel):
    audio_base64: str
    language_code: str = "hi"

class TranslateRequest(BaseModel):
    text: str
    source_language: str
    target_language: str

class TTSRequest(BaseModel):
    text: str
    language_code: str = "hi"
    gender: str = "female"

@router.get("/status")
def get_voice_service_status():
    return bhashini_service.get_status()

@router.get("/languages")
def get_supported_languages():
    return bhashini_service.get_supported_languages()

@router.post("/stt")
async def speech_to_text(req: STTRequest):
    return await bhashini_service.speech_to_text(req.audio_base64, req.language_code)

@router.post("/tts")
async def text_to_speech(req: TTSRequest):
    return await bhashini_service.text_to_speech(req.text, req.language_code, req.gender)

@router.post("/translate")
async def translate_text(req: TranslateRequest):
    return await bhashini_service.translate_text(
        req.text,
        req.source_language,
        req.target_language
    )
