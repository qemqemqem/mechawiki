# Interactive Agent: Missing Tool Result Bug Fix 🐛→✅

## The Problem

Interactive agents were crashing after `wait_for_user()` with this error:

```
litellm.BadRequestError: AnthropicException - 
messages.2: `tool_use` ids were found without `tool_result` blocks immediately after: toolu_01KCwZ7YoNCM6caEdTXsxuMo
```

## Root Cause Analysis

When `wait_for_user()` was called, the **tool_result event was never consumed**, leaving the conversation with a tool_call but no corresponding tool_result!

### The Bug Flow

**In BaseAgent (event generator):**
1. ✅ Yields `status` event (waiting_for_input)
2. ❌ Yields `tool_result` event ← **Never consumed!**
3. ✅ Adds tool result to conversation
4. ✅ Returns from generator

**In AgentRunner (event consumer):**
```python
for event in self.agent.run_forever(initial_prompt, max_turns=1):
    signal = self._handle_event(event)
    
    if signal == 'wait_for_input':  # Triggered by status event
        waiting_for_user = True
        break  # ← BREAKS TOO EARLY! Abandons tool_result event!
```

### The Conversation State (Broken)

```
assistant: "..." [tool_call: wait_for_user]
← tool_result is MISSING because event wasn't consumed!
user: "I am curious about the minerals"
```

When the LLM tried to process this conversation, it saw a tool_call without a tool_result, violating Anthropic's API requirements.

## The Fix

### Part 1: Don't Break Early - Consume All Events

**File:** `src/agents/agent_runner.py`

```python
# Before (BROKEN)
for event in self.agent.run_forever(initial_prompt, max_turns=1):
    signal = self._handle_event(event)
    
    if signal == 'wait_for_input':
        waiting_for_user = True
        break  # ← TOO EARLY! Tool result not consumed yet!

# After (FIXED)  
for event in self.agent.run_forever(initial_prompt, max_turns=1):
    signal = self._handle_event(event)
    
    if signal == 'wait_for_input':
        # Mark that we'll wait, but DON'T break yet
        # We need to consume remaining events (like tool_result)
        waiting_for_user = True
        # Loop continues, consumes tool_result, then exits naturally
```

### Part 2: Make `initial_message` Optional

**File:** `src/base_agent/base_agent.py`

```python
# Make initial_message optional so we can resume without adding duplicates
def run_forever(self, initial_message: Optional[str] = None, max_turns: int = 3):
    if initial_message is not None:
        self.add_user_message(initial_message)
```

### Part 3: Pass `None` When Resuming

**File:** `src/agents/agent_runner.py`

```python
if waiting_for_user:
    self._wait_for_user_message()
    initial_prompt = None  # Don't add duplicate message
else:
    initial_prompt = "Continue your task."
```

### Part 4: Defensive Programming - Automatic Repair

**File:** `src/base_agent/base_agent.py`

Added `_validate_and_repair_conversation_history()` method that runs **before every LLM call** to catch any orphaned tool_calls and automatically add dummy tool_results. This provides a safety net in case bugs slip through or conversation history is loaded from disk.

```python
def run_forever(self, initial_message: Optional[str] = None, max_turns: int = 3):
    # ...
    # Validate and repair conversation history (defensive programming)
    self._validate_and_repair_conversation_history()
    
    # Make LLM call
    response = litellm.completion(...)
```

**Benefits:**
- ✅ Prevents crashes from malformed conversation history
- ✅ Logs warnings when repairs are made (helps catch bugs)
- ✅ Handles edge cases like loading saved conversations
- ✅ Zero impact when conversation is already valid

## The Conversation State (Fixed)

```
assistant: "..." [tool_call: wait_for_user]
tool: [result for wait_for_user]    ← Now properly added! ✅
user: "I am curious about the minerals"
```

## Why This Works

1. **All events are consumed**: The loop doesn't break early, so `tool_result` is processed
2. **Tool result is logged**: The tool_result event is properly logged to JSONL
3. **Conversation is complete**: The tool_call has its corresponding tool_result
4. **No duplicates**: Passing `None` on resume prevents duplicate user messages
5. **Backward compatible**: Existing code that passes messages still works

## Testing

### Manual Test Flow

1. Start MechaWiki: `./start.sh`
2. Resume Interactive Agent in UI
3. Agent asks a question with `wait_for_user()`
4. Type a response (e.g., "I dance!")
5. Agent should continue **without crashing** ✅

### Expected Log Sequence

```jsonl
{"type": "tool_call", "tool": "wait_for_user", "args": {...}}
{"type": "status", "status": "waiting_for_input", ...}
{"type": "tool_result", "tool": "wait_for_user", "result": {...}}  ← NOW LOGGED!
{"type": "user_message", "content": "I am curious about the minerals"}
{"type": "tool_call", "tool": "add_to_story", ...}  ← Continues successfully!
```

## Files Changed

- `src/agents/agent_runner.py`: 
  - Don't break early when waiting for input - consume all events
  - Pass `None` when resuming after user input
- `src/base_agent/base_agent.py`: 
  - Made `initial_message` optional
  - Added `_validate_and_repair_conversation_history()` defensive check
  - Runs repair before every LLM call to catch any orphaned tool_calls

## Impact

- ✅ Interactive agents can now handle user responses without crashing
- ✅ Conversation format stays valid for Anthropic API
- ✅ Backward compatible with all existing agent code
- ✅ Cleaner architecture (no duplicate messages)
- ✅ Defensive programming prevents future similar bugs
- ✅ Automatic repair helps debug conversation history issues

## Related Patterns

This was actually **TWO bugs** that we fixed:

### Bug 1: Early Break Abandoning Events
- **Problem**: `break` in the event loop abandoned unconsumed events
- **Fix**: Set flag but continue consuming events until generator exhausts
- **Lesson**: When consuming generator events, exhaust the generator before acting on signals!

### Bug 2: Duplicate User Messages  
- **Problem**: `run_forever()` always added initial_message, even on resume
- **Fix**: Made initial_message optional, pass `None` when resuming
- **Lesson**: When resuming execution after external input, don't duplicate messages!

**The deeper lesson:** Event-driven architectures require careful coordination between producers (generators) and consumers (event loops). Signals can be passed through events, but the consumer must finish consuming before acting on control flow signals!

---

**Status:** FIXED ✅  
**Date:** 2025-11-08  
**Hunter:** Swift and Decisive Debugging 🏹

