"""Unit tests for Issue Detection and Hallucination Claim Verification."""

import pytest
from backend.app.services.issue_detection import IssueDetector
from backend.app.services.hallucination_detector import HallucinationDetector


@pytest.fixture
def issue_detector():
    return IssueDetector()


@pytest.fixture
def hallucination_detector():
    return HallucinationDetector()


def test_issue_detection_multi_label(issue_detector):
    text = "The product quality is good, but the delivery was delayed by five days and the packaging was damaged."
    detected = issue_detector.detect_issues(text)
    categories = {d["category"]: d["aspect_sentiment"] for d in detected}

    assert "Product quality" in categories
    assert categories["Product quality"] == "positive"
    assert "Delivery and shipping" in categories
    assert categories["Delivery and shipping"] == "negative"
    assert "Packaging" in categories
    assert categories["Packaging"] == "negative"


def test_issue_detection_negation_guard(issue_detector):
    # Negation guard: "no delivery delay" should not be flagged as a delivery complaint
    text = "Received the package on time with no delivery delay whatsoever."
    detected = issue_detector.detect_issues(text)
    complaints = [d for d in detected if d.get("is_complaint")]
    assert len(complaints) == 0


def test_hallucination_demo_scenario(hallucination_detector):
    review = "The product quality is good, but the delivery was delayed by five days and the packaging was damaged."
    response = (
        "Thank you for reaching out to us. "
        "We acknowledge that your delivery was delayed by five days. "
        "Your product was delivered on time without any delay. "
        "We have processed your refund of Rs. 2,000. "
        "Your replacement will arrive tomorrow."
    )

    res = hallucination_detector.verify_response(response, review)

    # 1 courtesy sentence filtered out
    assert len(res["courtesy_statements"]) == 1
    assert "Thank you" in res["courtesy_statements"][0]

    # 4 factual claims evaluated
    assert res["total_claims"] == 4
    status_map = {c["claim"]: c["status"] for c in res["claims"]}

    # Supported: delivery delay acknowledged
    assert any("delayed by five days" in k and v == "SUPPORTED" for k, v in status_map.items())

    # Contradicted: delivered on time
    assert any("delivered on time" in k and v == "CONTRADICTED" for k, v in status_map.items())

    # Unsupported: fake refund and fake replacement
    assert any("2,000" in k and v == "UNSUPPORTED" for k, v in status_map.items())
    assert any("tomorrow" in k and v == "UNSUPPORTED" for k, v in status_map.items())

    # Overall verdict
    assert res["overall_status"] == "FAIL_CONTRADICTED"
    assert res["contradiction_rate"] > 0
    assert res["unsupported_claim_rate"] > 0

