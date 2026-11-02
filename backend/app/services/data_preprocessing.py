"""Data Preprocessing Service for ConsumerVoice.

Performs schema inspection, data quality audit, text normalization,
ambiguous label detection, and leakage-safe dataset splitting.
"""

import json
import logging
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

logger = logging.getLogger(__name__)


def clean_text_basic(text: Any) -> str:
    """Normalize whitespace, unicode, and remove HTML while preserving negations and punctuation."""
    if text is None or pd.isna(text):
        return ""
    text_str = str(text)
    # Unicode NFKD normalization
    text_str = unicodedata.normalize("NFKD", text_str)
    # Remove HTML tags if present
    text_str = re.sub(r"<[^>]+>", " ", text_str)
    # Replace excessive repeated characters (e.g., 'sooooo' -> 'soo')
    text_str = re.sub(r"(.)\1{3,}", r"\1\1", text_str)
    # Normalize whitespaces
    text_str = re.sub(r"\s+", " ", text_str).strip()
    return text_str


def normalize_summary(text: Any) -> str:
    """Normalize summary for deduplication and grouping (lowercased, clean spaces, keep negations)."""
    cleaned = clean_text_basic(text).lower()
    # Normalize internal punctuation spacing
    cleaned = re.sub(r"[^\w\s\'-]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def parse_rating(rate_val: Any) -> Optional[float]:
    """Parse numeric rating, strictly validating 1.0 to 5.0 range and identifying malformed entries."""
    if rate_val is None or pd.isna(rate_val):
        return None
    val_str = str(rate_val).strip()
    try:
        val = float(val_str)
        if 1.0 <= val <= 5.0:
            return val
    except ValueError:
        pass
    # If the string is purely a number formatted with whitespace or 'stars'
    match = re.fullmatch(r"([1-5](?:\.[0-9]+)?)\s*(?:stars?|\/5)?", val_str, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


class DataPreprocessor:
    """End-to-end preprocessing and audit engine for Flipkart product reviews."""

    def __init__(self, raw_csv_path: str = "data/raw/Dataset-SA.csv", output_dir: str = "data/processed"):
        self.raw_csv_path = Path(raw_csv_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.audit_report: Dict[str, Any] = {}

    def audit_raw_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Perform comprehensive data quality inspection."""
        total_rows = len(df)
        total_cols = len(df.columns)

        missing_counts = df.isnull().sum().to_dict()
        exact_duplicates = int(df.duplicated().sum())

        # Sentiment label counts
        raw_sentiment_counts = df["Sentiment"].value_counts(dropna=False).to_dict()
        raw_sentiment_counts = {str(k): int(v) for k, v in raw_sentiment_counts.items()}

        # Rate check
        malformed_rate_indices = []
        for idx, val in df["Rate"].items():
            parsed = parse_rating(val)
            if parsed is None and pd.notna(val):
                malformed_rate_indices.append((idx, str(val)))

        # Unique summaries
        raw_summary_unique = int(df["Summary"].nunique(dropna=False))

        audit = {
            "total_records": total_rows,
            "total_columns": total_cols,
            "columns": list(df.columns),
            "missing_values": {str(k): int(v) for k, v in missing_counts.items()},
            "exact_duplicate_rows": exact_duplicates,
            "raw_sentiment_distribution": raw_sentiment_counts,
            "malformed_rate_count": len(malformed_rate_indices),
            "malformed_rate_samples": malformed_rate_indices[:10],
            "raw_distinct_summaries": raw_summary_unique,
        }
        return audit

    def process_and_split(self, random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
        """Run the full cleaning, deduplication, conflict detection and train/val/test split."""
        logger.info(f"Loading raw dataset from {self.raw_csv_path}...")
        df_raw = pd.read_csv(self.raw_csv_path)

        # 1. Audit raw
        audit_raw = self.audit_raw_data(df_raw)

        # 2. Add stable review ID
        df = df_raw.copy()
        df["review_id"] = [f"REV_{i+1:06d}" for i in range(len(df))]

        # 3. Clean and normalize Rate
        df["cleaned_rate"] = df["Rate"].apply(parse_rating)

        # 4. Normalize Sentiment
        df["normalized_sentiment"] = (
            df["Sentiment"]
            .astype(str)
            .str.strip()
            .str.lower()
        )
        valid_sentiments = {"positive", "negative", "neutral"}
        invalid_mask = ~df["normalized_sentiment"].isin(valid_sentiments)
        invalid_sentiment_count = int(invalid_mask.sum())

        # 5. Clean text columns
        df["cleaned_review"] = df["Review"].apply(clean_text_basic)
        df["cleaned_summary"] = df["Summary"].apply(clean_text_basic)
        df["normalized_summary"] = df["Summary"].apply(normalize_summary)

        # 6. Combined text for ablation study
        df["cleaned_combined"] = (df["cleaned_summary"] + " " + df["cleaned_review"]).str.strip()

        # Save full cleaned dataset for application analytics
        cleaned_reviews_path = self.output_dir / "cleaned_reviews.csv"
        df.to_csv(cleaned_reviews_path, index=False)
        logger.info(f"Saved full cleaned dataset with {len(df)} records to {cleaned_reviews_path}")

        # 7. Model training preparation: filter out empty normalized summaries and invalid sentiments
        valid_model_mask = (df["normalized_summary"] != "") & (~invalid_mask)
        df_valid_model = df[valid_model_mask].copy()

        # 8. Check conflicting labels on identical normalized_summary
        summary_sentiment_groups = (
            df_valid_model.groupby("normalized_summary")["normalized_sentiment"]
            .nunique()
        )
        conflicting_summaries = summary_sentiment_groups[summary_sentiment_groups > 1].index.tolist()

        ambiguous_df = df_valid_model[df_valid_model["normalized_summary"].isin(conflicting_summaries)].copy()
        ambiguous_path = self.output_dir / "ambiguous_labels.csv"
        ambiguous_df.to_csv(ambiguous_path, index=False)
        logger.info(
            f"Detected {len(conflicting_summaries)} conflicting summary groups ({len(ambiguous_df)} rows). "
            f"Saved to {ambiguous_path}"
        )

        # 9. Supervised training benchmark dataset: exclude ambiguous groups
        df_unambiguous = df_valid_model[~df_valid_model["normalized_summary"].isin(conflicting_summaries)].copy()

        # 10. For repeated identical summaries with same sentiment, retain 1 representative record to avoid data leakage
        df_benchmark = df_unambiguous.drop_duplicates(subset=["normalized_summary"]).copy()

        # 11. Stratified 80/10/10 split
        train_df, temp_df = train_test_split(
            df_benchmark,
            test_size=0.20,
            random_state=random_state,
            stratify=df_benchmark["normalized_sentiment"]
        )
        val_df, test_df = train_test_split(
            temp_df,
            test_size=0.50,
            random_state=random_state,
            stratify=temp_df["normalized_sentiment"]
        )

        # Save splits
        train_path = self.output_dir / "sentiment_train.csv"
        val_path = self.output_dir / "sentiment_validation.csv"
        test_path = self.output_dir / "sentiment_test.csv"

        train_df.to_csv(train_path, index=False)
        val_df.to_csv(val_path, index=False)
        test_df.to_csv(test_path, index=False)

        # Calculate sentiment distributions for splits
        train_dist = train_df["normalized_sentiment"].value_counts().to_dict()
        val_dist = val_df["normalized_sentiment"].value_counts().to_dict()
        test_dist = test_df["normalized_sentiment"].value_counts().to_dict()

        # 12. Rating-Sentiment consistency audit on cleaned data
        rating_sentiment_matrix = (
            df.dropna(subset=["cleaned_rate"])
            .groupby(["cleaned_rate", "normalized_sentiment"])
            .size()
            .unstack(fill_value=0)
            .to_dict()
        )

        full_audit = {
            **audit_raw,
            "invalid_sentiment_count": invalid_sentiment_count,
            "cleaned_total_rows": len(df),
            "conflicting_summary_groups_count": len(conflicting_summaries),
            "conflicting_rows_count": len(ambiguous_df),
            "benchmark_deduplicated_rows": len(df_benchmark),
            "splits": {
                "train_size": len(train_df),
                "train_distribution": {str(k): int(v) for k, v in train_dist.items()},
                "val_size": len(val_df),
                "val_distribution": {str(k): int(v) for k, v in val_dist.items()},
                "test_size": len(test_df),
                "test_distribution": {str(k): int(v) for k, v in test_dist.items()},
            },
            "rating_sentiment_consistency": rating_sentiment_matrix,
        }

        report_path = self.output_dir / "data_quality_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(full_audit, f, indent=2)

        logger.info(f"Full data quality report saved to {report_path}")
        self.audit_report = full_audit

        return train_df, val_df, test_df, df, full_audit
