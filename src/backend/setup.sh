#!/bin/bash

# FastAPI Setup Script for WSL
# This script creates a virtual environment and installs dependencies

echo "🚀 Setting up FastAPI application..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install it first:"
    echo "   sudo apt update && sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Found Python $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To run the application:"
echo "   bash run.sh"
echo ""
echo "Or manually:"
echo "   source venv/bin/activate"
echo "   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "The API will be available at: http://localhost:8000"
echo "API documentation at: http://localhost:8000/docs"
