# Page 4: Model Performance Comparison

> **Route**: `/models`  
> **Purpose**: The scientific scorecard comparing our two AI architectures (Baseline Logistic Regression vs. Fine-Tuned DistilBERT) on an independent test dataset of 9,189 unseen reviews.

---

## 📌 What Is on This Page?

- **Model Overview Cards (Top)**:
  - **Model A (TF-IDF + Logistic Regression)**:
    - **Accuracy**: 84.8%
    - **Macro F1**: 0.692
    - **Weighted F1**: 0.869
    - **Highlights**: Extremely fast CPU inference (~0.01 ms / sample), uses 40,000 n-gram features with balanced class weights, offers fully transparent mathematical explanations ($x_i \cdot \beta_k$).
    - Has an **"Active Model"** badge showing it powers live inference.
  - **Model B (Fine-Tuned DistilBERT Transformer)**:
    - **Accuracy**: 91.4%
    - **Macro F1**: 0.758
    - **Weighted F1**: 0.915
    - **Highlights**: Fine-tuned on Google Colab T4 GPU over 3 epochs, deep contextual language understanding, achieves **+6.59% accuracy improvement** over baseline.

- **Independent Test Split Benchmark Table**:
  - Compares both models side-by-side across all key academic metrics on 9,189 held-out reviews:
    - **Overall Accuracy**: 84.83% vs 91.42% (**+6.59%**)
    - **Macro F1-Score**: 0.6925 vs 0.7584 (**+0.0659**)
    - **Weighted F1-Score**: 0.8686 vs 0.9155 (**+0.0469**)
    - **Macro Precision**: 0.6742 vs 0.7522 (**+0.0780**)
    - **Macro Recall**: 0.7552 vs 0.7650 (**+0.0098**)

- **Class-Wise Performance Breakdown**:
  - Performance split across each sentiment class:
    - **Negative Class** (1,833 samples): LogReg F1 0.8085 vs DistilBERT F1 0.8670.
    - **Neutral Class** (492 samples): LogReg F1 0.3469 vs DistilBERT F1 0.4462.
    - **Positive Class** (6,864 samples): LogReg F1 0.9220 vs DistilBERT F1 0.9621.

- **Key Academic Finding Callout Box**:
  - Highlights why *Neutral* is the most difficult class across both models (it represents only ~5% of real reviews and often contains subtle mixed praise and complaint statements).

- **"View Detailed Evaluation" Expandable Drawer (Bottom)**:
  - Click to view the full $3 \times 3$ classification confusion matrices and training environment details (Google Colab T4 GPU, PyTorch, Hugging Face Transformers).

---

## 🎮 What Can You Do on This Page?

- **Compare the numbers**:
  - Show your teammate that DistilBERT is the stronger NLP model (+6.59% accuracy gain), especially for understanding subtle, contextual language.
- **Explain the engineering trade-off**:
  - **Logistic Regression**: Best for real-time production speed, zero GPU cost, and 100% transparent word-by-word attribution.
  - **DistilBERT**: Best for raw semantic understanding and complex multi-sentence nuances.
- **Expand the Detailed Evaluation Drawer**:
  - Click the bottom bar to show the exact confusion matrices and hardware specifications used during model training.
