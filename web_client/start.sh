#!/bin/bash

# Marina Web Client Startup Script
# Simple wrapper to start the web client with common options

echo "🤖 Starting Marina Web Client..."
echo "================================"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if Flask is installed
if ! python3 -c "import flask" &> /dev/null; then
    echo "⚠️  Flask not found. Installing dependencies..."
    pip3 install -r requirements.txt
fi

# Check if Marina CLI exists
if [ ! -f "../marina_cli.py" ]; then
    echo "⚠️  Warning: Marina CLI not found at ../marina_cli.py"
    echo "   Make sure marina_cli.py is in the parent directory"
fi

# Start the web client
echo "🚀 Starting web server..."
echo "   Access the web client at: http://localhost:5000"
echo "   Press Ctrl+C to stop the server"
echo ""

python3 run.py --host 127.0.0.1 --port 5000
