#!/usr/bin/env python3
"""Issue Classifier Training and Annotation Validation Script for ConsumerVoice.

Validates manual multi-label annotations from issue_annotation_template.csv,
strictly enforces that blank cells are treated as unannotated (not negative),
and trains a multi-label classifier (OneVsRest Logistic Regression or Transformer)
once sufficient annotated ground-truth records are available.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score
from sklearn.multiclass import OneVsRestClassifier
from sklearn.pipeline import Pipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

TAXONOMY_COLS = [
    "issue_product_quality",
    "issue_delivery_shipping",
    "issue_packaging",
    "issue_product_performance",
    "issue_usability",
    "issue_pricing_value",
    "issue_durability",
    "issue_size_fit",
    "issue_returns_refunds",
    "issue_customer_support",
]


def validate_annotations(df: pd.DataFrame) -> pd.DataFrame:
    """Filter strictly annotated rows where values are explicitly 0 or 1, never treating blanks as 0."""
    logger.info(f"Total template rows: {len(df)}")

    annotated_rows = []
    for idx, row in df.iterrows():
        is_row_annotated = True
        # Check if all taxonomy columns have explicit 0 or 1
        for col in TAXONOMY_COLS:
            val = str(row[col]).strip()
            if val not in ["0", "1", "0.0", "1.0"]:
                is_row_annotated = False
                break
        if is_row_annotated:
            annotated_rows.append(idx)

    valid_subset = df.loc[annotated_rows].copy()
    logger.info(f"Explicitly annotated rows found: {len(valid_subset)} out of {len(df)}")
    return valid_subset


def main():
    template_path = Path("data/processed/issue_annotation_template.csv")
    if not template_path.exists():
        logger.error(f"Template not found at {template_path}")
        sys.exit(1)

    df = pd.read_csv(template_path)
    annotated_df = validate_annotations(df)

    if len(annotated_df) < 50:
        logger.warning(
            f"Insufficient manual annotations ({len(annotated_df)} completed). "
            "A minimum of 50 fully verified records is required to train a supervised issue model. "
            "The system continues to use the contextual heuristic issue detector."
        )
        print("\n" + "="*60)
        print("ISSUE CLASSIFIER ANNOTATION STATUS")
        print("="*60)
        print(f"Total Template Records:     {len(df)}")
        print(f"Verified Annotated Records: {len(annotated_df)}")
        print("Status:                     Pending manual annotations")
        print("Active Engine:              Contextual Multi-label Issue Pattern Matcher")
        print("="*60 + "\n")
        sys.exit(0)

    # If annotations exist, train OneVsRest multi-label pipeline
    logger.info(f"Training multi-label classifier on {len(annotated_df)} samples...")
    X = annotated_df["Summary"].fillna("").astype(str)
    Y = annotated_df[TAXONOMY_COLS].astype(int)

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(max_features=10000, ngram_range=(1, 2))),
        ("clf", OneVsRestClassifier(LogisticRegression(class_weight="balanced", max_iter=1000))),
    ])

    pipeline.fit(X, Y)
    save_path = Path("backend/saved_models/issue_classifier_supervised.joblib")
    save_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, save_path)
    logger.info(f"Saved supervised multi-label classifier to {save_path}")


if __name__ == "__main__":
    main()

