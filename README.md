# ConsumerVoice: An Explainable, Hallucination-Aware Framework for Customer Feedback NLP

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-1.0.0-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3-61dafb.svg)](https://react.dev/)
[![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-3.4-38bdf8.svg)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**ConsumerVoice** is an enterprise-grade AI and Natural Language Processing platform designed to process unstructured e-commerce customer reviews, classify fine-grained product defects across 10 taxonomy categories, provide token-level prediction explanations, and verify AI-generated customer responses against source evidence to eliminate transactional hallucinations.

---

## 1. Key Capabilities

1. **Dual Sentiment Classification Engines**:
   - High-throughput TF-IDF + Balanced Logistic Regression baseline (**Macro F1: 0.6925**, **Accuracy: 84.83%**, latency: **0.008 ms/sample**).
   - Fine-tuned DistilBERT transformer (**Macro F1: 0.7584**, **Accuracy: 91.42%**, **Weighted F1: 0.9155**) trained with PyTorch, Hugging Face Transformers, and AdamW optimization.
2. **Local Feature Explainability (XAI)**:
   - Algebraic linear token attribution ($\text{TF-IDF} \times \beta$) highlighting positive supporting phrases and negative counter-evidence.
   - Transparent attribution notices for deep multi-head self-attention models.
3. **Multi-Label Contextual Issue Detection**:
   - Defect categorization across 10 taxonomy categories (Product quality, Delivery and shipping, Packaging, Product performance, Usability, Pricing and value, Durability, Size and fit, Returns and refunds, Customer support).
   - Contextual contrastive clause splitting and category-specific negation guards preventing false positive complaints (e.g., *"not delayed"* suppresses delivery issues while preserving customer support complaints in compound sentences).
4. **Citation-Backed Feedback Summarization**:
   - Extractive sentence ranking using TF-IDF centroid similarity retaining immutable review citations (`REV_000001`).
   - Optional Gemini abstractive mode powered by the official `google-genai` SDK.
5. **Grounded Customer Support Response Generation**:
   - Synthesizes professional support responses with anti-hallucination guardrails prohibiting fabricated refunds or unverified delivery dates.
6. **Evidence-Based Hallucination Screening**:
   - Decomposes AI responses into atomic factual claims, filters generic courtesy, and evaluates claims against customer feedback and corporate policies.
   - Classifies claims into `SUPPORTED`, `CONTRADICTED`, and `UNSUPPORTED`.
   - Computes Claim Support Rate, Unsupported Claim Rate, Contradiction Rate, and Evidence Coverage.
7. **SaaS Analytics Web Application**:
   - 4 primary focused pages: **Dashboard**, **Review Explorer**, **Analyze Feedback**, and **Model Comparison**.
   - Built with React 18, Vite, Tailwind CSS, Lucide icons, and Recharts.
   - Database of 50,000 real Flipkart reviews persisted locally in SQLite.

---

## 2. Technology Stack

- **Backend**: Python 3.11, FastAPI, Pydantic v2, SQLAlchemy, Uvicorn, Pandas, Scikit-learn, PyTorch, Hugging Face Transformers, Joblib, `google-genai`, Pytest.
- **Frontend**: React 18, Vite 6, Tailwind CSS, React Router v6, Axios, Recharts, Lucide React.
- **Persistence**: SQLite (`backend/consumervoice.db`).
- **Target Hardware**: macOS / Linux / Windows (designed to run efficiently on commodity CPUs without mandatory local GPUs).

---

## 3. Dataset Lineage & Preprocessing Integrity

ConsumerVoice uses the real-world **Flipkart Product Customer Reviews Dataset** (`data/raw/Dataset-SA.csv`):
- **Total Records**: 205,052 customer reviews across 6 original columns.
- **Target Feature**: `Summary` is the primary input feature to mirror the ground-truth labeling process. `Rate` is strictly excluded from training to prevent target leakage.
- **Data Hygiene Audit**:
  - Removed 34,375 exact duplicate rows.
  - Scrubbed malformed ratings and missing values.
  - Isolated 966 contradictory normalized summaries across 82,754 rows into `data/processed/ambiguous_labels.csv`.
- **Deduplicated Benchmark Records**: 91,890 unique, leakage-safe records.
- **Stratified Partitioning (Seed 42)**:
  - **Train (80%)**: 73,512 records
  - **Validation (10%)**: 9,189 records
  - **Untouched Test (10%)**: 9,189 records

> **Note on Dataset Exclusions:** In compliance with repository storage limits, raw and processed CSV files are excluded from Git. See [`data/raw/README.md`](data/raw/README.md) and [`data/processed/README.md`](data/processed/README.md) for download links and reproducible generation commands.

---

## 4. Model Benchmark Evaluation (Untouched Test Set)

All metrics were evaluated directly on the independent 9,189 test instances:

| Model | Architecture / Backbone | Macro F1 | Accuracy | Weighted F1 | Latency / Throughput | Status |
|---|---|---|---|---|---|---|
| **Majority Baseline (ZeroRule)** | Constant Positive Class | **0.2851** | 74.70% | 0.6389 | < 0.001 ms | Benchmark Reference |
| **TF-IDF + Balanced LogReg** | Scikit-learn Logistic Regression | **0.6925** | **84.83%** | **0.8686** | **0.008 ms/sample** | Production Baseline |
| **Fine-Tuned DistilBERT** | `distilbert-base-uncased` (6 layers, 12 heads) | **0.7584** | **91.42%** | **0.9155** | **~12 ms/sample** | Deep Transformer Model |

> **Evaluation Metrics:** Empirical metric JSON files ([`model_evaluation.json`](backend/saved_models/model_evaluation.json) and [`transformer_test_metrics.json`](backend/saved_models/transformer_test_metrics.json)) are tracked in Git. Large weight files (`model.safetensors` ~268 MB) are excluded. See [`backend/saved_models/README.md`](backend/saved_models/README.md) for model restoration instructions.

---

## 5. Quick Start Instructions (macOS / Linux)

### 5.1 One-Click Launch
To set up dependencies, prepare data splits, initialize the database, and launch both backend and frontend:
```bash
./start.sh
```

The application will launch at:
- **Frontend Dashboard**: [http://localhost:5173](http://localhost:5173)
- **FastAPI Backend**: [http://localhost:8000](http://localhost:8000)
- **Interactive OpenAPI Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)

To stop all background services safely:
```bash
./stop.sh
```

---

### 5.2 Manual Step-by-Step Execution

#### Step 1: Create Virtual Environment & Install Dependencies
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cd frontend && npm install && cd ..
```

#### Step 2: Prepare Dataset & Generate Splits
1. Place the Flipkart `Dataset-SA.csv` into `data/raw/` (see [`data/raw/README.md`](data/raw/README.md)).
2. Execute the preprocessing pipeline:
```bash
python scripts/prepare_dataset.py
```

#### Step 3: Train Sentiment Models & Initialize Database
```bash
python scripts/train_sentiment.py
python scripts/initialize_database.py
```

#### Step 4: Run Automated Tests
```bash
pytest backend/tests/ -v
cd frontend && npm run build && cd ..
```

#### Step 5: Start Application Services
In terminal 1 (Backend):
```bash
uvicorn backend.app.main:app --port 8000 --reload
```
In terminal 2 (Frontend):
```bash
cd frontend && npm run dev
```

---

## 6. Live Demonstration Scenario

Navigate to **Analyze Feedback** (`/analyze`) and test the multi-task pipeline:

**Customer Feedback**:
> *"The product quality is good, but the delivery was delayed by five days and the packaging was damaged."*

**System Response**:
1. **Sentiment Prediction**:
   - **Logistic Regression**: Classified as `Negative` (p = 0.992) with token attribution explaining $\beta_{\text{quality}} > 0$ vs. negative penalties for $\text{delayed}$ and $\text{damaged}$.
   - **Fine-Tuned DistilBERT**: Classified as `Negative` (p = 0.997) with contextual self-attention layers.
2. **Multi-Aspect Issues Detected**:
   - Product quality $\rightarrow$ `Positive Aspect` (Evidence: *"quality is good"*)
   - Delivery and shipping $\rightarrow$ `Issue Detected` (Evidence: *"delivery was delayed"*)
   - Packaging $\rightarrow$ `Issue Detected` (Evidence: *"packaging was damaged"*)
3. **Claim-Level Hallucination Screening**:
   - *"We acknowledge that your delivery was delayed by five days."* $\rightarrow$ **SUPPORTED**
   - *"Your product was delivered on time without any delay."* $\rightarrow$ **CONTRADICTED**
   - *"We have processed your refund of Rs. 2,000."* $\rightarrow$ **UNSUPPORTED** (Fabricated transactional commitment)
   - *"Your replacement will arrive tomorrow."* $\rightarrow$ **UNSUPPORTED** (Fabricated delivery date promise)

---

## 7. Repository Structure

```text
ConsumerVoice_GitHub/
├── backend/
│   ├── app/
│   │   ├── api/routes/          # REST endpoints (reviews, dashboard, summaries, etc.)
│   │   ├── core/config.py       # Pydantic & environment settings
│   │   ├── database/session.py  # SQLAlchemy engine & session
│   │   ├── models/entities.py   # SQLAlchemy ORM models
│   │   ├── schemas/domain.py    # Pydantic validation schemas
│   │   ├── services/
│   │   │   ├── data_preprocessing.py   # Cleaning, deduplication, conflict isolation
│   │   │   ├── sentiment_service.py    # Production inference & model switching
│   │   │   ├── explainability.py       # TF-IDF linear feature attribution
│   │   │   ├── issue_detection.py      # 10-category contextual rule matcher
│   │   │   ├── summarization.py        # TF-IDF extractive & Gemini abstractive
│   │   │   ├── response_generation.py  # Grounded safe support responses
│   │   │   └── hallucination_detector.py # Atomic claim evidence screening
│   │   └── main.py              # FastAPI application entrypoint
│   ├── saved_models/
│   │   ├── model_evaluation.json       # Genuine test set evaluation metrics
│   │   ├── transformer_test_metrics.json # DistilBERT benchmark metrics
│   │   └── README.md                   # Model weight restoration instructions
│   ├── tests/                   # 22 automated pytest unit and integration tests
│   └── requirements.txt
├── frontend/
│   ├── public/                  # Static assets
│   ├── src/
│   │   ├── components/          # Sidebar, Navbar, Layout
│   │   ├── pages/               # 4 primary pages (Dashboard, Explorer, Analyze, Models)
│   │   ├── services/api.js      # Axios client
│   │   ├── utils/               # Formatting and UI helpers
│   │   ├── App.jsx              # React Router definitions
│   │   └── main.jsx
│   ├── package.json
│   ├── package-lock.json
│   └── vite.config.js
├── data/
│   ├── raw/
│   │   └── README.md            # Raw Flipkart dataset acquisition guide
│   └── processed/
│       └── README.md            # Processed split generation guide
├── scripts/
│   ├── prepare_dataset.py       # Dataset audit & split generation
│   ├── train_sentiment.py       # Baseline model training & ablation
│   ├── train_transformer.py     # DistilBERT sequence classifier training script
│   ├── train_issue_classifier.py# Multi-label issue training pipeline
│   ├── initialize_database.py   # SQLite database seeding
│   ├── qa_browser_audit.py      # Browser QA validation script
│   └── verify_analyze_feedback.py # Dedicated Analyze Feedback browser test
├── notebooks/
│   └── ConsumerVoice_DistilBERT_Finetuning.ipynb # Google Colab GPU notebook
├── docs/
│   ├── architecture.md          # Architecture specification with Mermaid diagram
│   ├── methodology.md           # NLP algorithms, XAI, and verification logic
│   └── evaluation.md            # Experimental benchmark results & confusion matrix
├── .env.example
├── .gitignore
├── conftest.py
├── start.sh                     # Automated startup script
├── stop.sh                      # Clean shutdown script
└── README.md
```

---

## 8. Limitations & Scope

1. **Temporal Scope**: The Flipkart dataset lacks timestamp metadata; temporal trend forecasting is not supported.
2. **Neutral Class Density**: Neutral feedback accounts for only 4.9% of the dataset, resulting in lower neutral F1 (0.446) compared to positive (0.957) and negative (0.875).
3. **Evidence-Based Screening**: The hallucination detector audits claims against explicit source feedback and provided policies. It does not certify external real-world physical facts not documented in the premise texts.
