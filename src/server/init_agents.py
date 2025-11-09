#!/usr/bin/env python3
"""
Initialize test agents for the dev session.

This creates a clean dev_session with proper agents.json and config.yaml,
then lets the normal initialization flow take over.
"""
import sys
import os
from pathlib import Path
import json
from datetime import datetime

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from server.config import session_config
from agents.mock_agent import MockAgent


def init_test_agents():
    """Initialize test agents in the dev session ONLY.
    
    This function should ONLY be called for the dev_session, typically by start.sh.
    It completely resets the dev environment with fresh test agents.
    
    For production sessions, agents should be loaded from existing agents.json.
    
    This function:
    1. Cleans up the dev_session directory (removes old logs)
    2. Writes a proper agents.json with full configs including story files
    3. Writes config.yaml if needed
    4. Normal startup then reads from these files
    """
    
    # DEFENSIVE GUARD: Only run for dev_session
    if session_config.session_name != "dev_session":
        print(f"⚠️  WARNING: init_test_agents() called for session '{session_config.session_name}'")
        print(f"⚠️  This function should ONLY run for 'dev_session'. Skipping initialization.")
        return
    
    print("🤖 Initializing test agents for dev_session...")
    print("🧹 Cleaning dev_session directory...")
    
    # Clean up logs directory
    logs_dir = session_config.logs_dir
    if logs_dir.exists():
        for log_file in logs_dir.glob("*.jsonl"):
            log_file.unlink()
            print(f"  🗑️  Deleted: {log_file.name}")
    else:
        logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Define test agents with full configs including story files
    test_agents = [
        {
            "id": "reader-001",
            "name": "Reader Agent 1",
            "type": "ReaderAgent",
            "config": {
                "description": "Reads stories and creates wiki articles",
                "initial_prompt": "Start by listing some articles in the articles directory. Then advance through the story and comment on what you find interesting.",
                "model": "claude-haiku-4-5-20251001",
                "story_file": "story.txt"  # The full Tales of Wonder story
            },
            "created_at": datetime.now().isoformat(),
            "log_file": "logs/agent_reader-001.jsonl"
        },
        {
            "id": "writer-001",
            "name": "Writer Agent 1",
            "type": "WriterAgent",
            "config": {
                "description": "Writes stories from wiki content",
                "initial_prompt": "Search for some articles to get inspiration, then write a short story based on wiki content.",
                "model": "claude-haiku-4-5-20251001",
                "story_file": "stories/writer_story.md"  # Writer's output file
            },
            "created_at": datetime.now().isoformat(),
            "log_file": "logs/agent_writer-001.jsonl"
        },
        {
            "id": "interactive-001",
            "name": "Interactive Agent 1",
            "type": "InteractiveAgent",
            "config": {
                "description": "Creates interactive experiences",
                "initial_prompt": "Create an interactive adventure. Set the scene and ask the user what they want to do using wait_for_user().",
                "model": "claude-haiku-4-5-20251001",
                "story_file": "stories/interactive_adventure.md"  # Interactive story output
            },
            "created_at": datetime.now().isoformat(),
            "log_file": "logs/agent_interactive-001.jsonl"
        }
    ]
    
    # Write agents.json directly (clean reset for dev_session)
    agents_file = session_config.agents_file
    agents_data = {"agents": test_agents}
    
    with open(agents_file, 'w') as f:
        json.dump(agents_data, f, indent=2)
    
    print(f"  ✅ Wrote: agents.json with {len(test_agents)} agents")
    
    # Write config.yaml (if it doesn't exist or needs updating)
    config_file = session_config.session_dir / "config.yaml"
    config_data = f"""created_at: '{datetime.now().isoformat()}'
session_name: dev_session
wikicontent_branch: tales_of_wonder/main
"""
    with open(config_file, 'w') as f:
        f.write(config_data)
    
    print(f"  ✅ Wrote: config.yaml")
    print(f"\n✨ Test agents initialized in session '{session_config.session_name}'")
    print(f"📝 Config: {agents_file}")
    print(f"📁 Logs: {logs_dir}")


def start_test_agents(agent_manager=None):
    """Start all test agents in background threads (paused initially)."""
    print("\n🚀 Starting test agents (paused)...")
    
    # Get wikicontent path
    wikicontent_path = Path.home() / "Dev" / "wikicontent"
    if not wikicontent_path.exists():
        print(f"⚠️  Warning: wikicontent not found at {wikicontent_path}")
    
    agents = []
    
    # Start each agent
    for agent_data in session_config.list_agents():
        agent_id = agent_data["id"]
        agent_type = agent_data["type"]
        agent_config = agent_data.get("config", {})
        log_file = session_config.logs_dir / f"agent_{agent_id}.jsonl"
        
        # Use agent manager if available
        if agent_manager:
            agent = agent_manager.start_agent(
                agent_id=agent_id,
                agent_type=agent_type,
                log_file=log_file,
                wikicontent_path=wikicontent_path,
                agent_config=agent_config,
                start_paused=True  # Start in paused state (no race condition!)
            )
            print(f"  ⏸️  Started (paused): {agent_id} ({agent_type})")
        else:
            # Fallback for standalone usage
            agent = MockAgent(
                agent_id=agent_id,
                agent_type=agent_type,
                log_file=log_file,
                wikicontent_path=wikicontent_path
            )
            agent.start()
            agent.pause()
            print(f"  ⏸️  Started (paused): {agent_id} ({agent_type})")
        
        agents.append(agent)
    
    print(f"\n✅ {len(agents)} agents ready (paused)")
    print("💡 Resume agents via UI or API to begin activity")
    
    return agents


if __name__ == '__main__':
    # Initialize agents in config
    init_test_agents()
    
    # If run directly, start agents and keep running
    if '--start' in sys.argv:
        agents = start_test_agents()
        
        try:
            print("\n⌨️  Press Ctrl+C to stop...\n")
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n⏹️  Stopping agents...")
            for agent in agents:
                agent.stop()
            print("✅ Done!")

