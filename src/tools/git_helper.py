"""
Git helper utilities for automatically committing wikicontent changes.

This module provides functions to automatically commit file changes to git
in the wikicontent repository when files are edited by agents.
"""
import os
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any


def commit_file_change(
    filepath: str,
    operation: str = "edit",
    wikicontent_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Commit a file change to git in the wikicontent repository.
    
    This function will:
    1. Stage the specified file
    2. Create a commit with a descriptive message
    3. Return success/error status
    
    Parameters
    ----------
    filepath : str
        Path relative to wikicontent root (e.g. "articles/wizard.md")
    operation : str
        Type of operation: "edit", "create", "append", "rename", "delete"
    wikicontent_path : Path, optional
        Path to wikicontent directory. If not provided, uses environment variable
        or default location.
    
    Returns
    -------
    dict
        {
            "committed": bool,
            "message": str,
            "commit_hash": str | None
        }
    
    Examples
    --------
    >>> commit_file_change("articles/wizard.md", operation="edit")
    {"committed": True, "message": "Edit articles/wizard.md", "commit_hash": "abc123"}
    """
    try:
        # Get wikicontent path
        if wikicontent_path is None:
            wikicontent_path = Path(os.environ.get(
                'WIKICONTENT_PATH',
                str(Path.home() / "Dev" / "wikicontent")
            ))
        
        # Ensure the path is a Path object
        wikicontent_path = Path(wikicontent_path)
        
        # Check if wikicontent is a git repository
        git_dir = wikicontent_path / ".git"
        if not git_dir.exists():
            return {
                "committed": False,
                "message": f"Not a git repository: {wikicontent_path}",
                "commit_hash": None
            }
        
        # Stage the file
        result = subprocess.run(
            ["git", "add", filepath],
            cwd=wikicontent_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return {
                "committed": False,
                "message": f"Failed to stage file: {result.stderr}",
                "commit_hash": None
            }
        
        # Generate commit message based on operation
        commit_messages = {
            "edit": f"Edit {filepath}",
            "create": f"Create {filepath}",
            "append": f"Append to {filepath}",
            "rename": f"Rename {filepath}",
            "delete": f"Delete {filepath}"
        }
        commit_msg = commit_messages.get(operation, f"Update {filepath}")
        
        # Create commit
        result = subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=wikicontent_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            # Check if it's "nothing to commit" - this is OK
            if "nothing to commit" in result.stdout or "nothing to commit" in result.stderr:
                return {
                    "committed": False,
                    "message": "No changes to commit",
                    "commit_hash": None
                }
            return {
                "committed": False,
                "message": f"Failed to commit: {result.stderr}",
                "commit_hash": None
            }
        
        # Get the commit hash
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=wikicontent_path,
            capture_output=True,
            text=True
        )
        
        commit_hash = result.stdout.strip() if result.returncode == 0 else None
        
        return {
            "committed": True,
            "message": commit_msg,
            "commit_hash": commit_hash
        }
    
    except Exception as e:
        return {
            "committed": False,
            "message": f"Error committing file: {str(e)}",
            "commit_hash": None
        }


def commit_file_rename(
    old_filepath: str,
    new_filepath: str,
    wikicontent_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Commit a file rename to git using git mv.
    
    This function handles the special case of file renames by:
    1. Using git mv to rename the file in git's index
    2. Creating a commit with a descriptive message
    
    Parameters
    ----------
    old_filepath : str
        Original path relative to wikicontent root
    new_filepath : str
        New path relative to wikicontent root
    wikicontent_path : Path, optional
        Path to wikicontent directory
    
    Returns
    -------
    dict
        {
            "committed": bool,
            "message": str,
            "commit_hash": str | None
        }
    """
    try:
        # Get wikicontent path
        if wikicontent_path is None:
            wikicontent_path = Path(os.environ.get(
                'WIKICONTENT_PATH',
                str(Path.home() / "Dev" / "wikicontent")
            ))
        
        wikicontent_path = Path(wikicontent_path)
        
        # Check if wikicontent is a git repository
        git_dir = wikicontent_path / ".git"
        if not git_dir.exists():
            return {
                "committed": False,
                "message": f"Not a git repository: {wikicontent_path}",
                "commit_hash": None
            }
        
        # Use git mv to rename the file
        result = subprocess.run(
            ["git", "mv", old_filepath, new_filepath],
            cwd=wikicontent_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            # If git mv fails, try to stage both files manually
            subprocess.run(
                ["git", "add", old_filepath, new_filepath],
                cwd=wikicontent_path,
                capture_output=True,
                text=True
            )
        
        # Generate commit message
        commit_msg = f"Rename {old_filepath} to {new_filepath}"
        
        # Create commit
        result = subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=wikicontent_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            if "nothing to commit" in result.stdout or "nothing to commit" in result.stderr:
                return {
                    "committed": False,
                    "message": "No changes to commit",
                    "commit_hash": None
                }
            return {
                "committed": False,
                "message": f"Failed to commit: {result.stderr}",
                "commit_hash": None
            }
        
        # Get the commit hash
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=wikicontent_path,
            capture_output=True,
            text=True
        )
        
        commit_hash = result.stdout.strip() if result.returncode == 0 else None
        
        return {
            "committed": True,
            "message": commit_msg,
            "commit_hash": commit_hash
        }
    
    except Exception as e:
        return {
            "committed": False,
            "message": f"Error committing rename: {str(e)}",
            "commit_hash": None
        }


if __name__ == "__main__":
    # Test the git helper functions
    print("🧪 Testing git helper functions...")
    
    # Test commit_file_change
    print("\n📝 Testing commit_file_change:")
    result = commit_file_change("test.md", operation="edit")
    print(f"  Result: {result}")

