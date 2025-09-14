"""
Git utilities for managing content repository branches.
"""
import os
import subprocess
import toml
from pathlib import Path
from typing import Optional


def ensure_content_branch() -> bool:
    """
    Ensure we're on the correct branch in the content repository.
    
    Reads config.toml to determine:
    - content_repo: The git repository path
    - current_story: The story name (used as branch prefix)
    - content_branch: The branch suffix (defaults to "main")
    
    The target branch will be: {current_story}/{content_branch}
    
    Returns
    -------
    bool
        True if successfully on correct branch, False otherwise
    """
    try:
        # Load configuration
        config = toml.load("config.toml")
        
        content_repo = config["paths"]["content_repo"]
        current_story = config["story"]["current_story"]
        content_branch = config["story"].get("content_branch", "main")
        
        # Construct target branch name
        target_branch = f"{current_story}/{content_branch}"
        
        print(f"🎯 Target branch: {target_branch}")
        print(f"📁 Content repo: {content_repo}")
        
        # Check if content repo exists
        if not Path(content_repo).exists():
            print(f"❌ Content repository not found: {content_repo}")
            return False
        
        # Change to content repo directory
        original_cwd = os.getcwd()
        os.chdir(content_repo)
        
        try:
            # Check if we're in a git repository
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Check current branch
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                check=True
            )
            current_branch = result.stdout.strip()
            
            print(f"📍 Current branch: {current_branch}")
            
            # If we're already on the target branch, we're good
            if current_branch == target_branch:
                print(f"✅ Already on target branch: {target_branch}")
                return True
            
            # Check if target branch exists
            result = subprocess.run(
                ["git", "branch", "--list", target_branch],
                capture_output=True,
                text=True,
                check=True
            )
            
            if result.stdout.strip():
                # Branch exists, switch to it
                print(f"🔄 Switching to existing branch: {target_branch}")
                subprocess.run(
                    ["git", "checkout", target_branch],
                    check=True
                )
            else:
                # Branch doesn't exist, create it
                print(f"🆕 Creating new branch: {target_branch}")
                subprocess.run(
                    ["git", "checkout", "-b", target_branch],
                    check=True
                )
            
            print(f"✅ Successfully on branch: {target_branch}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Git operation failed: {e}")
            return False
        finally:
            # Always return to original directory
            os.chdir(original_cwd)
            
    except Exception as e:
        print(f"❌ Error ensuring content branch: {e}")
        return False


def get_content_repo_path() -> Optional[Path]:
    """
    Get the content repository path from config.
    
    Returns
    -------
    Optional[Path]
        Path to content repository, or None if config can't be loaded
    """
    try:
        config = toml.load("config.toml")
        content_repo = config["paths"]["content_repo"]
        return Path(content_repo)
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return None


if __name__ == "__main__":
    # Test the git helper
    print("🧪 Testing git helper...")
    success = ensure_content_branch()
    if success:
        print("✅ Git helper test passed!")
    else:
        print("❌ Git helper test failed!")
