#!/bin/bash
# MechaWiki Startup Script
# Starts both backend and frontend servers

# Exit on any error
set -e

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

# Validate wikicontent configuration
echo "🌿 Validating wikicontent configuration..."

# Use Python to parse config.toml and extract paths
WIKICONTENT_INFO=$(python3 << 'PYEOF'
import toml
import sys
try:
    config = toml.load('config.toml')
    content_repo = config['paths']['content_repo']
    content_branch = config['paths'].get('content_branch', 'main')
    print(f"{content_repo}|{content_branch}")
except Exception as e:
    print(f"ERROR|{e}", file=sys.stderr)
    sys.exit(1)
PYEOF
)

if [ $? -ne 0 ]; then
    echo "❌ Failed to parse config.toml"
    echo "Please check that config.toml is valid TOML format"
    exit 1
fi

# Split the output
CONTENT_REPO=$(echo "$WIKICONTENT_INFO" | cut -d'|' -f1)
CONTENT_BRANCH=$(echo "$WIKICONTENT_INFO" | cut -d'|' -f2)

# Check if wikicontent directory exists
if [ ! -d "$CONTENT_REPO" ]; then
    echo ""
    echo "❌ ═══════════════════════════════════════════════════════════"
    echo "❌ WIKICONTENT REPOSITORY NOT FOUND!"
    echo "❌ ═══════════════════════════════════════════════════════════"
    echo ""
    echo "Expected location: $CONTENT_REPO"
    echo ""
    echo "📋 To fix this:"
    echo "   1. Clone or create your wikicontent repository:"
    echo "      git clone <your-repo-url> $CONTENT_REPO"
    echo "      OR"
    echo "      mkdir -p $CONTENT_REPO && cd $CONTENT_REPO && git init"
    echo ""
    echo "   2. Update config.toml with the correct path:"
    echo "      [paths]"
    echo "      content_repo = \"/path/to/your/wikicontent\""
    echo ""
    exit 1
fi

# Check if it's a git repository
if [ ! -d "$CONTENT_REPO/.git" ]; then
    echo ""
    echo "❌ ═══════════════════════════════════════════════════════════"
    echo "❌ WIKICONTENT IS NOT A GIT REPOSITORY!"
    echo "❌ ═══════════════════════════════════════════════════════════"
    echo ""
    echo "Location: $CONTENT_REPO"
    echo ""
    echo "📋 To fix this:"
    echo "   cd $CONTENT_REPO"
    echo "   git init"
    echo "   git add ."
    echo "   git commit -m \"Initial commit\""
    echo ""
    exit 1
fi

# Check current branch
CURRENT_BRANCH=$(cd "$CONTENT_REPO" && git branch --show-current)

if [ "$CURRENT_BRANCH" != "$CONTENT_BRANCH" ]; then
    echo ""
    echo "⚠️  ═══════════════════════════════════════════════════════════"
    echo "⚠️  BRANCH MISMATCH!"
    echo "⚠️  ═══════════════════════════════════════════════════════════"
    echo ""
    echo "Expected branch: $CONTENT_BRANCH"
    echo "Current branch:  $CURRENT_BRANCH"
    echo ""
    echo "📋 To fix this, choose one option:"
    echo ""
    echo "   Option 1: Switch to the configured branch"
    echo "      cd $CONTENT_REPO"
    echo "      git checkout $CONTENT_BRANCH"
    echo ""
    echo "   Option 2: Update config.toml to use current branch"
    echo "      Edit config.toml and set:"
    echo "      [paths]"
    echo "      content_branch = \"$CURRENT_BRANCH\""
    echo ""
    echo "   Option 3: Create the branch if it doesn't exist"
    echo "      cd $CONTENT_REPO"
    echo "      git checkout -b $CONTENT_BRANCH"
    echo ""
    exit 1
fi

echo "✓ Wikicontent found: $CONTENT_REPO"
echo "✓ Branch confirmed: $CONTENT_BRANCH"

# Ensure agents directory exists in wikicontent
AGENTS_DIR="$CONTENT_REPO/agents"
if [ ! -d "$AGENTS_DIR" ]; then
    echo "📁 Creating agents directory..."
    mkdir -p "$AGENTS_DIR/logs"
    echo "✓ Created $AGENTS_DIR"
fi

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
