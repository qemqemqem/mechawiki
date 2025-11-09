"""
Log file watcher for agent activity.

Watches agent JSONL log files and provides real-time updates.
"""
import json
import logging
import queue
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)


class LogFileHandler(FileSystemEventHandler):
    """Handles log file changes."""
    
    def __init__(self, log_manager):
        self.log_manager = log_manager
        self.file_positions = {}  # Track file positions to read only new content
    
    def on_modified(self, event):
        """Handle log file modifications."""
        if event.is_directory or not event.src_path.endswith('.jsonl'):
            return
        
        file_path = Path(event.src_path)
        agent_id = self._extract_agent_id(file_path)
        
        if not agent_id:
            return
        
        # Read new entries from file
        self._read_new_entries(file_path, agent_id)
    
    def _extract_agent_id(self, file_path: Path) -> Optional[str]:
        """Extract agent ID from log file name."""
        # Format: agent_{agent_id}.jsonl
        name = file_path.stem
        if name.startswith('agent_'):
            return name[6:]  # Remove 'agent_' prefix
        return None
    
    def _read_new_entries(self, file_path: Path, agent_id: str):
        """Read new entries from log file."""
        try:
            # Get last position
            last_pos = self.file_positions.get(str(file_path), 0)
            
            with open(file_path, 'r') as f:
                # Seek to last position
                f.seek(last_pos)
                
                # Read new lines
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        log_entry = json.loads(line)
                        self.log_manager.process_log_entry(agent_id, log_entry)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse log entry: {e}")
                
                # Update position
                self.file_positions[str(file_path)] = f.tell()
        
        except Exception as e:
            logger.error(f"Error reading log file {file_path}: {e}")


class LogManager:
    """Manages agent log watching and provides updates."""
    
    def __init__(self, logs_dir: Path):
        self.logs_dir = logs_dir
        self.observer = Observer()
        self.handler = LogFileHandler(self)
        
        # Subscribers: agent_id -> list of queues
        self.subscribers: Dict[str, list] = {}
        
        # Agent status cache
        self.agent_status: Dict[str, dict] = {}
        
        # File feed subscribers (all file operations across all agents)
        self.file_feed_subscribers: list = []
        
        # Start watching
        self.observer.schedule(self.handler, str(logs_dir), recursive=False)
        self.observer.start()
        
        logger.info(f"📁 Started watching agent logs in {logs_dir}")
    
    def start_watching_agent(self, agent_id: str, log_file: str, agent_config: dict = None):
        """Start watching a specific agent's log.
        
        Args:
            agent_id: ID of the agent
            log_file: Path to agent's log file
            agent_config: Agent configuration dict (should contain 'story_file' key)
        """
        # Initialize status
        self.agent_status[agent_id] = {
            "status": "stopped",
            "last_action": None,
            "last_action_time": None,
            "story_file": None
        }
        
        # Get story file from agent config
        if agent_config and 'story_file' in agent_config:
            self.agent_status[agent_id]["story_file"] = agent_config['story_file']
        
        # Read existing log to build initial status
        log_path = Path(log_file)
        if log_path.exists():
            with open(log_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        log_entry = json.loads(line)
                        self._update_agent_status(agent_id, log_entry)
                    except json.JSONDecodeError:
                        pass
        
        logger.info(f"👁️ Started watching agent: {agent_id}")
    
    def stop_watching_agent(self, agent_id: str):
        """Stop watching an agent's log."""
        if agent_id in self.subscribers:
            del self.subscribers[agent_id]
        
        if agent_id in self.agent_status:
            del self.agent_status[agent_id]
        
        logger.info(f"👋 Stopped watching agent: {agent_id}")
    
    def subscribe_to_agent(self, agent_id: str) -> queue.Queue:
        """Subscribe to agent log updates."""
        q = queue.Queue(maxsize=100)
        
        if agent_id not in self.subscribers:
            self.subscribers[agent_id] = []
        
        self.subscribers[agent_id].append(q)
        logger.info(f"📬 New subscriber for agent: {agent_id}")
        
        return q
    
    def subscribe_to_file_feed(self) -> queue.Queue:
        """Subscribe to file operations feed (all agents)."""
        q = queue.Queue(maxsize=100)
        self.file_feed_subscribers.append(q)
        logger.info("📬 New subscriber for file feed")
        return q
    
    def process_log_entry(self, agent_id: str, log_entry: dict):
        """Process a new log entry."""
        # Update agent status
        self._update_agent_status(agent_id, log_entry)
        
        # Notify agent subscribers
        if agent_id in self.subscribers:
            for q in self.subscribers[agent_id]:
                try:
                    q.put_nowait(log_entry)
                except queue.Full:
                    logger.warning(f"Queue full for agent {agent_id}")
        
        # Check if this is a file operation
        if self._is_file_operation(log_entry):
            file_event = self._extract_file_event(agent_id, log_entry)
            if file_event:
                # Notify file feed subscribers
                for q in self.file_feed_subscribers:
                    try:
                        q.put_nowait(file_event)
                    except queue.Full:
                        logger.warning("File feed queue full")
    
    def _update_agent_status(self, agent_id: str, log_entry: dict):
        """Update cached agent status from log entry."""
        if agent_id not in self.agent_status:
            self.agent_status[agent_id] = {}
        
        entry_type = log_entry.get('type')
        
        # Update status
        if entry_type == 'status':
            self.agent_status[agent_id]['status'] = log_entry.get('status')
        
        # Update last action (non-status entries)
        if entry_type != 'status':
            self.agent_status[agent_id]['last_action'] = self._format_action(log_entry)
            self.agent_status[agent_id]['last_action_time'] = log_entry.get('timestamp')
    
    def _format_action(self, log_entry: dict) -> str:
        """Format a log entry into a human-readable action."""
        entry_type = log_entry.get('type')
        
        if entry_type == 'tool_call':
            tool = log_entry.get('tool', 'unknown')
            return f"Called {tool}()"
        
        elif entry_type == 'message':
            content = log_entry.get('content', '')
            preview = content[:50] + '...' if len(content) > 50 else content
            return f"Said: {preview}"
        
        elif entry_type == 'user_message':
            return "Received user message"
        
        else:
            return f"{entry_type}"
    
    def _is_file_operation(self, log_entry: dict) -> bool:
        """Check if log entry represents a file operation."""
        if log_entry.get('type') != 'tool_result':
            return False
        
        tool = log_entry.get('tool', '')
        file_tools = [
            'read_file', 'edit_file', 'add_to_story', 'add_to_my_story',
            'read_article', 'write_article', 'write_story', 'edit_story',
            'create_image', 'rename_my_story'
        ]
        
        return tool in file_tools
    
    def _extract_file_event(self, agent_id: str, log_entry: dict) -> Optional[dict]:
        """Extract file operation details from log entry."""
        tool = log_entry.get('tool', '')
        result = log_entry.get('result', {})
        
        if not isinstance(result, dict):
            return None
        
        # Handle rename operations specially (they have new_path instead of file_path)
        file_path = result.get('file_path')
        if not file_path and tool == 'rename_my_story':
            file_path = result.get('new_path')
        
        if not file_path:
            return None
        
        return {
            'type': 'file_changed',
            'agent_id': agent_id,
            'file_path': file_path,
            'action': tool,
            'changes': {
                'added': result.get('lines_added', 0),
                'removed': result.get('lines_removed', 0)
            },
            'timestamp': log_entry.get('timestamp')
        }
    
    def get_agent_status(self, agent_id: str) -> dict:
        """Get current agent status."""
        return self.agent_status.get(agent_id, {
            "status": "unknown",
            "last_action": None,
            "last_action_time": None
        })
    
    def stop(self):
        """Stop the log watcher."""
        self.observer.stop()
        self.observer.join()
        logger.info("🛑 Stopped log watcher")


# Global log manager instance
log_manager = None

def init_log_manager(logs_dir: Path):
    """Initialize the global log manager."""
    global log_manager
    log_manager = LogManager(logs_dir)
    return log_manager

