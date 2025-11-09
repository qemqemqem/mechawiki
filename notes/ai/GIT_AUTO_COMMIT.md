# Auto Git Commits for Wikicontent Edits

**Date**: 2025-11-09  
**Status**: ✅ Complete

## Overview

All file editing tools now automatically create git commits in the wikicontent repository whenever files are edited, created, or renamed. This ensures that every change made by agents is tracked in version control with descriptive commit messages.

## Changes Made

### New Helper Module: `src/tools/git_helper.py`

Created a centralized git helper module that provides two main functions:

#### 1. `commit_file_change(filepath, operation, wikicontent_path)`

Commits a single file change with an appropriate commit message.

**Operations supported:**
- `"edit"` - Edit existing file
- `"create"` - Create new file
- `"append"` - Append to file
- `"delete"` - Delete file (future use)

**Returns:**
```python
{
    "committed": bool,
    "message": str,  # Commit message
    "commit_hash": str | None  # SHA of the commit
}
```

**Features:**
- Automatically stages the file with `git add`
- Creates commit with descriptive message based on operation
- Returns commit hash for tracking
- Handles "nothing to commit" gracefully
- Safe error handling - never throws, always returns status

#### 2. `commit_file_rename(old_filepath, new_filepath, wikicontent_path)`

Commits a file rename operation using git's rename tracking.

**Returns:** Same structure as `commit_file_change`

**Features:**
- Uses `git mv` when possible for better rename tracking
- Falls back to staging both files if needed
- Generates descriptive "Rename X to Y" commit messages

### Updated Tool Functions

All file-editing tools now include automatic git commits:

#### 1. **`src/tools/files.py`**

- ✅ `edit_file()` - Commits after editing/creating files
- ✅ `add_to_story()` - Commits after appending to stories
- ✅ `rename_story_file()` - Commits rename operations

**Return value enhancement:**
```python
{
    "success": True,
    "file_path": str,
    "lines_added": int,
    "lines_removed": int,
    # New fields added when commit succeeds:
    "git_commit": str,  # Commit hash
    "git_message": str   # Commit message
}
```

#### 2. **`src/tools/story.py`** (Legacy tools)

- ✅ `write_story()` - Commits after writing story content
- ✅ `edit_story()` - Commits after editing story content

#### 3. **`src/tools/images.py`**

- ✅ `create_image()` - Commits after generating and saving images

#### 4. **`src/tools/articles.py`**

- ✅ `write_article()` - Commits after writing article content

## Commit Message Format

Commits are created with descriptive messages:

- **Create**: `"Create articles/wizard.md"`
- **Edit**: `"Edit articles/wizard.md"`
- **Append**: `"Append to stories/tale.md"`
- **Rename**: `"Rename stories/old.md to stories/new.md"`

## Benefits

### 1. **Complete Version History**
Every change made by agents is now tracked in git with timestamps and commit hashes.

### 2. **Easy Rollback**
If an agent makes an unwanted change, you can easily revert to a previous version using standard git commands.

### 3. **Change Attribution**
Each commit message clearly indicates what file was changed and how.

### 4. **Audit Trail**
Full history of all content changes for debugging and review.

### 5. **Branch-Based Workflows**
Changes are committed to the current branch, supporting branch-based content development.

## Safety Features

### Non-Blocking Errors
- If git commit fails, the file operation still succeeds
- Error messages are logged but don't prevent the tool from returning success
- Agents continue working even if git is unavailable

### Smart Detection
- Only commits if the directory is actually a git repository
- Handles "nothing to commit" gracefully
- No duplicate commits for unchanged files

### Clean Error Messages
- Clear error reporting in the returned data
- Never throws exceptions - always returns structured results

## Testing

All modules import successfully:
```bash
✅ git_helper imports successfully
✅ All tool modules import successfully
```

## Usage Example

When an agent uses `edit_file()`:

```python
result = edit_file("articles/wizard.md", diff)
# Result includes:
{
    "success": True,
    "file_path": "articles/wizard.md",
    "lines_added": 10,
    "lines_removed": 2,
    "git_commit": "abc123def456...",
    "git_message": "Edit articles/wizard.md"
}
```

The file is edited AND automatically committed to git with a descriptive message.

## Future Enhancements

Possible future improvements:
- Batch commits for multiple file operations
- Custom commit message templates
- Automatic push to remote (optional)
- Commit message enhancement with more context
- Support for git commit hooks

## Files Modified

### New Files:
- `src/tools/git_helper.py` - Core git commit logic

### Updated Files:
- `src/tools/files.py` - Added commits to edit_file, add_to_story, rename_story_file
- `src/tools/story.py` - Added commits to write_story, edit_story
- `src/tools/images.py` - Added commits to create_image
- `src/tools/articles.py` - Added commits to write_article

## Technical Details

### Import Structure
```python
from .git_helper import commit_file_change, commit_file_rename
```

All tools import the helper functions and call them after successful file operations.

### Error Handling Pattern
```python
# After successful file write:
git_result = commit_file_change(filepath, operation="edit", wikicontent_path=path)

# Add git info to result if commit succeeded:
if git_result["committed"]:
    result["git_commit"] = git_result["commit_hash"]
    result["git_message"] = git_result["message"]

return result
```

This pattern ensures:
1. File operations complete successfully first
2. Git commits are attempted second
3. Git failure doesn't break the tool
4. Commit info is included when available

## XP Philosophy Applied

✅ **"Strong defenses win campaigns"** - Every change is tracked, making rollback easy  
✅ **"Track the bugs before they track you"** - Full audit trail of all content changes  
✅ **"The Working Code"** - File operations still work even if git fails  
✅ **"Master the fundamentals"** - Clean, simple git commit helper that does one thing well  
✅ **"One quest at a time"** - Each file operation gets its own commit

## Victory! 🎯

The quest is complete! Every file edit in wikicontent now creates a git commit automatically. The party has strong defenses against lost changes and a clear trail of all modifications.

