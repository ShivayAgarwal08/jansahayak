import os
from typing import List, Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "JanSahayak"
    PROJECT_DESCRIPTION: str = "Multilingual Citizen-First Indian Civic-Tech Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Environment & Security
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "jansahayak-insecure-dev-secret-key-change-in-prod-32bytes")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # CORS
    FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "https://jansahayak.vercel.app"
    ]
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./jansahayak.db")
    
    # AI Services
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY", None)
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    # Bhashini Services (National Language Translation Mission)
    BHASHINI_USER_ID: Optional[str] = os.getenv("BHASHINI_USER_ID", None)
    BHASHINI_API_KEY: Optional[str] = os.getenv("BHASHINI_API_KEY", None)
    BHASHINI_PIPELINE_ENDPOINT: str = os.getenv(
        "BHASHINI_PIPELINE_ENDPOINT", 
        "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"
    )

    # Meta WhatsApp Cloud API
    WHATSAPP_VERIFY_TOKEN: Optional[str] = os.getenv("WHATSAPP_VERIFY_TOKEN", None)
    WHATSAPP_ACCESS_TOKEN: Optional[str] = os.getenv("WHATSAPP_ACCESS_TOKEN", None)
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = os.getenv("WHATSAPP_PHONE_NUMBER_ID", None)
    WHATSAPP_APP_SECRET: Optional[str] = os.getenv("WHATSAPP_APP_SECRET", None)
    WHATSAPP_API_URL: str = os.getenv("WHATSAPP_API_URL", "https://graph.facebook.com/v19.0")

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"

settings = Settings()
