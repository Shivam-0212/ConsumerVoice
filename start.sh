#!/usr/bin/env bash
# ==============================================================================
# ConsumerVoice Application Startup Script (macOS / Linux)
# Launches Backend (FastAPI :8000) and Frontend (Vite React :5173)
# ==============================================================================

set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "======================================================================"
echo "    ConsumerVoice: Explainable & Hallucination-Aware Feedback NLP     "
echo "======================================================================"

# 1. Check Python virtual environment
if [ ! -d ".venv" ]; then
    echo "[1/6] Creating Python virtual environment with Python 3.11..."
    if command -v /opt/homebrew/bin/python3.11 &>/dev/null; then
        /opt/homebrew/bin/python3.11 -m venv .venv
    elif command -v python3.11 &>/dev/null; then
        python3.11 -m venv .venv
    else
        python3 -m venv .venv
    fi
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r backend/requirements.txt
else
    source .venv/bin/activate
fi

# 2. Check and prepare dataset
if [ ! -f "data/processed/data_quality_report.json" ]; then
    echo "[2/6] Preparing dataset, performing data audit, and creating splits..."
    python scripts/prepare_dataset.py
else
    echo "[2/6] Processed dataset splits verified."
fi

# 3. Check and train baseline model if missing
if [ ! -f "backend/saved_models/sentiment_baseline.joblib" ]; then
    echo "[3/6] Training primary sentiment baseline model (TF-IDF + Logistic Regression)..."
    python scripts/train_sentiment.py
else
    echo "[3/6] Sentiment baseline model verified."
fi

# 3b. Verify DistilBERT transformer weights and resolve broken symlinks
if [ ! -f "backend/saved_models/distilbert_sentiment/config.json" ]; then
    if [ -f "ConsumerVoice_Private/trained_models/distilbert_sentiment/config.json" ]; then
        echo "Restoring DistilBERT transformer weights from ConsumerVoice_Private..."
        rm -rf backend/saved_models/distilbert_sentiment
        cp -r ConsumerVoice_Private/trained_models/distilbert_sentiment backend/saved_models/distilbert_sentiment
    elif [ -f "../ConsumerVoice_Private/trained_models/distilbert_sentiment/config.json" ]; then
        echo "Restoring DistilBERT transformer weights from ConsumerVoice_Private..."
        rm -rf backend/saved_models/distilbert_sentiment
        cp -r ../ConsumerVoice_Private/trained_models/distilbert_sentiment backend/saved_models/distilbert_sentiment
    fi
fi

# 4. Check and seed SQLite database
if [ ! -f "backend/consumervoice.db" ]; then
    echo "[4/6] Initializing and seeding SQLite database with real reviews..."
    python scripts/initialize_database.py
else
    echo "[4/6] SQLite database verified."
fi

# 5. Check frontend dependencies
echo "[5/6] Verifying frontend dependencies..."
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend npm packages..."
    cd frontend && npm install && cd ..
fi

# 6. Stop any stale instances on ports 8000 or 5173
if lsof -ti:8000 &>/dev/null; then
    echo "Freeing port 8000..."
    kill -9 $(lsof -ti:8000) 2>/dev/null || true
fi
if lsof -ti:5173 &>/dev/null; then
    echo "Freeing port 5173..."
    kill -9 $(lsof -ti:5173) 2>/dev/null || true
fi

# 7. Launch Backend
echo "[6/6] Launching ConsumerVoice Backend (FastAPI on :8000)..."
nohup uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 </dev/null > backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > .backend.pid

# 8. Launch Frontend
echo "Launching ConsumerVoice Frontend (Vite on :5173)..."
cd frontend
CI=true nohup node node_modules/vite/bin/vite.js --host 0.0.0.0 --port 5173 </dev/null > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../.frontend.pid
cd ..

sleep 2

echo "======================================================================"
echo "ConsumerVoice is running successfully!"
echo "----------------------------------------------------------------------"
echo "  Frontend Application:   http://localhost:5173"
echo "  Backend API Server:     http://localhost:8000"
echo "  Interactive API Docs:   http://localhost:8000/docs"
echo "----------------------------------------------------------------------"
echo "  Logs: backend.log and frontend.log"
echo "  To stop the application, run: ./stop.sh"
echo "======================================================================"
