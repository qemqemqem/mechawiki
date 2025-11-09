# BUGFIX: Duplicate Log Entries

## Problem

Agent logs showed duplicate entries in two scenarios:

### 1. Agent Startup - Duplicate "Agent started (paused)" entries

```jsonl
{"type": "status", "status": "paused", "message": "Agent started (paused)", "timestamp": "2025-11-08T18:30:31.915562"}
{"type": "status", "status": "paused", "message": "Agent started (paused)", "timestamp": "2025-11-08T18:30:33.260233"}
```

### 2. Pause/Resume - Duplicate control entries

```jsonl
{"timestamp": "2025-11-08T18:36:48.365518", "type": "status", "status": "paused", "message": "Paused by user"}
{"type": "status", "status": "paused", "message": "Paused by user", "timestamp": "2025-11-08T18:36:48.369009"}
```

## Root Causes

### Bug 1: Flask Debug Mode Double Initialization

Flask's debug mode (enabled via `debug=True` in `run_server()`) spawns TWO processes:
1. **Parent process** - watches for file changes and restarts the app
2. **Child process** - actually runs the Flask application

Both processes import `app.py`, causing module-level initialization code to run **twice**.

The agent initialization code in `app.py` (lines 30-37) was running in both processes:
```python
logger.info("🤖 Initializing test agents...")
from .init_agents import init_test_agents, start_test_agents
init_test_agents()
mock_agents = start_test_agents(agent_manager)
```

This meant each agent was being started twice - once per process!

#### Solution (Final Fix)

After multiple attempts, the working solution is to:
1. Move initialization into a function (not module-level code)
2. Call it from `run_server()` with the correct guard

```python
# In app.py - define function (not at module level)
def init_and_start_agents():
    """Initialize and start agents. Called once from run_server()."""
    logger.info("🤖 Initializing test agents...")
    from .init_agents import init_test_agents, start_test_agents
    init_test_agents()
    start_test_agents(agent_manager)

def run_server(host='localhost', port=5000, debug=True):
    # Only run when:
    # - Not in debug mode (run once), OR
    # - In debug mode AND in child process (WERKZEUG_RUN_MAIN='true')
    if not debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        init_and_start_agents()
    
    app.run(host=host, port=port, debug=debug, threaded=True)
```

**Why earlier attempts failed:**
- **Module-level check** `if werkzeug_run_main is None or werkzeug_run_main == 'true'` runs TWICE: once in initial process (None) and once in child process ('true')
- **Moving to function alone** doesn't help because `run_server()` is called from `__main__`, which runs in both initial and child processes

**Why this works:**
- **Non-debug**: `not debug` evaluates to True → runs once ✓
- **Debug initial**: `not debug` is False, `WERKZEUG_RUN_MAIN` is None → skips
- **Debug child**: `not debug` is False, `WERKZEUG_RUN_MAIN='true'` → runs once ✓

### Bug 2: Duplicate Log Writes in Pause/Resume

The pause/resume flow had **two separate places** writing to the log file:

1. **API endpoint** (`src/server/agents.py`) wrote directly to the log:
```python
# In pause_agent() endpoint
log_file = session_config.logs_dir / f"agent_{agent_id}.jsonl"
log_entry = {"timestamp": ..., "type": "status", "status": "paused", ...}
with open(log_file, 'a') as f:
    f.write(json.dumps(log_entry) + '\n')
```

2. Then called **AgentManager.pause_agent()**, which called **AgentRunner.pause()**, which wrote to the log AGAIN:
```python
# In AgentRunner.pause()
def pause(self):
    self._log({
        'type': 'status',
        'status': 'paused',
        'message': 'Paused by user'
    })
```

This violated the **single source of truth** principle - the AgentRunner should own its log file.

#### Solution

Remove direct log writes from API endpoints and let AgentRunner handle all log writes:

```python
# In pause_agent() endpoint - simplified
def pause_agent(agent_id):
    agent = session_config.get_agent(agent_id)
    if not agent:
        return jsonify({"error": "Agent not found"}), 404
    
    # Let the agent write to its own log
    agent_manager.pause_agent(agent_id)
    return jsonify({"status": "paused"})
```

The same fix was applied to:
- `/api/agents/<id>/pause` 
- `/api/agents/<id>/resume`
- `/api/agents/pause-all`
- `/api/agents/resume-all`

**Note:** The `/api/agents/<id>/message` endpoint still writes directly to the log, which is correct - user messages are external inputs that the agent reads from the log.

## Files Modified

- `src/server/app.py` - Added environment variable check to prevent double initialization
- `src/server/agents.py` - Removed duplicate log writes from pause/resume endpoints

## Testing

After these fixes:
- Agent logs should show only ONE "Agent started" entry per agent
- Pause/resume actions should log only ONE status entry per action

## Design Patterns

### Pattern 1: Flask Debug Mode Guard

This is a common Flask debug mode gotcha. The **correct** pattern for avoiding double initialization is:

```python
import os

def run_server(debug=True):
    # Only initialize in child process (debug) or when not debugging
    if not debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        initialize_resources()  # Runs exactly once
    
    app.run(debug=debug)
```

**Common mistake** (runs twice!):
```python
# At module level - WRONG!
if os.environ.get('WERKZEUG_RUN_MAIN') is None or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    initialize_resources()  # Runs in initial process AND child process!
```

Alternatively, use a proper **application factory pattern** which is the Flask best practice for production apps.

### Pattern 2: Single Owner for Log Files

**Each log file should have exactly ONE owner** that writes to it:
- AgentRunner owns agent log files and writes all agent events
- API endpoints read from logs (for status) and write only external inputs (user messages)
- Never have both the API and the agent write the same type of entry

This prevents race conditions, duplicate entries, and makes the system easier to reason about.

