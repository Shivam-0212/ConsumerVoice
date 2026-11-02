"""ConsumerVoice: An Explainable, Hallucination-Aware Framework for Customer Feedback NLP.

Main FastAPI Application Entrypoint.
"""

import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes import (
    dashboard,
    dataset,
    evaluations,
    health,
    responses,
    reviews,
    summaries,
)
from backend.app.core.config import ROOT_DIR, settings
from backend.app.database.session import Base, engine

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("consumervoice")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: ensures database tables exist and bootstraps production assets."""
    # 1. Bootstrap baseline model and production database if missing in cloud environment
    try:
        from scripts.download_production_assets import ensure_baseline_model, ensure_database
        ensure_baseline_model()
        from backend.app.services.sentiment_service import sentiment_service
        sentiment_service._load_baseline()
        ensure_database()
    except Exception as e:
        logger.warning(f"Asset bootstrap notice: {e}")

    # 2. Ensure SQLAlchemy tables exist with clean connection pool
    try:
        logger.info("Verifying ConsumerVoice application schema...")
        engine.dispose()
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logger.warning(f"Schema verification notice: {e}")

    yield


app = FastAPI(
    title="ConsumerVoice API",
    description=(
        "Production REST API for Explainable, Hallucination-Aware Customer Feedback NLP. "
        "Provides sentiment prediction, issue detection, extractive/abstractive summarization, "
        "grounded response generation, and claim-level verification."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS configuration supporting localhost, Vercel production, and preview domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://consumer-voice-rose.vercel.app",
        "https://consumer-voice.vercel.app",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(health.router, prefix="/api")
app.include_router(reviews.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(summaries.router, prefix="/api")
app.include_router(responses.router, prefix="/api")
app.include_router(evaluations.router, prefix="/api")
app.include_router(dataset.router, prefix="/api")


@app.get("/")
@app.head("/")
def root():
    return {
        "project": "ConsumerVoice",
        "tagline": "An Explainable, Hallucination-Aware Framework for Customer Feedback NLP",
        "docs": "/docs",
        "health": "/api/health",
    }

