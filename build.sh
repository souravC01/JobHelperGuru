#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Build React frontend
cd frontend
npm install
npm run build
cd ..
