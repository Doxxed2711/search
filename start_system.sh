#!/bin/bash
# Start both API server and scraper

echo "=========================================="
echo "Starting Marketplace Deal Finder System"
echo "=========================================="
echo ""

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Error: Virtual environment not found. Run setup_server.sh first"
    exit 1
fi

# Start API server in background
echo "Starting API server..."
python api/server.py > logs/api_server.log 2>&1 &
API_PID=$!
echo "API server started (PID: $API_PID)"

# Wait for API server to start
sleep 3

# Start scraper
echo ""
echo "Starting scraper..."
echo ""
python marketplace_scraper_ml.py --api-url http://localhost:5000

# When scraper stops, kill API server
echo ""
echo "Stopping API server..."
kill $API_PID

echo "System stopped"
