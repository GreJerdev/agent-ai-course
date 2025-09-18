#!/bin/bash

# LangGraph Project Setup Script
# This script creates a Python 3.10 virtual environment and installs dependencies

set -e  # Exit on any error

echo "🚀 Setting up LangGraph project environment..."
echo "================================================"

# Check if Python 3.10 is available
if ! command -v python3.10 &> /dev/null; then
    echo "❌ Python 3.10 is not installed or not in PATH"
    echo "Please install Python 3.10 first:"
    echo "  - macOS: brew install python@3.10"
    echo "  - Ubuntu: sudo apt install python3.10 python3.10-venv"
    echo "  - Or download from https://www.python.org/downloads/"
    exit 1
fi

echo "✅ Python 3.10 found: $(python3.10 --version)"

# Remove existing venv if it exists
if [ -d "venv" ]; then
    echo "🗑️  Removing existing virtual environment..."
    rm -rf venv
fi

# Create virtual environment
echo "🔨 Creating Python 3.10 virtual environment..."
python3.10 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found in current directory"
    exit 1
fi

# Install requirements
echo "📥 Installing requirements from requirements.txt..."
pip install -r requirements.txt

# Verify installation
echo "🔍 Verifying key packages..."
python -c "import langgraph; print(f'✅ LangGraph version: {langgraph.__version__}')" 2>/dev/null || echo "⚠️  LangGraph import failed"
python -c "import langchain; print(f'✅ LangChain version: {langchain.__version__}')" 2>/dev/null || echo "⚠️  LangChain import failed"

echo ""
echo "🎉 Setup completed successfully!"
echo "================================================"
echo ""
echo "To activate the virtual environment in the future, run:"
echo "  source venv/bin/activate"
echo ""
echo "To deactivate the virtual environment, run:"
echo "  deactivate"
echo ""
echo "Happy coding! 🐍"
