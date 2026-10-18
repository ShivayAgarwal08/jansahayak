from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import get_db

import os

router = APIRouter(tags=["Health"])

@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "JanSahayak Civic Platform API",
        "version": "1.0.0",
        "git_commit": os.environ.get("RENDER_GIT_COMMIT", os.environ.get("GIT_COMMIT", "dev")),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.get("/health/db")
def health_db(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        dialect = db.bind.dialect.name if db.bind else "unknown"
        return {
            "status": "healthy",
            "database": "connected",
            "dialect": dialect,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": "Database connection failed"
        }
