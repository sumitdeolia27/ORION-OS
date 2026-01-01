#!/bin/bash

echo "============================================================"
echo "ORION OS - Starting Backend Server"
echo "============================================================"
echo ""
echo "This will start the Python Flask backend server on port 5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo "============================================================"
echo ""

# Change to script directory
cd "$(dirname "$0")"

# Check if Python is installed
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "ERROR: Python is not installed or not in PATH"
    echo "Please install Python 3.11 or higher"
    exit 1
fi

# Use python3 if available, otherwise python
if command -v python3 &> /dev/null; then
    PYTHON=python3
else
    PYTHON=python
fi

# Check if required packages are installed
$PYTHON -c "import flask" &> /dev/null
if [ $? -ne 0 ]; then
    echo "Installing required Python packages..."
    $PYTHON -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install dependencies"
        exit 1
    fi
fi

# Start the backend server
echo "Starting backend server..."
echo ""
$PYTHON scripts/api_server.py
