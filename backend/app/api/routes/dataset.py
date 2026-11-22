"""Dataset health and audit reporting endpoints."""

import json
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException

from backend.app.core.config import ROOT_DIR, settings

router = APIRouter(prefix="/dataset", tags=["dataset"])
logger = logging.getLogger(__name__)


def _get_report_path() -> Path:
    """Resolve report path across root, GitHub directory, and private fallbacks."""
    candidates = [
        settings.DATA_PROCESSED_DIR / "data_quality_report.json",
        Path("data/processed/data_quality_report.json"),
        ROOT_DIR / "data" / "processed" / "data_quality_report.json",
        ROOT_DIR.parent / "ConsumerVoice_Private" / "processed_data" / "data_quality_report.json",
    ]
    for c in candidates:
        try:
            if c.exists():
                return c
        except Exception:
            pass
    return settings.DATA_PROCESSED_DIR / "data_quality_report.json"


@router.get("/quality")
def get_dataset_quality():
    """Return the audited dataset health report, cleaning stats, and splits."""
    report_file = _get_report_path()
    if not report_file.exists():
        raise HTTPException(
            status_code=404,
            detail="Data quality report not found. Run scripts/prepare_dataset.py first."
        )

    try:
        with open(report_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.error(f"Error reading quality report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

