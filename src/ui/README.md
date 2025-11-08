# MechaWiki UI - Getting Started 🏰⚔️

## Quick Start

```bash
./start.sh
```

This will:
1. Check and install Python & npm dependencies
2. Start the Flask backend (port 5000)
3. Start the Vite frontend (port 5173)
4. Open your browser to http://localhost:5173

## What's Been Built

### ✅ Backend (Flask + Python)
- **Agent Management API** (`src/server/agents.py`)
  - Create, pause, resume, archive agents
  - Send messages to agents
  - Stream agent logs via SSE
- **File Management API** (`src/server/files.py`)
  - List files from wikicontent
  - Get file content
  - Save file edits
  - Stream file changes via SSE
- **Log Watcher** (`src/server/log_watcher.py`)
  - Watches agent JSONL log files
  - Extracts file operations and status changes
  - Provides real-time updates to frontend
- **Mock Agent** (`src/agents/mock_agent.py`)
  - Simulates agent behavior for testing
  - Generates random activity (read/write files, think, talk)
  - Logs everything to JSONL

### ✅ Frontend (React + Vite)
- **Top Bar** - Connection status, branding
- **Agents Pane** (Left Side)
  - **Command Center**: List all agents with status indicators
  - **Agent View**: Individual agent logs, chat interface
  - **New Agent Modal**: Create agents with type selection
- **Files Pane** (Right Side)
  - **Files Feed**: Chronological feed of file changes (+X -Y diffs)
  - **File Viewer**: Monaco editor with edit/render toggle, wiki links
- **RPG-Inspired Theme**: Parchment backgrounds, medieval blue & gold accents

## Architecture Highlights

### Log-Based Updates (Key Innovation!)
Instead of watching the file system, we watch agent JSONL logs:
- Agents write all actions to `data/logs/agent_{id}.jsonl`
- Backend watches these files with `watchdog`
- File operations are logged with paths and diffs
- Frontend gets real-time updates via SSE

**Benefits:**
- ✅ Perfect agent attribution
- ✅ Complete activity history
- ✅ No duplicate file events
- ✅ Single source of truth

### Agent Types (v0)
1. **ReaderAgent** - Reads stories, creates wiki content
2. **WriterAgent** - Writes stories from wiki content
3. **InteractiveAgent** - Creates RPG-like experiences with user input

## Testing the UI

### 1. Start the Servers
```bash
./start.sh
```

### 2. Create a Mock Agent
In the UI:
1. Click "+ New Agent"
2. Name it "Test Reader"
3. Select "ReaderAgent"
4. Click "Create Agent"

### 3. Start the Mock Agent (Terminal)
```bash
cd /home/keenan/Dev/mechawiki
source .venv/bin/activate
python -c "
from src.agents.mock_agent import MockAgent
from pathlib import Path

# Create and start mock agent
log_file = Path('data/logs/agent_reader-20250108120000.jsonl')
wikicontent = Path.home() / 'Dev' / 'wikicontent'

agent = MockAgent('reader-20250108120000', 'ReaderAgent', log_file, wikicontent)
agent.start()

# Run for 60 seconds
import time
try:
    time.sleep(60)
except KeyboardInterrupt:
    pass

agent.stop()
"
```

You should see:
- Agent appears in Command Center
- Status changes (running → paused → waiting for input)
- Tool calls in Agent View
- File changes in Files Feed
- Real-time log streaming

## Project Structure

```
mechawiki/
├── start.sh                 # One-command startup
├── run_server.py            # Flask server entry point
├── config.toml              # Configuration
├── requirements.txt         # Python deps
├── data/
│   ├── agents.json          # Agent registry
│   └── logs/                # Agent JSONL logs
└── src/
    ├── server/              # Flask backend
    │   ├── app.py           # Main app
    │   ├── agents.py        # Agent endpoints
    │   ├── files.py         # File endpoints
    │   ├── config.py        # Config management
    │   └── log_watcher.py   # Log file watcher
    ├── agents/              # Agent implementations
    │   ├── reader_agent.py  # Real reader agent
    │   └── mock_agent.py    # Mock for testing
    └── ui/                  # React frontend
        ├── src/
        │   ├── App.jsx
        │   ├── components/
        │   │   ├── TopBar.jsx
        │   │   ├── AgentsPane.jsx
        │   │   ├── FilesPane.jsx
        │   │   ├── agents/
        │   │   │   ├── CommandCenter.jsx
        │   │   │   ├── AgentView.jsx
        │   │   │   └── NewAgentModal.jsx
        │   │   └── files/
        │   │       ├── FilesFeed.jsx
        │   │       └── FileViewer.jsx
        │   └── utils/
        │       └── time.js
        └── package.json
```

## Next Steps

### Integrate Real Agents
Replace mock agents with actual ReaderAgent/WriterAgent that use LLMs.

### Add More Features
- Agent-to-agent messaging (Researcher ↔ Interactive)
- Advanced file diff view
- Search across logs
- Export agent conversations
- Multi-user support

### Polish
- Better error handling
- Loading states
- Animations
- Keyboard shortcuts
- Dark mode toggle

## Development

### Backend Only
```bash
source .venv/bin/activate
python run_server.py
```

### Frontend Only
```bash
cd src/ui
npm run dev
```

### Install New Python Package
```bash
source .venv/bin/activate
pip install <package>
pip freeze > requirements.txt
```

### Install New npm Package
```bash
cd src/ui
npm install <package>
```

## Troubleshooting

**Port already in use:**
```bash
# Kill processes on ports 5000 or 5173
lsof -ti:5000 | xargs kill -9
lsof -ti:5173 | xargs kill -9
```

**Backend won't start:**
- Check `config.toml` exists
- Ensure Python 3.8+
- Check logs in terminal

**Frontend won't start:**
- Ensure Node.js 18+
- Delete `node_modules` and `npm install`
- Check for port conflicts

**No agents showing:**
- Check backend is running (http://localhost:5000/api/health)
- Check `data/agents.json` exists
- Create an agent via UI

## Design Philosophy

**"Swift and Decisive"** - The UI loads fast and updates in real-time

**"Strong defenses win campaigns"** - Log-based architecture prevents race conditions

**"The Working Code"** - Built with proven libraries (Flask, React, Monaco)

**"One quest at a time"** - Clean component separation, each does one thing well

---

**Ready to build with the agents? The UI is your command center!** 🏰⚔️

