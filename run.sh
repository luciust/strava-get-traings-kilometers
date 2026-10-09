#!/usr/bin/env bash
# Launcher script for Strava Training Kilometers Analytics TUI
# Automatically sets up the virtual environment and installs dependencies if needed.
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 1. Verify python3 availability
if ! command -v python3 &>/dev/null; then
    echo "❌ Error: python3 is not installed." >&2
    echo "Please install Python 3 (e.g.: sudo apt update && sudo apt install -y python3 python3-venv python3-pip)" >&2
    exit 1
fi

# 2. Check and initialize virtual environment
if [ ! -d ".venv" ] || [ ! -f ".venv/bin/python3" ]; then
    echo "📦 First launch detected: Creating virtual environment (.venv)..."
    if ! python3 -m venv .venv 2>/dev/null; then
        echo "⚠️  'python3 -m venv' failed. 'python3-venv' package may be missing." >&2
        echo "Run: sudo apt install -y python3-venv python3-pip" >&2
        echo "Attempting to continue with system Python..."
    fi
fi

# 3. Determine Python and Pip binaries
if [ -f ".venv/bin/activate" ]; then
    source ".venv/bin/activate"
    PYTHON_BIN=".venv/bin/python3"
    PIP_BIN=".venv/bin/pip"
else
    PYTHON_BIN="python3"
    PIP_BIN="pip3"
fi

# 4. Check if required libraries are installed
if ! "$PYTHON_BIN" -c "import textual, rich, requests, aiohttp, jinja2" &>/dev/null; then
    echo "📦 Installing required dependencies from requirements.txt..."
    if [ -f "$PIP_BIN" ] || command -v "$PIP_BIN" &>/dev/null; then
        "$PIP_BIN" install -r requirements.txt
    else
        "$PYTHON_BIN" -m pip install -r requirements.txt
    fi
    echo "✅ Dependencies installed successfully."
fi

# 5. Launch the application
exec "$PYTHON_BIN" main.py "$@"
