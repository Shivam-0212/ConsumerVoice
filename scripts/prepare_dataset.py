#!/usr/bin/env python3
"""Dataset Preparation Script for ConsumerVoice.

Performs data audit, text cleaning, duplicate & conflict handling,
and generates stratified splits.
"""

import logging
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.services.data_preprocessing import DataPreprocessor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main():
    raw_path = "data/raw/Dataset-SA.csv"
    if not Path(raw_path).exists():
        logger.error(f"Raw dataset not found at {raw_path}!")
        sys.exit(1)

    logger.info("Starting ConsumerVoice data preparation pipeline...")
    preprocessor = DataPreprocessor(raw_csv_path=raw_path, output_dir="data/processed")
    train_df, val_df, test_df, full_df, audit = preprocessor.process_and_split(random_state=42)

    print("\n" + "="*60)
    print("CONSUMERVOICE DATA QUALITY & PREPROCESSING REPORT")
    print("="*60)
    print(f"Total Raw Records:                {audit['total_records']:,}")
    print(f"Exact Duplicate Rows:             {audit['exact_duplicate_rows']:,}")
    print(f"Missing Values:                   {audit['missing_values']}")
    print(f"Malformed Ratings Detected:       {audit['malformed_rate_count']}")
    print(f"Distinct Raw Summaries:           {audit['raw_distinct_summaries']:,}")
    print(f"Conflicting Summary Groups:       {audit['conflicting_summary_groups_count']:,} ({audit['conflicting_rows_count']:,} rows)")
    print(f"Deduplicated Benchmark Records:   {audit['benchmark_deduplicated_rows']:,}")
    print("-" * 60)
    print(f"Train Split (80%):                {len(train_df):,} {audit['splits']['train_distribution']}")
    print(f"Val Split (10%):                  {len(val_df):,} {audit['splits']['val_distribution']}")
    print(f"Test Split (10%):                 {len(test_df):,} {audit['splits']['test_distribution']}")
    print("=" * 60)
    print("Outputs generated:")
    print(" - data/processed/cleaned_reviews.csv")
    print(" - data/processed/sentiment_train.csv")
    print(" - data/processed/sentiment_validation.csv")
    print(" - data/processed/sentiment_test.csv")
    print(" - data/processed/ambiguous_labels.csv")
    print(" - data/processed/data_quality_report.json")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()

