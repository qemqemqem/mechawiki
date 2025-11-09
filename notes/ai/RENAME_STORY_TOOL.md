# rename_my_story() Tool Implementation

## Summary

Added a `rename_my_story(new_filename)` tool to WriterAgent that allows agents to rename their story files dynamically. The tool handles both filesystem operations and configuration updates.

## Features Implemented

### 1. Core Functionality (`rename_story_file()` utility)
Located in `src/tools/files.py`

**Capabilities:**
- Renames files in wikicontent
- Creates target directories if needed
- Preserves file content
- Validates source file exists
- Checks target doesn't already exist
- Returns structured success/error responses

**Function Signature:**
```python
rename_story_file(old_filepath: str, new_filepath: str) -> Dict[str, Any]
```

**Returns:**
```python
{
    "success": bool,
    "message": str,
    "old_path": str,
    "new_path": str
}
# or on error:
{
    "success": False,
    "error": str
}
```

### 2. Agent Tool (`rename_my_story()`)
Added to `WriterAgent` class

**Features:**
- Bound to agent instance with closure
- Updates agent's `story_file` attribute
- Updates agent's system prompt with new filename
- Updates agents.json config via `SessionConfig.update_agent()`
- Smart path handling: just filename keeps same directory, full path moves to new location

**Tool Signature:**
```python
def rename_my_story(new_filename: str):
    """
    Rename your story file to a new name.
    
    Parameters:
    - new_filename: "new_name.md" or "stories/new_name.md"
    """
```

**Usage Examples:**
```python
# Rename in same directory
rename_my_story("epic_adventure.md")
# stories/writer_story.md → stories/epic_adventure.md

# Move to different directory
rename_my_story("stories/published/final.md")
# stories/draft.md → stories/published/final.md
```

### 3. Integration Points

**WriterAgent initialization:**
- Now accepts `agent_id` parameter
- Passes agent_id to rename tool for config updates

**AgentManager:**
- Automatically passes `agent_id` when creating WriterAgent instances
- Lines 106-108 in `src/server/agent_manager.py`

**SessionConfig:**
- Enhanced `update_agent()` to perform deep merge for nested config dicts
- Prevents overwriting other config keys when updating `story_file`

**Agent Prompt:**
- Updated `writer_agent.md` to document the rename tool
- Added to "Story Management" section
- Mentioned in best practices

### 4. Comprehensive Test Suite
Created `tests/test_rename_story.py` with 13 tests

**Test Classes:**
1. **TestRenameStoryFileUtility** (5 tests)
   - Basic rename functionality
   - Directory creation
   - Error handling for missing/existing files
   - Cross-directory renames

2. **TestWriterAgentRenameTool** (7 tests)
   - Tool presence in agent
   - Agent attribute updates
   - Filesystem changes
   - System prompt updates
   - Same-directory vs. cross-directory logic
   - Graceful error handling

3. **TestRenameToolIntegration** (1 test)
   - Rename then add_to_story workflow

**Test Results:** ✅ 13/13 passing

## Implementation Details

### Path Handling Logic
```python
# If just filename, keep current directory
if len(Path(new_filename).parts) == 1:
    new_filepath = str(old_path.parent / new_filename)
else:
    new_filepath = new_filename
```

### Config Update (Deep Merge)
```python
# SessionConfig.update_agent() now does:
merged_config = agent["config"].copy()
merged_config.update(updates["config"])
agent["config"] = merged_config
```

This preserves other config fields like `model`, `description`, etc.

### System Prompt Regeneration
After rename, the agent's system prompt is rebuilt with the new filename:
```python
self.system_prompt = f"""{base_prompt}

---

## Your Story File

**Your designated output file:** `{new_filepath}`

When you write new narrative content, use:
add_to_story(content="your prose here", filepath="{new_filepath}")
```

## Files Modified

1. `src/tools/files.py` - Added `rename_story_file()` utility
2. `src/agents/writer_agent.py` - Added `rename_my_story()` tool
3. `src/agents/prompts/writer_agent.md` - Documented rename capability
4. `src/server/agent_manager.py` - Pass agent_id to WriterAgent
5. `src/server/config.py` - Enhanced update_agent() with deep merge
6. `tests/test_rename_story.py` - 13 comprehensive tests
7. `tests/README.md` - Documented new test file

## Usage in Practice

When a WriterAgent calls `rename_my_story()`:

1. ✅ File is renamed in wikicontent filesystem
2. ✅ Agent's `story_file` attribute is updated
3. ✅ Agent's system prompt is regenerated with new path
4. ✅ agents.json is updated with new story_file in config
5. ✅ Agent can immediately continue writing to new file

**Example agent flow:**
```python
# Agent writes some content
add_to_story("Once upon a time...", "stories/writer_story.md")

# Agent decides to give it a better name
rename_my_story("tale_of_wonder.md")

# Agent continues writing to renamed file
add_to_story("Chapter 2...", "stories/tale_of_wonder.md")
```

## Error Handling

The tool returns errors as structured dicts, not exceptions:

- **Source not found:** `{"success": False, "error": "Source file not found: ..."}`
- **Target exists:** `{"success": False, "error": "Target file already exists: ..."}`
- **Config update fails:** Returns success but with warning message

This allows the agent to see and respond to errors gracefully.

## Testing Strategy

**Unit Tests:**
- Isolated testing of `rename_story_file()` utility
- Agent tool behavior with mocked filesystem
- Error conditions and edge cases

**Integration Tests:**
- Rename + add_to_story workflow
- Multiple renames in sequence
- Cross-directory moves

**Fixtures:**
- `temp_wikicontent` - Isolated filesystem for each test
- `temp_session` - Isolated session config
- Automatic cleanup after tests

## Philosophy Alignment

✅ **"Swift and Decisive"** - Tool executes quickly, updates everything needed  
✅ **"Strong defenses"** - 13 tests ensure reliability  
✅ **"Hunt with Purpose"** - Clear single responsibility  
✅ **"The Working Code"** - All tests pass, ready to use  

---

**Hunt with purpose! Give your stories the names they deserve.** 🏰✍️

