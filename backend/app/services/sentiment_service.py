"""Sentiment Analysis Service for ConsumerVoice.

Manages model loading, runtime inference on CPU, active model switching,
and coordinates with explainability.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import joblib
import numpy as np

from backend.app.services.data_preprocessing import clean_text_basic
from backend.app.services.explainability import ModelExplainer

logger = logging.getLogger(__name__)


class SentimentService:
    """Production service for sentiment prediction and active model management."""

    def __init__(
        self,
        baseline_path: str = "backend/saved_models/sentiment_baseline.joblib",
        transformer_dir: str = "backend/saved_models/distilbert_sentiment",
        evaluation_path: str = "backend/saved_models/model_evaluation.json",
    ):
        self.baseline_path = Path(baseline_path)
        self.transformer_dir = Path(transformer_dir)
        self.evaluation_path = Path(evaluation_path)

        self.baseline_model = None
        self.transformer_model = None
        self.transformer_tokenizer = None
        self.active_model_name = "sentiment_baseline"
        self.explainer = ModelExplainer()

        self._load_baseline()
        self._check_transformer_checkpoint()

    def _load_baseline(self):
        """Load scikit-learn TF-IDF + Logistic Regression pipeline."""
        if self.baseline_path.exists():
            try:
                self.baseline_model = joblib.load(self.baseline_path)
                self.explainer.set_pipeline(self.baseline_model)
                logger.info(f"Loaded sentiment baseline model from {self.baseline_path}")
            except Exception as e:
                logger.error(f"Failed loading sentiment baseline model: {e}")
        else:
            logger.warning(f"Sentiment baseline file not found at {self.baseline_path}")

    def _check_transformer_checkpoint(self) -> bool:
        """Check if trained DistilBERT weights are present and loadable on CPU."""
        if self.transformer_dir.exists() and (self.transformer_dir / "config.json").exists():
            try:
                import torch
                from transformers import AutoModelForSequenceClassification, AutoTokenizer

                logger.info(f"Loading fine-tuned DistilBERT from {self.transformer_dir} on CPU...")
                self.transformer_tokenizer = AutoTokenizer.from_pretrained(str(self.transformer_dir))
                self.transformer_model = AutoModelForSequenceClassification.from_pretrained(str(self.transformer_dir))
                # Ensure CPU execution for 8GB RAM safety
                self.transformer_model.to("cpu")
                self.transformer_model.eval()

                # Verify configuration id2label
                logger.info(
                    f"DistilBERT successfully loaded! Config id2label: {self.transformer_model.config.id2label}"
                )
                return True
            except Exception as e:
                logger.warning(f"DistilBERT checkpoint found but failed to load: {e}")
                self.transformer_model = None
                self.transformer_tokenizer = None
                return False
        return False

    def get_model_status(self) -> Dict[str, Any]:
        """Return status of all models and active inference model."""
        eval_data = {}
        if self.evaluation_path.exists():
            try:
                with open(self.evaluation_path, "r", encoding="utf-8") as f:
                    eval_data = json.load(f)
            except Exception as e:
                logger.error(f"Error reading evaluation data: {e}")

        has_transformer = self.transformer_model is not None

        return {
            "active_model": self.active_model_name,
            "baseline_loaded": self.baseline_model is not None,
            "transformer_loaded": has_transformer,
            "models_available": {
                "sentiment_baseline": {
                    "name": "TF-IDF + Balanced Logistic Regression",
                    "status": "ready" if self.baseline_model is not None else "missing",
                    "supports_explanation": True,
                    "is_active": self.active_model_name == "sentiment_baseline",
                },
                "transformer_distilbert": {
                    "name": "DistilBERT (distilbert-base-uncased Fine-Tuned)",
                    "status": "ready" if has_transformer else "pending_gpu_training",
                    "supports_explanation": False,
                    "is_active": self.active_model_name == "transformer_distilbert",
                },
            },
            "evaluations": eval_data.get("models", {}),
        }

    def set_active_model(self, model_name: str) -> bool:
        """Switch active model between baseline and transformer if available."""
        if model_name == "sentiment_baseline":
            if self.baseline_model is not None:
                self.active_model_name = "sentiment_baseline"
                logger.info("Active model switched to: sentiment_baseline")
                return True
        elif model_name == "transformer_distilbert":
            if self.transformer_model is None:
                # Attempt lazy reload if checkpoint exists
                self._check_transformer_checkpoint()

            if self.transformer_model is not None:
                self.active_model_name = "transformer_distilbert"
                logger.info("Active model switched to: transformer_distilbert")
                return True
            else:
                logger.warning("DistilBERT checkpoint not loaded; cannot set as active.")
                return False
        return False

    def predict_transformer(self, text: str) -> Dict[str, Any]:
        """Perform CPU inference using fine-tuned DistilBERT with batching support."""
        import torch

        # Class mapping: 0: negative, 1: neutral, 2: positive
        id2label = {0: "negative", 1: "neutral", 2: "positive"}
        if self.transformer_model.config.id2label:
            id2label = {int(k): v.lower() for k, v in self.transformer_model.config.id2label.items()}

        inputs = self.transformer_tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=192,
            padding=True,
        )

        with torch.no_grad():
            outputs = self.transformer_model(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1).squeeze().tolist()

        if isinstance(probs, float):
            probs = [probs]

        prob_dict = {
            id2label[i]: round(float(probs[i]), 4)
            for i in sorted(id2label.keys())
        }

        pred_idx = int(np.argmax(probs))
        pred_class = id2label[pred_idx]
        confidence = prob_dict[pred_class]

        # Feature explanation handling for Transformer:
        # Explicitly clarify that linear feature attribution is specific to Logistic Regression
        explanation = {
            "method": "transformer_deep_representation",
            "available": False,
            "summary": (
                f"DistilBERT classified text as '{pred_class}' with {confidence*100:.1f}% confidence. "
                "Linear feature attribution (TF-IDF coefficients) is specific to the Logistic Regression baseline "
                "and is disabled for Transformer inference to prevent misleading attributions."
            ),
            "positive_contributors": [],
            "negative_contributors": [],
            "disclaimer": (
                "Notice: Feature attribution is available exclusively when using the linear Logistic Regression baseline. "
                "DistilBERT generates contextual self-attention representations across 6 Transformer layers."
            ),
        }

        return {
            "sentiment": pred_class,
            "confidence": confidence,
            "probabilities": prob_dict,
            "active_model": "transformer_distilbert",
            "explanation": explanation,
        }

    def predict_baseline(self, text: str, include_explanation: bool = True) -> Dict[str, Any]:
        """Perform inference using TF-IDF + Logistic Regression pipeline."""
        if self.baseline_model is None:
            return {
                "sentiment": "neutral",
                "confidence": 0.333,
                "probabilities": {"negative": 0.333, "neutral": 0.334, "positive": 0.333},
                "active_model": "fallback_prior",
                "explanation": {
                    "available": False,
                    "summary": "Model checkpoint not found.",
                    "positive_contributors": [],
                    "negative_contributors": [],
                    "disclaimer": "No model loaded.",
                },
            }

        probs = self.baseline_model.predict_proba([text])[0]
        classes = list(self.baseline_model.classes_)
        prob_dict = {cls: round(float(probs[i]), 4) for i, cls in enumerate(classes)}

        pred_class = self.baseline_model.predict([text])[0]
        confidence = prob_dict[pred_class]

        explanation = None
        if include_explanation:
            explanation = self.explainer.explain_prediction(
                text=text,
                predicted_sentiment=pred_class,
                class_probabilities=prob_dict,
            )

        return {
            "sentiment": pred_class,
            "confidence": confidence,
            "probabilities": prob_dict,
            "active_model": "sentiment_baseline",
            "explanation": explanation,
        }

    def predict(
        self,
        text: str,
        include_explanation: bool = True,
        model_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Predict sentiment, compute calibrated probabilities, and generate explanation."""
        cleaned = clean_text_basic(text)
        target_model = model_name or self.active_model_name
        if not cleaned:
            return {
                "sentiment": "neutral",
                "confidence": 0.333,
                "probabilities": {"negative": 0.333, "neutral": 0.334, "positive": 0.333},
                "active_model": target_model,
                "explanation": {
                    "available": False,
                    "summary": "Empty text provided; defaulted to neutral prior.",
                    "positive_contributors": [],
                    "negative_contributors": [],
                    "disclaimer": "Empty input.",
                },
            }

        # Route to requested or active model
        if target_model == "transformer_distilbert" and self.transformer_model is not None:
            try:
                return self.predict_transformer(cleaned)
            except Exception as e:
                logger.error(f"DistilBERT inference error: {e}. Falling back to baseline.")

        return self.predict_baseline(cleaned, include_explanation=include_explanation)

    def predict_batch(self, texts: List[str], batch_size: int = 16) -> List[Dict[str, Any]]:
        """Efficient batch inference on CPU."""
        if not texts:
            return []

        if self.active_model_name == "transformer_distilbert" and self.transformer_model is not None:
            import torch
            id2label = {0: "negative", 1: "neutral", 2: "positive"}
            if self.transformer_model.config.id2label:
                id2label = {int(k): v.lower() for k, v in self.transformer_model.config.id2label.items()}

            results = []
            for i in range(0, len(texts), batch_size):
                batch_texts = [clean_text_basic(t) for t in texts[i:i + batch_size]]
                inputs = self.transformer_tokenizer(
                    batch_texts,
                    return_tensors="pt",
                    truncation=True,
                    max_length=192,
                    padding=True,
                )
                with torch.no_grad():
                    outputs = self.transformer_model(**inputs)
                    batch_probs = torch.softmax(outputs.logits, dim=-1).tolist()

                for probs in batch_probs:
                    prob_dict = {id2label[j]: round(float(probs[j]), 4) for j in sorted(id2label.keys())}
                    pred_idx = int(np.argmax(probs))
                    pred_class = id2label[pred_idx]
                    results.append({
                        "sentiment": pred_class,
                        "confidence": prob_dict[pred_class],
                        "probabilities": prob_dict,
                        "active_model": "transformer_distilbert",
                    })
            return results

        # Baseline batch inference
        results = []
        cleaned_batch = [clean_text_basic(t) for t in texts]
        probs_all = self.baseline_model.predict_proba(cleaned_batch)
        preds_all = self.baseline_model.predict(cleaned_batch)
        classes = list(self.baseline_model.classes_)

        for idx, pred_class in enumerate(preds_all):
            probs = probs_all[idx]
            prob_dict = {cls: round(float(probs[c_i]), 4) for c_i, cls in enumerate(classes)}
            results.append({
                "sentiment": pred_class,
                "confidence": prob_dict[pred_class],
                "probabilities": prob_dict,
                "active_model": "sentiment_baseline",
            })
        return results


# Module-level shared singleton instance
_instance: Optional[SentimentService] = None


def get_sentiment_service() -> SentimentService:
    global _instance
    if _instance is None:
        _instance = SentimentService()
    return _instance


# Export shared singleton instance
sentiment_service = get_sentiment_service()
