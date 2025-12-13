#!/bin/bash

# Simple script to run the shutdown service
echo "Starting Shutdown Service..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Python3 is required but not installed."
    exit 1
fi

# Install dependencies if needed
echo "Installing dependencies..."
pip install -r requirements.txt

# Run the service
echo "Running shutdown service on port 5001..."
python3 shutdown_service.py