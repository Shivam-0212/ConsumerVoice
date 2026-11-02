#!/usr/bin/env python3
"""Sentiment Model Training Script for ConsumerVoice.

Trains a leakage-safe TF-IDF + Logistic Regression pipeline on
cleaned review summaries, conducts ablation on Summary+Review,
evaluates on untouched test split, and computes comprehensive metrics.
"""

import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict

import joblib
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.pipeline import Pipeline

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Preserve negation words in stop words
NEGATION_WORDS = {
    "not", "no", "never", "neither", "nor", "none", "hardly", "scarcely",
    "barely", "doesn", "doesn't", "don", "don't", "wasn", "wasn't", "weren",
    "weren't", "isn", "isn't", "aren", "aren't", "won", "won't", "wouldn",
    "wouldn't", "couldn", "couldn't", "can't", "cannot", "without", "against"
}
CUSTOM_STOP_WORDS = list(ENGLISH_STOP_WORDS.difference(NEGATION_WORDS))


def create_pipeline(max_features: int = 40000) -> Pipeline:
    """Build scikit-learn Pipeline with custom TF-IDF Vectorizer and Logistic Regression."""
    vectorizer = TfidfVectorizer(
        max_features=max_features,
        ngram_range=(1, 2),
        min_df=2,
        sublinear_tf=True,
        stop_words=CUSTOM_STOP_WORDS,
    )
    classifier = LogisticRegression(
        max_iter=2000,
        class_weight="balanced",
        random_state=42,
        C=1.0,
        solver="lbfgs",
    )
    return Pipeline([
        ("tfidf", vectorizer),
        ("clf", classifier),
    ])


def evaluate_model(
    model: Any,
    x_test: pd.Series,
    y_test: pd.Series,
    labels: list = ["negative", "neutral", "positive"],
) -> Dict[str, Any]:
    """Calculate comprehensive classification metrics, confusion matrix, and latency."""
    # Measure latency on test set
    start_time = time.time()
    y_pred = model.predict(x_test)
    total_latency = time.time() - start_time
    avg_latency_ms = (total_latency / len(x_test)) * 1000.0

    acc = float(accuracy_score(y_test, y_pred))
    macro_p = float(precision_score(y_test, y_pred, average="macro", zero_division=0))
    macro_r = float(recall_score(y_test, y_pred, average="macro", zero_division=0))
    macro_f1 = float(f1_score(y_test, y_pred, average="macro", zero_division=0))
    weighted_f1 = float(f1_score(y_test, y_pred, average="weighted", zero_division=0))

    per_class = {}
    report = classification_report(y_test, y_pred, labels=labels, output_dict=True, zero_division=0)
    for label in labels:
        if label in report:
            per_class[label] = {
                "precision": float(report[label]["precision"]),
                "recall": float(report[label]["recall"]),
                "f1_score": float(report[label]["f1-score"]),
                "support": int(report[label]["support"]),
            }

    cm = confusion_matrix(y_test, y_pred, labels=labels).tolist()

    return {
        "accuracy": acc,
        "macro_precision": macro_p,
        "macro_recall": macro_r,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "per_class": per_class,
        "confusion_matrix": {
            "labels": labels,
            "matrix": cm,
        },
        "test_sample_count": len(x_test),
        "inference_latency_ms_per_sample": round(avg_latency_ms, 3),
    }


def main():
    processed_dir = Path("data/processed")
    train_path = processed_dir / "sentiment_train.csv"
    val_path = processed_dir / "sentiment_validation.csv"
    test_path = processed_dir / "sentiment_test.csv"
    models_dir = Path("backend/saved_models")
    models_dir.mkdir(parents=True, exist_ok=True)

    if not train_path.exists() or not test_path.exists():
        logger.error(f"Prepared splits not found in {processed_dir}. Run scripts/prepare_dataset.py first.")
        sys.exit(1)

    logger.info("Loading train, validation and test splits...")
    df_train = pd.read_csv(train_path)
    df_val = pd.read_csv(val_path)
    df_test = pd.read_csv(test_path)

    # Primary text input: Summary (cleaned_summary / normalized_summary)
    x_train_summary = df_train["cleaned_summary"].fillna("")
    y_train = df_train["normalized_sentiment"]

    x_val_summary = df_val["cleaned_summary"].fillna("")
    y_val = df_val["normalized_sentiment"]

    x_test_summary = df_test["cleaned_summary"].fillna("")
    y_test = df_test["normalized_sentiment"]

    # 1. Majority class baseline (DummyClassifier)
    logger.info("Evaluating majority-class ZeroRule baseline...")
    dummy = DummyClassifier(strategy="most_frequent")
    dummy.fit(x_train_summary, y_train)
    dummy_metrics = evaluate_model(dummy, x_test_summary, y_test)

    # 2. Train Primary Baseline: TF-IDF + Logistic Regression on Summary
    logger.info("Training primary Logistic Regression baseline on Summary...")
    start_train = time.time()
    pipeline = create_pipeline(max_features=40000)
    pipeline.fit(x_train_summary, y_train)
    training_time_sec = float(time.time() - start_train)
    logger.info(f"Training completed in {training_time_sec:.2f} seconds.")

    # Primary model evaluation on untouched test set
    logger.info("Evaluating primary baseline on untouched test split...")
    baseline_metrics = evaluate_model(pipeline, x_test_summary, y_test)
    baseline_metrics["training_time_seconds"] = round(training_time_sec, 2)
    baseline_metrics["input_feature"] = "Summary"
    baseline_metrics["vocabulary_size"] = len(pipeline.named_steps["tfidf"].vocabulary_)

    # Validation evaluation for sanity check
    val_metrics = evaluate_model(pipeline, x_val_summary, y_val)

    # Save primary model
    model_save_path = models_dir / "sentiment_baseline.joblib"
    joblib.dump(pipeline, model_save_path)
    logger.info(f"Primary baseline model saved to {model_save_path}")

    # 3. Ablation Study: Summary + Review comparison
    logger.info("Training ablation model on Summary + Review...")
    x_train_combined = df_train["cleaned_combined"].fillna("")
    x_test_combined = df_test["cleaned_combined"].fillna("")

    ablation_pipe = create_pipeline(max_features=40000)
    ablation_pipe.fit(x_train_combined, y_train)
    ablation_metrics = evaluate_model(ablation_pipe, x_test_combined, y_test)
    ablation_metrics["input_feature"] = "Summary + Review"

    # Assemble comprehensive evaluation artifact
    evaluation_record = {
        "active_model": "sentiment_baseline",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "models": {
            "majority_class_baseline": {
                "name": "Majority-Class ZeroRule",
                "type": "dummy",
                "metrics": dummy_metrics,
            },
            "sentiment_baseline": {
                "name": "TF-IDF + Balanced Logistic Regression",
                "type": "scikit-learn",
                "status": "ready",
                "is_active": True,
                "input_field": "Summary",
                "test_metrics": baseline_metrics,
                "val_metrics": {
                    "accuracy": val_metrics["accuracy"],
                    "macro_f1": val_metrics["macro_f1"],
                    "weighted_f1": val_metrics["weighted_f1"],
                },
            },
            "transformer_distilbert": {
                "name": "DistilBERT (distilbert-base-uncased)",
                "type": "transformer",
                "status": "pending_gpu_training",
                "is_active": False,
                "checkpoint_path": "backend/saved_models/distilbert_sentiment",
                "note": "Train via Google Colab GPU notebook or scripts/train_transformer.py",
                "test_metrics": None,
            },
            "ablation_summary_plus_review": {
                "name": "TF-IDF + Logistic Regression (Summary + Review)",
                "type": "scikit-learn-ablation",
                "test_metrics": ablation_metrics,
            },
        },
        "target_classes": ["negative", "neutral", "positive"],
    }

    eval_file = models_dir / "model_evaluation.json"
    with open(eval_file, "w", encoding="utf-8") as f:
        json.dump(evaluation_record, f, indent=2)

    logger.info(f"Model evaluation saved to {eval_file}")

    print("\n" + "="*60)
    print("MODEL EVALUATION BENCHMARK ON UNTOUCHED TEST SPLIT")
    print("="*60)
    print(f"Majority Baseline Macro F1:    {dummy_metrics['macro_f1']:.4f} (Accuracy: {dummy_metrics['accuracy']:.4f})")
    print(f"Primary Baseline Macro F1:     {baseline_metrics['macro_f1']:.4f} (Accuracy: {baseline_metrics['accuracy']:.4f})")
    print(f"Primary Baseline Weighted F1:  {baseline_metrics['weighted_f1']:.4f}")
    print(f"Primary Baseline Macro Rec:    {baseline_metrics['macro_recall']:.4f}")
    print(f"Primary Baseline Macro Prec:   {baseline_metrics['macro_precision']:.4f}")
    print(f"Inference Latency per sample:  {baseline_metrics['inference_latency_ms_per_sample']} ms")
    print("-" * 60)
    print("Per-class performance (Primary Baseline):")
    for cls_name, vals in baseline_metrics["per_class"].items():
        print(f"  [{cls_name.upper():8s}] Prec: {vals['precision']:.4f} | Rec: {vals['recall']:.4f} | F1: {vals['f1_score']:.4f} | Support: {vals['support']:,}")
    print("-" * 60)
    print(f"Ablation (Summary + Review) Macro F1: {ablation_metrics['macro_f1']:.4f} (Accuracy: {ablation_metrics['accuracy']:.4f})")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()

