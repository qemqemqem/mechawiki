# Flask Reloader: No More Duplicate Agent Startups! 🔥

## The Problem

Flask's auto-reloader was watching Python files and restarting the entire backend process on every code change. Each restart would:
1. Kill all agent threads (entire process restarted)
2. Re-run `init_and_start_agents()`
3. Log "Agent started (paused)" again

**Evidence from logs:**
```jsonl
{"type": "status", "status": "paused", "message": "Agent started (paused)", "timestamp": "2025-11-08T19:07:31..."}
{"type": "status", "status": "paused", "message": "Agent started (paused)", "timestamp": "2025-11-08T19:10:07..."}
{"type": "status", "status": "paused", "message": "Agent started (paused)", "timestamp": "2025-11-08T19:11:17..."}
{"type": "status", "status": "paused", "message": "Agent started (paused)", "timestamp": "2025-11-08T19:13:35..."}
```

Each entry corresponded to a Python file modification that triggered Flask's reloader.

## Root Cause

Flask's Werkzeug development server has an auto-reloader that watches for file changes. When ANY Python file changes, it:
1. Kills the current Flask process
2. Starts a new Flask process
3. Re-imports all modules
4. Re-runs initialization code

Since agents are threads inside the Flask process, they die with the process and must be restarted.

## The Fix

**Disabled Flask's auto-reloader** while keeping Vite's hot module reloading for the frontend.

### Changes Made

**File: `src/server/app.py`**

```python
def run_server(host='localhost', port=5000, debug=True):
    """Run the Flask development server."""
    # Initialize agents once at startup
    # In debug mode, we disable the reloader to prevent agents from restarting
    # on every code change (frontend has its own Vite reloader)
    init_and_start_agents()
    
    logger.info(f"🚀 Starting server on {host}:{port}")
    # Disable reloader to prevent agent restarts on Python file changes
    # Frontend has Vite for hot reloading, backend can be manually restarted
    app.run(host=host, port=port, debug=debug, threaded=True, use_reloader=False)
```

**Key change:** `use_reloader=False` instead of `use_reloader=debug`

**File: `start.sh`**

Added helpful message:
```bash
echo "💡 Frontend auto-reloads on changes (Vite)"
echo "💡 Backend requires manual restart for Python changes (agents stay running)"
```

### Bonus: Agent Manager Guards (Defense in Depth)

**File: `src/server/agent_manager.py`**

Added tracking flags to prevent duplicate initialization:
```python
def __init__(self):
    if self._initialized:
        return
    
    self._agents: Dict[str, Union[MockAgent, AgentRunner]] = {}
    self._agents_started = False  # Track if init_and_start_agents() has been called
    self._initialized = True

def mark_agents_started(self):
    """Mark that agents have been initialized."""
    self._agents_started = True

def agents_already_started(self) -> bool:
    """Check if agents have already been initialized."""
    return self._agents_started
```

These guards provide defense-in-depth, though they're not needed with the reloader disabled.

## How It Works Now

### Frontend (Vite) ✅
- **Still has hot module reloading**
- Changes to React/JSX files reload instantly
- No backend impact
- Runs independently on port 5173

### Backend (Flask) 🔄
- **No auto-reloader** (stays running)
- Agents start once and keep running
- Python changes require manual restart
- Debug mode still enabled for better error messages

### Agent Threads ⚡
- Start once at server startup
- Continue running through backend lifetime
- No duplicate "Agent started" log messages
- Survive across frontend reloads (different process)

## Testing

### Before Fix
```bash
# Start server
./start.sh

# Edit base_agent.py
# -> Flask reloads
# -> All agents restart
# -> Duplicate log entry appears

# Edit agent_runner.py  
# -> Flask reloads again
# -> All agents restart again
# -> Another duplicate log entry
```

**Result:** 5 duplicate "Agent started" messages in 6 minutes

### After Fix
```bash
# Start server
./start.sh

# Edit base_agent.py
# -> No reload, agents keep running

# Edit agent_runner.py
# -> No reload, agents keep running

# Manually restart when ready
# Ctrl+C, then ./start.sh again
```

**Result:** Only 1 "Agent started" message per full restart

## Trade-offs

### Pros ✅
- **No duplicate agent startups** - agents start once and stay running
- **No wasted LLM calls** - agents don't restart mid-task
- **Cleaner logs** - only real status changes appear
- **Frontend still hot-reloads** - Vite handles React changes independently
- **Agent state preserved** - no interruption during development
- **Faster** - no constant backend restarts

### Cons ⚠️
- **Manual backend restart needed** - Ctrl+C and re-run `./start.sh` for Python changes
- **Slightly slower dev cycle** - can't instantly test backend changes

### Mitigation

For rapid backend development, you can:
1. Write unit tests (fast feedback loop)
2. Use `pytest --watch` for TDD workflow
3. Keep a quick restart script handy
4. Only restart when testing integration changes

## Alternative Considered

We considered keeping the reloader but adding smarter guards to prevent duplicate initialization. However, this is complex because:
- Flask completely restarts the Python process
- All singleton state is lost (including AgentManager)
- Agent threads are killed by OS when process dies
- Would need file-based locks or PID tracking
- More complexity, more edge cases

**Verdict:** Disabling the reloader is the simplest, most reliable solution.

## Related Notes

- See `notes/BUGFIX_START_PAUSED.md` for the start_paused flag feature
- See `notes/BUGFIX_WAIT_FOR_USER_DUPLICATE_MESSAGE.md` for event consumption patterns

## Impact

- ✅ Clean agent logs (no duplicate startups)
- ✅ Agents stay running during development
- ✅ Frontend still has instant hot reloading
- ✅ Backend development still fast enough (manual restart)
- ✅ Simpler architecture (no complex guards needed)

---

**Status:** FIXED ✅  
**Date:** 2025-11-09  
**Hunter:** The Direct Path is Usually the Right Path 🏹

