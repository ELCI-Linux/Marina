#!/bin/bash
# Marina LLM API Server Startup Script

echo "🤖 Starting Marina LLM API Server..."
echo "======================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python3 first."
    exit 1
fi

# Change to Marina directory
cd "$(dirname "$0")"

# Check if dependencies are available
echo "🔍 Checking dependencies..."
if ! python3 -c "import requests" &> /dev/null; then
    echo "⚠️  Installing requests dependency..."
    pip3 install requests
fi

# Start the API server
echo "🚀 Starting Marina LLM API server on http://localhost:8000..."
echo "📝 Available endpoints:"
echo "   POST /api/llm/query - Process LLM queries"
echo "   GET  /api/status    - Server status"
echo "   GET  /api/models    - Available models"
echo ""
echo "💡 This server enables the Marina browser extension to communicate with local LLMs"
echo "🔗 Make sure your browser extension is loaded and configured"
echo ""
echo "Press Ctrl+C to stop the server"
echo "======================================="

# Run the server
python3 marina_llm_api.py --host localhost --port 8000
