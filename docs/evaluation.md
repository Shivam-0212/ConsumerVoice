# ConsumerVoice: Experimental Evaluation & Model Benchmark

## 1. Experimental Setup

- **Test Partition**: 9,189 unseen Flipkart customer feedback records (stratified: 6,864 Positive, 1,833 Negative, 492 Neutral).
- **Random Seed**: 42.
- **Evaluation Criteria**: Because the dataset possesses severe class imbalance (74.7% Positive in the deduplicated test set), **Macro F1** is utilized as the primary ranking metric, ensuring equal importance across positive, neutral, and negative customer experiences.

---

## 2. Quantitative Benchmark Results

All figures reported below were measured directly on the independent test set (9,189 records):

| Model Architecture | Input Field | Macro F1 (Primary) | Accuracy | Weighted F1 | Macro Precision | Macro Recall | Inference Latency |
|---|---|---|---|---|---|---|---|
| **Majority Baseline (ZeroRule)** | None | **0.2851** | 0.7470 | 0.6389 | 0.2490 | 0.3333 | < 0.001 ms |
| **TF-IDF + Balanced LogReg (Baseline)** | `Summary` | **0.6925** | **0.8483** | **0.8686** | **0.6742** | **0.7552** | **0.008 ms (CPU)** |
| **Ablation: TF-IDF + LogReg** | `Summary + Review` | **0.7110** | 0.8679 | 0.8752 | 0.7021 | 0.7480 | 0.015 ms (CPU) |
| **DistilBERT (Fine-Tuned Transformer)** | `Summary` | **0.7584** | **0.9142** | **0.9155** | **0.7522** | **0.7650** | **0.703 ms (T4) / 11 ms (CPU)** |

---

## 3. Class-Wise Performance Comparison

Evaluating performance across individual classes reveals how DistilBERT improves over the linear baseline:

### 3.1 Fine-Tuned DistilBERT Transformer (Active)
| Class | Precision | Recall | F1-Score | Support (Test Set) |
|---|---|---|---|---|
| **Negative** | 0.8595 | 0.8745 | **0.8670** | 1,833 |
| **Neutral** | 0.4302 | 0.4634 | **0.4462** | 492 |
| **Positive** | 0.9670 | 0.9572 | **0.9621** | 6,864 |
| **Macro Average** | **0.7522** | **0.7650** | **0.7584** | 9,189 |
| **Weighted Average** | **0.9168** | **0.9142** | **0.9155** | 9,189 |

### 3.2 TF-IDF + Balanced Logistic Regression (Baseline)
| Class | Precision | Recall | F1-Score | Support (Test Set) |
|---|---|---|---|---|
| **Negative** | 0.8016 | 0.8156 | **0.8085** | 1,833 |
| **Neutral** | 0.2487 | 0.5732 | **0.3469** | 492 |
| **Positive** | 0.9722 | 0.8767 | **0.9220** | 6,864 |
| **Macro Average** | **0.6742** | **0.7552** | **0.6925** | 9,189 |
| **Weighted Average** | **0.8998** | **0.8483** | **0.8686** | 9,189 |

### Key Improvements of DistilBERT:
1. **Defect Detection (Negative)**: F1 increased from **0.8085** to **0.8670** (+5.85 points), with precision jumping from 80.2% to 86.0%.
2. **Neutral Disambiguation**: Neutral F1 jumped from **0.3469** to **0.4462** (+9.93 points), with precision nearly doubling from 24.9% to 43.0%.
3. **Overall Accuracy**: Accuracy improved from **84.83%** to **91.42%** (+6.59 percentage points).

---

## 4. Confusion Matrix Analysis (Independent Test Split)

### DistilBERT Confusion Matrix (9,189 samples):
```
                  Predicted Negative   Predicted Neutral   Predicted Positive
Actual Negative          1,603                147                  83
Actual Neutral            123                 228                 141
Actual Positive           139                 155                6,570
```
- **True Negatives correctly classified**: 1,603 / 1,833 (87.5%)
- **True Neutrals correctly classified**: 228 / 492 (46.3%)
- **True Positives correctly classified**: 6,570 / 6,864 (95.7%)

### Logistic Regression Baseline Confusion Matrix:
```
                  Predicted Negative   Predicted Neutral   Predicted Positive
Actual Negative          1,495                262                  76
Actual Neutral            114                 282                  96
Actual Positive           256                 590                6,018
```

---

## 5. Hardware & Resource Profile (MacBook Air M2, 8 GB RAM)

- **Storage on Disk**: 267.8 MB (`model.safetensors` + `tokenizer.json`).
- **Memory Footprint**: ~578 MB RAM total process footprint.
- **CPU Inference Latency**:
  - Single sample: **11.02 ms**
  - Batch of 16 samples: **72.63 ms** (4.54 ms per sample)
- **Zero GPU Requirement**: Runs smoothly on local Apple Silicon CPU with low memory utilization.
