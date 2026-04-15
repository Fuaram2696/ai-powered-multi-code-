#!/bin/bash

echo "========================================"
echo "  AI Multi-Code Converter"
echo "  Starting Backend and Frontend..."
echo "========================================"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "[ERROR] .env file not found!"
    echo "Please create a .env file with your GROQ_API_KEY"
    echo "Example: GROQ_API_KEY=your_key_here"
    echo ""
    exit 1
fi

echo "[1/3] Installing Python dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Failed to install Python dependencies"
    exit 1
fi

echo ""
echo "[2/3] Starting Backend Server..."
python backend.py &
BACKEND_PID=$!
sleep 3

echo ""
echo "[3/3] Starting Frontend Server..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "========================================"
echo "  Servers Started Successfully!"
echo "========================================"
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:3000"
echo "========================================"
echo ""
echo "Press Ctrl+C to stop all servers..."

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
