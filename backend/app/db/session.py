from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

# Engine configuration with multi-environment support
database_url = settings.DATABASE_URL
connect_args = {}

if database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
elif database_url.startswith("postgres://"):
    # SQLAlchemy requires postgresql+psycopg:// for Psycopg 3
    database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
elif database_url.startswith("postgresql://") and not database_url.startswith("postgresql+"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

# Ensure SSL mode is enabled for remote PostgreSQL if not already specified
if database_url.startswith("postgresql") and "sslmode=" not in database_url:
    delimiter = "&" if "?" in database_url else "?"
    database_url = f"{database_url}{delimiter}sslmode=require"

engine = create_engine(
    database_url,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_recycle=300
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """
    FastAPI dependency yielding a thread-safe database session.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
