# Raw Dataset Instructions

## Dataset Overview

ConsumerVoice is evaluated and benchmarked on the real-world **Flipkart Product Customer Reviews Dataset**.

- **Dataset Name:** Flipkart Product Customer Reviews
- **Expected Filename:** `Dataset-SA.csv`
- **File Format:** CSV (Comma-Separated Values)
- **Original Size:** ~205,052 records (~33.4 MB)
- **Source:** Kaggle (Flipkart Customer Sentiment Dataset)

## Where to Obtain

You can acquire the dataset from Kaggle:
- **Search Query:** `Flipkart Product Customer Reviews Dataset` or `Kaggle Flipkart sentiment reviews`
- **Kaggle Dataset Identifier:** `nirali-p/flipkart-product-customer-reviews` or equivalent standard Flipkart customer review corpus.

## Setup Instructions

1. Download the raw CSV archive from Kaggle.
2. Ensure the file is named exactly:
   ```text
   Dataset-SA.csv
   ```
3. Place the file directly in this folder:
   ```text
   data/raw/Dataset-SA.csv
   ```

## Next Step: Data Preprocessing

Once `Dataset-SA.csv` is placed here, run the reproducible automated preprocessing pipeline from the repository root:

```bash
python scripts/prepare_dataset.py
```

This pipeline will:
1. Parse ratings (`1.0` - `5.0`), impute or clean nulls, and drop duplicate review records.
2. Map ratings to 3 sentiment classes:
   - Ratings 1 & 2 $\rightarrow$ **Negative** (`0`)
   - Rating 3 $\rightarrow$ **Neutral** (`1`)
   - Ratings 4 & 5 $\rightarrow$ **Positive** (`2`)
3. Flag sentiment-rating text polarity contradictions and isolate them to `data/processed/ambiguous_labels.csv`.
4. Create stratified 80% train, 10% validation, and 10% test splits in `data/processed/`.
5. Generate `data/processed/data_quality_report.json`.

