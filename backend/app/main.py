"""ConsumerVoice: An Explainable, Hallucination-Aware Framework for Customer Feedback NLP.

Main FastAPI Application Entrypoint.
"""

import logging
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
from backend.app.database.session import Base, engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("consumervoice")

# Initialize database schema
Base.metadata.create_all(bind=engine)

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
)

# CORS configuration for local React Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",
    ],
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
def root():
    return {
        "project": "ConsumerVoice",
        "tagline": "An Explainable, Hallucination-Aware Framework for Customer Feedback NLP",
        "docs": "/docs",
        "health": "/api/health",
    }

