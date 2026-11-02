#!/usr/bin/env python3
"""Transformer Fine-tuning Script for ConsumerVoice (DistilBERT).

Fine-tunes distilbert-base-uncased on customer product review summaries
for 3-class sentiment classification (Negative=0, Neutral=1, Positive=2).
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

LABEL_MAP = {"negative": 0, "neutral": 1, "positive": 2}
INV_LABEL_MAP = {0: "negative", 1: "neutral", 2: "positive"}


def parse_args():
    parser = argparse.ArgumentParser(description="Fine-tune DistilBERT on ConsumerVoice dataset.")
    parser.add_argument("--train_path", type=str, default="data/processed/sentiment_train.csv")
    parser.add_argument("--val_path", type=str, default="data/processed/sentiment_validation.csv")
    parser.add_argument("--test_path", type=str, default="data/processed/sentiment_test.csv")
    parser.add_argument("--model_name", type=str, default="distilbert-base-uncased")
    parser.add_argument("--output_dir", type=str, default="backend/saved_models/distilbert_sentiment")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--learning_rate", type=float, default=2e-5)
    parser.add_argument("--max_length", type=int, default=192)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main():
    args = parse_args()
    logger.info("Initializing Transformer fine-tuning runner...")

    # Check for PyTorch and Transformers
    try:
        import torch
        from transformers import (
            AutoModelForSequenceClassification,
            AutoTokenizer,
            Trainer,
            TrainingArguments,
        )
        from datasets import Dataset
    except ImportError as e:
        logger.warning(
            f"Transformer dependencies missing ({e}). "
            "To train locally or on GPU, install torch, transformers, datasets, evaluate: "
            "pip install torch transformers datasets evaluate scikit-learn\n"
            "Or execute the provided Colab notebook: notebooks/ConsumerVoice_DistilBERT_Finetuning.ipynb"
        )
        sys.exit(0)

    # Check hardware
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    logger.info(f"Target compute device: {device}")
    if device == "cpu":
        logger.warning(
            "Fine-tuning a Transformer on CPU will take multiple hours. "
            "Recommended to use Google Colab GPU notebook: notebooks/ConsumerVoice_DistilBERT_Finetuning.ipynb"
        )

    import pandas as pd
    from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, confusion_matrix

    train_df = pd.read_csv(args.train_path)
    val_df = pd.read_csv(args.val_path)
    test_df = pd.read_csv(args.test_path)

    # Filter and encode labels
    for df in [train_df, val_df, test_df]:
        df["label"] = df["normalized_sentiment"].map(LABEL_MAP)
        df["text"] = df["cleaned_summary"].fillna("")

    tokenizer = AutoTokenizer.from_pretrained(args.model_name)

    def tokenize_func(examples):
        return tokenizer(examples["text"], padding="max_length", truncation=True, max_length=args.max_length)

    train_ds = Dataset.from_pandas(train_df[["text", "label"]]).map(tokenize_func, batched=True)
    val_ds = Dataset.from_pandas(val_df[["text", "label"]]).map(tokenize_func, batched=True)
    test_ds = Dataset.from_pandas(test_df[["text", "label"]]).map(tokenize_func, batched=True)

    model = AutoModelForSequenceClassification.from_pretrained(
        args.model_name,
        num_labels=3,
        id2label=INV_LABEL_MAP,
        label2id=LABEL_MAP,
    )

    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        preds = logits.argmax(axis=-1)
        acc = accuracy_score(labels, preds)
        macro_f1 = f1_score(labels, preds, average="macro", zero_division=0)
        weighted_f1 = f1_score(labels, preds, average="weighted", zero_division=0)
        return {"accuracy": acc, "macro_f1": macro_f1, "weighted_f1": weighted_f1}

    training_args = TrainingArguments(
        output_dir=os.path.join(args.output_dir, "checkpoints"),
        evaluation_strategy="epoch",
        save_strategy="epoch",
        learning_rate=args.learning_rate,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size * 2,
        num_train_epochs=args.epochs,
        weight_decay=0.01,
        load_best_model_at_end=True,
        metric_for_best_model="macro_f1",
        greater_is_better=True,
        seed=args.seed,
        logging_steps=50,
        save_total_limit=1,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        tokenizer=tokenizer,
        compute_metrics=compute_metrics,
    )

    logger.info("Starting training loop...")
    start_time = time.time()
    trainer.train()
    training_time = time.time() - start_time

    # Save final model
    os.makedirs(args.output_dir, exist_ok=True)
    model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)

    # Evaluate on untouched test set
    test_preds = trainer.predict(test_ds)
    y_test_pred = test_preds.predictions.argmax(axis=-1)
    y_test_true = test_df["label"].values

    test_metrics = {
        "accuracy": float(accuracy_score(y_test_true, y_test_pred)),
        "macro_precision": float(precision_score(y_test_true, y_test_pred, average="macro", zero_division=0)),
        "macro_recall": float(recall_score(y_test_true, y_test_pred, average="macro", zero_division=0)),
        "macro_f1": float(f1_score(y_test_true, y_test_pred, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(y_test_true, y_test_pred, average="weighted", zero_division=0)),
        "training_time_seconds": round(training_time, 2),
        "confusion_matrix": {
            "labels": ["negative", "neutral", "positive"],
            "matrix": confusion_matrix(y_test_true, y_test_pred).tolist(),
        },
    }

    # Update model_evaluation.json
    eval_path = Path("backend/saved_models/model_evaluation.json")
    if eval_path.exists():
        with open(eval_path, "r") as f:
            data = json.load(f)
        data["models"]["transformer_distilbert"]["status"] = "ready"
        data["models"]["transformer_distilbert"]["test_metrics"] = test_metrics
        with open(eval_path, "w") as f:
            json.dump(data, f, indent=2)

    logger.info(f"DistilBERT fine-tuning finished! Metrics: {test_metrics}")


if __name__ == "__main__":
    main()

