# File Tools Refactoring

**Date**: 2025-11-09  
**Status**: ✅ Complete

## Overview

Refactored file operation tools to provide general-purpose read/edit capabilities inspired by the mockecy MCP server pattern, consolidating and clarifying the distinction between general file operations and story-specific operations.

## Changes Made

### New Tools Created (`src/tools/files.py`)

#### 1. **`read_file(filepath, start_line=None, end_line=None)`**
- **Purpose**: Read any file in wikicontent with optional line ranges
- **Returns**: `{"content": str}` or `{"error": str}`
- **Example**:
  ```python
  read_file("articles/wizard.md")
  read_file("stories/tale.md", start_line=10, end_line=20)
  ```

#### 2. **`edit_file(filepath, diff)`**
- **Purpose**: Edit or create files using Aider-style search/replace blocks
- **Diff Format**:
  ```
  <<<<<<< SEARCH
  old content to find
  =======
  new content to replace with
  >>>>>>> REPLACE
  ```
- **Returns**: 
  ```python
  {
      "success": bool,
      "error": str | None,
      "file_path": str,
      "lines_added": int,
      "lines_removed": int
  }
  ```
- **Features**:
  - Supports multiple search/replace blocks in one diff
  - Empty SEARCH block creates new file
  - Validates search text exists before replacing

#### 3. **`add_to_story(content, filepath)`**
- **Purpose**: Append narrative prose to the end of a story file
- **Use Case**: Writing sequential narrative content
- **Returns**: Same structured output as `edit_file` with `"mode": "append"`
- **Key Distinction**: Use this for continuing stories, use `edit_file` for surgical edits

### Tools Removed

These specialized tools are now redundant:

- ❌ `write_story()` → Replaced by `add_to_story()`
- ❌ `edit_story()` → Replaced by `edit_file()`
- ❌ `write_article()` → Replaced by `edit_file()` (for creating/editing articles)

### Tool Philosophy

**General-Purpose Tools**:
- `read_file()` - Read ANY file
- `edit_file()` - Edit ANY file with surgical precision

**Specialized Tools**:
- `add_to_story()` - Specific to narrative prose appending
- `read_article()` - Convenience wrapper for article reading (kept for backward compat)
- `search_articles()` - Search article directory
- `list_articles_in_directory()` - List articles

## Agent Updates

### WriterAgent
**New System Prompt**:
```
You have access to:
- File operations (read_file, edit_file) - Read and edit ANY file in wikicontent
- Story writing (add_to_story) - Append narrative prose to story files
- Article tools (read_article, search_articles, list_articles) - Search and read articles
- Image generation (create_image) - Generate artwork

Best practices:
- Use add_to_story() for writing new narrative content that flows sequentially
- Use edit_file() with search/replace blocks for surgical edits to existing content
- Use read_file() to check file contents before editing
```

### InteractiveAgent
Updated with same file tools, with guidance to:
- Use `add_to_story()` to record interactive sessions as narratives
- Use `edit_file()` to create/update wiki articles for story developments

### ReaderAgent
No changes needed (doesn't use write tools).

## Server/UI Updates

### Log Watcher (`src/server/log_watcher.py`)
```python
file_tools = ['read_file', 'edit_file', 'add_to_story', 'read_article', 'create_image']
```

### AgentView UI (`src/ui/src/components/agents/AgentView.jsx`)
```javascript
if ((toolName === 'read_file' || toolName === 'edit_file') && toolArgs.filepath) {
  return `${displayName}: ${toolArgs.filepath}`
}
if (toolName === 'add_to_story' && toolArgs.filepath) {
  return `${displayName}: ${toolArgs.filepath}`
}
```

### MockAgent
Updated to use `add_to_story` instead of `write_article`.

## Test Coverage

Created comprehensive test suite in `tests/test_new_file_tools.py`:

✅ **read_file**:
- Reads file successfully
- Reads with line range
- Returns error for nonexistent file

✅ **edit_file**:
- Creates new file with empty SEARCH block
- Edits existing file
- Handles multiple search/replace blocks
- Returns error for search text not found
- Returns error for invalid diff format

✅ **add_to_story**:
- Appends content to file
- Creates file if not exists
- Returns structured output with line counts

✅ **Integration**:
- Edit then read
- Add to story then edit

**All 13 tests passing!**

## Design Inspiration

This refactoring was inspired by the mockecy MCP server pattern (`~/Dev/mockecy/ai/mcp_server.py`), which uses:
- General-purpose `read_file()` and `edit_file()` 
- Aider-style search/replace blocks for precise editing
- Clear separation between reading and editing operations

## Benefits

1. **Consistency**: All file operations use the same interface
2. **Flexibility**: `edit_file` works on ANY file, not just stories or articles
3. **Precision**: Search/replace blocks enable surgical edits
4. **Clarity**: Tool names clearly indicate what they do:
   - `read_file` = read any file
   - `edit_file` = edit any file
   - `add_to_story` = append to story (the one specialized tool)

## Migration Notes

**Old Code** → **New Code**:

```python
# Old: Creating an article
write_article("wizard", "# Wizard\n\nContent...")

# New: Creating an article
edit_file("articles/wizard.md", """<<<<<<< SEARCH
=======
# Wizard

Content...
>>>>>>> REPLACE""")

# Old: Appending to story
write_story("Chapter 2...", "stories/tale.md", append=True)

# New: Appending to story
add_to_story("Chapter 2...", "stories/tale.md")

# Old: Editing story
edit_story("stories/tale.md", "old text", "new text")

# New: Editing any file
edit_file("stories/tale.md", """<<<<<<< SEARCH
old text
=======
new text
>>>>>>> REPLACE""")
```

## Future Enhancements

Possible additions:
- `delete_file()` - Delete files
- `list_files()` - List all files in wikicontent
- More sophisticated diff parsing (line numbers, fuzzy matching)

## Victory! 🏆

The direct path wins the race! We now have clean, general-purpose file tools that give agents full control over their content creation process.

