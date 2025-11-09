"""
Configuration management for MechaWiki server.

Handles agent configurations and paths.
"""
import os
import json
import logging
import toml
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_FILE = PROJECT_ROOT / "config.toml"

# Load configuration
if not CONFIG_FILE.exists():
    raise FileNotFoundError(
        f"Configuration file not found: {CONFIG_FILE}\n"
        f"Please create it from config.example.toml"
    )

config = toml.load(CONFIG_FILE)

# Extract paths from config
WIKICONTENT_PATH = Path(config["paths"]["content_repo"])
CONTENT_BRANCH = config["paths"].get("content_branch", "main")
AGENTS_DIR = WIKICONTENT_PATH / config["paths"].get("agents_dir", "agents")
AGENTS_FILE = AGENTS_DIR / "agents.json"
LOGS_DIR = AGENTS_DIR / "logs"
COSTS_LOG = AGENTS_DIR / "costs.log"

# Extract other settings
USE_MOCK_AGENTS = config["agent"].get("use_mock_agents", False)


class AgentConfig:
    """Manages agent configurations."""
    
    def __init__(self):
        self.agents_file = AGENTS_FILE
        self.logs_dir = LOGS_DIR
        self.costs_log = COSTS_LOG
        
        self._ensure_structure_exists()
    
    def _ensure_structure_exists(self):
        """Create agents directory structure if needed."""
        AGENTS_DIR.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        # Create agents.json if missing
        if not self.agents_file.exists():
            self._save_agents({"agents": []})
            logger.info(f"📝 Created agents file at {self.agents_file}")
        
        # Create costs.log if missing
        if not self.costs_log.exists():
            self.costs_log.touch()
            logger.info(f"📝 Created costs log at {self.costs_log}")
    
    def _load_agents(self) -> Dict:
        """Load agents from disk."""
        with open(self.agents_file, 'r') as f:
            return json.load(f)
    
    def _save_agents(self, data: Dict):
        """Save agents to disk."""
        with open(self.agents_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def list_agents(self) -> List[Dict]:
        """Get list of all agents."""
        agents_data = self._load_agents()
        return agents_data.get("agents", [])
    
    def get_agent(self, agent_id: str) -> Optional[Dict]:
        """Get specific agent by ID."""
        agents = self.list_agents()
        for agent in agents:
            if agent.get("id") == agent_id:
                return agent
        return None
    
    def add_agent(self, agent_data: Dict) -> Dict:
        """Add a new agent."""
        agents_data = self._load_agents()
        agents = agents_data.get("agents", [])
        
        # Ensure required fields
        if "id" not in agent_data:
            raise ValueError("Agent must have an 'id' field")
        
        # Check for duplicate ID
        if any(a.get("id") == agent_data["id"] for a in agents):
            raise ValueError(f"Agent with ID '{agent_data['id']}' already exists")
        
        # Add timestamp if not present
        if "created_at" not in agent_data:
            agent_data["created_at"] = datetime.now().isoformat()
        
        # Update log file path
        agent_data["log_file"] = f"logs/agent_{agent_data['id']}.jsonl"
        
        agents.append(agent_data)
        agents_data["agents"] = agents
        self._save_agents(agents_data)
        
        logger.info(f"✅ Added agent: {agent_data['id']}")
        return agent_data
    
    def update_agent(self, agent_id: str, updates: Dict) -> Optional[Dict]:
        """Update an existing agent.
        
        Performs deep merge for nested dicts like 'config'.
        """
        agents_data = self._load_agents()
        agents = agents_data.get("agents", [])
        
        for i, agent in enumerate(agents):
            if agent.get("id") == agent_id:
                # Deep merge for nested config dict
                if "config" in updates and "config" in agent:
                    # Merge config specifically
                    merged_config = agent["config"].copy()
                    merged_config.update(updates["config"])
                    agent["config"] = merged_config
                    # Remove config from updates so we don't double-apply
                    updates_copy = updates.copy()
                    del updates_copy["config"]
                    agent.update(updates_copy)
                else:
                    # Simple update for other fields
                    agent.update(updates)
                
                agents[i] = agent
                agents_data["agents"] = agents
                self._save_agents(agents_data)
                logger.info(f"✅ Updated agent: {agent_id}")
                return agent
        
        return None
    
    def remove_agent(self, agent_id: str) -> bool:
        """Remove an agent."""
        agents_data = self._load_agents()
        agents = agents_data.get("agents", [])
        
        filtered = [a for a in agents if a.get("id") != agent_id]
        if len(filtered) < len(agents):
            agents_data["agents"] = filtered
            self._save_agents(agents_data)
            logger.info(f"🗑️ Removed agent: {agent_id}")
            return True
        
        return False


# Global agent config instance
agent_config = AgentConfig()
