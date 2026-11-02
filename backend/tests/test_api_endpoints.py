"""Integration tests for FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["baseline_ready"] is True
    assert data["transformer_ready"] is True


def test_dashboard_overview_endpoint(client):
    res = client.get("/api/dashboard/overview")
    assert res.status_code == 200
    data = res.json()
    assert data["total_reviews"] > 0
    assert "positive_count" in data
    assert "negative_count" in data
    assert "neutral_count" in data
    assert len(data["top_issues"]) > 0


def test_review_analyze_endpoint_baseline(client):
    # Ensure baseline is active
    client.post("/api/evaluations/active-model", json={"model_name": "sentiment_baseline"})

    payload = {
        "text": "The cooler is very good quality and cooling is fantastic.",
        "include_explanation": True,
        "save_to_history": False,
    }
    res = client.post("/api/reviews/analyze", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["sentiment"] == "positive"
    assert data["active_model"] == "sentiment_baseline"
    assert data["confidence"] > 0.5
    assert data["explanation"]["available"] is True


def test_active_model_switch_and_transformer_analyze(client):
    """Test switching active model to transformer_distilbert and running analyze."""
    # 1. Switch to transformer_distilbert
    res_switch = client.post("/api/evaluations/active-model", json={"model_name": "transformer_distilbert"})
    assert res_switch.status_code == 200
    assert res_switch.json()["active_model"] == "transformer_distilbert"

    # 2. Check health reflects new active model
    res_health = client.get("/api/health")
    assert res_health.json()["active_model"] == "transformer_distilbert"

    # 3. Analyze review with active Transformer
    payload = {
        "text": "Best budget cooler nice cooling air flow super amazing.",
        "include_explanation": True,
        "save_to_history": False,
    }
    res_analyze = client.post("/api/reviews/analyze", json=payload)
    assert res_analyze.status_code == 200
    data = res_analyze.json()
    assert data["active_model"] == "transformer_distilbert"
    assert data["sentiment"] == "positive"
    assert "negative" in data["probabilities"]
    assert "neutral" in data["probabilities"]
    assert "positive" in data["probabilities"]
    # Explanation must NOT show linear TF-IDF attribution for Transformer
    assert data["explanation"]["available"] is False

    # 4. Switch back to baseline
    client.post("/api/evaluations/active-model", json={"model_name": "sentiment_baseline"})


def test_review_list_and_detail_endpoints(client):
    res = client.get("/api/reviews?page=1&page_size=5")
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) == 5
    sample_id = data["items"][0]["review_id"]

    # Detail
    res_det = client.get(f"/api/reviews/{sample_id}")
    assert res_det.status_code == 200
    assert res_det.json()["review"]["review_id"] == sample_id


def test_response_verify_endpoint(client):
    payload = {
        "customer_review": "The product quality is good, but the delivery was delayed by five days.",
        "response_text": "We acknowledge the delivery was delayed by five days. We have processed a refund of Rs. 500.",
    }
    res = client.post("/api/responses/verify", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["total_claims"] == 2
    assert data["supported_count"] == 1
    assert data["unsupported_count"] == 1


def test_evaluations_endpoint(client):
    res = client.get("/api/evaluations")
    assert res.status_code == 200
    data = res.json()
    assert data["baseline_loaded"] is True
    assert data["transformer_loaded"] is True
    assert "sentiment_baseline" in data["models_available"]
    assert "transformer_distilbert" in data["models_available"]
    assert data["evaluations"]["transformer_distilbert"]["test_metrics"] is not None
    assert data["evaluations"]["transformer_distilbert"]["test_metrics"]["accuracy"] > 0.90


def test_dataset_quality_endpoint(client):
    res = client.get("/api/dataset/quality")
    assert res.status_code == 200
    data = res.json()
    assert data["total_records"] == 205052


def test_dashboard_dataset_scope_and_insights(client):
    res = client.get("/api/dashboard/overview")
    assert res.status_code == 200
    data = res.json()
    assert data["dataset_scope"]["raw_total"] == 205052
    assert data["dataset_scope"]["imported_database"] > 0
    assert data["dataset_scope"]["train_split"] == 73512
    assert data["dataset_scope"]["test_split"] == 9189
    assert data["sample_summary"] is not None
    assert "summary" in data["sample_summary"]


def test_summaries_generate_with_review_ids(client):
    # Fetch 3 real reviews first
    res_list = client.get("/api/reviews?page=1&page_size=3")
    assert res_list.status_code == 200
    ids = [item["review_id"] for item in res_list.json()["items"]]

    res = client.post("/api/summaries/generate", json={"review_ids": ids, "prefer_abstractive": False})
    assert res.status_code == 200
    data = res.json()
    assert data["total_reviews_analyzed"] == len(ids)
    assert len(data["summary"]) > 0
