"""
Configuration management for MechaWiki server.

Handles session management and agent configurations.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SESSIONS_DIR = DATA_DIR / "sessions"
WIKICONTENT_PATH = Path.home() / "Dev" / "wikicontent"

# Default session (can be overridden by SESSION_NAME environment variable)
DEFAULT_SESSION = os.environ.get("SESSION_NAME", "dev_session")

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
SESSIONS_DIR.mkdir(exist_ok=True)


class SessionConfig:
    """Manages session configuration and agents."""
    
    def __init__(self, session_name: str = DEFAULT_SESSION):
        self.session_name = session_name
        self.session_dir = SESSIONS_DIR / session_name
        self.config_file = self.session_dir / "config.yaml"
        self.agents_file = self.session_dir / "agents.json"
        self.logs_dir = self.session_dir / "logs"
        
        self._ensure_session_exists()
    
    def _ensure_session_exists(self):
        """Create session directory structure if needed."""
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        # Create config.yaml if missing
        if not self.config_file.exists():
            import subprocess
            try:
                # Try to get current git branch from wikicontent
                result = subprocess.run(
                    ['git', 'branch', '--show-current'],
                    cwd=WIKICONTENT_PATH,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                branch = result.stdout.strip() or 'main'
            except:
                branch = 'main'
            
            config_data = {
                'session_name': self.session_name,
                'wikicontent_branch': branch,
                'created_at': datetime.now().isoformat()
            }
            
            # Write YAML config
            import yaml
            with open(self.config_file, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False)
            
            logger.info(f"📝 Created session config at {self.config_file}")
        
        # Create agents.json if missing
        if not self.agents_file.exists():
            self._save_agents({"agents": []})
            logger.info(f"📝 Created agents file at {self.agents_file}")
    
    def get_config(self) -> Dict:
        """Load session config from YAML."""
        import yaml
        with open(self.config_file, 'r') as f:
            return yaml.safe_load(f) or {}
    
    def update_config(self, updates: Dict):
        """Update session config."""
        import yaml
        config = self.get_config()
        config.update(updates)
        with open(self.config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
    
    def _load_agents(self) -> Dict:
        """Load agents from disk."""
        with open(self.agents_file, 'r') as f:
            return json.load(f)
    
    def _save_agents(self, data: Dict):
        """Save agents to disk."""
        with open(self.agents_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def list_agents(self) -> List[Dict]:
        """Get list of all agents in this session."""
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
        """Add a new agent to this session."""
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
        
        # Update log file path to be session-relative
        agent_data["log_file"] = f"logs/agent_{agent_data['id']}.jsonl"
        
        agents.append(agent_data)
        agents_data["agents"] = agents
        self._save_agents(agents_data)
        
        logger.info(f"✅ Added agent to session '{self.session_name}': {agent_data['id']}")
        return agent_data
    
    def update_agent(self, agent_id: str, updates: Dict) -> Optional[Dict]:
        """Update an existing agent in this session."""
        agents_data = self._load_agents()
        agents = agents_data.get("agents", [])
        
        for i, agent in enumerate(agents):
            if agent.get("id") == agent_id:
                # Merge updates
                agent.update(updates)
                agents[i] = agent
                agents_data["agents"] = agents
                self._save_agents(agents_data)
                logger.info(f"✅ Updated agent in session '{self.session_name}': {agent_id}")
                return agent
        
        return None
    
    def remove_agent(self, agent_id: str) -> bool:
        """Remove an agent from this session."""
        agents_data = self._load_agents()
        agents = agents_data.get("agents", [])
        
        filtered = [a for a in agents if a.get("id") != agent_id]
        if len(filtered) < len(agents):
            agents_data["agents"] = filtered
            self._save_agents(agents_data)
            logger.info(f"🗑️ Removed agent from session '{self.session_name}': {agent_id}")
            return True
        
        return False


# Global session config instance
session_config = SessionConfig(DEFAULT_SESSION)

