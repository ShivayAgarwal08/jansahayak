from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base

class SavedScheme(Base):
    __tablename__ = "saved_schemes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    scheme_id = Column(Integer, ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="saved_schemes")
    scheme = relationship("Scheme")

class AssessmentHistory(Base):
    __tablename__ = "assessment_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    scheme_id = Column(Integer, ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False)
    inputs_snapshot = Column(JSON, default=dict, nullable=False)
    status = Column(String(50), nullable=False)  # eligible, possibly_eligible, ineligible
    assessment_result = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="assessment_history")
    scheme = relationship("Scheme")

class ApplicationDraft(Base):
    __tablename__ = "application_drafts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    scheme_id = Column(Integer, ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    applicant_details = Column(JSON, default=dict, nullable=False)
    checklist_state = Column(JSON, default=dict, nullable=False)
    status = Column(String(30), default="draft", nullable=False)  # draft, ready
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="application_drafts")
    scheme = relationship("Scheme", back_populates="application_drafts")

class RtiDraft(Base):
    __tablename__ = "rti_drafts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    public_authority = Column(String(200), nullable=False)
    subject = Column(String(250), nullable=False)
    information_requested = Column(Text, nullable=False)
    time_period = Column(String(100), nullable=True)
    applicant_name = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    preferred_language = Column(String(10), default="en", nullable=False)
    status = Column(String(30), default="draft", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="rti_drafts")

class GrievanceDraft(Base):
    __tablename__ = "grievance_drafts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    department = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    previous_complaint_ref = Column(String(100), nullable=True)
    desired_resolution = Column(Text, nullable=False)
    applicant_name = Column(String(100), nullable=False)
    status = Column(String(30), default="draft", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="grievance_drafts")
