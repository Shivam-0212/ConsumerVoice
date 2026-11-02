"""System health and diagnostic endpoints."""

from fastapi import APIRouter
from backend.app.services.sentiment_service import sentiment_service

router = APIRouter(tags=["health"])


@router.get("/health")
@router.head("/health")
def health_check():
    """Verify application, database, and model availability."""
    status = sentiment_service.get_model_status()
    return {
        "status": "healthy",
        "service": "ConsumerVoice API",
        "version": "1.0.0",
        "active_model": status["active_model"],
        "baseline_ready": status["baseline_loaded"],
        "transformer_ready": status["transformer_loaded"],
    }

