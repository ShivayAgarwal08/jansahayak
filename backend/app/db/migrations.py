import logging
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

logger = logging.getLogger("jansahayak.db.migrations")

def ensure_schema_compatibility(engine: Engine):
    """
    Non-destructive schema evolution helper.
    Ensures that existing tables in Neon PostgreSQL (or SQLite) have all required columns
    added in recent phases, without dropping tables, truncating data, or requiring external tools.
    """
    inspector = inspect(engine)
    dialect_name = engine.dialect.name.lower()

    with engine.connect() as conn:
        # 1. Check knowledge_documents columns
        if inspector.has_table("knowledge_documents"):
            existing_cols = {col["name"] for col in inspector.get_columns("knowledge_documents")}
            
            # document_reference
            if "document_reference" not in existing_cols:
                logger.info("Adding missing column 'document_reference' to 'knowledge_documents' table")
                conn.execute(text("ALTER TABLE knowledge_documents ADD COLUMN document_reference VARCHAR(250)"))
                conn.commit()

            # retrieval_date
            if "retrieval_date" not in existing_cols:
                logger.info("Adding missing column 'retrieval_date' to 'knowledge_documents' table")
                default_clause = "DEFAULT CURRENT_TIMESTAMP"
                conn.execute(text(f"ALTER TABLE knowledge_documents ADD COLUMN retrieval_date TIMESTAMP {default_clause}"))
                conn.commit()

            # doc_type
            if "doc_type" not in existing_cols:
                logger.info("Adding missing column 'doc_type' to 'knowledge_documents' table")
                conn.execute(text("ALTER TABLE knowledge_documents ADD COLUMN doc_type VARCHAR(50) DEFAULT 'guidelines'"))
                conn.commit()

            # ocr_status
            if "ocr_status" not in existing_cols:
                logger.info("Adding missing column 'ocr_status' to 'knowledge_documents' table")
                conn.execute(text("ALTER TABLE knowledge_documents ADD COLUMN ocr_status VARCHAR(50) DEFAULT 'not_needed'"))
                conn.commit()

        # 2. Check document_chunks columns
        if inspector.has_table("document_chunks"):
            existing_cols = {col["name"] for col in inspector.get_columns("document_chunks")}

            # section_title
            if "section_title" not in existing_cols:
                logger.info("Adding missing column 'section_title' to 'document_chunks' table")
                conn.execute(text("ALTER TABLE document_chunks ADD COLUMN section_title VARCHAR(250)"))
                conn.commit()

            # embedding (JSON column)
            if "embedding" not in existing_cols:
                logger.info("Adding missing column 'embedding' to 'document_chunks' table")
                json_type = "JSON" if dialect_name != "postgresql" else "JSONB"
                # Using JSON type compatible with PostgreSQL and SQLite
                conn.execute(text("ALTER TABLE document_chunks ADD COLUMN embedding JSON"))
                conn.commit()

            # token_count
            if "token_count" not in existing_cols:
                logger.info("Adding missing column 'token_count' to 'document_chunks' table")
                conn.execute(text("ALTER TABLE document_chunks ADD COLUMN token_count INTEGER DEFAULT 0"))
                conn.commit()

    logger.info("Database schema compatibility verification completed.")
