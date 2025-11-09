# Mechawiki UI Plan 🏰⚔️
*RPG-Inspired Wiki Agent Interface*

## 🎯 Vision

A dual-pane web interface where users can observe and interact with AI agents as they read stories and build wiki content. The UI has a light, RPG-inspired aesthetic that makes the experience feel fun and game-like.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                      Top Bar                             │
│  [MechaWiki Logo] [Project Selector] [Status] [Settings]│
└─────────────────────────────────────────────────────────┘
┌──────────────────────┬──────────────────────────────────┐
│   LEFT PANE          │        RIGHT PANE                │
│   Agents             │        Files                     │
│                      │                                  │
│ ┌──────────────────┐ │ ┌──────────────────────────────┐ │
│ │ Command Center   │ │ │ Files Feed                   │ │
│ │ - Agent List     │ │ │ - Chronological             │ │
│ │ - Status (●/●)   │ │ │ - +17 -5 diffs              │ │
│ │ - Last Action    │ │ │ - Filter by agent           │ │
│ │ - [+ New Agent]  │ │ │ - Click to view             │ │
│ └──────────────────┘ │ └──────────────────────────────┘ │
│        OR            │           OR                     │
│ ┌──────────────────┐ │ ┌──────────────────────────────┐ │
│ │ Agent View       │ │ │ File Viewer                  │ │
│ │ - Thoughts       │ │ │ - Monaco Editor              │ │
│ │ - Tool Calls     │ │ │ - [Edit] toggle              │ │
│ │ - Messages       │ │ │ - Rendered preview           │ │
│ │ - [Chat box]     │ │ │ - Save button                │ │
│ └──────────────────┘ │ └──────────────────────────────┘ │
└──────────────────────┴──────────────────────────────────┘
```

## 📦 Tech Stack

### Backend (Flask + Python)
- **Flask**: Web server and API
- **Flask-CORS**: Cross-origin requests
- **watchdog**: File system monitoring for ~/Dev/wikicontent
- **Server-Sent Events (SSE)**: Real-time updates to frontend
- **Threading**: Background agent execution

### Frontend (React + Vite)
- **React 18**: UI framework
- **Vite**: Build tool and dev server
- **Monaco Editor**: Code/markdown editing
- **React Markdown**: Render markdown preview
- **CSS Modules**: RPG-inspired styling

## 🗂️ Project Structure

```
mechawiki/
├── src/
│   ├── agents/           # Agent implementations
│   │   ├── reader_agent.py
│   │   └── mock_agent.py  # NEW: Dummy agent for testing
│   ├── server/           # NEW: Flask backend
│   │   ├── app.py        # Main Flask app
│   │   ├── agents.py     # Agent management API
│   │   ├── files.py      # File watching & API
│   │   └── config.py     # Config management
│   └── ui/               # NEW: React frontend
│       ├── src/
│       │   ├── App.jsx
│       │   ├── components/
│       │   │   ├── AgentsPane/
│       │   │   │   ├── CommandCenter.jsx
│       │   │   │   ├── AgentView.jsx
│       │   │   │   └── NewAgentModal.jsx
│       │   │   ├── FilesPane/
│       │   │   │   ├── FilesFeed.jsx
│       │   │   │   └── FileViewer.jsx
│       │   │   └── TopBar.jsx
│       │   ├── styles/
│       │   │   └── rpg-theme.css
│       │   └── utils/
│       │       └── api.js
│       ├── package.json
│       └── vite.config.js
├── data/                 # NEW: Agent configs and logs
│   ├── agents.json       # Active agents configuration
│   └── logs/             # Agent log files
│       └── agent_{id}.jsonl
└── config.toml           # Project config
```

## 🔧 Backend API Design

### Agent Management Endpoints

```python
GET  /api/agents              # List all agents
POST /api/agents/create       # Create new agent
GET  /api/agents/{id}         # Get agent details
POST /api/agents/{id}/pause   # Pause agent
POST /api/agents/{id}/resume  # Resume agent
POST /api/agents/{id}/archive # Archive agent
POST /api/agents/{id}/message # Send message to agent

GET  /api/agents/{id}/logs    # Get agent logs (SSE stream)
```

### File Management Endpoints

```python
GET  /api/files              # List files in wikicontent
GET  /api/files/feed         # SSE stream of file changes
GET  /api/files/{path}       # Get file content
POST /api/files/{path}       # Save file content

GET  /api/files/changes      # Get recent file changes (with diffs)
```

### Health & Status

```python
GET  /api/health             # Server health check
GET  /api/status             # Overall system status
```

## 📝 Agent Config Format

**`data/agents.json`**
```json
{
  "agents": [
    {
      "id": "reader-001",
      "name": "Reader Agent 1",
      "type": "ReaderAgent",
      "status": "running",  // "running", "paused", "waiting_for_input", "stopped", "archived"
      "created_at": "2025-11-08T10:30:00Z",
      "config": {
        "story": "tales_of_wonder",
        "chunk_size": 500,
        "auto_pause": false
      },
      "log_file": "logs/agent_reader-001.jsonl"
    }
  ]
}
```

**Note:** Status ("running", "paused", "waiting_for_input", "stopped", "archived") and last action details are derived from reading the log file. The config file only stores the agent's identity and configuration.
- **running**: Agent actively processing
- **paused**: User manually paused the agent
- **waiting_for_input**: Agent needs user input to continue
- **stopped**: Agent has finished or been stopped
- **archived**: Agent is archived (inactive)

**Agent Log Format (`logs/agent_{id}.jsonl`)**
```jsonl
{"timestamp": "2025-11-08T10:30:00Z", "type": "status", "status": "running", "message": "Agent initialized"}
{"timestamp": "2025-11-08T10:30:15Z", "type": "tool_call", "tool": "advance", "args": {"num_words": 500}}
{"timestamp": "2025-11-08T10:30:16Z", "type": "tool_result", "tool": "advance", "result": "Advanced to word 500"}
{"timestamp": "2025-11-08T10:30:20Z", "type": "message", "role": "assistant", "content": "This story begins with..."}
{"timestamp": "2025-11-08T10:30:25Z", "type": "tool_call", "tool": "create_image", "args": {"prompt": "A dark castle on a hill"}}
{"timestamp": "2025-11-08T10:32:00Z", "type": "status", "status": "waiting_for_input", "message": "Should I continue with the next chunk?"}
{"timestamp": "2025-11-08T10:35:00Z", "type": "user_message", "content": "Yes, continue reading"}
{"timestamp": "2025-11-08T10:35:01Z", "type": "status", "status": "running", "message": "Resuming from user input"}
```

**Note:** The backend reads the log file to determine current status (last status entry), last action (last non-status entry), and agent history.

## 🎮 Agent Types (v0)

Based on the agent specs, we'll implement these agent types:

### Reader Agent
**Purpose**: Read stories and create encyclopedic wiki content  
**Tools**: advance(), read_article(), write_article(), search(), create_image()  
**Behavior**: Processes story chunks, creates/updates wiki articles, generates images

### Writer Agent  
**Purpose**: Take structured content and write stories  
**Tools**: read_article(), search(), write_story(), edit_story(), create_image()  
**Behavior**: Reads wiki content, writes prose, can revise earlier parts

### Interactive Agent
**Purpose**: Create RPG-like interactive experiences  
**Tools**: read_article(), search(), send_prose(), request_user_input(), create_image()  
**Behavior**: Writes prose, asks user for input, incorporates responses

*(Researcher and Recorder agents deferred to post-v0)*

## 🎮 Mock Agent for Testing

Create a simple `MockAgent` that simulates real agent behavior:
1. Runs in a loop with 1-3 second delays
2. Randomly performs actions:
   - Read a random file from wikicontent (log it)
   - Write/edit a random article (log with file path)
   - Generate a random "thought" message
   - Generate a random talk message
   - Create a random tool call (advance, search, etc.)
   - Occasionally change status to `waiting_for_input` (for Interactive type)
3. **Writes all actions to JSONL log file** with file paths
4. Simulates tool calls and messages

This lets us test:
- **Log file watching** (not file system watching!)
- Agent status indicators from logs
- Real-time log streaming to UI
- **File feed derived from agent logs**
- Chat message queueing
- Pause/resume functionality

## 🎨 UI Design Details

### RPG-Inspired Theme
- **Colors**:
  - Background: Parchment-like beige/cream (#F5F1E8)
  - Primary: Medieval blue (#2C5F99)
  - Accent: Gold (#D4AF37)
  - Success: Forest green (#2D5016)
  - Warning: Amber (#FF8C00)
  
- **Typography**:
  - Headers: Serif font with slight embellishment
  - Body: Clean sans-serif for readability, Papyrus-inspired fonts
  - Code: Monospace (Monaco default)

- **UI Elements**:
  - Subtle borders with aged paper texture
  - Status indicators: Glowing orbs (green/yellow/red)
  - Buttons: Slight 3D effect with hover state
  - Cards: Soft shadows, rounded corners

### Agents Pane - Command Center

```
┌─────────────────────────────────────────┐
│ 🏰 Agents Command Center                │
│                              [+ New]     │
├─────────────────────────────────────────┤
│ ● Reader Agent 1            [⏸][□][📦]  │
│   ReaderAgent • word 2500/10000          │
│   Last: Read chunk 5 of story            │
│   2m ago                                 │
├─────────────────────────────────────────┤
│ ◉ Wiki Builder Beta         [▶][□][📦]  │
│   WriterAgent • Waiting for input        │
│   Last: Updated "London" article         │
│   5m ago                                 │
├─────────────────────────────────────────┤
│ ◐ Image Generator          [▶][□][📦]  │
│   ImageAgent • Paused by user            │
│   Last: Created castle.png               │
│   10m ago                                │
└─────────────────────────────────────────┘

Legend:
● = Running (green)
◉ = Waiting for input (yellow/gold with pulse)
◐ = Paused by user (yellow)
○ = Stopped (gray)
[⏸] = Pause button (when running)
[▶] = Resume button (when paused/waiting)
[□] = Stop
[📦] = Archive
```

### Agents Pane - Individual Agent View

```
┌─────────────────────────────────────────┐
│ ← Back to Command Center                │
│ ● Reader Agent 1                          │
│   ReaderAgent • Running                  │
├─────────────────────────────────────────┤
│ [Messages] [Tools] [Thoughts] [Config]  │
├─────────────────────────────────────────┤
│                                          │
│ 🧠 Thinking...                           │
│ This passage describes London in a       │
│ dreamlike state...                       │
│                                          │
│ 🔧 advance(num_words=500)                │
│ → Advanced to word 2500 (25% complete)   │
│                                          │
│ 🤖 Assistant                             │
│ I found an interesting description of    │
│ London. Let me create an image for this. │
│                                          │
│ 🔧 create_image(name="dreamy-london")    │
│ → Created image: dreamy-london.png       │
│                                          │
│ ◉ Agent waiting for input                │
│                                          │
├─────────────────────────────────────────┤
│ [Type a message...            ] [Send]  │
└─────────────────────────────────────────┘
```

### Files Pane - Files Feed

```
┌─────────────────────────────────────────┐
│ 📚 Files Feed                            │
│ [All Agents ▼] [Search...]              │
├─────────────────────────────────────────┤
│ 📄 london.md                +17 -5      │
│    Reader Agent 1 • 2m ago               │
│                                          │
│ 🖼️ dreamy-london.png        +1 (new)   │
│    Reader Agent 1 • 5m ago               │
│                                          │
│ 📄 hasheesh-eater.md        +8 -2       │
│    Wiki Builder Beta • 10m ago          │
│                                          │
│ 📄 tales-of-wonder.md       +3 -0       │
│    Reader Agent 1 • 15m ago              │
└─────────────────────────────────────────┘
```

### Files Pane - File Viewer

```
┌─────────────────────────────────────────┐
│ 📄 london.md                             │
│ [< Back] [Render ▼] [Edit] [Save]      │
├─────────────────────────────────────────┤
│ RENDER MODE:                             │
│ # London                                 │
│                                          │
│ London is a great city mentioned in     │
│ "A Tale of London" from Tales of Wonder │
│ by Lord Dunsany.                         │
│                                          │
│ See also: [Hasheesh Eater], [Sultan]   │
│           ^^^^^^^^^^^^^^^^  ^^^^^^^^    │
│           (clickable wiki links)         │
│                                          │
│ In the hasheesh eater's vision...       │
│                                          │
│ --- OR ---                               │
│                                          │
│ EDIT MODE:                               │
│ (Monaco editor with syntax highlighting) │
│ Full markdown source, editable           │
│                                          │
└─────────────────────────────────────────┘
```

**Wiki Link Features:**
- Internal links like `[Article Name]` or `[[Article Name]]` are clickable
- Clicking a wiki link opens that article in the same pane
- Links to non-existent articles show in different color (red/dashed)
- Support for both `[article-name.md]` and `[Article Name]` formats
- Auto-complete suggestions when typing `[[` in edit mode

## 🔄 Real-Time File Watching

### Approach: Python `watchdog` + Server-Sent Events (SSE)

**The Plan:**
1. Use `watchdog` library to monitor `~/Dev/wikicontent` for file changes
2. When files change, calculate diffs and push to SSE queue
3. Frontend subscribes to SSE endpoint for real-time updates

### Backend Implementation

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import queue
import hashlib

class WikiContentHandler(FileSystemEventHandler):
    def __init__(self, sse_queue):
        self.sse_queue = sse_queue
        self.file_hashes = {}  # Track file hashes to avoid duplicate events
    
    def _get_file_hash(self, file_path):
        """Get MD5 hash of file content."""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return None
    
    def on_modified(self, event):
        if event.is_directory:
            return
        
        # Check if file actually changed (watchdog can fire multiple times)
        file_hash = self._get_file_hash(event.src_path)
        if file_hash == self.file_hashes.get(event.src_path):
            return  # No actual change
        
        self.file_hashes[event.src_path] = file_hash
        
        # Calculate diff
        file_path = event.src_path
        changes = self._calculate_diff(file_path)
        
        # Send to SSE queue
        self.sse_queue.put({
            'type': 'file_changed',
            'path': file_path,
            'changes': changes,
            'timestamp': datetime.now().isoformat(),
            'agent_id': self._detect_agent(file_path)
        })
    
    def on_created(self, event):
        if event.is_directory:
            return
        
        self.sse_queue.put({
            'type': 'file_created',
            'path': event.src_path,
            'timestamp': datetime.now().isoformat()
        })
    
    def _calculate_diff(self, file_path):
        """Calculate +/- lines changed (simplified)."""
        # TODO: Implement proper diff tracking
        return {"added": 0, "removed": 0}
    
    def _detect_agent(self, file_path):
        """Detect which agent modified the file."""
        # TODO: Track agent -> file writes
        return "unknown"

# Start file watcher
sse_queue = queue.Queue()
observer = Observer()
handler = WikiContentHandler(sse_queue)
observer.schedule(handler, path=WIKICONTENT_PATH, recursive=True)
observer.start()
```

### Frontend Implementation

```javascript
// Subscribe to file changes
const eventSource = new EventSource('/api/files/feed');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'file_changed') {
    // Update files feed
    setFileChanges(prev => [data, ...prev]);
    
    // If currently viewing this file, prompt to reload
    if (currentFile === data.path) {
      showReloadPrompt();
    }
  }
};
```

### ✨ Better Approach: Watch Agent Logs!

**The key insight**: Instead of watching the file system, **watch the agent JSONL log files**!

Each agent writes to `logs/agent_{id}.jsonl`. When agents perform file operations, they log them:

```jsonl
{"timestamp": "...", "type": "tool_call", "tool": "write_article", "args": {"article": "london.md", "content": "..."}}
{"timestamp": "...", "type": "tool_result", "tool": "write_article", "result": {"file_path": "articles/london.md", "lines_added": 17, "lines_removed": 5}}
```

**Advantages:**
✅ **Perfect agent attribution** - it's in the log!  
✅ **Diff info available** - agents can log +X -Y in tool results  
✅ **No duplicate events** - logs are append-only  
✅ **Catches all agent activity** - not just file writes  
✅ **Single source of truth** - logs already exist for agent history

**Implementation:**
1. Watch agent log files with `watchdog`
2. Parse new JSONL entries as they're appended
3. Extract file operations from tool calls/results
4. Build Files Feed from log entries
5. Get file content by reading actual files when needed

**For user edits**: We can still use git to detect uncommitted changes in wikicontent, or simply let users refresh manually. The primary use case is watching agents, not tracking manual edits.

## 🚀 Implementation Phases

### Phase 1: Foundation (Focus on UI)
- ✅ Flask backend skeleton
- ✅ React frontend with Vite
- ✅ Basic routing and layout
- ✅ Mock agent that generates dummy activity
- ✅ Agent config file structure

### Phase 2: Agents Pane
- Build Command Center view
- Build Individual Agent view
- New Agent modal
- Agent controls (pause/resume/archive)
- Real-time agent status updates

### Phase 3: Files Pane
- Build Files Feed
- File watcher backend
- Monaco editor integration
- Edit/Render toggle
- Real-time file updates

### Phase 4: Integration & Polish
- Wire up agents ↔ file watching
- Message queueing for agents
- RPG theme CSS
- Animations and transitions
- Error handling & edge cases

### Phase 5: Real Agents
- Integrate actual ReaderAgent
- Add more agent types
- Advanced agent configuration
- Agent-to-agent communication (future)

## 🚀 Start Script

Create `start.sh` at project root that:
1. Checks for Python & npm dependencies
2. Installs missing dependencies
3. Starts Flask backend (port 5000)
4. Starts Vite frontend (port 5173)
5. Directs user to http://localhost:5173

Inspired by mockecy's start.sh pattern.

## 🎯 Success Criteria

- [ ] User can see list of agents with status indicators
- [ ] User can create new agents via modal
- [ ] User can pause/resume/archive agents
- [ ] User can view individual agent's thoughts, tools, messages
- [ ] User can send messages to agents (queued if agent is busy)
- [ ] User can see chronological feed of file changes
- [ ] User can filter feed by agent
- [ ] User can click file to view in Monaco editor
- [ ] User can toggle between rendered markdown and edit mode
- [ ] File changes update in real-time
- [ ] UI has fun, RPG-inspired aesthetic
- [ ] Mock agent generates realistic dummy activity

## 🏰 The Quest Begins!

Ready to start building? Let's focus on **Phase 1: Foundation** first, getting the basic structure in place with mock agents. Then we'll build out the Agents pane (Phase 2) and Files pane (Phase 3) before polishing everything up!

**Stay the course, and let's build this with swift and decisive action!** ⚔️

