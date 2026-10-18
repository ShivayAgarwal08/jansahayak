import io
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from reportlab.pdfgen import canvas

from app.main import app
from app.core.config import settings
from app.db.session import Base, get_db
from app.db.seed_data import seed_database
from app.models.scheme import Scheme
from app.models.document import KnowledgeDocument, DocumentChunk
from app.services.rag.embeddings import (
    generate_embedding,
    compute_cosine_similarity,
    batch_generate_embeddings
)
from app.services.rag.chunker import chunk_document_text, extract_keywords_from_text
from app.services.rag.ingestion import extract_text_from_pdf, ingest_document
from app.services.rag.seed_corpus import seed_official_documents_corpus, OFFICIAL_SCHEME_DOCUMENTS
from app.services.rag.retrieval import retrieve_grounded_passages, search_official_documents

# Isolated SQLite in-memory database for RAG tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

Base.metadata.create_all(bind=test_engine)
init_db = TestingSessionLocal()
seed_database(init_db)
seed_official_documents_corpus(init_db)
init_db.close()

client = TestClient(app)

# 1. Document Chunking & Keyword Extraction Tests
def test_chunking_engine_and_keywords():
    sample_text = """# 1. Introduction & Objectives
The PM-KISAN scheme aims to provide income support to all landholding farmer families across India.

# 2. Financial Benefits
Under the scheme, ₹6,000 per year is transferred directly in three equal installments of ₹2,000 into Aadhaar-seeded bank accounts.

# 3. Mandatory Exclusion Criteria
Institutional landholders and all persons who paid income tax in the last assessment year are strictly ineligible."""

    chunks = chunk_document_text(sample_text, default_page=1, target_chunk_chars=200, overlap_chars=20)
    assert len(chunks) >= 3
    
    # Check section title preservation
    titles = [c.section_title for c in chunks]
    assert any("Introduction" in t or "Objectives" in t for t in titles)
    assert any("Financial Benefits" in t for t in titles)
    assert any("Exclusion Criteria" in t for t in titles)
    
    # Check keyword extraction
    all_kws = [kw for c in chunks for kw in c.keywords]
    assert any(k in all_kws for k in ["farmer", "kisan", "income", "tax", "aadhaar", "installments"])

# 2. Dense Vector Embeddings & Cosine Similarity Tests
def test_dense_embeddings_and_cosine_similarity():
    # Agricultural texts
    agri_text = "Landholding farmer with two bighas of cultivable land in Bihar seeking agricultural assistance."
    agri_query = "farmer cultivable land agricultural support"
    
    # Maternal health text
    maternal_text = "Pregnant women and lactating mothers receiving ₹5,000 maternity cash incentives for first child."
    
    vec_doc_agri = generate_embedding(agri_text)
    vec_q_agri = generate_embedding(agri_query)
    vec_maternal = generate_embedding(maternal_text)
    
    assert len(vec_doc_agri) == 128
    assert len(vec_q_agri) == 128
    assert len(vec_maternal) == 128
    
    sim_agri_match = compute_cosine_similarity(vec_q_agri, vec_doc_agri)
    sim_cross_domain = compute_cosine_similarity(vec_q_agri, vec_maternal)
    
    # High semantic similarity between matching agricultural query & document
    assert sim_agri_match > 0.50
    # Cross-domain similarity must be significantly lower
    assert sim_agri_match > sim_cross_domain

def test_batch_embedding_generation():
    texts = ["PM-KISAN guidelines", "PMAY-G rural housing", "Ayushman Bharat hospital cover"]
    vectors = batch_generate_embeddings(texts)
    assert len(vectors) == 3
    for v in vectors:
        assert len(v) == 128

# 3. PDF Ingestion & Honest Scanned PDF Detection Tests
def test_pdf_extraction_digital_text():
    # Create a genuine PDF with text stream using ReportLab
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer)
    c.drawString(100, 750, "GOVERNMENT OF INDIA - MINISTRY OF AGRICULTURE")
    c.drawString(100, 720, "PM-KISAN Operational Guidelines. Financial benefit is Rs 6,000 annually.")
    c.showPage()
    c.save()
    pdf_bytes = pdf_buffer.getvalue()
    
    result = extract_text_from_pdf(pdf_bytes)
    assert result["success"] is True
    assert result["total_pages"] == 1
    assert result["total_chars"] > 50
    assert result["ocr_status"] == "not_needed"
    assert result["is_scanned"] is False
    assert "PM-KISAN" in result["pages"][0][1]

def test_pdf_extraction_honest_scanned_detection():
    # Create a blank PDF simulating a scanned image without text layer
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer)
    # No drawString; draw a blank rectangle simulating an image scan
    c.rect(50, 50, 500, 700)
    c.showPage()
    c.save()
    pdf_bytes = pdf_buffer.getvalue()
    
    result = extract_text_from_pdf(pdf_bytes)
    assert result["success"] is True
    assert result["total_pages"] == 1
    # Scanned PDF must be detected and honestly flagged for OCR
    assert result["is_scanned"] is True
    assert result["ocr_status"] == "ocr_required"

# 4. Document Ingestion Pipeline & Metadata Persistence Tests
def test_ingest_document_pipeline_persistence():
    db = TestingSessionLocal()
    try:
        scheme = db.query(Scheme).filter(Scheme.slug == "pm-kisan").first()
        assert scheme is not None
        
        pages_content = [
            (1, "PM-KISAN Guidelines: Section 1. Income support of ₹6,000 annually for all landholder farmer families."),
            (2, "PM-KISAN Guidelines: Section 2. Income tax payees and government employees are excluded.")
        ]
        
        res = ingest_document(
            db=db,
            scheme_slug="pm-kisan",
            title="PM-KISAN Operational Guidelines Test Document",
            source_url="https://pmkisan.gov.in/test_guidelines.pdf",
            authority="Ministry of Agriculture",
            document_reference="Order No. Test-2026",
            doc_type="pdf",
            pages=pages_content
        )
        
        assert res["chunks_count"] >= 2
        assert res["total_pages"] == 2
        
        # Verify persistence in database
        doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.source_url == "https://pmkisan.gov.in/test_guidelines.pdf").first()
        assert doc is not None
        assert doc.authority == "Ministry of Agriculture"
        assert doc.document_reference == "Order No. Test-2026"
        
        chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).all()
        assert len(chunks) >= 2
        for ch in chunks:
            assert ch.embedding is not None
            assert len(ch.embedding) == 128
    finally:
        db.close()

# 5. Corpus Seeder Tests (All 8 Verified Schemes)
def test_official_corpus_seeded():
    db = TestingSessionLocal()
    try:
        doc_count = db.query(KnowledgeDocument).count()
        chunk_count = db.query(DocumentChunk).count()
        
        assert doc_count >= 8
        assert chunk_count >= 15
        
        # Verify each of the 8 national schemes has ingested knowledge documents
        expected_slugs = [
            "pm-kisan", "pmay-g", "ayushman-bharat-pmjay", "pmmvy",
            "ignoaps", "sukanya-samriddhi-yojana", "pm-svanidhi", "pm-vishwakarma"
        ]
        for slug in expected_slugs:
            scheme = db.query(Scheme).filter(Scheme.slug == slug).first()
            assert scheme is not None
            docs = db.query(KnowledgeDocument).filter(KnowledgeDocument.scheme_id == scheme.id).all()
            assert len(docs) >= 1
    finally:
        db.close()

# 6. Hybrid Vector Retrieval Tests Against Real Ingested Documents
def test_hybrid_vector_retrieval_relevance_pm_kisan():
    db = TestingSessionLocal()
    try:
        # Benchmark query
        query = "A farmer with 2 bighas of land in Bihar asking about government income support"
        passages = retrieve_grounded_passages(query=query, db=db, limit=3)
        
        assert len(passages) >= 1
        top = passages[0]
        assert top.scheme_slug == "pm-kisan"
        # Must be from genuine official document corpus (is_seeded_record == False)
        assert top.is_seeded_record is False
        assert "pmkisan.gov.in" in top.url
        assert top.page_number >= 1
        assert top.similarity_score is not None
        assert any("Semantic vector match" in r for r in top.match_reasons)
    finally:
        db.close()

def test_hybrid_vector_retrieval_relevance_pmay_g():
    db = TestingSessionLocal()
    try:
        query = "rural family living in a kutcha dilapidated house seeking housing financial assistance"
        passages = retrieve_grounded_passages(query=query, db=db, limit=3)
        
        assert len(passages) >= 1
        top = passages[0]
        assert top.scheme_slug == "pmay-g"
        assert top.is_seeded_record is False
        assert "pmayg.nic.in" in top.url
    finally:
        db.close()

def test_hybrid_vector_retrieval_relevance_ayushman():
    db = TestingSessionLocal()
    try:
        query = "senior citizen 70 years and above hospitalization cashless health insurance cover"
        passages = retrieve_grounded_passages(query=query, db=db, limit=3)
        
        assert len(passages) >= 1
        top = passages[0]
        assert top.scheme_slug == "ayushman-bharat-pmjay"
        assert top.is_seeded_record is False
        assert "pmjay.gov.in" in top.url
    finally:
        db.close()

# 7. Document Listing and Search API Endpoints Tests
def test_api_list_official_documents():
    res = client.get("/api/assistant/documents")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 8
    
    first_doc = data[0]
    assert "title" in first_doc
    assert "source_url" in first_doc
    assert "authority" in first_doc
    assert "total_pages" in first_doc
    assert "chunks_count" in first_doc
    assert "ocr_status" in first_doc

def test_api_search_documents():
    res = client.get("/api/assistant/search-documents?query=street%20vendor%20micro%20credit%20loan")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    top = data[0]
    assert top["scheme_slug"] == "pm-svanidhi"
    assert top["page_number"] >= 1
    assert "pmsvanidhi.mohua.gov.in" in top["url"]

def test_api_search_documents_empty_query():
    res = client.get("/api/assistant/search-documents?query=%20%20")
    assert res.status_code == 400

# 8. End-to-End Assistant Chat with Genuine RAG Citations
def test_e2e_assistant_chat_citations_with_rag():
    res = client.post("/api/assistant/chat", json={
        "query": "I am a street vendor in Delhi needing working capital loan of Rs 10000 to buy stock."
    })
    assert res.status_code == 200
    data = res.json()
    assert len(data["citations"]) >= 1
    
    # Check that citations carry official guideline document references
    top_citation = data["citations"][0]
    assert top_citation["scheme_slug"] == "pm-svanidhi"
    assert "pmsvanidhi.mohua.gov.in" in top_citation["url"]
    assert top_citation["page_number"] >= 1
    assert top_citation["is_seeded_record"] is False
    assert top_citation["similarity_score"] is not None
