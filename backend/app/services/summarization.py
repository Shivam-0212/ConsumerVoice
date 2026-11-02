"""Feedback Summarization Service for ConsumerVoice.

Provides local extractive summarization using sentence graph ranking
and optional abstractive summarization via the official google-genai SDK.
Retains source review citations and review IDs.
"""

import logging
import os
import re
from typing import Any, Dict, List, Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)


class SummarizationService:
    """Multi-mode feedback summarizer with strict review ID citation retention."""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
        self.client = None
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                logger.info(f"Initialized google-genai Client with model: {self.model_name}")
            except Exception as e:
                logger.warning(f"Could not initialize google-genai client: {e}. Using local extractive mode.")

    def extractive_summarize(
        self,
        reviews: List[Dict[str, Any]],
        num_sentences: int = 4
    ) -> Dict[str, Any]:
        """Generate extractive summary by ranking sentences based on TF-IDF salience."""
        if not reviews:
            return {
                "summary": "No customer reviews available for the selected criteria.",
                "mode": "local_extractive",
                "source_review_ids": [],
                "sentence_citations": [],
            }

        # Collect candidate sentences along with their source review_id
        candidates: List[Dict[str, Any]] = []
        for r in reviews:
            rev_id = r.get("review_id", "UNKNOWN")
            text = (str(r.get("Summary", "")) + ". " + str(r.get("Review", ""))).strip()
            # Split into clean sentences
            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 15]
            for s in sentences:
                candidates.append({
                    "sentence": s,
                    "review_id": rev_id,
                    "sentiment": r.get("Sentiment", "unknown")
                })

        if not candidates:
            # Fallback to summaries directly
            for r in reviews:
                s = str(r.get("Summary", "")).strip()
                if s:
                    candidates.append({
                        "sentence": s,
                        "review_id": r.get("review_id", "UNKNOWN"),
                        "sentiment": r.get("Sentiment", "unknown")
                    })

        if not candidates:
            return {
                "summary": "Insufficient textual data to generate a summary.",
                "mode": "local_extractive",
                "source_review_ids": [],
                "sentence_citations": [],
            }

        # If very few candidate sentences, return them directly
        if len(candidates) <= num_sentences:
            selected = candidates
        else:
            # TF-IDF sentence salience scoring
            raw_sentences = [c["sentence"] for c in candidates]
            try:
                tfidf = TfidfVectorizer(stop_words="english", max_features=1000)
                matrix = tfidf.fit_transform(raw_sentences)
                # Compute centroid sentence similarity
                centroid = matrix.mean(axis=0)
                scores = np.asarray(matrix.dot(centroid.T)).flatten()
                top_indices = np.argsort(scores)[::-1][:num_sentences]
                # Preserve original appearance order
                top_indices = sorted(top_indices)
                selected = [candidates[i] for i in top_indices]
            except Exception as e:
                logger.warning(f"Extractive TF-IDF scoring fallback: {e}")
                selected = candidates[:num_sentences]

        summary_text = " ".join([item["sentence"] for item in selected])
        source_ids = list(dict.fromkeys([item["review_id"] for item in selected]))

        return {
            "summary": summary_text,
            "mode": "local_extractive",
            "source_review_ids": source_ids,
            "sentence_citations": [
                {"sentence": item["sentence"], "review_id": item["review_id"]}
                for item in selected
            ],
            "total_reviews_analyzed": len(reviews),
        }

    def summarize(
        self,
        reviews: List[Dict[str, Any]],
        num_sentences: int = 4,
        prefer_abstractive: bool = True
    ) -> Dict[str, Any]:
        """Summarize feedback using Gemini if available, falling back to local extractive."""
        if prefer_abstractive and self.client and self.api_key:
            try:
                # Prepare grounded prompt
                sample_reviews = reviews[:30]  # Limit to top 30 to respect prompt limits
                review_lines = []
                for idx, r in enumerate(sample_reviews):
                    rid = r.get("review_id", f"R{idx+1}")
                    sm = r.get("Summary", "")
                    rv = r.get("Review", "")
                    review_lines.append(f"[{rid}] Summary: {sm} | Details: {rv}")

                prompt = (
                    "You are a factual customer feedback summarization engine for ConsumerVoice.\n"
                    "Synthesize the key points from the following customer reviews into an accurate summary.\n"
                    "RULES:\n"
                    "1. Only state facts directly expressed in the provided reviews.\n"
                    "2. Include the bracketed review IDs like [REV_000001] for every key finding.\n"
                    "3. Do not invent trends, numbers, or issues not present in the reviews.\n"
                    "4. Keep the summary between 3 to 5 sentences.\n\n"
                    "REVIEWS:\n" + "\n".join(review_lines) + "\n\nSUMMARY:"
                )

                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                )
                if response and response.text:
                    abstractive_text = response.text.strip()
                    # Extract cited review IDs
                    cited_ids = list(dict.fromkeys(re.findall(r"\[(REV_\d+)\]", abstractive_text)))
                    if not cited_ids:
                        cited_ids = [r.get("review_id") for r in sample_reviews if r.get("review_id")]

                    return {
                        "summary": abstractive_text,
                        "mode": "gemini_abstractive",
                        "model": self.model_name,
                        "source_review_ids": cited_ids,
                        "total_reviews_analyzed": len(reviews),
                    }
            except Exception as e:
                logger.warning(f"Gemini summarization failed ({e}). Reverting to local extractive mode.")

        # Local extractive fallback
        return self.extractive_summarize(reviews, num_sentences=num_sentences)

