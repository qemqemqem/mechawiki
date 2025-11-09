# MechaWiki 🏰

**AI-powered story analysis and wiki generation system with real-time agent monitoring**

MechaWiki is a project that uses AI agents to read stories, write stories, and create interactive RPG experiences - all while building a wiki of structured content.

## Quick Start

```bash
./start.sh
```

Visit **http://localhost:5173** to see the UI!

The system starts with **3 demo agents** (one of each type), **truly paused from the start** (no race conditions!):
- 🤖 **Reader Agent 1** (ReaderAgent) - Reads articles and advances through stories
- ✍️ **Writer Agent 1** (WriterAgent) - Writes stories from wiki content
- 🎮 **Interactive Agent 1** (InteractiveAgent) - Creates interactive experiences

**To activate:** Click the ▶️ resume button in the UI for each agent you want to run.

**Create new agents:** Use the "New Agent" button - these start running immediately.

### ⚡ Real Agents Enabled by Default!

MechaWiki now uses **real LLM-powered agents** by default:
- Event-based generators that yield events instead of printing
- AgentRunner consumes events and writes to JSONL logs
- Line-at-a-time buffering for responsive streaming
- 300k context limit with automatic archiving
- All 3 agent types: ReaderAgent, WriterAgent, InteractiveAgent

**Requirements:** Add your Claude API key to `config.toml`

**Test without UI:** `python test_real_agents.py`

### 🌿 Branch-Based Configuration

MechaWiki uses git branches in your wikicontent repository for project isolation. All agent data (configurations, logs, costs) is stored in the `agents/` directory on your current branch.

Configure your branch in `config.toml`:
```toml
[paths]
content_repo = "/home/keenan/Dev/wikicontent"
content_branch = "tales_of_wonder/main"
```

Switch projects by checking out a different branch in wikicontent and updating `config.toml`.

See `notes/IMPLEMENTATION_COMPLETE.md` for full details!

## What Is This?

MechaWiki uses AI agents that read through stories (like *Dracula* or *Tales of Wonder*) and automatically create wiki-style documentation about characters, locations, themes, and plot points. It can also work in reverse - taking wiki content and writing stories from it.

### Agent Types (v0)

- **Reader Agent** - Processes stories chunk-by-chunk, creates wiki articles, generates images
- **Writer Agent** - Takes wiki content and writes compelling prose
- **Interactive Agent** - Creates RPG-like experiences where users become part of the story

## Content Repository (Wikicontent)

MechaWiki stores all wiki content and agent data in a **separate git repository** called "wikicontent". This separation allows you to:
- Version control your content independently from the application code
- Share content repos between team members
- Work on multiple projects by switching branches
- Back up and sync content using git

### Repository Location

By default, wikicontent is expected at `~/Dev/wikicontent` but you can configure any location in `config.toml`:

```toml
[paths]
content_repo = "/home/keenan/Dev/wikicontent"  # Your wikicontent location
content_branch = "tales_of_wonder/main"        # Which branch to use
```

**Note:** The `start.sh` script validates this location and branch before starting. If not found, it provides clear instructions on how to set it up.

### Repository Structure

Your wikicontent repository should have this structure:

```
wikicontent/                    # Root of content repository (separate git repo)
├── .git/                       # Git tracking
│
├── articles/                   # Wiki articles (markdown)
│   ├── lord-dunsany.md
│   ├── tales-of-wonder.md
│   └── ...
│
├── stories/                    # Story files
│   ├── the-sultans-dreamer.md
│   ├── the-mist-keeper.md
│   └── ...
│
├── images/                     # Generated or uploaded images
│   ├── dunsany-london-dream.png
│   └── ...
│
├── songs/                      # Song/poem content (optional)
│
├── story.txt                   # Main source story (if using ReaderAgent)
│
└── agents/                     # Agent data (per branch, git-tracked)
    ├── agents.json             # Agent configurations
    ├── costs.log               # LLM cost tracking
    └── logs/                   # Agent activity logs (JSONL)
        ├── agent_reader-001.jsonl
        ├── agent_writer-001.jsonl
        └── agent_interactive-001.jsonl
```

### Setting Up Wikicontent

**Option 1: Create a new repository**
```bash
mkdir -p ~/Dev/wikicontent
cd ~/Dev/wikicontent
git init
mkdir -p articles stories images agents/logs
echo "# My Wiki Content" > README.md
git add .
git commit -m "Initial commit"
```

**Option 2: Clone an existing repository**
```bash
git clone <your-repo-url> ~/Dev/wikicontent
```

**Option 3: Use a different location**
```bash
# Create anywhere
mkdir -p /path/to/my/content && cd /path/to/my/content
git init

# Update config.toml to point to it
[paths]
content_repo = "/path/to/my/content"
```

### Branch Strategy

Use git branches to isolate different projects:

```bash
# Working on Tales of Wonder
cd ~/Dev/wikicontent
git checkout -b tales_of_wonder/main

# Working on Dracula analysis  
git checkout -b dracula/main

# Experimental features
git checkout -b tales_of_wonder/experimental
```

Update `config.toml` to match your active branch, and MechaWiki will use that branch's content and agents.

### Why Separate Repositories?

1. **Version Control**: Content changes are tracked independently from code changes
2. **Portability**: Share or backup content without the application
3. **Collaboration**: Multiple people can work on content using git workflows
4. **Branch Isolation**: Different projects/stories on different branches
5. **Size Management**: Large content repos don't bloat the main codebase

## Features

### 🎮 Real-Time Agent Monitoring
Watch your agents work through a beautiful RPG-inspired interface:
- See agent status (●running, ◉waiting for input, ◐paused)
- View tool calls, messages, and thinking in real-time
- Chat with agents while they're working
- Pause/resume/archive agents on the fly

### 📚 Live Wiki Feed
Track file changes as agents create and edit wiki content:
- Chronological feed of all file operations
- Diff summaries (+17 -5 lines changed)
- Filter by specific agent
- Click to view/edit files with Monaco editor

### 📝 Wiki-Style Content
- Markdown articles with clickable internal links
- Images generated by agents
- Structured data about stories
- Full edit capabilities through the UI

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Frontend (React)                  │
│  - Agents Pane: Command Center & Agent Views        │
│  - Files Pane: Feed & Viewer (Monaco Editor)        │
└────────────────────┬────────────────────────────────┘
                     │ SSE (Real-time updates)
┌────────────────────┴────────────────────────────────┐
│                 Backend (Flask)                      │
│  - Agent Management API                              │
│  - File Serving & Editing API                       │
│  - Log Watcher (monitors agent JSONL files)         │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────┐
│              Agent Log Files (JSONL)                 │
│  wikicontent/agents/logs/agent_{id}.jsonl           │
│  - All agent actions logged here                    │
│  - Backend watches these for updates                │
└─────────────────────────────────────────────────────┘
```

**Key Innovation**: Instead of watching the file system directly, we watch agent log files. This gives us perfect attribution, complete history, and eliminates race conditions.

## Project Structure

This repository (MechaWiki) contains only the application code:

- **`src/server/`** - Flask backend (Python)
- **`src/ui/`** - React frontend (Vite)
- **`src/agents/`** - Agent implementations (ReaderAgent, WriterAgent, InteractiveAgent)
- **`src/tools/`** - Agent tools (read/write articles, search, images, git operations)
- **`config.toml`** - Configuration (API keys, paths, settings)
- **`start.sh`** - Startup script (validates config and launches servers)

**All content lives in a separate git repository** (see [Content Repository](#content-repository-wikicontent) section above).

## Documentation

- **[UI Documentation](src/ui/README.md)** - Frontend setup and architecture
- **[Plan Document](notes/ui_plan.md)** - Full design and implementation plan
- **[Agent User Stories](notes/agents_user_stories.md)** - Agent types and use cases
- **[Agent Implementation](notes/agents_tools_and_implementation.md)** - Technical details

## Requirements

- **Python 3.8+** with pip
- **Node.js 18+** with npm
- **Git** (for wikicontent management)
- **Wikicontent Repository** - A separate git repository for content (see [Content Repository](#content-repository-wikicontent))

All Python and Node dependencies are auto-installed by `start.sh`.

The wikicontent repository must be set up before first run - `start.sh` will validate its location and provide setup instructions if needed.

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

### Test Real Agents
```bash
source .venv/bin/activate
python test_real_agents.py
```

This tests:
- Event streaming from BaseAgent
- AgentRunner event consumption
- All 3 agent types (Reader, Writer, Interactive)
- JSONL logging

### Initialize Mock Test Agents (Default)
```bash
source .venv/bin/activate
python src/server/init_agents.py --start
```

### Run Single Mock Agent (for testing)
```bash
source .venv/bin/activate
python src/agents/mock_agent.py
```

## Philosophy

This project follows XP (Extreme Programming) principles with an RPG flavor:

- **"Swift and Decisive"** - Real-time updates, fast iteration
- **"Strong defenses win campaigns"** - Log-based architecture prevents bugs
- **"The Working Code"** - Focus on delivering value, not perfect plans
- **"One quest at a time"** - Clean separation of concerns

## Status

**Phase 1: Foundation** ✅ COMPLETE
- Flask backend with SSE
- React frontend with RPG theme
- Mock agents for testing
- Real-time log streaming
- File viewing and editing

**Next Steps:**
- Integrate real LLM-powered agents
- Add Researcher & Recorder agents
- Enhanced file diff views
- Agent-to-agent messaging

---

**Built with passion for working code and epic adventures.** 🏰⚔️
