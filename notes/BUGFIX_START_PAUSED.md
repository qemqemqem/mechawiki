# Start Paused - No More Race Conditions! 🏁

## Problem

Demo agents were starting **running** and then immediately being **paused**, causing a race condition:

```jsonl
{"status": "running", "message": "Agent started", "timestamp": "...590440"}
{"status": "paused", "message": "Paused by user", "timestamp": "...590631"}
```

Only 191 microseconds between these events! But in that time:
- The agent thread is running
- Could make an LLM call before seeing the pause signal
- Could perform actions before being paused
- Wasteful to start and immediately pause

## The Fix

### 1. Added `start_paused` Parameter to `AgentRunner`

```python
def __init__(
    self,
    agent_instance: BaseAgent,
    agent_id: str,
    log_file: Path,
    agent_config: Optional[Dict[str, Any]] = None,
    start_paused: bool = False  # <-- NEW!
):
    # ...
    self.running = False
    self.paused = start_paused  # <-- Respects initial state
```

### 2. Updated `start()` to Respect Initial State

**Before:**
```python
def start(self):
    self.running = True
    self.paused = False  # <-- Always unpaused!
    self.thread.start()
```

**After:**
```python
def start(self):
    self.running = True
    # Don't override self.paused - respect start_paused setting
    self.thread.start()
```

### 3. Updated `_run_loop()` to Log Correct Initial Status

```python
def _run_loop(self):
    # Log initial status based on paused state
    if self.paused:
        self._log({'type': 'status', 'status': 'paused', 'message': 'Agent started (paused)'})
    else:
        self._log({'type': 'status', 'status': 'running', 'message': 'Agent started'})
```

### 4. Updated `AgentManager.start_agent()`

```python
def start_agent(
    self,
    agent_id: str,
    agent_type: str,
    log_file: Path,
    wikicontent_path: Path,
    agent_config: Optional[Dict] = None,
    use_real_agent: Optional[bool] = None,
    start_paused: bool = False  # <-- NEW!
):
    # For real agents:
    runner = AgentRunner(
        agent_instance=agent_instance,
        agent_id=agent_id,
        log_file=log_file,
        agent_config=agent_config or {},
        start_paused=start_paused  # <-- Pass through
    )
    
    # For mock agents:
    agent = MockAgent(...)
    agent.start()
    if start_paused:
        agent.pause()
```

### 5. Updated `init_agents.py`

**Before (race condition):**
```python
agent = agent_manager.start_agent(...)
agent_manager.pause_agent(agent_id)  # <-- Race!
```

**After (clean):**
```python
agent = agent_manager.start_agent(
    ...,
    start_paused=True  # <-- No race!
)
```

## How It Works Now

### Demo Agents (Paused on Start)

```python
# In init_agents.py
agent_manager.start_agent(
    agent_id="reader-001",
    agent_type="ReaderAgent",
    start_paused=True  # <-- Paused from the start!
)
```

**Log output:**
```jsonl
{"status": "paused", "message": "Agent started (paused)", "timestamp": "..."}
```

No "running" status ever appears! Agent is paused from the very first moment.

### UI-Created Agents (Running by Default)

```python
# In agents.py create_agent endpoint
agent_manager.start_agent(
    agent_id=agent_id,
    agent_type=data['type'],
    # start_paused defaults to False
)
```

**Log output:**
```jsonl
{"status": "running", "message": "Agent started", "timestamp": "..."}
```

Agent begins working immediately.

## Benefits

### ✅ No Race Conditions
- Agent respects `start_paused` from the very beginning
- No time window where agent could make LLM calls
- No wasted API calls or compute

### ✅ Clean Logs
**Before:**
```jsonl
{"status": "running", ...}
{"status": "paused", ...}  // <-- confusing!
```

**After (paused):**
```jsonl
{"status": "paused", "message": "Agent started (paused)", ...}
```

**After (running):**
```jsonl
{"status": "running", "message": "Agent started", ...}
```

### ✅ Predictable Behavior
- Demo agents: Always start paused
- UI-created agents: Always start running
- No surprises!

## Testing

### Demo Agents
```bash
./start.sh
```

Check logs:
```bash
cat data/sessions/dev_session/logs/agent_reader-001.jsonl
```

Expected first line:
```jsonl
{"type":"status","status":"paused","message":"Agent started (paused)",...}
```

### UI-Created Agents

1. Click "New Agent" button
2. Create agent
3. Check its log immediately

Expected first line:
```jsonl
{"type":"status","status":"running","message":"Agent started",...}
```

## Victory Conditions 🎉

- ✅ Demo agents start in paused state (no "running" status first)
- ✅ No race condition or wasted LLM calls
- ✅ Clean, consistent logs
- ✅ UI-created agents still start running
- ✅ `start_paused` parameter available for any use case

---

**Status:** FIXED ✅  
**Date:** 2025-11-08  
**Impact:** Agents now start in correct initial state with no race conditions!

