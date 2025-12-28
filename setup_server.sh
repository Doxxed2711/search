#!/bin/bash
# Setup script for the marketplace deal scraper server

echo "=========================================="
echo "Marketplace Deal Scraper - Server Setup"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

if [ $? -ne 0 ]; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p ml_models api logs

# Check for Firebase credentials
echo ""
echo "=========================================="
echo "Firebase Setup"
echo "=========================================="
echo ""
echo "To enable push notifications to Android app, you need Firebase credentials."
echo ""
echo "Steps to get Firebase credentials:"
echo "1. Go to https://console.firebase.google.com/"
echo "2. Create a new project or select existing one"
echo "3. Go to Project Settings > Service Accounts"
echo "4. Click 'Generate New Private Key'"
echo "5. Save the JSON file as 'api/firebase_credentials.json'"
echo ""

if [ -f "api/firebase_credentials.json" ]; then
    echo "✓ Firebase credentials found!"
else
    echo "⚠ Firebase credentials NOT found"
    echo "  Push notifications will not work until you add credentials"
    echo "  Save your Firebase credentials to: api/firebase_credentials.json"
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Configure the scraper: python marketplace_scraper_ml.py --setup"
echo "2. Start the API server: python api/server.py"
echo "3. Start the scraper: python marketplace_scraper_ml.py"
echo ""
echo "Or run both with start_system.sh"
echo ""
