"""
Agent Manager - Manages running agent instances.

Supports both MockAgent (for testing) and real agents via AgentRunner.
"""
import logging
import os
from pathlib import Path
from typing import Dict, Optional, Union
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.mock_agent import MockAgent
from agents.agent_runner import AgentRunner

logger = logging.getLogger(__name__)

# Check environment variable for default agent type
# USE_MOCK_AGENTS=true means use mocks, otherwise use real agents (default)
_USE_MOCK_AGENTS = os.environ.get('USE_MOCK_AGENTS', 'false').lower() == 'true'
_USE_REAL_AGENTS_DEFAULT = not _USE_MOCK_AGENTS


class AgentManager:
    """Singleton manager for agent instances."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._agents: Dict[str, Union[MockAgent, AgentRunner]] = {}
        self._agents_started = False  # Track if init_and_start_agents() has been called
        self._initialized = True
        logger.info("🤖 Agent Manager initialized")
    
    def start_agent(
        self,
        agent_id: str,
        agent_type: str,
        log_file: Path,
        wikicontent_path: Path,
        agent_config: Optional[Dict] = None,
        use_real_agent: Optional[bool] = None,
        start_paused: bool = False
    ) -> Union[MockAgent, AgentRunner]:
        """
        Start a new agent instance.
        
        Args:
            agent_id: Unique agent ID
            agent_type: Type of agent (ReaderAgent, WriterAgent, etc.)
            log_file: Path to JSONL log file
            wikicontent_path: Path to wikicontent directory
            agent_config: Optional agent configuration dict
            use_real_agent: If True, use real agent. If False, use mock. 
                          If None, use environment variable USE_MOCK_AGENTS (default: real agents)
            start_paused: If True, agent starts in paused state (default: False)
        """
        # Check if already running
        if agent_id in self._agents:
            logger.warning(f"Agent {agent_id} is already running")
            return self._agents[agent_id]
        
        # Determine whether to use real agent
        if use_real_agent is None:
            use_real_agent = _USE_REAL_AGENTS_DEFAULT
        
        if use_real_agent:
            # Import real agent classes
            from agents.reader_agent import ReaderAgent
            from agents.writer_agent import WriterAgent
            from agents.interactive_agent import InteractiveAgent
            
            # Map agent_type to class
            agent_classes = {
                'ReaderAgent': ReaderAgent,
                'WriterAgent': WriterAgent,
                'InteractiveAgent': InteractiveAgent,
            }
            
            agent_class = agent_classes.get(agent_type)
            if not agent_class:
                logger.error(f"Unknown agent type: {agent_type}, falling back to MockAgent")
                use_real_agent = False
            else:
                # Create real agent instance
                # Pass story_file and other configs
                init_params = {
                    'model': agent_config.get('model', 'claude-haiku-4-5-20251001'),
                }
                
                # Add story_file if specified in config
                if 'story_file' in agent_config:
                    init_params['story_file'] = agent_config['story_file']
                
                # Add agent_id for WriterAgent (needed for rename tool)
                if agent_type == 'WriterAgent':
                    init_params['agent_id'] = agent_id
                
                agent_instance = agent_class(**init_params)
                
                # Wrap in AgentRunner
                runner = AgentRunner(
                    agent_instance=agent_instance,
                    agent_id=agent_id,
                    log_file=log_file,
                    agent_config=agent_config or {},
                    start_paused=start_paused
                )
                runner.start()
                
                self._agents[agent_id] = runner
                status_msg = "paused" if start_paused else "running"
                logger.info(f"✅ Started real agent ({status_msg}): {agent_id} ({agent_type})")
                return runner
        
        # Fallback: use MockAgent
        if not use_real_agent:
            agent = MockAgent(
                agent_id=agent_id,
                agent_type=agent_type,
                log_file=log_file,
                wikicontent_path=wikicontent_path
            )
            agent.start()
            
            if start_paused:
                agent.pause()
            
            self._agents[agent_id] = agent
            status_msg = "paused" if start_paused else "running"
            logger.info(f"✅ Started mock agent ({status_msg}): {agent_id}")
            return agent
    
    def stop_agent(self, agent_id: str):
        """Stop an agent instance."""
        if agent_id not in self._agents:
            logger.warning(f"Agent {agent_id} is not running")
            return
        
        agent = self._agents[agent_id]
        agent.stop()
        del self._agents[agent_id]
        logger.info(f"🛑 Stopped agent: {agent_id}")
    
    def pause_agent(self, agent_id: str):
        """Pause an agent instance."""
        agent = self._agents.get(agent_id)
        if agent:
            agent.pause()
            logger.info(f"⏸️  Paused agent: {agent_id}")
    
    def resume_agent(self, agent_id: str):
        """Resume an agent instance."""
        agent = self._agents.get(agent_id)
        if agent:
            agent.resume()
            logger.info(f"▶️  Resumed agent: {agent_id}")
    
    def pause_all(self):
        """Pause all running agents."""
        for agent_id in list(self._agents.keys()):
            self.pause_agent(agent_id)
        logger.info("⏸️  Paused all agents")
    
    def resume_all(self):
        """Resume all paused agents."""
        for agent_id in list(self._agents.keys()):
            self.resume_agent(agent_id)
        logger.info("▶️  Resumed all agents")
    
    def get_agent(self, agent_id: str) -> Optional[Union[MockAgent, AgentRunner]]:
        """Get a running agent instance."""
        return self._agents.get(agent_id)
    
    def is_running(self, agent_id: str) -> bool:
        """Check if an agent is running."""
        agent = self._agents.get(agent_id)
        if not agent:
            return False
        
        # Check if thread is alive
        if isinstance(agent, (MockAgent, AgentRunner)):
            return agent.is_alive() if hasattr(agent, 'is_alive') else agent.running
        
        return False
    
    def list_running(self) -> list:
        """Get list of running agent IDs."""
        return list(self._agents.keys())
    
    def mark_agents_started(self):
        """Mark that agents have been initialized (prevents duplicate initialization on reloads)."""
        self._agents_started = True
    
    def agents_already_started(self) -> bool:
        """Check if agents have already been initialized."""
        return self._agents_started
    
    def stop_all(self):
        """Stop all running agents."""
        for agent_id in list(self._agents.keys()):
            self.stop_agent(agent_id)
        logger.info("🛑 Stopped all agents")


# Global singleton instance
agent_manager = AgentManager()

