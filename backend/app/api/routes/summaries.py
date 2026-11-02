"""Summarization endpoints for ConsumerVoice."""

import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.entities import GeneratedSummaryModel, ReviewModel
from backend.app.schemas.domain import SummaryGenerateRequest, SummaryGenerateResponse
from backend.app.services.summarization import SummarizationService

router = APIRouter(prefix="/summaries", tags=["summaries"])
logger = logging.getLogger(__name__)

summarization_service = SummarizationService()


@router.post("/generate", response_model=SummaryGenerateResponse)
def generate_summary(payload: SummaryGenerateRequest, db: Session = Depends(get_db)):
    """Generate extractive or abstractive feedback summary grounded in source reviews."""
    query = db.query(ReviewModel)

    if payload.review_ids:
        query = query.filter(ReviewModel.review_id.in_(payload.review_ids))

    if payload.product_name:
        query = query.filter(ReviewModel.product_name.ilike(f"%{payload.product_name.strip()}%"))

    if payload.sentiment:
        query = query.filter(ReviewModel.normalized_sentiment == payload.sentiment.strip().lower())

    limit_count = len(payload.review_ids) if payload.review_ids else payload.sample_size
    records = query.limit(limit_count).all()

    if not records:
        raise HTTPException(
            status_code=404,
            detail="No reviews matched the specified filtering criteria."
        )

    reviews_data = [
        {
            "review_id": r.review_id,
            "Summary": r.summary,
            "Review": r.review_text or "",
            "Sentiment": r.normalized_sentiment,
        }
        for r in records
    ]

    summary_result = summarization_service.summarize(
        reviews_data,
        num_sentences=4,
        prefer_abstractive=payload.prefer_abstractive
    )

    # Persist summary record
    try:
        summary_record = GeneratedSummaryModel(
            summary_text=summary_result["summary"],
            mode=summary_result["mode"],
            filter_sentiment=payload.sentiment,
            filter_product=payload.product_name,
            source_review_count=len(reviews_data),
            source_ids_json=json.dumps(summary_result.get("source_review_ids", [])),
        )
        db.add(summary_record)
        db.commit()
    except Exception as e:
        logger.warning(f"Failed to persist summary record: {e}")
        db.rollback()

    return SummaryGenerateResponse(
        summary=summary_result["summary"],
        mode=summary_result["mode"],
        source_review_ids=summary_result.get("source_review_ids", []),
        total_reviews_analyzed=len(reviews_data),
        model=summary_result.get("model"),
        sentence_citations=summary_result.get("sentence_citations"),
    )

