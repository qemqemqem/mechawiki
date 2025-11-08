#!/bin/bash
# MechaWiki Startup Script
# Starts both backend and frontend servers

echo "🏰 Starting MechaWiki..."
echo ""

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found!"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"

# Check for Node/npm
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found!"
    echo "Please install Node.js 18 or higher"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ npm not found!"
    echo "Please install npm"
    exit 1
fi

echo "✓ Node.js found: $(node --version)"
echo "✓ npm found: $(npm --version)"
echo ""

# Check and install Python dependencies
echo "📦 Checking Python dependencies..."
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
fi

echo "Activating virtual environment..."
source .venv/bin/activate

if ! pip show flask &> /dev/null; then
    echo "Installing Python dependencies..."
    pip install -q -r requirements.txt
else
    echo "✓ Python dependencies installed"
fi

echo ""

# Check and install npm dependencies
echo "📦 Checking npm dependencies..."
cd src/ui

if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm install
else
    echo "✓ npm dependencies installed"
fi

cd ../..
echo ""

# Check for config file
if [ ! -f "config.toml" ]; then
    echo "⚠️  config.toml not found!"
    echo "Creating from example..."
    cp config.example.toml config.toml
    echo "✓ Created config.toml - please edit with your API keys"
    echo ""
fi

# Create data directories
mkdir -p data/sessions/dev_session/logs
echo "✓ Created session directories"
echo ""

# Start backend in background
echo "🚀 Starting Flask backend (port 5000)..."
source .venv/bin/activate
python3 run_server.py &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"
echo ""

# Wait a moment for backend to start
sleep 2

# Start frontend in background
echo "🚀 Starting Vite frontend (port 5173)..."
cd src/ui
npm run dev &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"
cd ../..
echo ""

# Wait a moment for frontend to start
sleep 3

echo "✨ MechaWiki is running!"
echo ""
echo "📍 Frontend: http://localhost:5173"
echo "📍 Backend:  http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Trap Ctrl+C to kill both processes
trap "echo ''; echo '🛑 Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT

# Wait for both processes
wait

