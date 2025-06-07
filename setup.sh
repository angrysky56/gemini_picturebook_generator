#!/bin/bash
"""
Setup script for the Gemini Picture Book Generator
"""

echo "🎨 Setting up Gemini Picture Book Generator..."

# Check if we're in the right directory
if [ ! -f "enhanced_story_generator.py" ]; then
    echo "❌ Please run this script from the gemini_picturebook_generator directory"
    exit 1
fi

# Activate virtual environment
echo "🐍 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📚 Installing Python packages..."
pip install -r requirements.txt

# Check if .env file exists and has API key
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.template .env
    echo "Please edit .env file and add your Google API key"
elif grep -q "your_google_api_key_here" .env; then
    echo "⚠️  Please update your API key in the .env file"
fi

echo "✅ Setup complete!"
echo "💡 To test: python test_api.py"
echo "🎨 To run: python enhanced_story_generator.py"
