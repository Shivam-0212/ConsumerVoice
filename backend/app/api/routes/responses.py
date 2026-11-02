"""Customer response generation and evidence-based verification endpoints."""

import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.entities import GeneratedResponseModel, VerificationResultModel
from backend.app.schemas.domain import (
    ResponseGenerateRequest,
    ResponseGenerateResponse,
    ResponseVerifyRequest,
    ResponseVerifyResponse,
)
from backend.app.services.hallucination_detector import HallucinationDetector
from backend.app.services.issue_detection import IssueDetector
from backend.app.services.response_generation import ResponseGenerator
from backend.app.services.sentiment_service import sentiment_service

router = APIRouter(prefix="/responses", tags=["responses"])
logger = logging.getLogger(__name__)

response_generator = ResponseGenerator()
hallucination_detector = HallucinationDetector()
issue_detector = IssueDetector()


@router.post("/generate", response_model=ResponseGenerateResponse)
def generate_customer_response(
    payload: ResponseGenerateRequest,
    db: Session = Depends(get_db),
):
    """Generate grounded customer support response without making unverified commitments."""
    customer_text = payload.customer_text.strip()
    if not customer_text:
        raise HTTPException(status_code=400, detail="Customer text cannot be empty.")

    # Infer sentiment and issues if not provided in payload
    sentiment = payload.sentiment
    if not sentiment:
        pred = sentiment_service.predict(customer_text, include_explanation=False)
        sentiment = pred["sentiment"]

    detected_issues = payload.detected_issues
    if detected_issues is None:
        detected_issues = issue_detector.detect_issues(customer_text)

    # Generate response
    res = response_generator.generate_response(
        customer_text=customer_text,
        sentiment=sentiment,
        detected_issues=detected_issues,
        company_policies=payload.company_policies,
        review_id=payload.review_id,
        use_gemini=payload.use_gemini,
    )

    # Persist in database
    try:
        record = GeneratedResponseModel(
            review_id=payload.review_id,
            response_text=res["response"],
            mode=res["mode"],
            sentiment_used=sentiment,
            issues_addressed_json=json.dumps(res.get("issues_addressed", [])),
        )
        db.add(record)
        db.commit()
    except Exception as e:
        logger.warning(f"Could not persist generated response: {e}")
        db.rollback()

    return ResponseGenerateResponse(
        response=res["response"],
        mode=res["mode"],
        review_id=payload.review_id,
        grounding_safeguards_applied=res.get("grounding_safeguards_applied", True),
        sentiment_acknowledged=res.get("sentiment_acknowledged"),
        issues_addressed=res.get("issues_addressed", []),
        model=res.get("model"),
    )


@router.post("/verify", response_model=ResponseVerifyResponse)
def verify_response_claims(
    payload: ResponseVerifyRequest,
    db: Session = Depends(get_db),
):
    """Decompose response into claims and verify against customer review and company policy."""
    response_text = payload.response_text.strip()
    customer_review = payload.customer_review.strip()

    if not response_text:
        raise HTTPException(status_code=400, detail="Response text cannot be empty.")
    if not customer_review:
        raise HTTPException(status_code=400, detail="Customer review evidence cannot be empty.")

    verification = hallucination_detector.verify_response(
        response_text=response_text,
        customer_review=customer_review,
        company_policies=payload.company_policies,
    )

    # Persist verification result
    try:
        record = VerificationResultModel(
            overall_status=verification["overall_status"],
            claim_support_rate=verification["claim_support_rate"],
            unsupported_claim_rate=verification["unsupported_claim_rate"],
            contradiction_rate=verification["contradiction_rate"],
            evidence_coverage=verification["evidence_coverage"],
            total_claims=verification["total_claims"],
            claims_json=json.dumps(verification["claims"]),
        )
        db.add(record)
        db.commit()
    except Exception as e:
        logger.warning(f"Could not persist verification result: {e}")
        db.rollback()

    return ResponseVerifyResponse(**verification)

