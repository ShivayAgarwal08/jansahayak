from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.db.session import engine, Base, SessionLocal
from app.db.seed_data import seed_database
import app.models  # ensure models are registered with Base.metadata

# Import API Routers
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.schemes import router as schemes_router
from app.api.eligibility import router as eligibility_router
from app.api.assistant import router as assistant_router
from app.api.voice import router as voice_router
from app.api.applications import router as applications_router
from app.api.rti import router as rti_router
from app.api.grievances import router as grievances_router
from app.api.dashboard import router as dashboard_router
from app.api.feedback import router as feedback_router
from app.api.admin import router as admin_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure database tables exist & seed initial verified schemes
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield
    # Shutdown logic if needed

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
origins = list(settings.ALLOWED_ORIGINS)
if settings.FRONTEND_ORIGIN and settings.FRONTEND_ORIGIN not in origins:
    origins.append(settings.FRONTEND_ORIGIN)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler for Unhandled Errors (Prevents leaking stack traces or credentials)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log securely without sensitive payload
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred. Please try again later.",
            "path": request.url.path
        }
    )

# Include Routers under API prefix (/api)
api_prefix = settings.API_V1_STR
app.include_router(health_router, prefix=api_prefix)
app.include_router(auth_router, prefix=api_prefix)
app.include_router(schemes_router, prefix=api_prefix)
app.include_router(eligibility_router, prefix=api_prefix)
app.include_router(assistant_router, prefix=api_prefix)
app.include_router(voice_router, prefix=api_prefix)
app.include_router(applications_router, prefix=api_prefix)
app.include_router(rti_router, prefix=api_prefix)
app.include_router(grievances_router, prefix=api_prefix)
app.include_router(dashboard_router, prefix=api_prefix)
app.include_router(feedback_router, prefix=api_prefix)
app.include_router(admin_router, prefix=api_prefix)

@app.get("/")
def root():
    return {
        "message": "Welcome to JanSahayak (जनसहायक) API",
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health"
    }
