"""
General file operation tools for agents.

These tools provide reading and editing capabilities for any file in wikicontent,
inspired by the mockecy MCP server pattern.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional
import re
from .git_helper import commit_file_change, commit_file_rename


def read_file(
    filepath: str,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None
) -> Dict[str, Any]:
    """
    Read the contents of a file in wikicontent.
    
    Parameters
    ----------
    filepath : str
        Path relative to wikicontent root (e.g. "articles/wizard.md", "stories/tale.md")
    start_line : int, optional
        Starting line number (1-indexed, inclusive)
    end_line : int, optional
        Ending line number (1-indexed, inclusive)
    
    Returns
    -------
    dict
        {"content": str} on success, or {"error": str} on failure
    
    Examples
    --------
    >>> read_file("articles/merlin.md")
    {"content": "# Merlin\n\nA powerful wizard..."}
    
    >>> read_file("stories/adventure.md", start_line=1, end_line=10)
    {"content": "First 10 lines of the story..."}
    """
    try:
        # Get wikicontent path from environment or default
        wikicontent_path = Path(os.environ.get(
            'WIKICONTENT_PATH',
            str(Path.home() / "Dev" / "wikicontent")
        ))
        
        # Construct full path
        full_path = wikicontent_path / filepath
        
        # Check if file exists
        if not full_path.exists():
            return {"error": f"File not found: {filepath}"}
        
        # Read file content
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Apply line range if specified
        if start_line is not None or end_line is not None:
            lines = content.splitlines()
            start_idx = (start_line - 1) if start_line else 0
            end_idx = end_line if end_line else len(lines)
            content = "\n".join(lines[start_idx:end_idx])
        
        return {"content": content}
    
    except Exception as e:
        return {"error": f"Error reading file: {str(e)}"}


def edit_file(filepath: str, diff: str) -> Dict[str, Any]:
    """
    Edit an existing file or create a new file using Aider-style search/replace blocks.
    
    Diff format:
    ```
    <<<<<<< SEARCH
    old content to find
    =======
    new content to replace with
    >>>>>>> REPLACE
    ```
    
    Multiple search/replace blocks can be provided in a single diff.
    
    To create a new file, use an empty SEARCH block:
    ```
    <<<<<<< SEARCH
    =======
    new file content here
    >>>>>>> REPLACE
    ```
    
    Parameters
    ----------
    filepath : str
        Path relative to wikicontent root (e.g. "articles/wizard.md")
    diff : str
        Aider-style diff with search/replace blocks
    
    Returns
    -------
    dict
        {
            "success": bool,
            "error": str | None,
            "file_path": str,
            "lines_added": int,
            "lines_removed": int
        }
    
    Examples
    --------
    >>> diff = '''
    ... <<<<<<< SEARCH
    ... old text
    ... =======
    ... new text
    ... >>>>>>> REPLACE
    ... '''
    >>> edit_file("articles/wizard.md", diff)
    {"success": True, "error": None, ...}
    """
    try:
        # Get wikicontent path
        wikicontent_path = Path(os.environ.get(
            'WIKICONTENT_PATH',
            str(Path.home() / "Dev" / "wikicontent")
        ))
        
        full_path = wikicontent_path / filepath
        
        # Check if file exists
        file_exists = full_path.exists()
        original_content = ""
        
        if file_exists:
            with open(full_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
        
        # Apply diff
        new_content, error = _apply_diff(original_content, diff, file_exists)
        
        if error:
            return {
                "success": False,
                "error": error
            }
        
        # Ensure directory exists
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write new content
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        # Calculate line changes
        old_lines = original_content.count('\n') + 1 if original_content else 0
        new_lines = new_content.count('\n') + 1 if new_content else 0
        lines_added = max(0, new_lines - old_lines)
        lines_removed = max(0, old_lines - new_lines)
        
        # Commit the change to git
        operation = "create" if not file_exists else "edit"
        git_result = commit_file_change(filepath, operation=operation, wikicontent_path=wikicontent_path)
        
        result = {
            "success": True,
            "error": None,
            "file_path": filepath,
            "lines_added": lines_added,
            "lines_removed": lines_removed
        }
        
        # Add git commit info to result
        if git_result["committed"]:
            result["git_commit"] = git_result["commit_hash"]
            result["git_message"] = git_result["message"]
        
        return result
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Error editing file: {str(e)}"
        }


def add_to_story(content: str, filepath: str) -> Dict[str, Any]:
    """
    Append narrative prose to the end of a story file.
    
    This is the tool for writing new story content that flows sequentially.
    Use this when you're continuing a narrative, not when editing existing content.
    For editing existing content, use edit_file() instead.
    
    Parameters
    ----------
    content : str
        The narrative prose to append to the story
    filepath : str
        Path relative to wikicontent root (e.g. "stories/adventure.md")
    
    Returns
    -------
    dict
        {
            "success": bool,
            "message": str,
            "file_path": str,
            "lines_added": int,
            "lines_removed": int,
            "mode": "append"
        }
    
    Examples
    --------
    >>> add_to_story("The wizard cast a spell...", "stories/tale.md")
    {"success": True, "message": "Appended to stories/tale.md", ...}
    """
    try:
        # Get wikicontent path
        wikicontent_path = Path(os.environ.get(
            'WIKICONTENT_PATH',
            str(Path.home() / "Dev" / "wikicontent")
        ))
        
        full_path = wikicontent_path / filepath
        
        # Ensure directory exists
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Append content
        with open(full_path, 'a', encoding='utf-8') as f:
            f.write(content)
        
        lines_added = content.count('\n') + 1
        
        # Commit the change to git
        git_result = commit_file_change(filepath, operation="append", wikicontent_path=wikicontent_path)
        
        result = {
            "success": True,
            "message": f"Appended to {filepath}",
            "file_path": filepath,
            "lines_added": lines_added,
            "lines_removed": 0,
            "mode": "append"
        }
        
        # Add git commit info to result
        if git_result["committed"]:
            result["git_commit"] = git_result["commit_hash"]
            result["git_message"] = git_result["message"]
        
        return result
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def rename_story_file(old_filepath: str, new_filepath: str) -> Dict[str, Any]:
    """
    Rename a story file in wikicontent.
    
    This is a utility function used by agent tools to rename their story files.
    It only handles the file system operation, not agent config updates.
    
    Parameters
    ----------
    old_filepath : str
        Current path relative to wikicontent root
    new_filepath : str
        New path relative to wikicontent root
    
    Returns
    -------
    dict
        {"success": bool, "message": str, "old_path": str, "new_path": str}
        or {"success": bool, "error": str}
    """
    try:
        # Get wikicontent path
        wikicontent_path = Path(os.environ.get(
            'WIKICONTENT_PATH',
            str(Path.home() / "Dev" / "wikicontent")
        ))
        
        old_full_path = wikicontent_path / old_filepath
        new_full_path = wikicontent_path / new_filepath
        
        # Check if old file exists
        if not old_full_path.exists():
            return {
                "success": False,
                "error": f"Source file not found: {old_filepath}"
            }
        
        # Check if new file already exists
        if new_full_path.exists():
            return {
                "success": False,
                "error": f"Target file already exists: {new_filepath}"
            }
        
        # Ensure target directory exists
        new_full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Rename the file
        old_full_path.rename(new_full_path)
        
        # Commit the rename to git
        git_result = commit_file_rename(old_filepath, new_filepath, wikicontent_path=wikicontent_path)
        
        result = {
            "success": True,
            "message": f"Renamed story file from {old_filepath} to {new_filepath}",
            "old_path": old_filepath,
            "new_path": new_filepath
        }
        
        # Add git commit info to result
        if git_result["committed"]:
            result["git_commit"] = git_result["commit_hash"]
            result["git_message"] = git_result["message"]
        
        return result
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Error renaming file: {str(e)}"
        }


def _apply_diff(original_content: str, diff: str, file_exists: bool) -> tuple[str, Optional[str]]:
    """
    Apply Aider-style search/replace diff to content.
    
    Returns (new_content, error_message).
    If error_message is not None, the operation failed.
    """
    # Parse diff blocks - use simpler pattern that captures everything between markers
    pattern = r'<<<<<<< SEARCH(.*?)=======(.*?)>>>>>>> REPLACE'
    raw_matches = re.findall(pattern, diff, re.DOTALL)
    
    # Clean up the captured content (strip leading/trailing newlines and whitespace)
    matches = [(search.strip(), replace.strip()) for search, replace in raw_matches]
    
    if not matches:
        return None, "Invalid diff format. Expected <<<<<<< SEARCH / ======= / >>>>>>> REPLACE blocks."
    
    new_content = original_content
    
    for search_text, replace_text in matches:
        # Handle new file creation (empty search block)
        if not search_text.strip():
            if not file_exists or not original_content.strip():
                # File doesn't exist or is empty - create it
                new_content = replace_text
                continue
            else:
                return None, "Cannot use empty SEARCH block on existing non-empty file. Use specific search text to edit."
        
        # Check if search text exists in content
        if search_text not in new_content:
            return None, f"Search text not found in file:\n---\n{search_text}\n---"
        
        # Replace the text
        new_content = new_content.replace(search_text, replace_text, 1)  # Replace only first occurrence
    
    return new_content, None


if __name__ == "__main__":
    # Test the file operation functions
    print("🧪 Testing file operation functions...")
    
    # Test read_file
    print("\n📚 Testing read_file:")
    result = read_file("test.md")
    print(f"  Result: {result}")

