#!/usr/bin/env bash
# ==============================================================================
# ConsumerVoice Render Build Script
# Prepares Python environment, installs dependencies, and restores production assets.
# ==============================================================================

set -o errexit

echo "======================================================================"
echo "    ConsumerVoice: Cloud Backend Build (Render / Linux Environment)    "
echo "======================================================================"

python -m pip install --upgrade pip
pip install -r backend/requirements.txt

# Attempt to download baseline model and database assets during build step
python scripts/download_production_assets.py || {
    echo "Notice: Asset download skipped during build step; will initialize at runtime."
}

echo "======================================================================"
echo "    ConsumerVoice Backend Build Finished Successfully                  "
echo "======================================================================"
