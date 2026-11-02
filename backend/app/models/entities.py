"""SQLAlchemy database models for ConsumerVoice."""

import datetime
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from backend.app.database.session import Base


class ReviewModel(Base):
    __tablename__ = "reviews"

    review_id = Column(String(32), primary_key=True, index=True)
    product_name = Column(String(512), index=True)
    product_price = Column(String(64), nullable=True)
    rate = Column(String(64), nullable=True)
    cleaned_rate = Column(Float, nullable=True, index=True)
    review_text = Column(Text, nullable=True)
    summary = Column(Text, nullable=False)
    cleaned_summary = Column(Text, nullable=True)
    normalized_sentiment = Column(String(32), index=True, nullable=False)
    is_benchmark = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    predictions = relationship("SentimentPredictionModel", back_populates="review", cascade="all, delete-orphan")
    issues = relationship("IssueDetectionModel", back_populates="review", cascade="all, delete-orphan")


class SentimentPredictionModel(Base):
    __tablename__ = "sentiment_predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    review_id = Column(String(32), ForeignKey("reviews.review_id", ondelete="CASCADE"), nullable=True, index=True)
    predicted_sentiment = Column(String(32), nullable=False)
    confidence = Column(Float, nullable=False)
    prob_negative = Column(Float, default=0.0)
    prob_neutral = Column(Float, default=0.0)
    prob_positive = Column(Float, default=0.0)
    model_used = Column(String(64), default="sentiment_baseline")
    input_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    review = relationship("ReviewModel", back_populates="predictions")


class IssueDetectionModel(Base):
    __tablename__ = "issue_detections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    review_id = Column(String(32), ForeignKey("reviews.review_id", ondelete="CASCADE"), nullable=True, index=True)
    category = Column(String(128), index=True, nullable=False)
    aspect_sentiment = Column(String(32), nullable=False)
    matched_evidence = Column(Text, nullable=True)
    confidence = Column(Float, default=0.90)
    detection_method = Column(String(64), default="contextual_rule_pattern")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    review = relationship("ReviewModel", back_populates="issues")


class GeneratedSummaryModel(Base):
    __tablename__ = "generated_summaries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    summary_text = Column(Text, nullable=False)
    mode = Column(String(64), default="local_extractive")
    filter_sentiment = Column(String(32), nullable=True)
    filter_product = Column(String(512), nullable=True)
    source_review_count = Column(Integer, default=0)
    source_ids_json = Column(Text, default="[]")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class GeneratedResponseModel(Base):
    __tablename__ = "generated_responses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    review_id = Column(String(32), nullable=True, index=True)
    response_text = Column(Text, nullable=False)
    mode = Column(String(64), default="local_template")
    sentiment_used = Column(String(32), nullable=True)
    issues_addressed_json = Column(Text, default="[]")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class VerificationResultModel(Base):
    __tablename__ = "verification_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    response_id = Column(Integer, nullable=True, index=True)
    overall_status = Column(String(64), nullable=False)
    claim_support_rate = Column(Float, default=0.0)
    unsupported_claim_rate = Column(Float, default=0.0)
    contradiction_rate = Column(Float, default=0.0)
    evidence_coverage = Column(Float, default=0.0)
    total_claims = Column(Integer, default=0)
    claims_json = Column(Text, default="[]")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class IssueAnnotationModel(Base):
    __tablename__ = "issue_annotations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    review_id = Column(String(32), unique=True, index=True, nullable=False)
    issue_product_quality = Column(Integer, default=0)
    issue_delivery_shipping = Column(Integer, default=0)
    issue_packaging = Column(Integer, default=0)
    issue_product_performance = Column(Integer, default=0)
    issue_usability = Column(Integer, default=0)
    issue_pricing_value = Column(Integer, default=0)
    issue_durability = Column(Integer, default=0)
    issue_size_fit = Column(Integer, default=0)
    issue_returns_refunds = Column(Integer, default=0)
    issue_customer_support = Column(Integer, default=0)
    annotator_notes = Column(Text, nullable=True)
    is_annotated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

