#!/usr/bin/env python3
"""
Initialize dumb test agents for the dev session.

Creates several mock agents (reader, writer, researcher) that run in the background
and generate random activity for testing the UI.
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
    """Initialize test agents in the dev session."""
    
    print("🤖 Initializing test agents...")
    
    # Define test agents - one of each type
    test_agents = [
        {
            "id": "reader-001",
            "name": "Reader Agent 1",
            "type": "ReaderAgent",
            "config": {
                "description": "Reads stories and creates wiki articles",
                "initial_prompt": "Start by listing some articles in the articles directory. Then advance through the story and comment on what you find interesting.",
                "model": "claude-haiku-4-5-20251001"
            }
        },
        {
            "id": "writer-001",
            "name": "Writer Agent 1",
            "type": "WriterAgent",
            "config": {
                "description": "Writes stories from wiki content",
                "initial_prompt": "Search for some articles to get inspiration, then write a short story based on wiki content.",
                "model": "claude-haiku-4-5-20251001"
            }
        },
        {
            "id": "interactive-001",
            "name": "Interactive Agent 1",
            "type": "InteractiveAgent",
            "config": {
                "description": "Creates interactive experiences",
                "initial_prompt": "Create an interactive adventure. Set the scene and ask the user what they want to do using wait_for_user().",
                "model": "claude-haiku-4-5-20251001"
            }
        }
    ]
    
    # Add agents to session config
    for agent_data in test_agents:
        # Check if agent already exists
        existing = session_config.get_agent(agent_data["id"])
        if existing:
            print(f"  ⏭️  Agent {agent_data['id']} already exists")
            continue
        
        # Add to config (SessionConfig.add_agent expects a dict)
        session_config.add_agent(agent_data)
        
        # Create empty log file
        log_file = session_config.logs_dir / f"agent_{agent_data['id']}.jsonl"
        log_file.touch()
        
        print(f"  ✅ Created agent {agent_data['id']} ({agent_data['name']})")
    
    print(f"\n✨ Test agents initialized in session '{session_config.session_name}'")
    print(f"📝 Config: {session_config.agents_file}")
    print(f"📁 Logs: {session_config.logs_dir}")


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

