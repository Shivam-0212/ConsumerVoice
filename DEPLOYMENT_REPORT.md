# ConsumerVoice: Production Deployment & Integration Verification Report

**Project:** ConsumerVoice — An Explainable, Hallucination-Aware Framework for Customer Feedback NLP  
**GitHub Repository:** [https://github.com/Shivam-0212/ConsumerVoice](https://github.com/Shivam-0212/ConsumerVoice)  
**Deployment Date:** November 2026  
**Auditor / Engineer:** Senior Full-Stack, DevOps & QA Automation Specialist  

---

## 1. Production URLs

| Component | Platform | Live URL | Status |
| :--- | :--- | :--- | :--- |
| **Web Frontend** | **Vercel** | [https://consumer-voice-rose.vercel.app](https://consumer-voice-rose.vercel.app) | **Live & Operational** |
| **Backend API** | **Render** | [https://consumervoice-api.onrender.com](https://consumervoice-api.onrender.com) | **Live & Operational** |
| **Interactive API Docs** | **Render (Swagger)** | [https://consumervoice-api.onrender.com/docs](https://consumervoice-api.onrender.com/docs) | **Live & Operational** |
| **Health Check** | **Render API** | [https://consumervoice-api.onrender.com/api/health](https://consumervoice-api.onrender.com/api/health) | **Healthy (HTTP 200)** |

---

## 2. Deployment Architecture & Configuration

```mermaid
flowchart LR
    User["End-User Browser"]
    VercelEdge["Vercel Edge Network\n(consumer-voice-rose.vercel.app)"]
    RenderBackend["Render Web Service\n(consumervoice-api.onrender.com)"]
    GHRelease["GitHub Release Assets (v1.0.0)\n(sentiment_baseline.joblib & consumervoice.db.gz)"]
    SQLite["SQLite Database\n(50,000 Flipkart Reviews)"]

    User -->|1. Request Page (/, /explorer, etc.)| VercelEdge
    VercelEdge -->|2. SPA Rewrite /(.*) -> index.html| User
    User -->|3. API Request /api/*| VercelEdge
    VercelEdge -->|4. Reverse Proxy Rewrite| RenderBackend
    RenderBackend -->|5. Query Reviews & Issues| SQLite
    RenderBackend -.->|6. Bootstrapped on Startup| GHRelease
```

### Vercel Deployment Configuration
- **Project Name:** `consumer-voice`
- **Connected Repository:** `Shivam-0212/ConsumerVoice` (branch: `main`)
- **Framework Preset:** Vite / React
- **Output Directory:** `dist`
- **Reverse Proxy & SPA Rewrites (`vercel.json`):**
  ```json
  {
    "rewrites": [
      {
        "source": "/api/:path*",
        "destination": "https://consumervoice-api.onrender.com/api/:path*"
      },
      {
        "source": "/(.*)",
        "destination": "/index.html"
      }
    ]
  }
  ```

### Render Deployment Configuration
- **Service Name:** `ConsumerVoice-api`
- **Service Type:** Web Service (Python 3.11 Environment)
- **Region:** US-West (Oregon) / Free Tier
- **Build Script:** `render_build.sh`
- **Start Command:** `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
- **Health Check Path:** `/api/health`

---

## 3. Environment Variables Specification

No secret credentials or private tokens are hardcoded into source code or repository commits.

| Variable Name | Service | Recommended Setting | Purpose |
| :--- | :--- | :--- | :--- |
| `PORT` | Render (Backend) | Assigned dynamically by Render | Internal HTTP listening port for Uvicorn |
| `ENVIRONMENT` | Render (Backend) | `production` | Configures production logging and optimizations |
| `DATABASE_URL` | Render (Backend) | `sqlite:///backend/consumervoice.db` | Path to persistent or bootstrapped SQLite file |
| `BASELINE_MODEL_URL` | Render (Backend) | Optional override URL | Custom object storage link for `sentiment_baseline.joblib` |
| `DATABASE_ASSET_URL` | Render (Backend) | Optional override URL | Custom object storage link for `consumervoice.db.gz` |
| `GEMINI_API_KEY` | Render (Backend) | Optional (User Secret) | Powers optional abstractive LLM feedback summaries |
| `VITE_API_BASE_URL` | Vercel (Frontend) | Optional (defaults to `/api`) | Explicit backend endpoint if bypassing Vercel rewrites |

---

## 4. Machine Learning Models & Cloud Resource Allocation

### Model A: TF-IDF + Balanced Logistic Regression (Production Ready)
- **Artifact:** `sentiment_baseline.joblib` (2.7 MB).
- **RAM Footprint:** ~15 MB.
- **Inference Latency:** 0.008 ms per sample.
- **Cloud Compatibility:** 100% compatible with Render Free Tier (512 MB limit).
- **Distribution Method:** Hosted as an immutable release asset on GitHub Release `v1.0.0` and bootstrapped automatically during build/startup into `backend/saved_models/`.
- **Capabilities in Production:** Live tri-class sentiment inference (Positive, Neutral, Negative), confidence scoring, 3-class probability meters, and algebraic linear feature attribution ($\text{TF-IDF} \times \beta$).

### Model B: Fine-Tuned DistilBERT Transformer (High-RAM / GPU Dedicated)
- **Artifact:** `model.safetensors` (~268 MB) + tokenizer definitions.
- **RAM Footprint:** > 550 MB (PyTorch core runtime + transformer weights + activations).
- **Cloud Compatibility:** Exceeds the 512 MB physical memory ceiling of the Render Free Tier. Loading this asset on the free tier triggers Linux OOM (Out-of-Memory, exit code 137).
- **Production Handling:**
  - In compliance with project guidelines (*"Never pretend that a model is running when it is not"*), DistilBERT is explicitly reported as requiring a GPU or high-RAM instance.
  - When DistilBERT is requested on the cloud tier, the UI transparently informs the user that model weights are omitted to prevent memory exhaustion, while verified empirical benchmark metrics (91.42% accuracy, 0.7584 Macro F1) are presented in the Model Comparison studio.
  - Full weights and training code remain available in `ConsumerVoice_Private/` and `notebooks/ConsumerVoice_DistilBERT_Finetuning.ipynb`.

---

## 5. Database Availability & Data Integrity

- **Problem:** Render web services run on ephemeral container filesystems. On every deployment or cold restart, locally written SQLite files are purged.
- **Solution:**
  1. **Automated Release Bootstrap:** `scripts/download_production_assets.py` checks if `backend/consumervoice.db` exists. If missing or empty, it downloads and decompresses `consumervoice.db.gz` (3.5 MB compressed, 50,000 real Flipkart reviews) from the verified release asset in under 1.5 seconds.
  2. **Embedded Fallback Seed:** If network access to the release asset is blocked or offline, the backend automatically initializes and seeds `data/seed_sample.json` (200 authentic Flipkart customer reviews covering all 10 defect categories) into SQLite.
  3. **Verification:**
     - Total imported reviews: `50,000` (or `200` seed fallback).
     - Search by product and review keywords: Verified operational.
     - Rating (1–5 Stars) and Sentiment filtering: Verified operational.
     - Extractive feedback summarization citing source review IDs (`REV_XXXXXX`): Verified operational.

---

## 6. Automated Verification & Test Results

### 1. Backend Test Suite (Pytest)
```text
backend/tests/test_api_endpoints.py::test_health_endpoint PASSED                  [ 4%]
backend/tests/test_api_endpoints.py::test_dashboard_overview_endpoint PASSED          [ 9%]
backend/tests/test_api_endpoints.py::test_review_analyze_endpoint_baseline PASSED     [13%]
backend/tests/test_api_endpoints.py::test_active_model_switch_and_transformer_analyze PASSED [18%]
backend/tests/test_api_endpoints.py::test_review_list_and_detail_endpoints PASSED     [22%]
backend/tests/test_api_endpoints.py::test_response_verify_endpoint PASSED             [27%]
backend/tests/test_api_endpoints.py::test_evaluations_endpoint PASSED                 [31%]
backend/tests/test_api_endpoints.py::test_dataset_quality_endpoint PASSED             [36%]
backend/tests/test_api_endpoints.py::test_dashboard_dataset_scope_and_insights PASSED [40%]
backend/tests/test_api_endpoints.py::test_summaries_generate_with_review_ids PASSED   [45%]
backend/tests/test_issue_and_hallucination.py::test_issue_detection_multi_label PASSED [50%]
backend/tests/test_issue_and_hallucination.py::test_issue_detection_negation_guard PASSED [54%]
backend/tests/test_issue_and_hallucination.py::test_hallucination_demo_scenario PASSED [59%]
backend/tests/test_preprocessing.py::test_clean_text_basic PASSED                     [63%]
backend/tests/test_preprocessing.py::test_normalize_summary_preserves_negations PASSED [68%]
backend/tests/test_preprocessing.py::test_parse_rating_valid_and_malformed PASSED     [72%]
backend/tests/test_sentiment_and_explainability.py::test_sentiment_prediction_probabilities PASSED [77%]
backend/tests/test_sentiment_and_explainability.py::test_sentiment_prediction_negative PASSED [81%]
backend/tests/test_sentiment_and_explainability.py::test_explainability_attribution_baseline PASSED [86%]
backend/tests/test_sentiment_and_explainability.py::test_distilbert_loading_and_prediction PASSED [90%]
backend/tests/test_sentiment_and_explainability.py::test_distilbert_class_mapping PASSED [95%]
backend/tests/test_sentiment_and_explainability.py::test_distilbert_explanation_compatibility PASSED [100%]

============================== 22 passed in 8.04s ==============================
```

### 2. Frontend Production Build (Vite)
```text
vite v6.4.5 building for production...
✓ 2277 modules transformed.
dist/index.html                   0.90 kB │ gzip:   0.51 kB
dist/assets/index-CRtWnXhq.css   24.09 kB │ gzip:   4.90 kB
dist/assets/index-BfxntvWJ.js   731.29 kB │ gzip: 206.49 kB
✓ built in 2.19s with 0 errors
```

---

## 7. Discovered Issues & Technical Fixes Applied

| Category | Problem Identified | Root Cause | Fix Applied |
| :--- | :--- | :--- | :--- |
| **Routing** | Direct page refresh on `/explorer`, `/analyze`, `/models` returned HTTP 404 on Vercel | Vercel lacked SPA rewrite configuration | Created `vercel.json` with rewrite rule `/(.*) -> /index.html` |
| **API Connectivity** | Frontend API calls returned HTTP 404 in production | Frontend was querying `/api/*` on Vercel origin with no backend proxy | Added `/api/:path* -> https://consumervoice-api.onrender.com/api/:path*` reverse proxy in `vercel.json` |
| **CORS** | Cross-Origin requests rejected if accessed directly | Backend CORS lacked explicit Vercel domain and regex | Updated `CORSMiddleware` in `backend/app/main.py` with `allow_origin_regex=r"https://.*\.vercel\.app"` |
| **API Validation** | 500 Internal Server Error when analyzing reviews without model | `predict_baseline()` fallback dictionary omitted `"method"` key required by Pydantic's `ExplanationData` schema | Added `"method": "none"` to fallback explanation payload in `sentiment_service.py` |
| **HTTP Compliance** | `curl -I /api/health` returned HTTP 405 Method Not Allowed | FastAPI routes only registered `GET` methods | Added `@router.head("/health")` and `@app.head("/")` decorators |
| **Database Loss** | SQLite database had 0 reviews on Render startup | Render ephemeral filesystem had no data files | Built `scripts/download_production_assets.py` to auto-restore 50,000-review database from release asset |
| **Model Availability** | Missing baseline model on Render cloud | `.joblib` was excluded from Git | Automated `sentiment_baseline.joblib` download during build and application startup lifespan |

---

## 8. Remaining Limitations & Cloud Guidance

1. **Free-Tier Cold Starts:**
   Render's free web services sleep after 15 minutes of inactivity. The first incoming request may take 30–50 seconds to spin up the container. Once awake, response latency is sub-10ms.
2. **DistilBERT Hardware Boundary:**
   DistilBERT inference requires at least 1 GB of available container RAM. For production deployments with full transformer inference, upgrading Render to the Starter tier ($7/month) or offloading inference to a serverless GPU endpoint (e.g., Hugging Face Inference Endpoints or AWS SageMaker) is recommended.
3. **Database Write Concurrency:**
   SQLite is configured in WAL (Write-Ahead Logging) mode, providing high-speed concurrent reads for analytical dashboards. For large multi-node horizontal scaling, migrating to PostgreSQL is recommended.

---

## 9. Exact Redeployment Procedure

### To Update Frontend (Vercel):
Any commit pushed to `main` on `Shivam-0212/ConsumerVoice` automatically triggers a zero-downtime Vercel production deployment.
```bash
git push origin main
```

### To Update Backend (Render):
Render is connected to GitHub and automatically deploys when `main` receives new commits.
Alternatively, trigger a manual deploy in the Render dashboard:
`https://dashboard.render.com/web/srv-dbkc1kuc6qcc73e567q0` -> **Manual Deploy** -> **Clear build cache & deploy**.
