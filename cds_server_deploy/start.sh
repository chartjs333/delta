#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "============================================================"
echo "  Starting DeltaReduce Clinical Decision Support Prototype"
echo "============================================================"

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 is not installed."
    exit 1
fi

# Launch server directly - Python will automatically create and enter .venv if needed
python3 -u server.py
