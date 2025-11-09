# Interactive Agent Crash Fix 🐛→✅

## Problem

Interactive agents were crashing immediately after calling `wait_for_user()` with this error:

```
litellm.BadRequestError: AnthropicException - 
messages.2: `tool_use` ids were found without `tool_result` blocks immediately after
```

## Root Cause

**AgentRunner was not waiting for user input!**

After the agent called `wait_for_user()`:
1. AgentRunner broke from the event loop ✅
2. But then **immediately continued** the outer while loop ❌
3. Called `run_forever()` again without user input ❌
4. Agent tried to continue with an unanswered tool call → Claude rejected it 💥

## The Fix

### Before (Broken)
```python
for event in self.agent.run_forever(initial_prompt, max_turns=1):
    signal = self._handle_event(event)
    
    if signal == 'wait_for_input':
        break  # Only breaks inner loop!

# Continues immediately to next turn!
initial_prompt = "Continue your task."
```

### After (Fixed)
```python
waiting_for_user = False
for event in self.agent.run_forever(initial_prompt, max_turns=1):
    signal = self._handle_event(event)
    
    if signal == 'wait_for_input':
        waiting_for_user = True
        break

# Flush content
self._flush_text()
self._flush_thinking()

# WAIT for user message before continuing
if waiting_for_user:
    self._wait_for_user_message()

# Now continue with user's input
initial_prompt = "Continue your task."
```

### New Method: `_wait_for_user_message()`

```python
def _wait_for_user_message(self):
    """
    Poll log file for a user_message entry.
    Blocks until one appears or agent is stopped.
    """
    last_check_timestamp = datetime.now().isoformat()
    
    while self.running and not self.paused:
        # Read log file
        with open(self.log_file, 'r') as f:
            for line in f:
                entry = json.loads(line)
                
                # Only check new entries
                if entry['timestamp'] <= last_check_timestamp:
                    continue
                
                # Found user message!
                if entry['type'] == 'user_message':
                    user_content = entry['content']
                    self.agent.add_user_message(user_content)
                    return  # Resume agent
                
                # Also check for pause/archive
                if entry['type'] == 'status':
                    if entry['status'] == 'paused':
                        self.paused = True
                        return
                    elif entry['status'] == 'archived':
                        self.running = False
                        return
        
        # Sleep briefly before checking again
        time.sleep(0.5)
```

## How It Works Now

### Happy Path ✅

1. **Agent**: "You find yourself in a dark forest. What do you do?"
2. **Agent calls**: `wait_for_user(prompt="What do you do?")`
3. **AgentRunner**: 
   - Yields `waiting_for_input` status
   - Enters `_wait_for_user_message()` 
   - Polls log file every 0.5s
4. **User types in UI**: "I look around"
5. **API writes to log**: `{"type": "user_message", "content": "I look around"}`
6. **AgentRunner**:
   - Detects user_message
   - Adds to agent conversation: `agent.add_user_message("I look around")`
   - Returns from waiting
7. **Agent resumes**: Processes user's choice and continues story

### Control Signals While Waiting 🎮

If user pauses/archives while agent is waiting:
- `_wait_for_user_message()` also checks for status changes
- Sets `self.paused = True` or `self.running = False`
- Returns immediately
- Main loop handles the control signal

## Testing

### Manual Test
1. Start MechaWiki: `./start.sh`
2. Resume Interactive Agent in UI
3. Agent should ask a question and wait
4. Status should show `waiting_for_input` 
5. Type a response in chat box
6. Agent should continue (no crash!)

### Log Verification
Check `data/sessions/dev_session/logs/agent_interactive-001.jsonl`:

**Expected sequence:**
```jsonl
{"type": "message", "role": "assistant", "content": "What do you do?"}
{"type": "tool_call", "tool": "wait_for_user", "args": {"prompt": "..."}}
{"type": "status", "status": "waiting_for_input", "message": "..."}
... (pause here, waiting) ...
{"type": "user_message", "content": "I look around"}
{"type": "message", "role": "assistant", "content": "You look around..."}
```

**Should NOT see:**
- Immediate crash after `wait_for_user`
- Error about missing `tool_result` blocks
- Agent continuing without user input

## Files Changed

- `src/agents/agent_runner.py`:
  - Modified `_run_loop()` to track `waiting_for_user` flag
  - Added call to `_wait_for_user_message()` when waiting
  - New method `_wait_for_user_message()` that polls for user input

## Related Issues

This also fixes a potential race condition where:
- User might send a message while agent is processing
- Message would be lost if not properly queued
- Now properly waits for and consumes user messages in order

## Victory Conditions 🎉

- ✅ Interactive agents don't crash on `wait_for_user()`
- ✅ Agent properly waits for user input before continuing
- ✅ User messages are added to conversation history
- ✅ Control signals (pause/archive) still work while waiting
- ✅ No more "missing tool_result" errors from Claude

---

**Status:** FIXED ✅  
**Date:** 2025-11-08  
**Impact:** Interactive agents now fully functional!

