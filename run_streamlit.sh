#!/usr/bin/env bash
# ==============================================================================
# Helper Script to Launch NIFTY-Pulse Streamlit Dashboard
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

if [ -d ".venv" ]; then
    echo "Activating virtual environment (.venv)..."
    source .venv/bin/activate
fi

export PYTHONPATH="."
echo "Starting Streamlit Dashboard on http://localhost:8501..."
streamlit run streamlit_app.py --server.port=8501 --server.address=0.0.0.0
