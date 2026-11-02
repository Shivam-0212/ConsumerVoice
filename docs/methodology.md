# ConsumerVoice: Scientific & Engineering Methodology

## 1. Problem Formulation & Task Definition

Customer feedback in e-commerce is characterized by high volume, class imbalance, informal colloquialisms, multi-aspect polarity, and lack of ground-truth operational metadata. Furthermore, modern generative AI systems deployed for customer support frequently generate unverified transactional promises (e.g., promising immediate refunds or delivery dates), creating acute legal and operational liabilities.

**ConsumerVoice** addresses this challenge through a multi-tier framework:
1. **Leakage-Safe Sentiment Classification**: Tri-class sentiment prediction (Negative, Neutral, Positive) trained on customer review summaries with strict train/val/test isolation.
2. **Transparent Explainability (XAI)**: Algebraic local token attribution providing auditability for every prediction.
3. **Multi-Label Aspect Issue Detection**: Contextual categorization across 10 defect categories with negation suppression.
4. **Citation-Backed Feedback Summarization**: Extractive sentence ranking linking findings back to immutable review IDs.
5. **Evidence-Based Hallucination Screening**: Fine-grained claim decomposition and tripartite factual verification (`SUPPORTED`, `CONTRADICTED`, `UNSUPPORTED`).

---

## 2. Dataset Preprocessing & Data Lineage

### 2.1 Raw Dataset Audit
- **Source**: Flipkart Product Customer Reviews Dataset (205,052 records).
- **Target Variable**: Original `Sentiment` column (Positive: 166,581, Negative: 28,232, Neutral: 10,239).
- **Primary Input Feature**: `Summary`. The original labels were derived from VADER analysis on `Summary`; hence, using `Summary` provides the true ground-truth correspondence.
- **Rating Isolation**: The `Rate` column is preserved for independent rating-sentiment audits and is strictly excluded from the classifier's feature space to prevent target leakage.

### 2.2 Hygiene & Integrity Protocols
1. **Malformed Rating Handling**: Identified and scrubbed 3 malformed records where product descriptions erroneously shifted into the rating column (e.g. `Pigeon Favourite Electric Kettle`, `Bajaj DX 2 L/W Dry Iron`, `Nova Plus Amaze NI 10`).
2. **Ambiguous Conflict Quarantine**: Found 966 distinct normalized summary strings associated with conflicting sentiment labels across 82,754 records. Rather than applying an arbitrary majority vote that injects label noise, all conflicting records were quarantined into `data/processed/ambiguous_labels.csv`.
3. **Deduplication for Benchmark Safety**: For identical normalized summaries with unanimous labels, 1 representative record was retained for the benchmark corpus (91,890 samples), preventing identical text from appearing across train and test partitions.
4. **Independent Stratified Partitioning**:
   - Training Set (80%): 73,512 records (Pos: 54,908, Neg: 14,662, Neu: 3,942)
   - Validation Set (10%): 9,189 records (Pos: 6,863, Neg: 1,833, Neu: 493)
   - Untouched Test Set (10%): 9,189 records (Pos: 6,864, Neg: 1,833, Neu: 492)

---

## 3. Sentiment Model Implementations

### 3.1 Model A: TF-IDF + Balanced Logistic Regression (Primary Baseline)
- **Feature Extraction**: `TfidfVectorizer` with:
  - $N$-gram range: $(1, 2)$
  - Max features: 40,000
  - Sublinear term frequency scaling: $\text{tf} = 1 + \log(\text{tf})$
  - Minimum document frequency: $\text{min\_df} = 2$
  - Custom stop word list retaining critical negation tokens (`not`, `no`, `never`, `nor`, `neither`, `without`, `barely`, `hardly`, etc.).
- **Classifier**: Multi-class Logistic Regression with L-BFGS solver, L2 regularization ($C=1.0$), and `class_weight='balanced'`. Balanced weights assign inverse class frequencies:
  $$w_c = \frac{N}{3 \times N_c}$$
  ensuring sensitivity to minority negative and neutral complaints.

### 3.2 Model B: DistilBERT Pretrained Transformer
- **Base Architecture**: `distilbert/distilbert-base-uncased` (6 transformer layers, 12 attention heads, 768 hidden dimensions, 66M parameters).
- **Classification Head**: Linear layer projecting `[CLS]` pooled embeddings to 3 logits corresponding to Negative (0), Neutral (1), and Positive (2).
- **Training Protocol**:
  - Max sequence length: 192 tokens
  - Optimizer: AdamW ($\text{lr} = 2 \times 10^{-5}$, weight decay = 0.01)
  - Epochs: 2–3 with early stopping patience of 1
  - Execution: Google Colab T4/A100 GPU notebook (`notebooks/ConsumerVoice_DistilBERT_Finetuning.ipynb`) and standalone script (`scripts/train_transformer.py`).

---

## 4. Explainable AI (XAI) Formulation

For the linear sentiment pipeline, local feature attribution is computed directly from model parameters without perturbation noise:

$$\text{Attribution}(w_i, y^*) = x_i \cdot \beta_{y^*, i}$$

Where:
- $y^*$ is the predicted class index.
- $x_i$ is the TF-IDF coordinate for token or bigram $w_i$ in the input text.
- $\beta_{y^*, i}$ is the learned weight vector coefficient for feature $i$ in class $y^*$.

Tokens with $\text{Attribution}(w_i, y^*) > 0$ serve as corroborating drivers for the prediction, while tokens with $\text{Attribution}(w_i, y^*) < 0$ represent opposing counter-evidence that lowered prediction confidence.

---

## 5. Multi-Label Contextual Issue Detection

The dataset does not contain manual issue labels. Rather than fabricating synthetic ground truth, a robust 10-category contextual rule matcher was engineered:

| Category | Typical Complaint Indicators | Negation Guards |
|---|---|---|
| **Product quality** | `poor quality`, `cheap plastic`, `defective finish`, `counterfeit` | `no quality issue`, `good quality` |
| **Delivery and shipping** | `delivery delayed`, `late shipping`, `slow courier`, `not on time` | `no delivery delay`, `fast delivery` |
| **Packaging** | `damaged packaging`, `broken box`, `torn package`, `crushed` | `secure packaging`, `intact box` |
| **Product performance** | `stopped working`, `overheating`, `poor battery backup`, `low cooling` | `works fine`, `no performance issue` |
| **Usability** | `hard to use`, `complicated setup`, `no manual`, `difficult to assemble` | `easy to use`, `simple setup` |
| **Pricing and value** | `overpriced`, `waste of money`, `not worth it`, `costly` | `value for money`, `reasonable price` |
| **Durability** | `broke after 2 days`, `cracked within a week`, `low durability` | `sturdy build`, `long lasting` |
| **Size and fit** | `size too small`, `tight fit`, `mismatched size`, `loose fit` | `perfect fit`, `fits well` |
| **Returns and refunds** | `refund not received`, `return rejected`, `unable to return` | `easy return`, `quick refund` |
| **Customer support** | `customer care rude`, `unhelpful support`, `no response from seller` | `helpful support`, `great service` |

---

## 6. Evidence-Based Hallucination Screening

The hallucination verification service decomposes AI-generated customer responses into atomic claims and verifies them against customer review feedback and confirmed organizational policies.

```
AI Response Text ──> [Sentence Splitting & Token Cleaning]
                            │
                            ├──> Non-factual Courtesy Phrases (Excluded)
                            │
                            └──> Atomic Factual Claims
                                       │
                                       ├──> Unverified Commitment Check (Refunds, Dates)
                                       ├──> Evidence Retrieval (Sentence Overlap / NLI)
                                       └──> Contradiction Audit (Semantic Polar Inversion)
                                                   │
                                                   ▼
                                     [SUPPORTED / CONTRADICTED / UNSUPPORTED]
```

### 6.1 Metric Formulations
1. **Claim Support Rate**:
   $$\text{CSR} = \frac{\text{Supported Claims}}{\text{Total Factual Claims}} \times 100$$
2. **Contradiction Rate**:
   $$\text{CR} = \frac{\text{Contradicted Claims}}{\text{Total Factual Claims}} \times 100$$
3. **Unsupported Claim Rate**:
   $$\text{UCR} = \frac{\text{Unsupported Claims}}{\text{Total Factual Claims}} \times 100$$
4. **Evidence Coverage**:
   $$\text{EC} = \frac{\text{Claims with Retrieved Evidence}}{\text{Total Factual Claims}} \times 100$$

