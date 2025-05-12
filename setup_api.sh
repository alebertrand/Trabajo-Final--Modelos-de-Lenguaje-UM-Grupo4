#!/bin/bash

# Prepare environment and install requirements
echo "Creating venv and installing dependencies..."

# Always deactivate conda
conda deactivate 2>/dev/null || true

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Environment ready. You can now run the API with run_api.sh"
