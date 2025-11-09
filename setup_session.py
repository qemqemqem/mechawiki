#!/usr/bin/env python3
"""
Session Setup Wizard
Creates and configures a new MechaWiki session
"""
import os
import sys
import subprocess
import yaml
import json
from pathlib import Path
from datetime import datetime


def print_banner(text):
    """Print a stylish banner"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def get_current_git_branch(wikicontent_path):
    """Get current branch from wikicontent repo"""
    try:
        result = subprocess.run(
            ['git', 'branch', '--show-current'],
            cwd=wikicontent_path,
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip() or None
    except Exception as e:
        print(f"⚠️  Could not detect git branch: {e}")
        return None


def get_git_branches(wikicontent_path):
    """Get list of all branches from wikicontent repo"""
    try:
        result = subprocess.run(
            ['git', 'branch', '-a'],
            cwd=wikicontent_path,
            capture_output=True,
            text=True,
            timeout=5
        )
        branches = []
        for line in result.stdout.split('\n'):
            line = line.strip()
            if line and not line.startswith('*'):
                # Remove 'remotes/origin/' prefix if present
                branch = line.replace('remotes/origin/', '')
                if branch not in branches and not branch.startswith('HEAD'):
                    branches.append(branch)
            elif line.startswith('*'):
                # Current branch
                branch = line[2:].strip()
                if branch not in branches:
                    branches.append(branch)
        return sorted(set(branches))
    except Exception as e:
        print(f"⚠️  Could not list git branches: {e}")
        return []


def prompt_choice(question, options, default=None):
    """Prompt user to choose from a list of options"""
    print(f"\n{question}")
    for i, option in enumerate(options, 1):
        default_marker = " (default)" if default and option == default else ""
        print(f"  {i}. {option}{default_marker}")
    
    if default:
        print(f"\nPress Enter for default, or enter a number [1-{len(options)}]: ", end='')
    else:
        print(f"\nEnter a number [1-{len(options)}]: ", end='')
    
    while True:
        choice = input().strip()
        
        if not choice and default:
            return default
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx]
        except ValueError:
            pass
        
        print(f"Please enter a number between 1 and {len(options)}: ", end='')


def prompt_text(question, default=None):
    """Prompt user for text input"""
    if default:
        prompt = f"\n{question}\n[{default}]: "
    else:
        prompt = f"\n{question}\n> "
    
    result = input(prompt).strip()
    return result if result else default


def prompt_yes_no(question, default=True):
    """Prompt user for yes/no"""
    default_text = "Y/n" if default else "y/N"
    result = input(f"\n{question} [{default_text}]: ").strip().lower()
    
    if not result:
        return default
    
    return result in ['y', 'yes']


def create_session(session_name, session_dir, config_data):
    """Create the session directory structure and files"""
    print("\n🚀 Creating session structure...")
    
    # Create directories
    session_dir.mkdir(parents=True, exist_ok=True)
    (session_dir / "logs").mkdir(exist_ok=True)
    
    # Write config.yaml
    config_file = session_dir / "config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(config_data, f, default_flow_style=False)
    print(f"✓ Created config.yaml")
    
    # Write empty agents.json
    agents_file = session_dir / "agents.json"
    with open(agents_file, 'w') as f:
        json.dump({"agents": []}, f, indent=2)
    print(f"✓ Created agents.json")
    
    print(f"\n✨ Session '{session_name}' created successfully!")


def main():
    # Get session name from environment
    session_name = os.environ.get("SESSION_NAME")
    
    if not session_name:
        print("❌ Error: SESSION_NAME environment variable not set!")
        sys.exit(1)
    
    print_banner(f"🏰 MechaWiki Session Setup: {session_name}")
    
    print("Let's configure your new session!")
    print("\nThis wizard will help you set up:")
    print("  • Session directory structure")
    print("  • Wikicontent branch configuration")
    print("  • Initial session settings")
    
    # Paths
    project_root = Path(__file__).parent
    data_dir = project_root / "data"
    sessions_dir = data_dir / "sessions"
    session_dir = sessions_dir / session_name
    wikicontent_path = Path.home() / "Dev" / "wikicontent"
    
    # Check if wikicontent exists
    if not wikicontent_path.exists():
        print(f"\n⚠️  Warning: wikicontent directory not found at {wikicontent_path}")
        print("   MechaWiki expects wikicontent to be cloned there.")
        if not prompt_yes_no("Continue anyway?", default=False):
            print("Aborted.")
            sys.exit(1)
        branch = "main"
    else:
        # Detect current branch
        current_branch = get_current_git_branch(wikicontent_path)
        all_branches = get_git_branches(wikicontent_path)
        
        if all_branches:
            print(f"\n📍 Available branches in wikicontent:")
            if current_branch:
                print(f"   Current branch: {current_branch}")
            
            branch = prompt_choice(
                "\n📂 Which branch should this session use?",
                all_branches,
                default=current_branch or all_branches[0]
            )
        else:
            # Fallback if we can't list branches
            branch = prompt_text(
                "📂 Which wikicontent branch should this session use?",
                default=current_branch or "main"
            )
    
    # Optional: Session description
    description = prompt_text(
        "📝 Session description (optional, press Enter to skip):",
        default=""
    )
    
    # Summary
    print_banner("Session Configuration Summary")
    print(f"  Session Name:   {session_name}")
    print(f"  Branch:         {branch}")
    if description:
        print(f"  Description:    {description}")
    print(f"  Location:       {session_dir}")
    
    if not prompt_yes_no("\n✅ Create this session?", default=True):
        print("\n❌ Session creation cancelled.")
        sys.exit(1)
    
    # Create config data
    config_data = {
        'session_name': session_name,
        'wikicontent_branch': branch,
        'created_at': datetime.now().isoformat()
    }
    
    if description:
        config_data['description'] = description
    
    # Create the session
    create_session(session_name, session_dir, config_data)
    
    print("\n" + "=" * 70)
    print("  🎉 Ready to hunt!")
    print("=" * 70)
    print(f"\nYour session '{session_name}' is configured and ready.")
    print("The startup script will now continue launching MechaWiki.")
    print("")


if __name__ == "__main__":
    main()

