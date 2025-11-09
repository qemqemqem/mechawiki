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

## Solution

Guard the initialization code to only run in the child process (or when not in debug mode):

```python
# WERKZEUG_RUN_MAIN is None (not in debug) or 'true' (debug child process)
werkzeug_run_main = os.environ.get('WERKZEUG_RUN_MAIN')
if werkzeug_run_main is None or werkzeug_run_main == 'true':
    logger.info("🤖 Initializing test agents...")
    from .init_agents import init_test_agents, start_test_agents
    init_test_agents()
    mock_agents = start_test_agents(agent_manager)
```

Flask sets `WERKZEUG_RUN_MAIN='true'` only in the child process, so this check ensures initialization only happens once.

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

This is a common Flask debug mode gotcha. Any expensive or stateful initialization at module level needs this guard:

```python
import os

# Only run in actual app process, not reloader parent
if os.environ.get('WERKZEUG_RUN_MAIN') is None or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    # Initialize expensive resources here
    pass
```

Alternatively, move initialization into an `@app.before_first_request` handler (deprecated in Flask 2.3+) or use a proper application factory pattern.

### Pattern 2: Single Owner for Log Files

**Each log file should have exactly ONE owner** that writes to it:
- AgentRunner owns agent log files and writes all agent events
- API endpoints read from logs (for status) and write only external inputs (user messages)
- Never have both the API and the agent write the same type of entry

This prevents race conditions, duplicate entries, and makes the system easier to reason about.

