"""Dataset health and audit reporting endpoints."""

import json
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/dataset", tags=["dataset"])
logger = logging.getLogger(__name__)

REPORT_PATH = Path("data/processed/data_quality_report.json")


@router.get("/quality")
def get_dataset_quality():
    """Return the audited dataset health report, cleaning stats, and splits."""
    if not REPORT_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="Data quality report not found. Run scripts/prepare_dataset.py first."
        )

    try:
        with open(REPORT_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.error(f"Error reading quality report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

