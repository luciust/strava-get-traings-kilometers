#!/usr/bin/env bash
# Launcher script for Strava Training Kilometers Analytics TUI
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -d ".venv" ]; then
    source ".venv/bin/activate"
fi

# Run the app
python3 main.py "$@"
