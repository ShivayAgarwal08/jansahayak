from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base

class Scheme(Base):
    __tablename__ = "schemes"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False, index=True)
    name_hi = Column(String(200), nullable=True)
    summary = Column(Text, nullable=False)
    summary_hi = Column(Text, nullable=True)
    department = Column(String(200), nullable=False)
    scope = Column(String(20), default="central", nullable=False)  # "central" or "state"
    applicable_states = Column(JSON, default=list, nullable=False)  # ["ALL"] or list of states
    category = Column(String(50), nullable=False, index=True)  # agriculture, housing, health, etc.
    beneficiary_types = Column(JSON, default=list, nullable=False)  # ["farmers", "women", ...]
    benefits_summary = Column(Text, nullable=False)
    
    # Structured criteria evaluated by deterministic Python engine
    eligibility_rules = Column(JSON, default=dict, nullable=False)
    exclusions = Column(JSON, default=list, nullable=False)
    required_documents = Column(JSON, default=list, nullable=False)
    application_steps = Column(JSON, default=list, nullable=False)
    official_portal_url = Column(String(500), nullable=False)
    
    verification_status = Column(String(30), default="verified", nullable=False)  # verified, under_review, deprecated
    last_verified_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    sources = relationship("SchemeSource", back_populates="scheme", cascade="all, delete-orphan")
    application_drafts = relationship("ApplicationDraft", back_populates="scheme")
    knowledge_documents = relationship("KnowledgeDocument", back_populates="scheme", cascade="all, delete-orphan")

class SchemeSource(Base):
    __tablename__ = "scheme_sources"

    id = Column(Integer, primary_key=True, index=True)
    scheme_id = Column(Integer, ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False)
    source_title = Column(String(300), nullable=False)
    source_url = Column(String(500), nullable=False)
    issuing_authority = Column(String(300), nullable=False)
    document_reference = Column(String(200), nullable=True)  # Gazette Notification, Order No.
    verified_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    scheme = relationship("Scheme", back_populates="sources")
