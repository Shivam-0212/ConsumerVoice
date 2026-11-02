"""Model evaluation and active model management endpoints."""

import json
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException

from backend.app.schemas.domain import ActiveModelSetRequest
from backend.app.services.sentiment_service import sentiment_service

router = APIRouter(prefix="/evaluations", tags=["evaluations"])
logger = logging.getLogger(__name__)


@router.get("")
def get_evaluations():
    """Return genuine model benchmark comparison metrics."""
    return sentiment_service.get_model_status()


@router.post("/active-model")
def set_active_model(payload: ActiveModelSetRequest):
    """Switch active model between baseline and transformer if available."""
    success = sentiment_service.set_active_model(payload.model_name)
    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot switch to '{payload.model_name}'. Checkpoint missing or loading failed."
        )
    return {
        "status": "success",
        "active_model": sentiment_service.active_model_name,
    }

