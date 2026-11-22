# ConsumerVoice: An Explainable, Hallucination-Aware Framework for Customer Feedback NLP

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-1.0.0-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3-61dafb.svg)](https://react.dev/)
[![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-3.4-38bdf8.svg)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**ConsumerVoice** is an enterprise-grade AI and Natural Language Processing platform designed to process unstructured e-commerce customer reviews, classify fine-grained product defects across 10 taxonomy categories, provide token-level prediction explanations, and verify AI-generated customer responses against source evidence to eliminate transactional hallucinations.

---

## 🚀 Production Deployment Architecture

ConsumerVoice is designed for a decoupled cloud deployment using **Vercel** for frontend static delivery and **Render** for backend API services:

| Component | Platform | Role | Target URL / Placeholder | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Frontend Web Application** | **Vercel** | React 18 + Vite SPA | `https://<your-project>.vercel.app` | *Configured for deployment* |
| **Backend API Service** | **Render** | FastAPI + Uvicorn ASGI | `https://<your-service>.onrender.com` | *Configured for deployment* |
| **Interactive API Docs** | **Render** | Swagger / OpenAPI UI | `https://<your-service>.onrender.com/docs` | *Configured for deployment* |
| **Health Check Endpoint** | **Render** | System diagnostic probe | `https://<your-service>.onrender.com/api/health` | *Configured for deployment* |

### Architecture Overview

```mermaid
flowchart LR
    Browser["User Browser"]
    VercelEdge["Vercel Edge Network\n(React 18 + Vite SPA)"]
    RenderBackend["Render Web Service\n(FastAPI + Uvicorn)"]
    GHRelease["GitHub Release v1.0.0\n(sentiment_baseline.joblib)"]
    SQLite["SQLite Database\n(Seeded from seed_sample.json)"]

    Browser -->|1. Load SPA UI| VercelEdge
    Browser -->|2. API Requests /api/*| VercelEdge
    VercelEdge -->|3. Reverse Proxy (frontend/vercel.json)| RenderBackend
    RenderBackend -->|4. CORS headers allow *.vercel.app| Browser
    RenderBackend -->|5. Query Reviews & Insights| SQLite
    RenderBackend -.->|6. Auto-download on boot| GHRelease
```

- **Frontend Hosting (Vercel)**: Deploys from `frontend/` as a static SPA bundle. Because the Vercel project's Root Directory is set to `frontend`, Vercel reads `frontend/vercel.json`, which applies client-side SPA routing (`/(.*) -> /index.html`) and an automated reverse proxy forwarding `/api/:path*` to the Render backend service. (A matching `vercel.json` is also placed at the repository root to support deployments configured without a custom root directory).
- **Backend Hosting (Render)**: Deploys from the repository root via `./render_build.sh` and `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`. Binds dynamically to `0.0.0.0:$PORT` with native CORS middleware configured to authorize requests from all `https://*.vercel.app` origins.
- **Production ML Baseline (Live Inference)**: High-throughput TF-IDF + Balanced Logistic Regression model (`sentiment_baseline.joblib`, 2.7 MB, ~15 MB RAM, sub-1ms CPU latency) serving live sentiment predictions, calibrated probabilities, and linear feature attribution.
- **DistilBERT Offline Evaluation**: Fine-tuned DistilBERT weights (~268 MB) require > 550 MB RAM, exceeding the 512 MB physical ceiling of Render Free Tier (which triggers Linux Out-Of-Memory exit code 137). In compliance with architectural specifications, live transformer inference is omitted on lightweight free-tier cloud instances while empirical benchmark results (91.42% accuracy, 0.7584 Macro F1) are verified and displayed in the Model Comparison dashboard. Live transformer serving is supported on dedicated GPU or 1GB+ RAM instances.
- **Database Initialization**: On startup, if no external database asset is provided, `scripts/download_production_assets.py` automatically initializes and seeds `backend/consumervoice.db` in **~200 ms** using the committed `data/seed_sample.json` (200 authentic Flipkart reviews covering all defect categories).
- **Ephemeral Storage on Render Free**: Container storage on Render Free tier is ephemeral and resets on container sleep or redeployment. Any ad-hoc prediction history generated during a session resets cleanly upon container reboot, while the core review corpus is re-seeded automatically on boot.

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
   - Database of authentic Flipkart customer reviews persisted in SQLite (seeded with 200 benchmark reviews for lightweight cloud deployment; expandable to 50,000 locally).

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

## 6. Cloud Deployment Guide (Vercel & Render)

ConsumerVoice is fully configured for free-tier cloud deployment using **Vercel** for frontend hosting and **Render** for the backend API (subject to platform free-tier quotas and resource limits).

### 6.1 Pre-Deployment: Release v1.0.0 Model Asset Setup
The backend's cloud bootstrap script (`scripts/download_production_assets.py`) automatically retrieves the production model weights (`sentiment_baseline.joblib`, 2.7 MB) from GitHub Release `v1.0.0` during build and container boot.

> **Important Note:** Release `v1.0.0` does not exist by default on a newly initialized repository. Before deploying to Render, create Release `v1.0.0` and attach `sentiment_baseline.joblib` using the GitHub CLI or GitHub web interface:

```bash
# Publish Release v1.0.0 with the baseline model weights
# (Run from project root /Users/shivamrai/Desktop/ConsumerVoice):
gh release create v1.0.0 \
  ConsumerVoice_Private/trained_models/sentiment_baseline.joblib \
  --repo Shivam-0212/ConsumerVoice \
  --title "ConsumerVoice v1.0.0 Baseline Model" \
  --notes "Production TF-IDF + Logistic Regression baseline weights (sentiment_baseline.joblib)."
```
*(Alternatively, if running from inside `ConsumerVoice_GitHub`, pass `backend/saved_models/sentiment_baseline.joblib`).*

*(If this asset is not uploaded, the backend will still boot and serve API requests using the embedded 200-review seed database, but live sentiment analysis will return neutral prior probabilities with a configuration notice until the asset is attached).*

---

### 6.2 Backend Deployment on Render

1. Create a **New Web Service** on [Render](https://dashboard.render.com).
2. Connect your GitHub repository (`Shivam-0212/ConsumerVoice`).
3. Configure service parameters:
   - **Name**: `consumervoice-api` (or preferred service name)
   - **Region**: Any (e.g., *Oregon, US-West* or *Frankfurt, EU*)
   - **Branch**: `main`
   - **Root Directory**: *(leave blank — repository root)*
   - **Runtime**: `Python 3`
   - **Build Command**: `./render_build.sh`
   - **Start Command**: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: `Free`
4. Expand **Advanced** and set:
   - **Health Check Path**: `/api/health`
5. Under **Environment Variables**, add:
   - `ENVIRONMENT`: `production` *(Recommended: enables production optimizations)*
   - `DATABASE_URL`: `sqlite:///backend/consumervoice.db` *(Optional: the backend automatically defaults to `sqlite:///<ROOT_DIR>/backend/consumervoice.db` if unset)*
   - `DATABASE_ASSET_URL`: *(Optional: URL to an external compressed `.db.gz` database. If omitted, the service immediately seeds from `data/seed_sample.json` without attempting remote downloads)*
   - `GEMINI_API_KEY`: *(Optional: your Google Gemini API key for abstractive support response generation; if omitted, the system falls back to the built-in template response generator)*
6. Click **Create Web Service**.

---

### 6.3 Frontend Deployment on Vercel

1. Create a **New Project** on [Vercel](https://vercel.com).
2. Import the `ConsumerVoice` GitHub repository.
3. Configure build settings:
   - **Framework Preset**: `Vite`
   - **Root Directory**: Click **Edit** and choose `frontend` *(Vercel will detect `frontend/vercel.json` for SPA routing and API proxying)*
   - **Build Command**: `npm run build` *(default)*
   - **Output Directory**: `dist` *(default)*
   - **Install Command**: `npm install` *(default)*
4. Under **Environment Variables**, add:
   - `VITE_API_BASE_URL`: `https://<your-render-service>.onrender.com/api`
     *(Configures the frontend API client with your actual Render backend endpoint; trailing slashes are stripped automatically. If omitted, the client defaults to `/api`, which is proxied by `frontend/vercel.json`'s rewrite rule).*
5. Click **Deploy**.

---

### 6.4 Production Runtime Behavior

- **Database Auto-Seeding**: Render free containers operate on an ephemeral filesystem. On container startup, `scripts/download_production_assets.py` checks for `backend/consumervoice.db`. When `DATABASE_ASSET_URL` is omitted, it immediately initializes and seeds 200 authentic Flipkart benchmark reviews from `data/seed_sample.json` in **~200 ms** with zero remote download delay.
- **Ephemeral Session Persistence**: Ad-hoc query logs and visitor-generated summaries persist while the container is awake. If the container sleeps after 15 minutes of inactivity or restarts on redeployment, session history resets to the clean 200-review benchmark state.
- **Model Execution Distinction**:
  - **Baseline Model (Live Serving)**: The TF-IDF + Balanced Logistic Regression pipeline executes directly in memory on Render Free (~15 MB RAM, sub-1ms CPU latency). It powers live sentiment classification, confidence scores, 3-class probability meters, and algebraic linear feature attributions ($\text{TF-IDF} \times \beta$) for positive and negative token contributors.
  - **DistilBERT Transformer (Offline Evaluation)**: Fine-tuned DistilBERT weights (~268 MB) achieve 91.42% test accuracy and 0.7584 Macro F1, but inference requires > 550 MB RAM, exceeding Render's 512 MB free tier ceiling. To prevent container termination (Linux OOM exit code 137), live transformer inference is omitted on free cloud instances. DistilBERT is provided for offline evaluation, GPU fine-tuning (`notebooks/ConsumerVoice_DistilBERT_Finetuning.ipynb`), and benchmark comparison in the Model Comparison dashboard, which renders its genuine test evaluation metrics and confusion matrices loaded from `model_evaluation.json`.

---

## 7. Live Demonstration Scenario

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

## 8. Repository Structure

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

## 9. Limitations & Scope

1. **Temporal Scope**: The Flipkart dataset lacks timestamp metadata; temporal trend forecasting is not supported.
2. **Neutral Class Density**: Neutral feedback accounts for only 4.9% of the dataset, resulting in lower neutral F1 (0.446) compared to positive (0.957) and negative (0.875).
3. **Evidence-Based Screening**: The hallucination detector audits claims against explicit source feedback and provided policies. It does not certify external real-world physical facts not documented in the premise texts.
4. **DistilBERT Cloud Memory Boundary**: Fine-tuned DistilBERT inference requires > 550 MB RAM. To prevent Out-Of-Memory (OOM exit code 137) termination on the 512 MB Render Free tier, live transformer inference is omitted on free cloud instances, while empirical benchmark metrics (91.42% accuracy, 0.7584 Macro F1) are verified and rendered in the Model Comparison studio. Full GPU inference is supported locally or on paid instances.
5. **Ephemeral Storage on Render Free**: Free-tier web services on Render operate on ephemeral filesystems. The SQLite database automatically re-seeds 200 authentic benchmark reviews on startup, while visitor-generated query logs reset upon container reboot.
6. **Free-Tier Cold Starts**: Free-tier containers on Render enter sleep mode after 15 minutes of inactivity; the initial wake-up request may require 30–50 seconds before responding with sub-10ms latency.
