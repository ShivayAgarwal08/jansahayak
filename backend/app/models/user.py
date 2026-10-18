from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.db.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="citizen", nullable=False)  # "citizen" or "admin"
    preferred_language = Column(String(10), default="en", nullable=False)
    state = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    saved_schemes = relationship("SavedScheme", back_populates="user", cascade="all, delete-orphan")
    application_drafts = relationship("ApplicationDraft", back_populates="user", cascade="all, delete-orphan")
    rti_drafts = relationship("RtiDraft", back_populates="user", cascade="all, delete-orphan")
    grievance_drafts = relationship("GrievanceDraft", back_populates="user", cascade="all, delete-orphan")
    assessment_history = relationship("AssessmentHistory", back_populates="user", cascade="all, delete-orphan")
