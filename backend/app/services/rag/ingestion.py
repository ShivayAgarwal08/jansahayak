import io
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple, Union
from sqlalchemy.orm import Session

from app.models.scheme import Scheme
from app.models.document import KnowledgeDocument, DocumentChunk
from app.services.rag.chunker import chunk_document_text
from app.services.rag.embeddings import generate_embedding

logger = logging.getLogger("jansahayak.rag.ingestion")

try:
    from pypdf import PdfReader
    HAVE_PYPDF = True
except ImportError:
    HAVE_PYPDF = False

def extract_text_from_pdf(pdf_source: Union[bytes, io.BytesIO, str]) -> Dict[str, Any]:
    """
    Extract text page-by-page from a PDF stream or file path using pypdf.
    Detects scanned image-only PDFs honestly and flags when OCR is required.
    """
    if not HAVE_PYPDF:
        return {
            "success": False,
            "error": "pypdf library not installed",
            "ocr_status": "error",
            "pages": [],
            "total_pages": 0
        }

    try:
        if isinstance(pdf_source, bytes):
            stream = io.BytesIO(pdf_source)
        elif isinstance(pdf_source, str):
            stream = open(pdf_source, "rb")
        else:
            stream = pdf_source

        reader = PdfReader(stream)
        total_pages = len(reader.pages)
        pages_data: List[Tuple[int, str]] = []
        total_text_len = 0

        for idx, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            clean_text = page_text.strip()
            total_text_len += len(clean_text)
            pages_data.append((idx + 1, clean_text))

        if isinstance(pdf_source, str):
            stream.close()

        # Honest Scanned PDF Detection:
        # If total extracted characters across all pages is under 50, it is a scanned bitmap PDF
        is_scanned = total_text_len < 50 and total_pages > 0
        ocr_status = "ocr_required" if is_scanned else "not_needed"

        if is_scanned:
            logger.warning(
                f"PDF with {total_pages} pages yielded only {total_text_len} characters. Scanned PDF detected; OCR is required."
            )

        return {
            "success": True,
            "total_pages": total_pages,
            "total_chars": total_text_len,
            "ocr_status": ocr_status,
            "is_scanned": is_scanned,
            "pages": pages_data,
            "error": None
        }
    except Exception as e:
        logger.error(f"Error parsing PDF: {e}")
        return {
            "success": False,
            "error": str(e),
            "ocr_status": "error",
            "pages": [],
            "total_pages": 0
        }

def ingest_document(
    db: Session,
    scheme_slug: str,
    title: str,
    source_url: str,
    authority: str,
    document_reference: Optional[str] = None,
    doc_type: str = "guidelines",
    pages: Optional[List[Tuple[int, str]]] = None,
    raw_text: Optional[str] = None,
    ocr_status: str = "not_needed"
) -> Dict[str, Any]:
    """
    Ingest a verified government scheme document into the knowledge base.
    Splits into meaningful chunks, computes dense embeddings, and stores source metadata.
    """
    scheme = db.query(Scheme).filter(Scheme.slug == scheme_slug).first()
    if not scheme:
        raise ValueError(f"Scheme with slug '{scheme_slug}' not found in database.")

    # Idempotent: check if document already exists by source_url and title
    doc = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.scheme_id == scheme.id,
        KnowledgeDocument.source_url == source_url
    ).first()

    if not doc:
        doc = KnowledgeDocument(
            scheme_id=scheme.id,
            title=title,
            source_url=source_url,
            authority=authority,
            document_reference=document_reference,
            retrieval_date=datetime.now(timezone.utc),
            doc_type=doc_type,
            ocr_status=ocr_status,
            total_pages=len(pages) if pages else 1
        )
        db.add(doc)
        db.flush()
    else:
        # Update metadata & clear old chunks for re-ingestion
        doc.title = title
        doc.authority = authority
        doc.document_reference = document_reference
        doc.retrieval_date = datetime.now(timezone.utc)
        doc.doc_type = doc_type
        doc.ocr_status = ocr_status
        doc.total_pages = len(pages) if pages else 1
        db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).delete()
        db.flush()

    # Process pages or raw text into chunks
    chunks_to_add: List[DocumentChunk] = []
    chunk_counter = 0

    if pages:
        for page_num, page_content in pages:
            if not page_content.strip():
                continue
            page_chunks = chunk_document_text(page_content, default_page=page_num)
            for c in page_chunks:
                embedding = generate_embedding(c.content)
                chunks_to_add.append(DocumentChunk(
                    document_id=doc.id,
                    chunk_index=chunk_counter,
                    page_number=page_num,
                    section_title=c.section_title,
                    content=c.content,
                    keywords=c.keywords,
                    embedding=embedding,
                    token_count=c.token_count
                ))
                chunk_counter += 1
    elif raw_text:
        text_chunks = chunk_document_text(raw_text, default_page=1)
        for c in text_chunks:
            embedding = generate_embedding(c.content)
            chunks_to_add.append(DocumentChunk(
                document_id=doc.id,
                chunk_index=chunk_counter,
                page_number=c.page_number,
                section_title=c.section_title,
                content=c.content,
                keywords=c.keywords,
                embedding=embedding,
                token_count=c.token_count
            ))
            chunk_counter += 1

    for chunk in chunks_to_add:
        db.add(chunk)

    db.commit()
    db.refresh(doc)

    return {
        "document_id": doc.id,
        "scheme_slug": scheme.slug,
        "title": doc.title,
        "source_url": doc.source_url,
        "authority": doc.authority,
        "total_pages": doc.total_pages,
        "chunks_count": len(chunks_to_add),
        "ocr_status": doc.ocr_status,
        "created_at": doc.created_at.isoformat()
    }
