#!/usr/bin/env python3
"""
Initialize and start agents from the agents.json configuration.

This loads agents from wikicontent/agents/agents.json and starts them.
"""
import sys
import os
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from server.config import agent_config, WIKICONTENT_PATH, AGENTS_DIR
from agents.mock_agent import MockAgent


def _ensure_agent_directories(agent_id: str, agent_type: str):
    """
    Ensure agent-specific directory structure exists.
    
    Called during initialization to ensure existing agents have their directories.
    """
    agent_dir = AGENTS_DIR / agent_id
    
    # Create base agent directory
    agent_dir.mkdir(parents=True, exist_ok=True)
    
    # All agents get a scratchpad
    scratchpad_dir = agent_dir / "scratchpad"
    scratchpad_dir.mkdir(exist_ok=True)
    
    # Writer and Interactive agents get stories directory
    if agent_type in ['WriterAgent', 'InteractiveAgent']:
        stories_dir = agent_dir / "stories"
        stories_dir.mkdir(exist_ok=True)
        
        # Create initial story.md file if it doesn't exist
        story_file = stories_dir / "story.md"
        if not story_file.exists():
            story_file.write_text(f"# {agent_id} Story\n\nYour story begins here...\n")
    
    # Writer agents get subplots directory
    if agent_type == 'WriterAgent':
        subplots_dir = agent_dir / "subplots"
        subplots_dir.mkdir(exist_ok=True)


def start_agents(agent_manager=None):
    """Start all agents from configuration (paused initially)."""
    print("\n🚀 Starting agents (paused)...")
    
    if not WIKICONTENT_PATH.exists():
        print(f"⚠️  Warning: wikicontent not found at {WIKICONTENT_PATH}")
    
    agents = []
    
    # Start each agent from configuration
    for agent_data in agent_config.list_agents():
        agent_id = agent_data["id"]
        agent_type = agent_data["type"]
        agent_cfg = agent_data.get("config", {})
        log_file = agent_config.logs_dir / f"agent_{agent_id}.jsonl"
        
        # Ensure agent's directory structure exists
        _ensure_agent_directories(agent_id, agent_type)
        
        # Use agent manager if available
        if agent_manager:
            agent = agent_manager.start_agent(
                agent_id=agent_id,
                agent_type=agent_type,
                log_file=log_file,
                wikicontent_path=WIKICONTENT_PATH,
                agent_config=agent_cfg,
                start_paused=True  # Start in paused state (no race condition!)
            )
            print(f"  ⏸️  Started (paused): {agent_id} ({agent_type})")
        else:
            # Fallback for standalone usage
            agent = MockAgent(
                agent_id=agent_id,
                agent_type=agent_type,
                log_file=log_file,
                wikicontent_path=WIKICONTENT_PATH
            )
            agent.start()
            agent.pause()
            print(f"  ⏸️  Started (paused): {agent_id} ({agent_type})")
        
        agents.append(agent)
    
    print(f"\n✅ {len(agents)} agents ready (paused)")
    print("💡 Resume agents via UI or API to begin activity")
    
    return agents


if __name__ == '__main__':
    # If run directly, start agents and keep running
    agents = start_agents()
    
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
