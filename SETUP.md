# MechaWiki Setup Guide

Quick setup instructions for getting MechaWiki running.

---

## Prerequisites

- **Python 3.8+**
- **Node.js 18+**
- **Git**

---

## Quick Start

### 1. Clone Repositories

```bash
cd ~/Dev

# Clone MechaWiki
git clone <mechawiki-repo-url> mechawiki

# Clone AgenticMemory (for memtool dependency)
git clone --recurse-submodules <AgenticMemory-repo-url> AgenticMemory
```

**Important:** Both repos should be in the same parent directory (e.g., `~/Dev/`) for automatic setup.

### 2. Set Up Wikicontent

MechaWiki needs a git-managed content repository:

```bash
# Option A: Clone existing wikicontent
git clone <wikicontent-repo-url> ~/Dev/wikicontent

# Option B: Create new wikicontent
mkdir -p ~/Dev/wikicontent
cd ~/Dev/wikicontent
git init
mkdir articles images stories agents
git add .
git commit -m "Initial commit"
```

### 3. Configure

```bash
cd ~/Dev/mechawiki

# Copy example config
cp config.example.toml config.toml

# Edit config.toml and set:
# - Your API key (ANTHROPIC_API_KEY or OPENAI_API_KEY)
# - Path to wikicontent (if different from ~/Dev/wikicontent)
```

### 4. Run!

```bash
./start.sh
```

That's it! The script will:
- ✅ Create Python virtual environment
- ✅ Install all dependencies (including memtool)
- ✅ Start memtool server
- ✅ Start Flask backend
- ✅ Start Vite frontend

Open **http://localhost:5173** in your browser!

---

## Troubleshooting

### "memtool not found"

If you see this error, make sure AgenticMemory is cloned:

```bash
cd ~/Dev
git clone --recurse-submodules <AgenticMemory-repo-url> AgenticMemory

# Then try again
cd mechawiki
./start.sh
```

The script checks these locations:
- `~/Dev/AgenticMemory/memtool`
- `../AgenticMemory/memtool` (relative to mechawiki)
- `/home/keenan/Dev/AgenticMemory/memtool` (absolute)

If your AgenticMemory is in a different location:

```bash
cd ~/Dev/mechawiki
source .venv/bin/activate
pip install -e /path/to/AgenticMemory/memtool
```

### "wikicontent not found"

Make sure wikicontent exists and is a git repository:

```bash
cd ~/Dev/wikicontent
git status  # Should show it's a git repo

# If not initialized:
git init
git add .
git commit -m "Initial commit"
```

Then update `config.toml`:

```toml
[paths]
content_repo = "/path/to/your/wikicontent"
```

### Port already in use

If port 5000 or 5173 is already in use:

```bash
# Find and kill the process
lsof -ti:5000 | xargs kill
lsof -ti:5173 | xargs kill
```

---

## Development

### Backend only
```bash
source .venv/bin/activate
python run_server.py
```

### Frontend only
```bash
cd src/ui
npm run dev
```

### View logs
```bash
tail -f backend.log
tail -f frontend.log
tail -f memtool.log
```

---

## What's Included

### Dependencies Auto-Installed
- **Python packages** (Flask, litellm, etc.)
- **Node packages** (React, Vite, etc.)
- **memtool** (multi-document context expansion)

### Services Started
1. **memtool server** (port 18861) - Context expansion
2. **Flask backend** (port 5000) - API and agents
3. **Vite frontend** (port 5173) - React UI

---

## Architecture

```
MechaWiki/
├── src/
│   ├── agents/          # Agent implementations
│   ├── tools/           # Agent tools (including get_context)
│   ├── server/          # Flask backend
│   └── ui/              # React frontend
├── data/sessions/       # Session data and logs
├── config.toml          # Configuration
└── start.sh             # Startup script

wikicontent/             # Separate git repo
├── articles/            # Wiki articles
├── images/              # Generated images
├── stories/             # Generated stories
└── agents/              # Agent configs and logs

AgenticMemory/           # Separate git repo (dependency)
└── memtool/             # Context expansion tool
```

---

## Next Steps

1. **Open UI:** http://localhost:5173
2. **Check agents:** See 3 demo agents (paused by default)
3. **Resume an agent:** Click ▶️ to start
4. **Create new agent:** Click "New Agent" button
5. **Explore tools:** Agents have access to `get_context()` for rich multi-document queries

---

## Documentation

- **Full integration:** `notes/ai/MEMTOOL_INTEGRATION_COMPLETE.md`
- **Memory algorithm:** `notes/ai/MEMORY_ALGORITHM_DEEP_DIVE.md`
- **Project docs:** `notes/` directory

---

**Questions?** Check the `notes/` directory or ask the team!

