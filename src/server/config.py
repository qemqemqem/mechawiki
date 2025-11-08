"""
Configuration management for MechaWiki server.

Handles loading and saving agent configurations.
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
AGENTS_CONFIG_FILE = DATA_DIR / "agents.json"
LOGS_DIR = DATA_DIR / "logs"
WIKICONTENT_PATH = Path.home() / "Dev" / "wikicontent"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)


class AgentConfig:
    """Manages agent configuration file."""
    
    def __init__(self, config_file: Path = AGENTS_CONFIG_FILE):
        self.config_file = config_file
        self._ensure_config_exists()
    
    def _ensure_config_exists(self):
        """Create empty config if it doesn't exist."""
        if not self.config_file.exists():
            self._save({"agents": []})
            logger.info(f"📝 Created new agents config at {self.config_file}")
    
    def _load(self) -> Dict:
        """Load config from disk."""
        with open(self.config_file, 'r') as f:
            return json.load(f)
    
    def _save(self, data: Dict):
        """Save config to disk."""
        with open(self.config_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def list_agents(self) -> List[Dict]:
        """Get list of all agents."""
        config = self._load()
        return config.get("agents", [])
    
    def get_agent(self, agent_id: str) -> Optional[Dict]:
        """Get specific agent by ID."""
        agents = self.list_agents()
        for agent in agents:
            if agent.get("id") == agent_id:
                return agent
        return None
    
    def add_agent(self, agent_data: Dict) -> Dict:
        """Add a new agent to config."""
        config = self._load()
        agents = config.get("agents", [])
        
        # Ensure required fields
        if "id" not in agent_data:
            raise ValueError("Agent must have an 'id' field")
        
        # Check for duplicate ID
        if any(a.get("id") == agent_data["id"] for a in agents):
            raise ValueError(f"Agent with ID '{agent_data['id']}' already exists")
        
        # Add timestamp if not present
        if "created_at" not in agent_data:
            agent_data["created_at"] = datetime.now().isoformat()
        
        agents.append(agent_data)
        config["agents"] = agents
        self._save(config)
        
        logger.info(f"✅ Added agent: {agent_data['id']}")
        return agent_data
    
    def update_agent(self, agent_id: str, updates: Dict) -> Optional[Dict]:
        """Update an existing agent."""
        config = self._load()
        agents = config.get("agents", [])
        
        for i, agent in enumerate(agents):
            if agent.get("id") == agent_id:
                # Merge updates
                agent.update(updates)
                agents[i] = agent
                config["agents"] = agents
                self._save(config)
                logger.info(f"✅ Updated agent: {agent_id}")
                return agent
        
        return None
    
    def remove_agent(self, agent_id: str) -> bool:
        """Remove an agent from config."""
        config = self._load()
        agents = config.get("agents", [])
        
        filtered = [a for a in agents if a.get("id") != agent_id]
        if len(filtered) < len(agents):
            config["agents"] = filtered
            self._save(config)
            logger.info(f"🗑️ Removed agent: {agent_id}")
            return True
        
        return False


# Global config instance
agent_config = AgentConfig()

