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

## The Conversation State (Fixed)

```
assistant: [tool_call: wait_for_user]
tool: [result for wait_for_user]
user: "I dance!"                    ← Added by _wait_for_user_message()
                                    ← No duplicate! ✅
```

## Why This Works

1. When resuming after user input, the user's message is **already in the conversation**
2. Passing `None` to `run_forever()` tells it to continue **without adding another message**
3. The conversation format stays valid for Anthropic's API
4. **Backward compatible**: Existing code that passes messages still works

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
{"type": "tool_result", "tool": "wait_for_user", "result": {...}}
{"type": "status", "status": "waiting_for_input", ...}
{"type": "user_message", "content": "I dance!"}
{"type": "tool_call", "tool": "add_to_story", ...}  ← Continues successfully!
```

## Files Changed

- `src/base_agent/base_agent.py`: Made `initial_message` optional
- `src/agents/agent_runner.py`: Pass `None` when resuming after user input

## Impact

- ✅ Interactive agents can now handle user responses without crashing
- ✅ Conversation format stays valid for Anthropic API
- ✅ Backward compatible with all existing agent code
- ✅ Cleaner architecture (no duplicate messages)

## Related Patterns

This bug was similar to the previous `wait_for_user` fix (BUGFIX_INTERACTIVE_AGENT.md), but **different**:

- **Previous bug**: AgentRunner wasn't waiting for user input at all
- **This bug**: AgentRunner WAS waiting, but then added a duplicate message on resume

**The lesson:** When resuming agent execution after external input, be careful not to add redundant messages to the conversation history!

---

**Status:** FIXED ✅  
**Date:** 2025-11-08  
**Hunter:** Swift and Decisive Debugging 🏹

