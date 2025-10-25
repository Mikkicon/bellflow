#!/bin/bash

# FastAPI Run Script for WSL
# This script activates the virtual environment and starts the FastAPI server

echo "🚀 Starting FastAPI application..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup.sh first:"
    echo "   bash setup.sh"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "❌ Dependencies not installed. Please run setup.sh first:"
    echo "   bash setup.sh"
    exit 1
fi

echo "✅ Virtual environment activated"
echo "🌐 Starting FastAPI server..."
echo ""
echo "📍 API will be available at: http://localhost:8000"
echo "📚 API documentation at: http://localhost:8000/docs"
echo "🔍 Alternative docs at: http://localhost:8000/redoc"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
