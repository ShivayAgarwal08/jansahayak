from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base

class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, index=True)
    scheme_id = Column(Integer, ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(250), nullable=False)
    source_url = Column(String(500), nullable=False)
    authority = Column(String(200), nullable=False)
    document_reference = Column(String(250), nullable=True)  # Order No., Notification
    retrieval_date = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    doc_type = Column(String(50), default="guidelines", nullable=False)  # pdf, guidelines, web_page
    ocr_status = Column(String(50), default="not_needed", nullable=False)  # not_needed, ocr_required, completed
    total_pages = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    scheme = relationship("Scheme", back_populates="knowledge_documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, default=1, nullable=False)
    section_title = Column(String(250), nullable=True)
    content = Column(Text, nullable=False)
    keywords = Column(JSON, default=list, nullable=False)
    embedding = Column(JSON, nullable=True)  # Dense vector embedding (list of floats)
    token_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    document = relationship("KnowledgeDocument", back_populates="chunks")
