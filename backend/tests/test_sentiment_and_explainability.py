"""Unit tests for Sentiment Prediction and Model Explainability."""

import pytest
from backend.app.services.sentiment_service import SentimentService
from backend.app.services.explainability import ModelExplainer


@pytest.fixture
def sentiment_svc():
    svc = SentimentService()
    # Reset to baseline initially
    svc.set_active_model("sentiment_baseline")
    return svc


def test_sentiment_prediction_probabilities(sentiment_svc):
    res = sentiment_svc.predict("great cooler excellent air flow and amazing quality")
    assert res["sentiment"] == "positive"
    assert res["confidence"] > 0.70
    assert "probabilities" in res
    probs = res["probabilities"]
    assert abs(sum(probs.values()) - 1.0) < 0.05
    assert set(probs.keys()) == {"negative", "neutral", "positive"}


def test_sentiment_prediction_negative(sentiment_svc):
    res = sentiment_svc.predict("terrible defect worst product waste of money")
    assert res["sentiment"] == "negative"
    assert res["confidence"] > 0.60


def test_explainability_attribution_baseline(sentiment_svc):
    sentiment_svc.set_active_model("sentiment_baseline")
    res = sentiment_svc.predict("great quality and fast delivery", include_explanation=True)
    exp = res["explanation"]
    assert exp["available"] is True
    assert exp["method"] == "tfidf_coefficient_attribution"
    assert len(exp["positive_contributors"]) > 0
    assert any("great" in tok["token"] for tok in exp["positive_contributors"])
    assert "disclaimer" in exp


def test_distilbert_loading_and_prediction(sentiment_svc):
    """Verify DistilBERT loads config.json + model.safetensors and runs inference on CPU."""
    assert sentiment_svc.transformer_model is not None
    assert sentiment_svc.transformer_tokenizer is not None

    # Switch to DistilBERT
    switched = sentiment_svc.set_active_model("transformer_distilbert")
    assert switched is True
    assert sentiment_svc.active_model_name == "transformer_distilbert"

    # Positive sample
    pos_res = sentiment_svc.predict("great cooler excellent air flow and amazing quality")
    assert pos_res["active_model"] == "transformer_distilbert"
    assert pos_res["sentiment"] == "positive"
    assert pos_res["confidence"] > 0.80
    assert "negative" in pos_res["probabilities"]
    assert "neutral" in pos_res["probabilities"]
    assert "positive" in pos_res["probabilities"]

    # Negative sample
    neg_res = sentiment_svc.predict("useless product very bad cooler complete waste")
    assert neg_res["active_model"] == "transformer_distilbert"
    assert neg_res["sentiment"] == "negative"
    assert neg_res["confidence"] > 0.80

    # Reset
    sentiment_svc.set_active_model("sentiment_baseline")


def test_distilbert_class_mapping(sentiment_svc):
    """Verify class mapping: 0=Negative, 1=Neutral, 2=Positive."""
    id2label = sentiment_svc.transformer_model.config.id2label
    # Normalizing keys as ints
    id2label_int = {int(k): v.lower() for k, v in id2label.items()}
    assert id2label_int[0] == "negative"
    assert id2label_int[1] == "neutral"
    assert id2label_int[2] == "positive"


def test_distilbert_explanation_compatibility(sentiment_svc):
    """Verify prediction explanation displayed for DistilBERT does NOT show Logistic Regression attributions."""
    sentiment_svc.set_active_model("transformer_distilbert")
    res = sentiment_svc.predict("good cooler but delayed shipping", include_explanation=True)
    exp = res["explanation"]

    # Must be marked unavailable for linear attribution
    assert exp["available"] is False
    assert len(exp["positive_contributors"]) == 0
    assert len(exp["negative_contributors"]) == 0
    assert "Linear feature attribution" in exp["summary"] or "DistilBERT" in exp["summary"]

    # Reset
    sentiment_svc.set_active_model("sentiment_baseline")
