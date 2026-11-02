"""Pydantic schemas for ConsumerVoice API requests and responses."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ReviewItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    review_id: str
    product_name: Optional[str] = "Unknown Product"
    product_price: Optional[str] = None
    rate: Optional[str] = None
    cleaned_rate: Optional[Any] = None
    review_text: Optional[str] = None
    summary: Optional[str] = ""
    normalized_sentiment: Optional[str] = "neutral"
    is_benchmark: bool = False


class ReviewListResponse(BaseModel):
    items: List[ReviewItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class ReviewDetailResponse(BaseModel):
    review: ReviewItem
    predictions: List[Dict[str, Any]] = []
    issues: List[Dict[str, Any]] = []


class ReviewAnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    model_name: Optional[str] = None
    include_explanation: bool = True
    save_to_history: bool = False


class FeatureContributor(BaseModel):
    token: str
    score: float
    impact: str


class ExplanationData(BaseModel):
    method: str
    available: bool
    summary: str
    positive_contributors: List[FeatureContributor] = []
    negative_contributors: List[FeatureContributor] = []
    disclaimer: str


class ReviewAnalyzeResponse(BaseModel):
    sentiment: str
    confidence: float
    probabilities: Dict[str, float]
    active_model: str
    explanation: Optional[ExplanationData] = None
    issues: List[Dict[str, Any]] = []
    issue_summary: Dict[str, Any] = {}


class SummaryGenerateRequest(BaseModel):
    product_name: Optional[str] = None
    sentiment: Optional[str] = None
    issue_category: Optional[str] = None
    sample_size: int = Field(default=25, ge=5, le=100)
    prefer_abstractive: bool = True
    review_ids: Optional[List[str]] = None


class SummaryGenerateResponse(BaseModel):
    summary: str
    mode: str
    source_review_ids: List[str] = []
    total_reviews_analyzed: int
    model: Optional[str] = None
    sentence_citations: Optional[List[Dict[str, str]]] = None


class ResponseGenerateRequest(BaseModel):
    customer_text: str = Field(..., min_length=2)
    sentiment: Optional[str] = None
    detected_issues: Optional[List[Dict[str, Any]]] = None
    company_policies: Optional[List[str]] = None
    review_id: Optional[str] = None
    use_gemini: bool = True


class ResponseGenerateResponse(BaseModel):
    response: str
    mode: str
    review_id: Optional[str] = None
    grounding_safeguards_applied: bool
    sentiment_acknowledged: Optional[str] = None
    issues_addressed: List[str] = []
    model: Optional[str] = None


class ResponseVerifyRequest(BaseModel):
    response_text: str = Field(..., min_length=5)
    customer_review: str = Field(..., min_length=2)
    company_policies: Optional[List[str]] = None


class ClaimVerificationItem(BaseModel):
    claim: str
    status: str
    verdict_reason: str
    matched_evidence: Optional[str] = None
    confidence: float
    method: str


class ResponseVerifyResponse(BaseModel):
    overall_status: str
    claim_support_rate: float
    unsupported_claim_rate: float
    contradiction_rate: float
    evidence_coverage: float
    total_claims: int
    supported_count: int
    unsupported_count: int
    contradicted_count: int
    claims: List[ClaimVerificationItem] = []
    courtesy_statements: List[str] = []
    disclaimer: str


class DashboardOverviewResponse(BaseModel):
    total_reviews: int
    positive_count: int
    negative_count: int
    neutral_count: int
    positive_percent: float
    negative_percent: float
    neutral_percent: float
    rating_distribution: Dict[str, int]
    top_issues: List[Dict[str, Any]]
    top_products: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]
    dataset_scope: Optional[Dict[str, int]] = None
    sample_summary: Optional[Dict[str, Any]] = None


class ActiveModelSetRequest(BaseModel):
    model_name: str

