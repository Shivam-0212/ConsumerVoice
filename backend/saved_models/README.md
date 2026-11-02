# Saved Models Directory

This directory stores evaluation metrics and trained machine learning artifacts for ConsumerVoice.

## Model Evaluation Results (Committed Artifacts)

The genuine empirical evaluation metrics evaluated on the 9,189 independent test records are preserved in Git:
- **`model_evaluation.json`**: Benchmark metrics, class-wise precision/recall/F1, and confusion matrices for both the Logistic Regression baseline and the fine-tuned DistilBERT transformer.
- **`transformer_test_metrics.json`**: Detailed test loss, accuracy, macro/weighted F1, and evaluation runtime statistics for the DistilBERT model.

## Model Artifact Exclusions

Individual model weights (such as `model.safetensors`, approx. 268 MB, and `sentiment_baseline.joblib`) exceed standard GitHub individual file limitations and are excluded via `.gitignore`.

## How to Generate or Restore Trained Model Artifacts

### 1. Primary Sentiment Baseline (TF-IDF + Logistic Regression)

To train and generate the scikit-learn pipeline artifact (`sentiment_baseline.joblib`):
```bash
python scripts/train_sentiment.py
```
This trains a multi-class Logistic Regression model with sublinear TF-IDF feature extraction ($N$-gram range 1–2, 10,000 max features) and writes `backend/saved_models/sentiment_baseline.joblib`.

### 2. Deep Transformer (Fine-Tuned DistilBERT)

The transformer model is a fine-tuned `distilbert-base-uncased` classifier trained for 3 epochs with AdamW optimization, linear learning rate warm-up, and Cross-Entropy loss.

You can reproduce or restore the model in two ways:

- **Via Google Colab (Recommended for GPU Acceleration):**
  1. Open the included notebook: `notebooks/ConsumerVoice_DistilBERT_Finetuning.ipynb`.
  2. Upload `data/processed/sentiment_train.csv` and `data/processed/sentiment_validation.csv`.
  3. Execute training on a T4 GPU (~15 minutes).
  4. Download the exported `distilbert_sentiment` directory and extract it into:
     ```text
     backend/saved_models/distilbert_sentiment/
     ```
     Ensure it contains:
     - `config.json`
     - `model.safetensors` (~268 MB)
     - `tokenizer.json`
     - `tokenizer_config.json`

- **Via Local PyTorch Script (GPU or CPU):**
  ```bash
  python scripts/train_transformer.py
  ```

