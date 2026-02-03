#!/usr/bin/env bash
# Create and activate conda env for SISR CXR Enhancer (isolated from system)
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Creating conda env 'sisr'..."
conda env create -f environment.yml

echo ""
echo "Done. Activate and run with:"
echo "  conda activate sisr"
echo "  python app.py"
echo ""
echo "Then open http://localhost:7860"
