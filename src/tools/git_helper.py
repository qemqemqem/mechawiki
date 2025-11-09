"""
Git helper utilities for automatically committing wikicontent changes.

This module provides functions to automatically commit file changes to git
in the wikicontent repository when files are edited by agents.
"""
import os
import subprocess
import threading
from pathlib import Path
from typing import Optional, Dict, Any

# Thread-local storage for agent log paths
_thread_locals = threading.local()


def set_agent_log_path(log_path: Optional[Path]):
    """Set the current agent's log path in thread-local storage."""
    _thread_locals.agent_log_path = log_path


def get_agent_log_path() -> Optional[Path]:
    """Get the current agent's log path from thread-local storage."""
    return getattr(_thread_locals, 'agent_log_path', None)


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
        
        # Also stage agent log file and agent subdirectory if available
        agent_log_path = get_agent_log_path()
        agent_log_relative = None
        agent_subdir_relative = None
        if agent_log_path:
            try:
                # Convert to Path and get relative path from wikicontent_path
                agent_log_path = Path(agent_log_path)
                if agent_log_path.is_relative_to(wikicontent_path):
                    agent_log_relative = str(agent_log_path.relative_to(wikicontent_path))
                    # Stage the agent log
                    subprocess.run(
                        ["git", "add", agent_log_relative],
                        cwd=wikicontent_path,
                        capture_output=True,
                        text=True
                    )
                    
                    # Extract agent ID from log path (e.g., "agent_reader-agent-005.jsonl" -> "reader-agent-005")
                    log_filename = agent_log_path.name
                    if log_filename.startswith("agent_"):
                        agent_id = log_filename[6:].replace(".jsonl", "")  # Remove "agent_" prefix and ".jsonl" suffix
                        
                        # Stage the agent's subdirectory (e.g., agents/reader-agent-005/)
                        agent_subdir = wikicontent_path / "agents" / agent_id
                        if agent_subdir.exists() and agent_subdir.is_dir():
                            agent_subdir_relative = f"agents/{agent_id}/"
                            subprocess.run(
                                ["git", "add", agent_subdir_relative],
                                cwd=wikicontent_path,
                                capture_output=True,
                                text=True
                            )
                    
                    # Don't fail if staging log/subdir fails - it's optional
            except (ValueError, OSError):
                # Log path not relative to wikicontent or other error - skip it
                agent_log_relative = None
                agent_subdir_relative = None
        
        # Generate commit message based on operation
        commit_messages = {
            "edit": f"Edit {filepath}",
            "create": f"Create {filepath}",
            "append": f"Append to {filepath}",
            "rename": f"Rename {filepath}",
            "delete": f"Delete {filepath}"
        }
        commit_msg = commit_messages.get(operation, f"Update {filepath}")
        
        # Add agent context to commit message if included
        agent_context_parts = []
        if agent_log_relative:
            agent_context_parts.append(f"log: {agent_log_relative}")
        if agent_subdir_relative:
            agent_context_parts.append(f"agent dir: {agent_subdir_relative}")
        
        if agent_context_parts:
            commit_msg += f" (with {', '.join(agent_context_parts)})"
        
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

