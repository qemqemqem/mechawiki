#!/bin/bash
# MechaWiki Startup Script
# Starts both backend and frontend servers

# Exit on any error
set -e

# Set UTF-8 encoding for Python (fixes emoji/Unicode issues on Windows)
export PYTHONIOENCODING=utf-8

echo "🏰 Starting MechaWiki..."
echo ""

# Check for Python
if ! command -v python &> /dev/null; then
    echo "❌ Python 3 not found!"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

echo "✓ Python 3 found: $(python --version)"

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
    python -m venv .venv
fi

echo "Activating virtual environment..."
source .venv/Scripts/activate

# Check if memtool is installed (key dependency)
if ! .venv/Scripts/python -c "import memtool" 2>/dev/null; then
    echo "Installing Python dependencies..."
    pip install -q -r requirements.txt
elif ! pip show flask &> /dev/null; then
    echo "Installing Python dependencies..."
    pip install -q -r requirements.txt
else
	pip install -q -r requirements.txt
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
WIKICONTENT_INFO=$(python << 'PYEOF'
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

# Clear debug logs on startup
DEBUG_LOGS_DIR="$AGENTS_DIR/debug_logs"
if [ -d "$DEBUG_LOGS_DIR" ]; then
    echo "🧹 Clearing debug logs..."
    rm -f "$DEBUG_LOGS_DIR"/*.log
    echo "✓ Debug logs cleared"
else
    echo "📁 Creating debug_logs directory..."
    mkdir -p "$DEBUG_LOGS_DIR"
    echo "✓ Created $DEBUG_LOGS_DIR"
fi

echo ""
echo "📋 Debug logs will be written to:"
echo "   Server:  $DEBUG_LOGS_DIR/server.log"
echo "   Agents:  $DEBUG_LOGS_DIR/{agent-id}.log"
echo ""

# Check for memtool installation and install if needed
echo "🧠 Checking memtool installation..."
if ! .venv/Scripts/python -c "import memtool" 2>/dev/null; then
    echo "⚠️  memtool not found, attempting to install..."
    
    # Common paths to check for AgenticMemory
    MEMTOOL_PATHS=(
        "/home/keenan/Dev/AgenticMemory/memtool"
        "../AgenticMemory/memtool"
        "~/Dev/AgenticMemory/memtool"
    )
    
    MEMTOOL_FOUND=false
    for MEMTOOL_PATH in "${MEMTOOL_PATHS[@]}"; do
        # Expand ~ if present
        EXPANDED_PATH="${MEMTOOL_PATH/#\~/$HOME}"
        
        if [ -d "$EXPANDED_PATH" ] && [ -f "$EXPANDED_PATH/pyproject.toml" ]; then
            echo "   Found memtool at: $EXPANDED_PATH"
            echo "   Installing..."
            if pip install -q -e "$EXPANDED_PATH"; then
                echo "✓ memtool installed successfully"
                MEMTOOL_FOUND=true
                break
            else
                echo "❌ Failed to install memtool"
                exit 1
            fi
        fi
    done
    
    if [ "$MEMTOOL_FOUND" = false ]; then
        echo ""
        echo "❌ ═══════════════════════════════════════════════════════════"
        echo "❌ MEMTOOL NOT FOUND!"
        echo "❌ ═══════════════════════════════════════════════════════════"
        echo ""
        echo "memtool provides multi-document context expansion for agents."
        echo ""
        echo "📋 To install, you need the AgenticMemory repository:"
        echo ""
        echo "   1. Clone AgenticMemory (if not already cloned):"
        echo "      cd ~/Dev"
        echo "      git clone --recurse-submodules <AgenticMemory-repo-url>"
        echo ""
        echo "   2. Then run this script again:"
        echo "      ./start.sh"
        echo ""
        echo "   OR install manually:"
        echo "      pip install -e /path/to/AgenticMemory/memtool"
        echo ""
        echo "📖 See: notes/ai/MEMTOOL_INTEGRATION_COMPLETE.md"
        echo ""
        exit 1
    fi
else
    echo "✓ memtool already installed"
fi

# Start memtool server
echo "🧠 Starting memtool server (port 18861)..."

# Check if server is already running (Windows-compatible)
if netstat -ano | grep ":18861" | grep "LISTENING" >/dev/null 2>&1 ; then
    echo "⚠️  Port 18861 is already in use!"
    echo "   This might be an old memtool server."
    echo "   Attempting to stop it..."

    # Try to stop via memtool CLI
    if .venv/Scripts/python -m memtool.cli server stop 2>/dev/null; then
        echo "✓ Stopped old server"
        sleep 1
    else
        # Force kill - get PID from netstat on Windows
        OLD_PID=$(netstat -ano | grep ":18861" | grep "LISTENING" | awk '{print $5}' | head -1)
        if [ -n "$OLD_PID" ]; then
            taskkill //PID $OLD_PID //F 2>/dev/null
            echo "✓ Killed process on port 18861"
            sleep 1
        fi
    fi
fi

# Start memtool server in background (no --repo argument needed)
.venv/Scripts/python -m memtool.cli server start --port 18861 > memtool.log 2>&1 &
MEMTOOL_PID=$!
echo "memtool PID: $MEMTOOL_PID"

# Wait for memtool to be ready
echo "⏳ Waiting for memtool server to initialize..."
sleep 2

# Check if memtool is still running
if ! kill -0 $MEMTOOL_PID 2>/dev/null; then
    echo ""
    echo "❌ ═══════════════════════════════════════════════════════════"
    echo "❌ MEMTOOL SERVER FAILED TO START!"
    echo "❌ ═══════════════════════════════════════════════════════════"
    echo ""
    echo "Last 20 lines of memtool.log:"
    echo "─────────────────────────────────────────────────────────────"
    tail -20 memtool.log
    echo "─────────────────────────────────────────────────────────────"
    echo ""
    exit 1
fi

# Build index (or load if exists)
echo "📚 Building/loading memtool index..."

if ! .venv/Scripts/python scripts/ensure_memtool_index.py; then
    echo "❌ Index build/load failed"
    kill $MEMTOOL_PID 2>/dev/null
    exit 1
fi

echo "✓ memtool server ready"
echo ""

# Start backend in background
echo "🚀 Starting Flask backend (port 5000)..."
source .venv/Scripts/activate
python run_server.py > backend.log 2>&1 &
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

# Trap Ctrl+C to kill all processes
trap "echo ''; echo '🛑 Stopping servers...'; kill $MEMTOOL_PID $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT

# Wait for both processes
wait
