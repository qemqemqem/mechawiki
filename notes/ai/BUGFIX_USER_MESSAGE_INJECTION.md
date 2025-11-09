# User Message Injection Bug Fix 🐛→✅

## Problem

When a user sent a message to a running agent via the UI, the message would:
1. ✅ Get logged to the JSONL file
2. ❌ **NOT** get injected into the agent's conversation history
3. ❌ Agent would continue its task, completely ignoring the user's message

**Example:**
```jsonl
{"timestamp": "2025-11-09T12:18:49.688997", "type": "user_message", "content": "what was the first message from me that you see?"}
{"type": "message", "role": "assistant", "content": "Let me read some of the analysis and project-related articles to understand the collection better.", "timestamp": "2025-11-09T12:18:52.972368"}
```

The agent completely ignored the user's question!

## Root Cause

**The `_check_control_signals()` method only checked for pause/resume/archive commands - NOT user messages!**

The `_wait_for_user_message()` method DOES inject user messages, but it only runs when:
1. Agent explicitly calls `wait_for_user()` (interactive agents)
2. Agent finishes its task
3. Agent encounters an error

**When the agent is actively working**, user messages were logged but never injected!

## The Fix

### 1. Expand `_check_control_signals()` to also check for user messages

```python
def _check_control_signals(self):
    """Check log file for pause/resume/archive commands AND user messages."""
    # ... existing status change handling ...
    
    # Look for user messages and inject them into conversation
    elif entry.get('type') == 'user_message':
        user_content = entry.get('content', '')
        if user_content:
            # Add to agent's conversation history
            self.agent.add_user_message(user_content)
            # Set flag so we don't add another prompt
            self.user_message_injected = True
            logger.info(f"💬 Injected user message into {self.agent_id}: {user_content[:50]}...")
```

### 2. Track when user message is injected to prevent double prompts

```python
# Added tracking flag
self.user_message_injected = False

# In main loop:
if self.user_message_injected:
    initial_prompt = None
    self.user_message_injected = False
```

Without this, we'd have:
- User's message: "what was the first message?"
- Auto-added prompt: "Continue your task." ❌

Now we just have:
- User's message: "what was the first message?" ✅

## Timing

User messages are now picked up **at the start of each turn**! 

**What's a "turn"?**
- A turn = one complete LLM call + all its tool executions
- Agent may execute multiple tools per turn
- Turns are kept short (`max_turns=1`) so user messages are picked up quickly

**Flow:**
1. Agent completes current turn (all tool calls finish)
2. `_check_control_signals()` runs at start of next loop iteration
3. If user message found, inject it and skip continuation prompt
4. Agent's next LLM call sees the user's message

**Why not inject between tool executions?**

We initially tried injecting user messages between individual tool calls, but this breaks Anthropic's API requirements:

```
❌ BROKEN:
  Assistant: [calls tool1, tool2, tool3]
  Tool result 1
  USER MESSAGE ← Breaks structure!
  Tool result 2 ← No matching tool_use!
  Tool result 3
```

Anthropic requires ALL tool results to follow their corresponding assistant message before the next user message.

```
✅ CORRECT:
  Assistant: [calls tool1, tool2, tool3]
  Tool result 1
  Tool result 2
  Tool result 3
  USER MESSAGE ← Safe injection point
  Assistant: [responds to user]
```

## Testing

To test this fix:
1. Start an agent
2. While it's actively working, send it a message
3. The agent should respond to your message on the next turn

## Files Changed

- `src/agents/agent_runner.py`:
  - Modified `_check_control_signals()` to check for user messages
  - Added `self.user_message_injected` tracking flag
  - Modified main loop to skip continuation prompt when user message injected

## Impact

✅ Users can now interrupt running agents with questions/directions
✅ Agents will respond to user messages even when not explicitly waiting for input
✅ No breaking changes - backward compatible with existing behavior

