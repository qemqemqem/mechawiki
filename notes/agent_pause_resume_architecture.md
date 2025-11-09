# Agent Pause/Resume Architecture 🎮

## The Challenge

When a user clicks "Pause" or "Resume" in the UI, how does the agent (running in a separate background thread) know to stop/start its activity?

## Current State (Broken)

Currently:
1. UI sends `POST /api/agents/{id}/pause`
2. Backend writes a log entry: `{"type": "status", "status": "paused", ...}`
3. **But the agent thread keeps running!** ❌

The `MockAgent` class has a `self.paused` flag, but nothing is checking it except within `_random_action()`, and nothing is setting it except the agent itself during `wait_for_input`.

## The Architecture Question

There are several approaches:

### Option 1: Log File as Control Channel ⭐ RECOMMENDED

**How it works:**
- Agent's inner loop reads its own log file before each action
- If it sees a `status: "paused"` entry newer than its last action, it pauses
- When paused, it continuously checks the log for `status: "running"` entries

**Pros:**
- Consistent with our "logs are source of truth" philosophy
- No shared state between Flask process and agent threads
- Pause/resume commands are permanently recorded
- Works even if agent is restarted

**Cons:**
- Agents must read their log file frequently
- Slight delay (up to action interval) before pause takes effect

**Implementation:**
```python
class MockAgent:
    def __init__(self, ...):
        self.last_checked_timestamp = None
        
    def _check_control_commands(self):
        """Read log file for control commands."""
        with open(self.log_file, 'r') as f:
            for line in f:
                entry = json.loads(line)
                timestamp = entry.get('timestamp')
                
                # Only check entries newer than our last check
                if self.last_checked_timestamp and timestamp <= self.last_checked_timestamp:
                    continue
                
                if entry.get('type') == 'status':
                    status = entry.get('status')
                    if status == 'paused':
                        self.paused = True
                    elif status == 'running' and self.paused:
                        self.paused = False
                        
        self.last_checked_timestamp = datetime.now().isoformat()
    
    def _run_loop(self):
        while self.running:
            # Check for control commands
            self._check_control_commands()
            
            if self.paused:
                time.sleep(0.5)  # Check more frequently when paused
                continue
            
            # Do action...
```

### Option 2: Shared State Dictionary

**How it works:**
- Flask maintains a global dict: `agent_states = {"agent-001": {"paused": False}}`
- Agent threads check this dict in their loop

**Pros:**
- Immediate effect (no delay)
- Simple implementation

**Cons:**
- Shared state between processes (need locks)
- Not recorded in logs (logs become incomplete)
- Lost if server restarts
- Breaks "logs as source of truth" principle

### Option 3: Agent Manager Service

**How it works:**
- Create `AgentManager` singleton that holds all agent thread references
- API endpoints call methods on AgentManager
- Manager directly calls `agent.pause()` on the thread object

**Pros:**
- Direct control
- Immediate effect

**Cons:**
- Tight coupling between API and agent instances
- Harder to scale (agents must run in same process as Flask)
- Doesn't work for real LLM agents running as separate processes

## Recommendation: Option 1 (Log-Based Control)

**Why:** It's architecturally consistent, works across processes, provides audit trail, and prepares us for real agents.

## Implementation Plan

### 1. Update MockAgent Class

Add log monitoring to the agent's run loop:

```python
def _check_for_control_signals(self):
    """Check log file for pause/resume/stop commands."""
    # Read recent log entries
    # Look for status changes
    # Update self.paused and self.running accordingly
```

### 2. Current API Endpoints (Already Done)

These already write to logs correctly:
- `POST /api/agents/{id}/pause` → writes `status: "paused"`
- `POST /api/agents/{id}/resume` → writes `status: "running"`
- `POST /api/agents/{id}/archive` → writes `status: "archived"`

### 3. Agent Lifecycle States

```
┌─────────┐
│ running │ ←──┐
└────┬────┘    │
     │         │
     │ pause   │ resume
     │         │
     ↓         │
┌─────────┐   │
│ paused  │ ──┘
└────┬────┘
     │
     │ archive
     ↓
┌──────────┐
│ archived │ (stopped permanently)
└──────────┘
```

### 4. Special Cases

**waiting_for_input:**
- Agent pauses itself via `self.paused = True`
- Writes `status: "waiting_for_input"`
- Waits for `user_message` entry in log
- Auto-resumes when message appears

**User pauses while waiting_for_input:**
- Agent sees `status: "paused"` in log
- Changes from `waiting_for_input` → `paused`
- Will NOT auto-resume on user message

**Archive:**
- Writes `status: "archived"`
- Sets `self.running = False`
- Thread exits gracefully

## Testing Strategy

1. Create agent, verify it starts running
2. Pause agent, verify it stops taking actions within 3 seconds
3. Resume agent, verify it starts again
4. Pause while agent is `waiting_for_input`
5. Archive agent, verify thread exits

## Migration Path

1. ✅ API endpoints already write correct log entries
2. ⏳ Update `MockAgent._run_loop()` to check logs
3. ⏳ Test with UI
4. ⏳ Document for real agent implementations

## For Real Agents (Future)

Real LLM agents will likely run as **separate processes**, not threads. Options:

1. **Same approach**: Agent process reads its log file for control signals
2. **Signal files**: Create `agent_{id}.control` files (e.g., `PAUSE`, `RESUME`)
3. **IPC**: Use sockets, named pipes, or message queues
4. **Database**: Use a shared database for control state

**Recommendation**: Stick with log-based approach. It works for both threads and processes, maintains audit trail, and is simple.

---

## Immediate Fix for MockAgent

Update the `_run_loop` method to check the log file for control commands before each action. This makes pause/resume work immediately.

**Priority:** HIGH - core functionality
**Effort:** ~30 minutes
**Files:** `src/agents/mock_agent.py`

