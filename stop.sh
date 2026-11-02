#!/usr/bin/env bash
# ==============================================================================
# ConsumerVoice Application Shutdown Script
# ==============================================================================

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "Shutting down ConsumerVoice application services..."

if [ -f ".backend.pid" ]; then
    PID=$(cat .backend.pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID 2>/dev/null || true
        echo "Backend server (PID $PID) stopped."
    fi
    rm -f .backend.pid
fi

if [ -f ".frontend.pid" ]; then
    PID=$(cat .frontend.pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID 2>/dev/null || true
        echo "Frontend dev server (PID $PID) stopped."
    fi
    rm -f .frontend.pid
fi

# Force-clean any lingering listeners on 8000 or 5173
if lsof -ti:8000 &>/dev/null; then
    kill -9 $(lsof -ti:8000) 2>/dev/null || true
    echo "Cleared port 8000."
fi
if lsof -ti:5173 &>/dev/null; then
    kill -9 $(lsof -ti:5173) 2>/dev/null || true
    echo "Cleared port 5173."
fi

echo "ConsumerVoice services stopped successfully."

