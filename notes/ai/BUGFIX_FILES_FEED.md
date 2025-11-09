# Bug Fix: Files Feed Not Showing Agent File Changes

## Problem 1: Files Feed Not Detecting Changes
The Files Feed UI wasn't detecting file changes made by agents (e.g., `write_article`, `edit_story`, `create_image`).

## Problem 2: Read Operations Not Shown
The Files Feed didn't show when agents read articles. We wanted read operations to appear with "read" instead of line counts.

## Root Cause
The tools were returning **simple strings** instead of **structured dictionaries**. The log watcher expects tool results to contain:
- `file_path`: relative path to the modified file
- `lines_added`: number of lines added
- `lines_removed`: number of lines removed

## Solution
Updated all file operation tools to return structured data instead of strings:

### Tools Updated
1. **`write_article`** (`src/tools/articles.py`)
   - Now returns dict with `file_path`, `lines_added`, `lines_removed`, `message`
   - Calculates line diff by comparing old/new content

2. **`write_story`** (`src/tools/story.py`)
   - Returns dict with `file_path`, `lines_added`, `lines_removed`, `message`
   - Handles append vs overwrite modes correctly

3. **`edit_story`** (`src/tools/story.py`)
   - Returns dict with `file_path`, `lines_added`, `lines_removed`, `message`
   - Calculates line changes from search/replace operation

4. **`create_image`** (`src/tools/images.py`)
   - Returns dict with `file_path`, `lines_added` (1), `lines_removed` (0), `message`
   - Includes extra metadata: `orientation`, `size`, `generator`

## How It Works

### Data Flow
```
Agent Tool
  ↓ returns dict
BaseAgent._execute_tool()
  ↓ yields tool_result event with raw dict
AgentRunner._handle_event()
  ↓ logs event to JSONL
LogManager.process_log_entry()
  ↓ detects file operation, extracts file_path
File Feed (UI)
  ↓ displays file change
```

### Log Format (Before)
```jsonl
{"type": "tool_result", "tool": "write_article", "result": "✅ Successfully wrote to article.md", "timestamp": "..."}
```

### Log Format (After)
```jsonl
{"type": "tool_result", "tool": "write_article", "result": {
  "file_path": "articles/article.md",
  "lines_added": 45,
  "lines_removed": 0,
  "message": "✅ Successfully wrote to article.md"
}, "timestamp": "..."}
```

## Log Watcher Detection
The `LogManager` in `src/server/log_watcher.py`:
1. Watches for `tool_result` events
2. Checks if tool is in `file_tools` list (line 219)
3. Extracts `file_path`, `lines_added`, `lines_removed` from result dict (line 223-245)
4. Broadcasts file event to Files Feed subscribers

## Testing
To verify the fix:
1. Start the server
2. Watch an agent that writes files (e.g., writer agent)
3. Check Files Feed UI for new entries
4. Click on file entry to view content

## Read Operations Support (Added Later)

### Problem
The Files Feed wasn't showing when agents read articles. We wanted read operations to appear with "read" instead of line counts.

### Solution

#### Backend: `read_article` Updated
`src/tools/articles.py` - Now returns structured data:
```python
{
    "file_path": "articles/example.md",
    "content": "...",  # The actual article content
    "lines_added": 0,
    "lines_removed": 0,
    "read": True,
    "message": "📖 Read article: example.md"
}
```

#### Log Watcher Updated
`src/server/log_watcher.py` (line 219-223) - Added `read_article`, `write_article`, `write_story`, `edit_story` to the `file_tools` list.

#### Frontend: Show "read" Label
`src/ui/src/components/files/FilesFeed.jsx` - Updated `formatChanges`:
```javascript
const formatChanges = (changes) => {
  if (!changes) return ''
  const { added = 0, removed = 0 } = changes
  // If both are 0, it's a read operation
  if (added === 0 && removed === 0) return 'read'
  return `+${added} -${removed}`
}
```

### Test Coverage
✅ **107 tests passing**
- 2 new tests for `read_article` structured output
- 4 existing tests updated for new dict return format
- All integration tests passing

## Notes
- Error cases still return strings (e.g., "❌ Error: ...")
- The `message` field in success dicts preserves the original human-readable message
- Agents see the JSON-stringified version in their conversation context
- Binary files (images) use `lines_added: 1` as a sentinel for "new file"
- Read operations use `lines_added: 0, lines_removed: 0` to indicate no modification

