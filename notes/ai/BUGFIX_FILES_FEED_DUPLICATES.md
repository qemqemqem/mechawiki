# Bug Fix: Duplicate File Events in Files Feed

## Problem
File operations were appearing twice in the Files Feed UI.

## Root Cause

### React Strict Mode Double-Mounting
In React development mode, **Strict Mode** intentionally mounts components twice to help detect side effects. This causes the `useEffect` in `App.jsx` to run twice:

```javascript
useEffect(() => {
  fetchAgents()
  fetchInitialFiles()
  connectToFileFeed()  // Called twice!
}, [])
```

### Multiple EventSource Connections
Each time `connectToFileFeed()` runs, it creates a new `EventSource` connection to `/api/files/feed`. The backend creates a **new queue subscription** for each connection:

```python
@bp.route('/feed', methods=['GET'])
def file_feed():
    def generate():
        feed_queue = log_manager.subscribe_to_file_feed()  # New queue each time!
        # ...
```

### No Deduplication
The frontend was adding events to state without checking for duplicates:

```javascript
if (data.type === 'file_changed') {
  setFileChanges(prev => [data, ...prev])  // Always adds, no check!
}
```

## Result
Same file operation event received on **both** EventSource connections → appears **twice** in the UI.

## Solution

### Frontend Deduplication
Added deduplication logic in `src/ui/src/App.jsx`:

```javascript
eventSource.onmessage = (event) => {
  try {
    const data = JSON.parse(event.data)
    if (data.type === 'file_changed') {
      setFileChanges(prev => {
        // Create unique key for deduplication
        const key = `${data.timestamp}-${data.agent_id}-${data.file_path}-${data.action}`
        
        // Check if this event already exists
        const exists = prev.some(item => {
          const itemKey = `${item.timestamp}-${item.agent_id}-${item.file_path}-${item.action}`
          return itemKey === key
        })
        
        if (exists) {
          return prev // Skip duplicate
        }
        
        return [data, ...prev]
      })
    }
  } catch (error) {
    // Ignore keepalive messages
  }
}
```

### Why This Works
- **Unique Key**: Combines `timestamp`, `agent_id`, `file_path`, and `action` to uniquely identify each file event
- **Existence Check**: Before adding, checks if an event with the same key already exists in state
- **Skip Duplicates**: Returns unchanged state if duplicate detected

## Alternative Solutions Considered

### 1. Disable React Strict Mode
❌ **Not recommended** - Strict Mode helps catch bugs and is standard for React development.

### 2. Backend Deduplication
❌ **Not the right place** - The backend is correctly emitting events to all subscribers. The issue is multiple subscriptions from the same client.

### 3. Cleanup EventSource on Unmount
✅ **Already implemented** - The useEffect has a cleanup function that closes the EventSource, but Strict Mode still causes double-mounting.

### 4. Frontend Deduplication (Chosen)
✅ **Best solution** - Handles duplicates regardless of source (Strict Mode, network issues, browser tabs, etc.)

## Testing
To verify the fix:
1. Open the app in development mode (React Strict Mode enabled)
2. Have an agent perform file operations
3. Check Files Feed - each operation should appear only once
4. Check browser console - should see two "📡 Connected to file feed" messages (Strict Mode), but no duplicate entries in UI

## Notes
- This fix also protects against duplicates from other sources (network retries, multiple browser tabs, etc.)
- The deduplication key includes the action type, so if an agent reads the same file twice, both reads will appear (as expected)
- Production builds don't use Strict Mode, so this was primarily a development issue, but the fix is valuable for production too

