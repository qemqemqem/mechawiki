"""
Story tools for WriterAgent.

These tools allow agents to write and edit stories in wikicontent.
"""
import os
from pathlib import Path
from typing import Dict, Any
from .git_helper import commit_file_change


def write_story(content: str, filepath: str, append: bool = True) -> Dict[str, Any]:
    """
    Write content to a story file.
    
    Parameters
    ----------
    content : str
        The story content to write
    filepath : str
        Relative path within wikicontent (e.g. "stories/tale_of_wonder.md")
    append : bool
        If True, append to existing file. If False, overwrite.
    
    Returns
    -------
    dict
        Result with success status and message
    """
    try:
        # Get wikicontent path from environment or default
        wikicontent_path = Path(os.environ.get(
            'WIKICONTENT_PATH',
            str(Path.home() / "Dev" / "wikicontent")
        ))
        
        # Construct full path
        full_path = wikicontent_path / filepath
        
        # Ensure directory exists
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Calculate line changes
        lines_removed = 0
        if full_path.exists():
            with open(full_path, 'r') as f:
                old_content = f.read()
            if not append:
                # If overwriting, old lines are removed
                lines_removed = old_content.count('\n') + 1
        
        # Write content
        mode = 'a' if append else 'w'
        with open(full_path, mode) as f:
            f.write(content)
        
        lines_added = content.count('\n') + 1
        
        # Commit the change to git
        operation = "append" if append else "edit"
        git_result = commit_file_change(filepath, operation=operation, wikicontent_path=wikicontent_path)
        
        result = {
            "success": True,
            "message": f"{'Appended to' if append else 'Wrote'} {filepath}",
            "file_path": filepath,
            "lines_added": lines_added,
            "lines_removed": lines_removed,
            "mode": "append" if append else "overwrite"
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


def edit_story(
    filepath: str,
    search: str,
    replace: str
) -> Dict[str, Any]:
    """
    Edit story content by searching and replacing text.
    
    Parameters
    ----------
    filepath : str
        Relative path within wikicontent (e.g. "stories/tale_of_wonder.md")
    search : str
        Text to search for
    replace : str
        Text to replace with
    
    Returns
    -------
    dict
        Result with success status and changes made
    """
    try:
        # Get wikicontent path
        wikicontent_path = Path(os.environ.get(
            'WIKICONTENT_PATH',
            str(Path.home() / "Dev" / "wikicontent")
        ))
        
        full_path = wikicontent_path / filepath
        
        if not full_path.exists():
            return {
                "success": False,
                "error": f"File not found: {filepath}"
            }
        
        # Read current content
        with open(full_path, 'r') as f:
            content = f.read()
        
        # Check if search string exists
        if search not in content:
            return {
                "success": False,
                "error": f"Search string not found in {filepath}"
            }
        
        # Count occurrences
        occurrences = content.count(search)
        
        # Replace
        new_content = content.replace(search, replace)
        
        # Calculate line changes (approximation)
        old_lines = content.count('\n') + 1
        new_lines = new_content.count('\n') + 1
        lines_added = max(0, new_lines - old_lines)
        lines_removed = max(0, old_lines - new_lines)
        
        # Write back
        with open(full_path, 'w') as f:
            f.write(new_content)
        
        return {
            "success": True,
            "message": f"Replaced {occurrences} occurrence(s) in {filepath}",
            "file_path": filepath,
            "lines_added": lines_added,
            "lines_removed": lines_removed,
            "occurrences": occurrences
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_story_status(filepath: str) -> Dict[str, Any]:
    """
    Get status information about a story file.
    
    Parameters
    ----------
    filepath : str
        Relative path within wikicontent
    
    Returns
    -------
    dict
        File status information (exists, size, word count, etc.)
    """
    try:
        wikicontent_path = Path(os.environ.get(
            'WIKICONTENT_PATH',
            str(Path.home() / "Dev" / "wikicontent")
        ))
        
        full_path = wikicontent_path / filepath
        
        if not full_path.exists():
            return {
                "success": True,
                "exists": False,
                "filepath": str(full_path)
            }
        
        # Get file stats
        stats = full_path.stat()
        
        # Read content for word count
        with open(full_path, 'r') as f:
            content = f.read()
        
        word_count = len(content.split())
        line_count = content.count('\n') + 1
        char_count = len(content)
        
        return {
            "success": True,
            "exists": True,
            "filepath": str(full_path),
            "size_bytes": stats.st_size,
            "word_count": word_count,
            "line_count": line_count,
            "char_count": char_count,
            "modified": stats.st_mtime
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

