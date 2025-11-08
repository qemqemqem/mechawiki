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
    
    # Define test agents
    test_agents = [
        {
            "id": "reader-001",
            "name": "Story Reader Alpha",
            "type": "ReaderAgent",
            "config": {
                "description": "Reads stories and creates wiki articles"
            }
        },
        {
            "id": "writer-001",
            "name": "Tale Weaver Beta",
            "type": "WriterAgent",
            "config": {
                "description": "Writes stories from wiki content"
            }
        },
        {
            "id": "researcher-001",
            "name": "Lore Keeper Gamma",
            "type": "ResearcherAgent",
            "config": {
                "description": "Researches and organizes wiki information"
            }
        },
        {
            "id": "interactive-001",
            "name": "Quest Master Delta",
            "type": "InteractiveAgent",
            "config": {
                "description": "Creates interactive experiences"
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
        
        # Add to config
        session_config.add_agent(
            agent_id=agent_data["id"],
            name=agent_data["name"],
            agent_type=agent_data["type"],
            config=agent_data["config"]
        )
        
        # Create empty log file
        log_file = session_config.logs_dir / f"agent_{agent_data['id']}.jsonl"
        log_file.touch()
        
        print(f"  ✅ Created agent {agent_data['id']} ({agent_data['name']})")
    
    print(f"\n✨ Test agents initialized in session '{session_config.session_name}'")
    print(f"📝 Config: {session_config.agents_file}")
    print(f"📁 Logs: {session_config.logs_dir}")


def start_test_agents():
    """Start all test agents in background threads."""
    print("\n🚀 Starting test agents...")
    
    # Get wikicontent path
    wikicontent_path = Path.home() / "Dev" / "wikicontent"
    if not wikicontent_path.exists():
        print(f"⚠️  Warning: wikicontent not found at {wikicontent_path}")
    
    agents = []
    
    # Start each agent
    for agent_data in session_config.list_agents():
        agent_id = agent_data["id"]
        agent_type = agent_data["type"]
        log_file = session_config.logs_dir / f"agent_{agent_id}.jsonl"
        
        # Create and start mock agent
        agent = MockAgent(
            agent_id=agent_id,
            agent_type=agent_type,
            log_file=log_file,
            wikicontent_path=wikicontent_path
        )
        agent.start()
        agents.append(agent)
        
        print(f"  🟢 Started {agent_id} ({agent_type})")
    
    print(f"\n✅ {len(agents)} agents running in background")
    print("💡 Agents will continue running while the server is active")
    
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

