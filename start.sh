#!/bin/bash
# MechaWiki Startup Script
# Starts both backend and frontend servers

# Exit on any error
set -e

export SESSION_NAME=tales_of_wonder

# Session configuration
export SESSION_NAME="${SESSION_NAME:-dev_session}"

# Use mock agents for testing (set to 'true' to disable real LLM-powered agents)
export USE_MOCK_AGENTS=${USE_MOCK_AGENTS:-false}

echo "🏰 Starting MechaWiki..."
echo ""
echo "Session: $SESSION_NAME"
echo "Agent Mode: $([ "$USE_MOCK_AGENTS" = "true" ] && echo "🎭 MOCK AGENTS (testing)" || echo "⚡ REAL AGENTS (LLM-powered)")"
echo ""

# Check if session exists, run setup wizard if not
SESSION_DIR="data/sessions/$SESSION_NAME"
if [ ! -d "$SESSION_DIR" ] && [ "$SESSION_NAME" != "dev_session" ]; then
    echo "📋 Session '$SESSION_NAME' doesn't exist yet."
    echo "Running setup wizard..."
    echo ""
    
    # Check for Python first
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python 3 not found!"
        echo "Please install Python 3.8 or higher"
        exit 1
    fi
    
    # Run setup script
    python3 setup_session.py
    
    # Check if setup was successful
    if [ ! -d "$SESSION_DIR" ]; then
        echo ""
        echo "❌ Session setup failed or was cancelled."
        exit 1
    fi
    
    echo ""
fi

# Clean dev_session on every start (WARNING!)
if [ "$SESSION_NAME" = "dev_session" ]; then
    echo "⚠️  ═══════════════════════════════════════════════════════════"
    echo "⚠️  WARNING: Cleaning dev_session - SESSION DATA IS BEING DELETED!"
    echo "⚠️  ═══════════════════════════════════════════════════════════"
    echo "⚠️  "
    echo "⚠️  Deleting: data/sessions/dev_session/"
    echo "⚠️  This includes:"
    echo "⚠️    - All agent configurations in agents.json"
    echo "⚠️    - All agent logs in logs/"
    echo "⚠️    - Session config in config.yaml"
    echo "⚠️  ═══════════════════════════════════════════════════════════"
    echo ""
    
    # Delete the dev_session directory
    if [ -d "data/sessions/dev_session" ]; then
        rm -rf data/sessions/dev_session
        echo "✓ Cleaned dev_session"
    else
        echo "✓ dev_session doesn't exist yet (first run)"
    fi
    echo ""
fi

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

# Create session directories
mkdir -p "data/sessions/$SESSION_NAME/logs"
echo "✓ Created session directories for: $SESSION_NAME"
echo ""

# Start backend in background
echo "🚀 Starting Flask backend (port 5000)..."
source .venv/bin/activate
python3 run_server.py > backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Wait for backend to initialize (agents take time to start)
echo "⏳ Waiting for backend initialization (5 seconds)..."
sleep 5

# Check if backend is still running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo ""
    echo "❌ ═══════════════════════════════════════════════════════════"
    echo "❌ BACKEND FAILED TO START!"
    echo "❌ ═══════════════════════════════════════════════════════════"
    echo ""
    echo "Last 30 lines of backend.log:"
    echo "─────────────────────────────────────────────────────────────"
    tail -30 backend.log
    echo "─────────────────────────────────────────────────────────────"
    echo ""
    echo "Check backend.log for full error details."
    exit 1
fi

# Check for critical errors in backend log (even if process is alive)
if grep -q "CRITICAL ERROR DURING AGENT INITIALIZATION" backend.log; then
    echo ""
    echo "❌ ═══════════════════════════════════════════════════════════"
    echo "❌ AGENT INITIALIZATION FAILED!"
    echo "❌ ═══════════════════════════════════════════════════════════"
    echo ""
    echo "Last 30 lines of backend.log:"
    echo "─────────────────────────────────────────────────────────────"
    tail -30 backend.log
    echo "─────────────────────────────────────────────────────────────"
    echo ""
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo "✓ Backend started successfully"
echo ""

# Start frontend in background
echo "🚀 Starting Vite frontend (port 5173)..."
cd src/ui
npm run dev > ../../frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"
cd ../..

# Wait a moment and check if frontend is still running
sleep 2

if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo "❌ Frontend failed to start! Check frontend.log for details:"
    tail -20 frontend.log
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo "✓ Frontend started successfully"
echo ""
if [ "$USE_MOCK_AGENTS" = "true" ]; then
    echo "🎭 Mock agents active - no API keys needed"
else
    echo "⚡ Real agents active - ensure config.toml has valid API keys!"
fi
echo ""

echo "✨ MechaWiki is running!"
echo ""
echo "📍 Backend:  http://localhost:5000"
echo ""
echo "📍 Frontend: http://localhost:5173 << Click here to open the UI"
echo ""
echo "💡 Frontend auto-reloads on changes (Vite)"
echo "💡 Backend requires manual restart for Python changes (agents stay running)"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Trap Ctrl+C to kill both processes
trap "echo ''; echo '🛑 Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT

# Wait for both processes
wait

