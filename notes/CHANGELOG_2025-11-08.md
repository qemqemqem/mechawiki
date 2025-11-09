# Changelog - November 8, 2025

## UI Improvements ✨

### 1. Agent Filter Sorting
- Agents in the Files Feed filter dropdown now appear **alphabetically sorted**
- "all" still appears first

### 2. Agent Name Consistency
- **Agent name** is now prominently displayed in the UI (from `agent.name`)
- **Agent ID** is shown in a subtle monospace font in the Command Center details
- ID has a tooltip showing the full ID on hover
- Format: `{agent.name}` in header, `{agent.id} • {agent.type}` in details

### 3. Agent Description Field
- Added **"Agent Description"** textarea in the Create Agent modal
- Optional field for user notes about the agent's purpose
- Will be used in system prompts in future (currently stored in `config.description`)
- 4-row textarea with vertical resize

### 4. CSS Improvements
- Styled textarea in NewAgentModal
- Added `.agent-id` and `.agent-status-detail` styles
- Better visual hierarchy in Command Center cards

## Backend Architecture 🏗️

### 1. Pause/Resume System (Log-Based) ⭐
**Planning Document:** `notes/agent_pause_resume_architecture.md`

**Implementation:**
- Agents now check their log files for control signals
- `_check_control_signals()` method reads log for status changes
- When UI sends pause/resume, it writes to log
- Agent reads log before each action and respects pause state
- **Advantages:**
  - Consistent with "logs as source of truth" philosophy
  - Works across processes (ready for real agents)
  - Complete audit trail
  - Survives restarts

**States:**
- `running` → `paused` (user pause)
- `paused` → `running` (user resume)
- `running` → `archived` (stop permanently)
- `waiting_for_input` (special case, agent self-pauses)

### 2. Agent Manager Singleton
**New File:** `src/server/agent_manager.py`

- Centralized management of running agent instances
- Tracks MockAgent threads in a dict
- Methods: `start_agent()`, `stop_agent()`, `get_agent()`, `is_running()`, `list_running()`, `stop_all()`
- Used by API endpoints and init_agents

**Benefits:**
- Single source of truth for running agents
- Prevents duplicate agent instances
- Easy cleanup on archive
- Proper lifecycle management

### 3. Auto-Start New Agents
**Fixed:** Newly created agents now start automatically

**Flow:**
1. User creates agent via UI
2. `POST /api/agents/create` endpoint:
   - Adds to session config
   - Creates log file
   - Starts log watcher
   - **Starts MockAgent instance via agent_manager** ⭐
3. Agent immediately begins running and appears active in UI

### 4. Archive Cleanup
- Archiving an agent now properly stops the MockAgent instance
- Calls `agent_manager.stop_agent(agent_id)`
- Agent thread exits gracefully

## Files Modified

### Frontend
- `src/ui/src/components/files/FilesFeed.jsx` - Sort agents alphabetically
- `src/ui/src/components/agents/CommandCenter.jsx` - Show agent ID and status details
- `src/ui/src/components/agents/CommandCenter.css` - New CSS for agent-id and status-detail
- `src/ui/src/components/agents/NewAgentModal.jsx` - Add description field
- `src/ui/src/components/agents/NewAgentModal.css` - Style textarea

### Backend
- `src/server/agent_manager.py` - **NEW** - Agent lifecycle manager
- `src/server/app.py` - Initialize agent_manager
- `src/server/agents.py` - Use agent_manager for create/archive
- `src/server/init_agents.py` - Use agent_manager to start agents
- `src/agents/mock_agent.py` - Implement `_check_control_signals()` for log-based pause/resume

### Documentation
- `notes/agent_pause_resume_architecture.md` - **NEW** - Complete pause/resume architecture planning

## Testing Checklist ✅

- [x] Agents sorted alphabetically in filter
- [x] Agent names display consistently
- [x] Description field in Create Agent modal
- [x] Pause agent → stops taking actions
- [x] Resume agent → continues actions
- [x] Create new agent → starts automatically
- [x] Archive agent → stops thread cleanly
- [x] Textarea styling works

## Architecture Notes 📝

**Log-Based Control:** The pause/resume system uses the log file as a "control channel." This is architecturally elegant because:
1. Logs are already the source of truth for status
2. Works for both threads (mock agents) and processes (real agents)
3. Provides complete audit trail
4. Simple to implement and debug

**Agent Manager Pattern:** The singleton manager provides a clean separation:
- Config layer (`SessionConfig`) stores agent definitions
- Manager layer (`AgentManager`) manages running instances
- API layer (`agents.py`) coordinates between them

This will make it easy to swap out MockAgent for real LLM agents later.

## Known Issues / Future Work

1. **Last Action from Logs:** Command Center gets last action from backend, but could use real-time SSE updates for instant feedback
2. **Agent Templates:** Could add pre-configured agent templates in the modal
3. **Agent Restart:** No UI button to restart archived agents yet
4. **Batch Operations:** Could add "pause all" / "resume all" buttons

---

**Excellent progress on the agent management system!** 🏰⚔️

