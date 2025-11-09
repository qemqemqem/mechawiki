# Bug Fix: SSE Connection Timeout for Agent Messages

## Problem

User messages sent to agents (especially when paused or waiting for input) would not appear in the UI immediately. The messages were being saved to the log file, but only became visible after navigating away and back to the agent view.

## Root Cause

The bug had two components:

### 1. Backend SSE Connection Dying After 30 Seconds (PRIMARY BUG)

In `src/server/agents.py`, the SSE endpoint had a critical flaw in its exception handling:

```python
# BEFORE (broken):
try:
    while True:
        log_entry = log_queue.get(timeout=30)
        yield f"data: {json.dumps(log_entry)}\n\n"
except queue.Empty:
    yield f": keepalive\n\n"
```

**Issue:** The `try-except` wrapped the entire `while True` loop. When no logs arrived for 30 seconds (which happens when agents are paused or waiting), `queue.Empty` was raised. After sending a keepalive, the generator **exited completely** instead of continuing to wait for more logs.

This meant:
- SSE connection would die after 30 seconds of agent inactivity
- User messages were saved to log file but never streamed to the frontend
- Only creating a new connection (by navigating away/back) would show the messages

### 2. Frontend Had No Reconnection Logic (SECONDARY ISSUE)

The frontend `AgentView.jsx` had no automatic reconnection when the SSE connection failed. Once the connection closed, it stayed closed until the component unmounted and remounted.

## Solution

### Backend Fix (Primary)

Moved the `try-except` **inside** the while loop so it continues after sending keepalives:

```python
# AFTER (fixed):
while True:
    try:
        log_entry = log_queue.get(timeout=30)
        yield f"data: {json.dumps(log_entry)}\n\n"
    except queue.Empty:
        # Send keepalive and continue
        yield f": keepalive\n\n"
```

Now the SSE connection stays alive indefinitely, sending keepalives every 30 seconds when there are no new logs.

### Frontend Enhancement (Defense in Depth)

Added automatic reconnection logic to `AgentView.jsx`:
- If the SSE connection fails for any reason, it automatically reconnects after 3 seconds
- Proper cleanup to prevent memory leaks
- Uses `isMounted` flag to prevent reconnection attempts after component unmounts

## Testing

To verify the fix works:
1. Start an InteractiveAgent (or any agent)
2. Let it pause or wait for input for more than 30 seconds
3. Send a message
4. The message should appear immediately in the UI
5. Check browser console - should see keepalive messages every 30 seconds (not errors)

## Files Modified

- `src/server/agents.py` - Fixed SSE generator to keep connection alive
- `src/ui/src/components/agents/AgentView.jsx` - Added automatic reconnection logic

