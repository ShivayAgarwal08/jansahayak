import pytest
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, ForeignKey, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base
from unittest.mock import patch, MagicMock

from app.db.migrations import ensure_schema_compatibility
from app.db.seed_data import seed_database, VERIFIED_SCHEMES
from app.services.rag.seed_corpus import seed_official_documents_corpus, OFFICIAL_SCHEME_DOCUMENTS
from app.models.scheme import Scheme
from app.models.document import KnowledgeDocument, DocumentChunk

MigrationTestBase = declarative_base()

class LegacyKnowledgeDocument(MigrationTestBase):
    __tablename__ = "knowledge_documents"
    id = Column(Integer, primary_key=True)
    scheme_id = Column(Integer, nullable=False)
    title = Column(String(250), nullable=False)
    source_url = Column(String(500), nullable=False)
    authority = Column(String(200), nullable=False)
    total_pages = Column(Integer, default=1)

class LegacyDocumentChunk(MigrationTestBase):
    __tablename__ = "document_chunks"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, default=1)
    content = Column(Text, nullable=False)
    keywords = Column(JSON, default=list)

def test_ensure_schema_compatibility_adds_missing_columns():
    """
    Simulates an existing legacy PostgreSQL / SQLite database that lacks the newly added
    RAG columns, verifying that ensure_schema_compatibility non-destructively alters tables.
    """
    engine = create_engine("sqlite:///:memory:")
    # 1. Create legacy schema
    MigrationTestBase.metadata.create_all(bind=engine)
    
    # Verify legacy columns before migration
    inspector = inspect(engine)
    initial_doc_cols = {col["name"] for col in inspector.get_columns("knowledge_documents")}
    assert "document_reference" not in initial_doc_cols
    assert "retrieval_date" not in initial_doc_cols
    assert "doc_type" not in initial_doc_cols
    assert "ocr_status" not in initial_doc_cols

    initial_chunk_cols = {col["name"] for col in inspector.get_columns("document_chunks")}
    assert "section_title" not in initial_chunk_cols
    assert "embedding" not in initial_chunk_cols
    assert "token_count" not in initial_chunk_cols

    # 2. Run schema evolution migration
    ensure_schema_compatibility(engine)

    # 3. Verify all new columns were safely added
    updated_inspector = inspect(engine)
    updated_doc_cols = {col["name"] for col in updated_inspector.get_columns("knowledge_documents")}
    assert "document_reference" in updated_doc_cols
    assert "retrieval_date" in updated_doc_cols
    assert "doc_type" in updated_doc_cols
    assert "ocr_status" in updated_doc_cols

    updated_chunk_cols = {col["name"] for col in updated_inspector.get_columns("document_chunks")}
    assert "section_title" in updated_chunk_cols
    assert "embedding" in updated_chunk_cols
    assert "token_count" in updated_chunk_cols

def test_transaction_rollback_on_failed_seed_operation():
    """
    Verifies that when a seed query or insertion fails, the session is cleanly rolled back
    and subsequent queries on the session do NOT raise InFailedSqlTransaction.
    """
    engine = create_engine("sqlite:///:memory:")
    from app.db.session import Base
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # Pre-seed verified schemes
        seed_database(db)

        # Force a failure during a document seed attempt
        with patch("app.services.rag.seed_corpus.ingest_document", side_effect=RuntimeError("Simulated database constraint failure")):
            with pytest.raises(RuntimeError):
                seed_official_documents_corpus(db)

        # Verify that because rollback was executed, the session is NOT poisoned:
        # A subsequent query succeeds without transaction aborted error!
        count = db.query(Scheme).count()
        assert count > 0
    finally:
        db.close()

def test_idempotent_repeated_seeding():
    """
    Verifies that running seed_database and seed_official_documents_corpus multiple times
    is fully idempotent and does not produce duplicate records or primary key collisions.
    """
    engine = create_engine("sqlite:///:memory:")
    from app.db.session import Base
    Base.metadata.create_all(bind=engine)
    ensure_schema_compatibility(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # Run 1
        res1_schemes = seed_database(db)
        res1_corpus = seed_official_documents_corpus(db)
        assert res1_corpus["documents_ingested"] == len(OFFICIAL_SCHEME_DOCUMENTS)

        scheme_count_1 = db.query(Scheme).count()
        doc_count_1 = db.query(KnowledgeDocument).count()
        chunk_count_1 = db.query(DocumentChunk).count()

        # Run 2 (immediate restart)
        seed_database(db)
        res2_corpus = seed_official_documents_corpus(db)
        assert res2_corpus["documents_skipped"] == len(OFFICIAL_SCHEME_DOCUMENTS)
        assert res2_corpus["documents_ingested"] == 0

        assert db.query(Scheme).count() == scheme_count_1
        assert db.query(KnowledgeDocument).count() == doc_count_1
        assert db.query(DocumentChunk).count() == chunk_count_1

        # Run 3 (subsequent deployment)
        seed_database(db)
        res3_corpus = seed_official_documents_corpus(db)
        assert res3_corpus["documents_skipped"] == len(OFFICIAL_SCHEME_DOCUMENTS)
        assert db.query(KnowledgeDocument).count() == doc_count_1
    finally:
        db.close()

def test_partial_seeding_recovery():
    """
    Verifies that if the database only has a subset of schemes or documents,
    subsequent startup cleanly completes the missing records without duplicating existing ones.
    """
    engine = create_engine("sqlite:///:memory:")
    from app.db.session import Base
    Base.metadata.create_all(bind=engine)
    ensure_schema_compatibility(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # 1. Seed only the first 2 schemes manually
        for data in VERIFIED_SCHEMES[:2]:
            data_copy = dict(data)
            data_copy.pop("sources", None)
            db.add(Scheme(**data_copy))
        db.commit()
        assert db.query(Scheme).count() == 2

        # 2. Run seed_database - should complete remaining schemes
        seed_database(db)
        assert db.query(Scheme).count() == len(VERIFIED_SCHEMES)

        # 3. Seed official documents corpus
        res_corpus = seed_official_documents_corpus(db)
        assert res_corpus["documents_ingested"] == len(OFFICIAL_SCHEME_DOCUMENTS)
        assert db.query(KnowledgeDocument).count() == len(OFFICIAL_SCHEME_DOCUMENTS)
    finally:
        db.close()
