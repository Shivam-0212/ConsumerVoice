"""Explainable AI (XAI) Service for ConsumerVoice.

Calculates local feature attributions using TF-IDF feature values
multiplied by linear model coefficients, generating token-level
contributions and human-readable reasoning.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class ModelExplainer:
    """Explainer for linear sentiment models using TF-IDF coefficient attributions."""

    def __init__(self, pipeline: Any = None):
        self.pipeline = pipeline

    def set_pipeline(self, pipeline: Any):
        self.pipeline = pipeline

    def explain_prediction(
        self,
        text: str,
        predicted_sentiment: str,
        class_probabilities: Dict[str, float],
        top_k: int = 6
    ) -> Dict[str, Any]:
        """Explain linear model prediction via local TF-IDF coefficient contributions."""
        if not self.pipeline:
            return {
                "method": "none",
                "available": False,
                "summary": "Model pipeline is not initialized.",
                "positive_contributors": [],
                "negative_contributors": [],
                "disclaimer": "Explanation unavailable.",
            }

        try:
            tfidf = self.pipeline.named_steps.get("tfidf")
            clf = self.pipeline.named_steps.get("clf")

            if not tfidf or not clf or not hasattr(clf, "coef_"):
                return {
                    "method": "unavailable",
                    "available": False,
                    "summary": "Active model architecture does not support linear coefficient attribution.",
                    "positive_contributors": [],
                    "negative_contributors": [],
                    "disclaimer": "Feature attribution is only supported for linear and gradient-attribution architectures.",
                }

            # Map predicted class to coefficient index
            classes = list(clf.classes_)
            if predicted_sentiment not in classes:
                return {
                    "method": "unavailable",
                    "available": False,
                    "summary": f"Target class {predicted_sentiment} not in model classes.",
                    "positive_contributors": [],
                    "negative_contributors": [],
                    "disclaimer": "Feature attribution unavailable.",
                }

            class_idx = classes.index(predicted_sentiment)
            coefs = clf.coef_[class_idx]

            # Vectorize the single text instance
            vec = tfidf.transform([text])
            feature_names = tfidf.get_feature_names_out()

            # Non-zero coordinates in sparse matrix
            row, cols = vec.nonzero()
            contributions: List[Tuple[str, float]] = []

            for col_idx in cols:
                token = feature_names[col_idx]
                tf_val = vec[0, col_idx]
                c_weight = coefs[col_idx]
                score = float(tf_val * c_weight)
                contributions.append((token, score))

            # Sort by contribution
            sorted_by_score = sorted(contributions, key=lambda x: x[1], reverse=True)

            positive_contributors = [
                {"token": t, "score": round(s, 4), "impact": "supports_prediction"}
                for t, s in sorted_by_score if s > 0
            ][:top_k]

            negative_contributors = [
                {"token": t, "score": round(s, 4), "impact": "opposes_prediction"}
                for t, s in sorted(contributions, key=lambda x: x[1]) if s < 0
            ][:top_k]

            # Construct human-readable explanation
            pos_words = [item["token"] for item in positive_contributors]
            neg_words = [item["token"] for item in negative_contributors]

            prob = class_probabilities.get(predicted_sentiment, 0.0)
            if pos_words:
                words_str = ", ".join(f"'{w}'" for w in pos_words[:3])
                summary = (
                    f"The model predicted '{predicted_sentiment}' ({prob*100:.1f}% confidence) primarily "
                    f"driven by phrases such as {words_str}."
                )
                if neg_words:
                    neg_str = ", ".join(f"'{w}'" for w in neg_words[:2])
                    summary += f" Counter-evidence from terms like {neg_str} reduced prediction certainty."
            else:
                summary = (
                    f"The model predicted '{predicted_sentiment}' ({prob*100:.1f}% confidence) based on "
                    f"general prior class distribution and broad linguistic features."
                )

            return {
                "method": "tfidf_coefficient_attribution",
                "available": True,
                "predicted_sentiment": predicted_sentiment,
                "confidence": prob,
                "summary": summary,
                "positive_contributors": positive_contributors,
                "negative_contributors": negative_contributors,
                "disclaimer": (
                    "Notice: Feature attribution indicates model algorithmic behavior and token influence. "
                    "It does not constitute conclusive proof that the prediction is factually accurate."
                ),
            }

        except Exception as e:
            logger.error(f"Error computing explanation: {e}", exc_info=True)
            return {
                "method": "error",
                "available": False,
                "summary": f"Could not compute explanation: {str(e)}",
                "positive_contributors": [],
                "negative_contributors": [],
                "disclaimer": "Feature attribution error.",
            }

