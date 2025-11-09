# Test Agents Setup 🤖

## Overview

The MechaWiki system now automatically initializes and starts **4 dumb test agents** when the server launches. These agents generate random activity to test the UI and backend systems.

## Test Agents

### 1. Reader Agent 1 (`reader-001`)
- **Type**: ReaderAgent
- **Behavior**: 
  - Reads random articles from wikicontent
  - Advances through stories with random word counts
  - Creates tool calls for `advance()` and `read_article()`
  - Generates occasional thinking messages

### 2. Writer Agent 1 (`writer-001`)
- **Type**: WriterAgent
- **Behavior**:
  - Writes/edits random articles
  - Simulates file changes with diff stats (+lines/-lines)
  - Logs tool calls for `write_article()` and `edit_story()`
  - Occasional search operations

### 3. Researcher Agent 1 (`researcher-001`)
- **Type**: ResearcherAgent
- **Behavior**:
  - Searches for articles and content
  - Reads and analyzes wiki content
  - Generates research-related tool calls
  - Creates thinking logs about connections

### 4. Interactive Agent 1 (`interactive-001`)
- **Type**: InteractiveAgent  
- **Behavior**:
  - Sends prose messages to the UI
  - **Occasionally pauses and waits for user input** (10% chance)
  - Reads articles for context
  - Interactive storytelling simulation

## Activity Pattern

Each agent:
1. Runs continuously in a background thread
2. Takes random actions every **1-3 seconds**
3. Logs all actions to `data/sessions/dev_session/logs/agent_{id}.jsonl`
4. Simulates realistic delays for different operations
5. Uses the same log format as real agents

## Actions

Each agent can perform weighted random actions:
- **read_article** (30%) - Read a random wiki article
- **write_article** (25%) - Write/edit a random article
- **search** (15%) - Search for content
- **advance** (15%, ReaderAgent only) - Advance through a story
- **think** (10%) - Generate internal reasoning
- **talk** (5%) - Send a message to the UI

## Automatic Initialization

The agents are initialized automatically when Flask starts:

```python
# src/server/app.py
from .init_agents import init_test_agents, start_test_agents
init_test_agents()      # Create agents in session config
mock_agents = start_test_agents()  # Start background threads
```

## Manual Management

### Initialize agents (without starting)
```bash
source .venv/bin/activate
python src/server/init_agents.py
```

### Start agents in background
```bash
source .venv/bin/activate
python src/server/init_agents.py --start
```

### Run a single standalone mock agent
```bash
source .venv/bin/activate
python src/agents/mock_agent.py
```

## Files

- **`src/agents/mock_agent.py`** - MockAgent class implementation
- **`src/server/init_agents.py`** - Agent initialization and startup
- **`data/sessions/dev_session/agents.json`** - Agent configuration
- **`data/sessions/dev_session/logs/agent_*.jsonl`** - Agent activity logs

## Testing with Test Agents

These agents are perfect for testing:

✅ Real-time log streaming (SSE)  
✅ Agent status indicators (●running, ◉waiting, ◐paused)  
✅ File feed population from agent logs  
✅ Diff summaries (+17 -5)  
✅ Agent filtering in Files Feed  
✅ Chat message queueing  
✅ Pause/resume functionality  
✅ Interactive agent input waiting  

## Customization

To customize agent behavior, edit the weights in `mock_agent.py`:

```python
self.actions = [
    ('read_article', 0.3),   # 30% chance
    ('write_article', 0.25), # 25% chance
    ('search', 0.15),        # 15% chance
    # ...
]
```

Or adjust timing:
```python
time.sleep(random.uniform(1, 3))  # Wait 1-3 seconds between actions
```

## Next Steps

These test agents will be replaced with real LLM-powered agents in the next phase, but they follow the exact same log format and API, so the UI integration is identical.

---

**The mock armies are assembled and ready for testing!** 🏰⚔️

