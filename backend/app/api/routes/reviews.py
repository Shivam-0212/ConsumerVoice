"""Review endpoints for ConsumerVoice."""

import json
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.entities import IssueDetectionModel, ReviewModel, SentimentPredictionModel
from backend.app.schemas.domain import (
    ReviewAnalyzeRequest,
    ReviewAnalyzeResponse,
    ReviewDetailResponse,
    ReviewItem,
    ReviewListResponse,
)
from backend.app.services.issue_detection import IssueDetector
from backend.app.services.sentiment_service import sentiment_service

router = APIRouter(prefix="/reviews", tags=["reviews"])
logger = logging.getLogger(__name__)

issue_detector = IssueDetector()


@router.get("", response_model=ReviewListResponse)
def get_reviews(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: Optional[str] = None,
    product: Optional[str] = None,
    sentiment: Optional[str] = None,
    rate: Optional[float] = None,
    db: Session = Depends(get_db),
):
    """Retrieve paginated and filtered reviews."""
    query = db.query(ReviewModel)

    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                ReviewModel.summary.ilike(search_pattern),
                ReviewModel.review_text.ilike(search_pattern),
                ReviewModel.product_name.ilike(search_pattern),
            )
        )

    if product:
        query = query.filter(ReviewModel.product_name.ilike(f"%{product.strip()}%"))

    if sentiment:
        query = query.filter(ReviewModel.normalized_sentiment == sentiment.strip().lower())

    if rate is not None:
        query = query.filter(ReviewModel.cleaned_rate == rate)

    total = query.count()
    offset = (page - 1) * page_size
    items = query.order_by(ReviewModel.review_id.asc()).offset(offset).limit(page_size).all()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return ReviewListResponse(
        items=[ReviewItem.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{review_id}", response_model=ReviewDetailResponse)
def get_review_detail(review_id: str, db: Session = Depends(get_db)):
    """Retrieve details for a single review along with past predictions and issues."""
    review = db.query(ReviewModel).filter(ReviewModel.review_id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail=f"Review with ID '{review_id}' not found.")

    # Retrieve existing predictions and issues, or run on the fly if empty
    predictions = (
        db.query(SentimentPredictionModel)
        .filter(SentimentPredictionModel.review_id == review_id)
        .all()
    )
    issues = (
        db.query(IssueDetectionModel)
        .filter(IssueDetectionModel.review_id == review_id)
        .all()
    )

    pred_list = [
        {
            "predicted_sentiment": p.predicted_sentiment,
            "confidence": p.confidence,
            "probabilities": {
                "negative": p.prob_negative,
                "neutral": p.prob_neutral,
                "positive": p.prob_positive,
            },
            "model_used": p.model_used,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in predictions
    ]

    issue_list = [
        {
            "category": i.category,
            "aspect_sentiment": i.aspect_sentiment,
            "matched_evidence": i.matched_evidence,
            "confidence": i.confidence,
            "detection_method": i.detection_method,
        }
        for i in issues
    ]

    # If no recorded issues, compute live
    if not issue_list:
        combined_text = f"{review.summary}. {review.review_text or ''}".strip()
        live_issues = issue_detector.detect_issues(combined_text)
        issue_list = live_issues

    return ReviewDetailResponse(
        review=ReviewItem.model_validate(review),
        predictions=pred_list,
        issues=issue_list,
    )


@router.post("/analyze", response_model=ReviewAnalyzeResponse)
def analyze_review_text(
    payload: ReviewAnalyzeRequest,
    db: Session = Depends(get_db),
):
    """Perform real-time multi-task NLP analysis: sentiment + feature explanation + multi-label issues."""
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Review text cannot be empty.")

    # 1. Sentiment prediction + Feature Attribution
    pred_res = sentiment_service.predict(
        text,
        include_explanation=payload.include_explanation,
        model_name=payload.model_name,
    )

    # 2. Issue and aspect detection
    detected_issues = issue_detector.detect_issues(text)
    issue_summary = issue_detector.summarize_issues(detected_issues)

    # 3. Optional persistence
    if payload.save_to_history:
        try:
            pred_record = SentimentPredictionModel(
                predicted_sentiment=pred_res["sentiment"],
                confidence=pred_res["confidence"],
                prob_negative=pred_res["probabilities"].get("negative", 0.0),
                prob_neutral=pred_res["probabilities"].get("neutral", 0.0),
                prob_positive=pred_res["probabilities"].get("positive", 0.0),
                model_used=pred_res["active_model"],
                input_text=text[:500],
            )
            db.add(pred_record)
            db.commit()
        except Exception as e:
            logger.warning(f"Could not persist prediction history: {e}")
            db.rollback()

    return ReviewAnalyzeResponse(
        sentiment=pred_res["sentiment"],
        confidence=pred_res["confidence"],
        probabilities=pred_res["probabilities"],
        active_model=pred_res["active_model"],
        explanation=pred_res.get("explanation"),
        issues=detected_issues,
        issue_summary=issue_summary,
    )

