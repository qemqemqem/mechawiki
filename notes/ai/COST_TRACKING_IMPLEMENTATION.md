# Cost Tracking Implementation 💰

**Status:** ✅ Complete and Integrated

## Overview

Added session-wide cost tracking using litellm's built-in `completion_cost()` utility. Costs are tracked across all agents and logged to `costs.log` at dollar milestones. Frontend displays total session cost discretely in the top right.

## What Was Added

### 1. BaseAgent Cost Tracking

**File:** `src/base_agent/base_agent.py`

**New Properties:**
- `total_cost` - Cumulative USD cost across all turns
- `total_prompt_tokens` - Total prompt tokens used
- `total_completion_tokens` - Total completion tokens used  
- `turn_count` - Number of LLM calls made

**New Method:**
```python
agent.get_cost_stats()
# Returns:
# {
#     "total_cost": 0.000350,
#     "total_prompt_tokens": 220,
#     "total_completion_tokens": 130,
#     "total_tokens": 350,
#     "turn_count": 2,
#     "average_cost_per_turn": 0.000175
# }
```

**Automatic Logging:**
Every turn logs to console:
```
💰 Turn 1 | Cost: $0.000150 | Tokens: 100p + 50c = 150t | Total: $0.000150
💰 Turn 2 | Cost: $0.000200 | Tokens: 120p + 80c = 200t | Total: $0.000350
```

### 2. Session-Wide Cost Tracker

**File:** `src/server/cost_tracker.py`

**New Module:**
- Tracks cumulative costs across all agents in a session
- Thread-safe for multi-agent environments
- Logs milestones to `costs.log` when crossing dollar thresholds
- Example log entries:
  ```
  [2025-11-09 14:23:45] First dollar spent! Total: $1.00
  [2025-11-09 14:45:12] Another $1 spent. Total spend this session: $2.00
  ```

**Milestone Logging:**
- Only logs when crossing full dollar amounts ($1, $2, $3, etc.)
- Keeps `costs.log` clean and focused on significant milestones
- No spam from tiny incremental costs

### 3. AgentRunner Integration

**File:** `src/agents/agent_runner.py`

- Reports incremental costs to session tracker after each turn
- No cost data in JSONL logs (keeps event logs clean)
- Automatic reporting - no configuration needed

### 4. API Endpoint

**File:** `src/server/agents.py`

**New Endpoint:**
```
GET /api/agents/session/cost
```

Returns session-wide cost statistics across all agents.

**Response:**
```json
{
  "total_cost": 0.001234,
  "total_cost_dollars": "$0.00",
  "agent_costs": {
    "reader-001": 0.000456,
    "writer-001": 0.000778
  }
}
```

### 5. Frontend Display

**Files:** `src/ui/src/components/TopBar.jsx`, `TopBar.css`, `App.jsx`

**Display:**
- Discrete cost badge in top right corner next to "Connected"
- Shows formatted cost (e.g., "$0.05")
- Automatically polls every 10 seconds
- Styled to match the connection status badge

## How It Works

### Cost Calculation

Uses **litellm's `completion_cost()`** which:
- Knows pricing for all major models (Claude, GPT-4, Gemini, etc.)
- Handles different pricing for prompt vs completion tokens
- Automatically stays updated with provider pricing
- Falls back gracefully if pricing info unavailable

### Token Tracking

Extracts usage info from litellm response objects:
- **Streaming responses:** Usage info in final chunk
- **Non-streaming responses:** Usage info in response.usage
- Handles both cases automatically

### Cost Persistence

Cost data flows through multiple channels:
1. **Console logs** (via Python logger) - Per-turn debugging
2. **costs.log** (milestone logging) - Dollar threshold events
3. **In-memory tracker** (CostTracker) - Real-time session totals
4. **API endpoint** (GET /session/cost) - Frontend polling
5. **Frontend display** (TopBar) - User-visible cost counter

## Usage Examples

### Python Code

```python
from src.base_agent.base_agent import BaseAgent

# Create agent - cost tracking is automatic!
agent = BaseAgent(model="claude-haiku-4-5-20251001")

# Run agent
for event in agent.run_forever("Hello!", max_turns=3):
    pass

# Get stats
stats = agent.get_cost_stats()
print(f"Total cost: ${stats['total_cost']:.6f}")
print(f"Total tokens: {stats['total_tokens']:,}")
```

See `src/examples/cost_tracking_example.py` for a complete example.

### HTTP API

```bash
# Get session-wide cost stats
curl http://localhost:5000/api/agents/session/cost

# Response:
# {
#   "total_cost": 0.001234,
#   "total_cost_dollars": "$0.00",
#   "agent_costs": {
#     "reader-001": 0.000456,
#     "writer-001": 0.000778
#   }
# }
```

### Milestone Log File

```bash
# Check costs.log for dollar milestones
cat data/sessions/dev_session/costs.log

# Example output:
# [2025-11-09 14:23:45] First dollar spent! Total: $1.00
# [2025-11-09 14:45:12] Another $1 spent. Total spend this session: $2.00
# [2025-11-09 15:12:33] Another $1 spent. Total spend this session: $3.00
```

### Frontend Display

The cost display appears in the top right corner:
- **Location:** Next to the "Connected" status badge
- **Updates:** Every 10 seconds via polling
- **Style:** Discrete, semi-transparent badge with 💰 icon
- **Format:** Formatted currency string (e.g., "$0.05")

## Models Supported

All litellm-supported models automatically get cost tracking:
- ✅ Anthropic (Claude Sonnet, Haiku, Opus)
- ✅ OpenAI (GPT-4, GPT-3.5)
- ✅ Google (Gemini Pro, etc.)
- ✅ Custom models (with custom pricing)

## Implementation Details

### Files Modified

1. **src/base_agent/base_agent.py**
   - Added cost tracking properties to `__init__` (total_cost, token counts, turn_count)
   - Added `get_cost_stats()` method for querying costs
   - Updated streaming/non-streaming handlers to capture usage info
   - Added cost calculation using `litellm.completion_cost()` in `run_forever()`
   - Logs per-turn costs to console

2. **src/server/cost_tracker.py** (NEW)
   - Session-wide cost tracking with milestone logging
   - Thread-safe for multi-agent environments
   - Writes to `costs.log` when crossing dollar thresholds
   - Tracks per-agent costs and session totals

3. **src/server/app.py**
   - Initialize cost tracker on server startup
   - Pass session directory to tracker

4. **src/agents/agent_runner.py**
   - Added `_report_cost_to_tracker()` method
   - Reports incremental costs to session tracker after each turn
   - Tracks `last_reported_cost` to avoid double-counting

5. **src/server/agents.py**
   - Added `/api/agents/session/cost` endpoint
   - Returns session-wide cost stats from tracker

6. **src/ui/src/components/TopBar.jsx**
   - Added `sessionCost` prop
   - Displays cost badge in top-bar-right div
   - Shows formatted cost with 💰 icon

7. **src/ui/src/components/TopBar.css**
   - Added `.cost-display` styles
   - Matches connection-status badge styling
   - Discrete, semi-transparent appearance

8. **src/ui/src/App.jsx**
   - Added `sessionCost` state
   - Added `fetchSessionCost()` function
   - Set up polling interval (10 seconds)
   - Pass cost to TopBar component

## Testing

### Start the Server
```bash
cd /home/keenan/Dev/mechawiki
./start.sh
```

### Check Cost Stats
```bash
# API endpoint
curl http://localhost:5000/api/agents/session/cost

# Milestone log
tail -f data/sessions/dev_session/costs.log
```

### View in Frontend
1. Navigate to http://localhost:3000
2. Look for the 💰 badge in the top right corner
3. It updates every 10 seconds
4. Watch costs.log for dollar milestones

## Design Decisions

### Why Milestone Logging?
- **Clean logs:** Only log significant events (dollar thresholds)
- **Human-readable:** Easy to spot when costs are adding up
- **Low noise:** No spam from tiny incremental costs

### Why Session-Wide Tracking?
- **Single source of truth:** One cost total for the entire session
- **Multi-agent support:** Tracks all agents together
- **Simpler UI:** One number to display, not per-agent breakdowns

### Why Not in JSONL Logs?
- **Separation of concerns:** JSONL logs are for agent events, not financial data
- **Different lifecycle:** Costs persist across agent restarts
- **Cleaner structure:** costs.log is human-readable milestone tracking

## Future Enhancements

Possible additions (not implemented yet):
- 🔮 Budget alerts (notify when crossing thresholds)
- 🔮 Cost breakdown by model type
- 🔮 Historical cost graphs in UI
- 🔮 Export costs.log to CSV/JSON
- 🔮 Per-agent cost visualization

## Notes

- **No setup required** - Cost tracking is automatic for all agents
- **Zero overhead** - Uses litellm's built-in utilities (no extra API calls)
- **Graceful fallback** - If cost calculation fails, logs warning and continues
- **Model-aware** - Different models have different pricing automatically handled
- **Battle-tested** - litellm's cost tracking is widely used and maintained

---

**Cost tracking is now live! Hunt down those API expenses with precision! 🎯**

