"""
AgentRunner - Consumes events from BaseAgent and writes to JSONL logs.

Bridges the event-yielding BaseAgent to MechaWiki's log-based architecture.
No monkey-patching needed - just a clean event consumer!
"""
import json
import logging
import time
import threading
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Import base agent and exception
import sys
sys.path.append(str(Path(__file__).parent.parent))
from base_agent.base_agent import BaseAgent, ContextLengthExceeded
from tools.git_helper import set_agent_log_path


class AgentRunner:
    """
    Consumes events from BaseAgent generators and writes to JSONL.
    
    Handles:
    - Line-at-a-time message buffering
    - JSONL logging with timestamps
    - Log-based control signals (pause/resume/archive)
    - Context limit exceptions
    """
    
    def __init__(
        self,
        agent_instance: BaseAgent,
        agent_id: str,
        log_file: Path,
        agent_config: Optional[Dict[str, Any]] = None,
        start_paused: bool = False,
        cost_tracker = None
    ):
        """
        Initialize AgentRunner.
        
        Args:
            agent_instance: A BaseAgent subclass instance
            agent_id: Unique agent ID
            log_file: Path to JSONL log file
            agent_config: Optional agent configuration dict
            start_paused: If True, agent starts in paused state (default: False)
            cost_tracker: Optional cost tracker instance for reporting costs
        """
        self.agent = agent_instance
        self.agent_id = agent_id
        self.log_file = Path(log_file)
        self.agent_config = agent_config or {}
        self.cost_tracker = cost_tracker
        
        # Set log path on agent for git commit tracking
        self.agent.log_path = self.log_file
        
        # Control state
        self.running = False
        self.paused = start_paused  # Can start paused!
        self.thread = None
        self.last_log_check = None
        
        # Message accumulation (line-at-a-time buffering)
        self.accumulated_text = ""
        self.accumulated_thinking = ""
        
        # Track last reported cost for incremental reporting
        self.last_reported_cost = 0.0
        
        # Track if user message was injected (so we don't add another prompt)
        self.user_message_injected = False
        
        # Set up debug logging for this agent
        self.debug_logger = self._setup_debug_logging()
        
        # Load existing conversation history from log file
        self._load_history_from_log()
    
    def _setup_debug_logging(self):
        """Set up per-agent debug log file handler.
        
        Creates a dedicated debug log file at agents/debug_logs/{agent_id}.log
        for capturing all Python logging output for this specific agent.
        
        Returns:
            logging.Logger: Configured logger for this agent
        """
        # Import config here to avoid circular imports
        from server.config import agent_config
        
        # Create a logger specific to this agent
        debug_logger = logging.getLogger(f"agent.{self.agent_id}")
        debug_logger.setLevel(logging.DEBUG)
        
        # Create file handler for debug logs
        debug_log_file = agent_config.debug_logs_dir / f"{self.agent_id}.log"
        file_handler = logging.FileHandler(debug_log_file, mode='a')
        file_handler.setLevel(logging.DEBUG)
        
        # Create detailed formatter for debug logs
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # Add handler to this agent's logger
        debug_logger.addHandler(file_handler)
        
        # Log the initialization
        debug_logger.info("=" * 80)
        debug_logger.info(f"🔍 Debug logging initialized for agent: {self.agent_id}")
        debug_logger.info(f"📁 Log file: {debug_log_file}")
        debug_logger.info("=" * 80)
        
        return debug_logger
    
    def _load_history_from_log(self):
        """Load conversation history from existing log file.
        
        This reconstructs the agent's conversation history from previous sessions,
        allowing the agent to resume with full context of what happened before.
        """
        if not self.log_file.exists():
            logger.info(f"No existing log file for {self.agent_id}, starting fresh")
            return
        
        logger.info(f"📚 Loading conversation history for {self.agent_id} from {self.log_file}")
        
        messages_loaded = 0
        accumulated_assistant_text = ""
        current_tool_calls = []
        
        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    try:
                        entry = json.loads(line)
                        entry_type = entry.get('type')
                        
                        # Skip status entries and thinking
                        if entry_type in ['status', 'thinking', 'error']:
                            continue
                        
                        # Accumulate assistant message text
                        if entry_type == 'message' and entry.get('role') == 'assistant':
                            accumulated_assistant_text += entry.get('content', '')
                        
                        # Handle tool calls
                        elif entry_type == 'tool_call':
                            # Add tool call to list
                            tool_call_id = f"call_{entry.get('tool')}_{len(current_tool_calls)}"
                            current_tool_calls.append({
                                "id": tool_call_id,
                                "type": "function",
                                "function": {
                                    "name": entry.get('tool'),
                                    "arguments": json.dumps(entry.get('args', {}))
                                }
                            })
                        
                        # Handle tool results
                        elif entry_type == 'tool_result':
                            tool_name = entry.get('tool')
                            result = entry.get('result')
                            
                            # If we have pending tool calls, create an assistant message with them
                            if current_tool_calls:
                                # Flush accumulated text into assistant message with tool calls
                                self.agent.messages.append({
                                    "role": "assistant",
                                    "content": accumulated_assistant_text,
                                    "tool_calls": current_tool_calls
                                })
                                messages_loaded += 1
                                accumulated_assistant_text = ""
                            
                            # Find the matching tool call
                            matching_call = None
                            for tc in current_tool_calls:
                                if tc['function']['name'] == tool_name:
                                    matching_call = tc
                                    break
                            
                            # Add tool result message
                            if matching_call:
                                tool_result_msg = {
                                    "role": "tool",
                                    "tool_call_id": matching_call['id'],
                                    "name": tool_name,
                                    "content": json.dumps(result) if not isinstance(result, str) else result
                                }
                                self.agent.messages.append(tool_result_msg)
                                messages_loaded += 1
                            
                            # Clear tool calls list
                            current_tool_calls = []
                        
                        # Handle user messages
                        elif entry_type == 'user_message':
                            # Flush any accumulated assistant text
                            if accumulated_assistant_text:
                                self.agent.messages.append({
                                    "role": "assistant",
                                    "content": accumulated_assistant_text
                                })
                                messages_loaded += 1
                                accumulated_assistant_text = ""
                            
                            # Add user message
                            self.agent.messages.append({
                                "role": "user",
                                "content": entry.get('content', '')
                            })
                            messages_loaded += 1
                    
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse log line: {line[:100]}")
                        continue
            
            # Flush any remaining accumulated text
            if accumulated_assistant_text:
                self.agent.messages.append({
                    "role": "assistant",
                    "content": accumulated_assistant_text
                })
                messages_loaded += 1
            
            # Validate and repair the loaded history
            if messages_loaded > 0:
                self.agent._validate_and_repair_conversation_history()
                logger.info(f"✅ Loaded {messages_loaded} conversation turns from log file")
                logger.info(f"📊 Agent now has {len(self.agent.messages)} messages in history")
        
        except Exception as e:
            logger.error(f"Error loading history from log: {e}")
            logger.info("Agent will start with empty history")
    
    def _log(self, log_entry: Dict):
        """Write JSONL log entry with timestamp."""
        log_entry['timestamp'] = datetime.now().isoformat()
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def _flush_text(self):
        """Flush accumulated text as a message."""
        if self.accumulated_text.strip():
            self._log({
                'type': 'message',
                'role': 'assistant',
                'content': self.accumulated_text
            })
            self.accumulated_text = ""
    
    def _flush_thinking(self):
        """Flush accumulated thinking."""
        if self.accumulated_thinking.strip():
            self._log({
                'type': 'thinking',
                'content': self.accumulated_thinking
            })
            self.accumulated_thinking = ""
    
    def _report_cost_to_tracker(self):
        """Report incremental cost to session tracker."""
        if not self.cost_tracker:
            return  # No cost tracker provided, skip silently
        
        # Get current total cost from agent
        current_cost = self.agent.total_cost
        
        # Calculate incremental cost since last report
        incremental_cost = current_cost - self.last_reported_cost
        
        if incremental_cost > 0:
            try:
                self.cost_tracker.add_cost(self.agent_id, incremental_cost)
                self.last_reported_cost = current_cost
                logger.info(f"💰 Reported ${incremental_cost:.6f} to cost tracker (session total: ${self.cost_tracker.get_total_cost():.6f})")
            except Exception as e:
                logger.warning(f"Failed to report cost: {e}")
    
    def _handle_event(self, event: Dict) -> Optional[str]:
        """
        Process a single event from the agent.
        
        Returns:
            Signal string if special handling needed, None otherwise
        """
        event_type = event['type']
        
        if event_type == 'text_token':
            self.accumulated_text += event['content']
            # Flush on newlines (line-at-a-time)
            if '\n' in event['content']:
                self._flush_text()
        
        elif event_type == 'thinking_token':
            self.accumulated_thinking += event['content']
            # Flush on newlines
            if '\n' in event['content']:
                self._flush_thinking()
        
        elif event_type == 'thinking_start':
            # Just a marker, don't log
            pass
        
        elif event_type == 'thinking_end':
            # Flush any remaining thinking
            self._flush_thinking()
        
        elif event_type in ['tool_call', 'tool_result', 'status']:
            # Flush any accumulated text/thinking first
            self._flush_text()
            self._flush_thinking()
            # Log event immediately
            self._log(event)
            
            # Debug log for tool calls and status changes
            if event_type == 'tool_call':
                self.debug_logger.debug(f"🔧 Tool call: {event.get('tool')}({event.get('args', {})})")
            elif event_type == 'tool_result':
                result_preview = str(event.get('result', ''))[:100]
                self.debug_logger.debug(f"📦 Tool result: {result_preview}...")
            elif event_type == 'status':
                self.debug_logger.info(f"🔄 Status change: {event.get('status')} - {event.get('message', '')}")
            
            # Special handling for waiting_for_input
            if event_type == 'status' and event.get('status') == 'waiting_for_input':
                return 'wait_for_input'  # Signal to break turn
            
            # Special handling for finished
            if event_type == 'status' and event.get('status') == 'finished':
                return 'finished'  # Signal to finish agent
        
        return None
    
    def _check_control_signals(self):
        """Check log file for pause/resume/archive commands AND user messages."""
        if not self.log_file.exists():
            return
        
        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        timestamp = entry.get('timestamp', '')
                        
                        # Only check new entries
                        if self.last_log_check and timestamp <= self.last_log_check:
                            continue
                        
                        # Look for status changes
                        if entry.get('type') == 'status':
                            status = entry.get('status')
                            
                            if status == 'paused':
                                self.paused = True
                                self.debug_logger.info("⏸️ Received PAUSE signal from control log")
                            elif status == 'running' and self.paused:
                                self.paused = False
                                self.debug_logger.info("▶️ Received RESUME signal from control log")
                            elif status == 'archived':
                                self.running = False
                                self.debug_logger.info("📦 Received ARCHIVE signal - shutting down")
                        
                        # Look for user messages and inject them into conversation
                        elif entry.get('type') == 'user_message':
                            user_content = entry.get('content', '')
                            if user_content:
                                # Add to agent's conversation history
                                self.agent.add_user_message(user_content)
                                # Set flag so we don't add another prompt
                                self.user_message_injected = True
                                logger.info(f"💬 Injected user message into {self.agent_id}: {user_content[:50]}...")
                                self.debug_logger.info(f"💬 User message injected: {user_content[:100]}...")
                    
                    except json.JSONDecodeError:
                        continue
            
            self.last_log_check = datetime.now().isoformat()
        
        except Exception:
            pass  # Ignore read errors
    
    def _wait_for_user_message(self):
        """
        Poll log file for a user_message entry.
        Blocks until one appears or agent is stopped.
        """
        last_check_timestamp = datetime.now().isoformat()
        
        while self.running and not self.paused:
            try:
                if not self.log_file.exists():
                    time.sleep(0.5)
                    continue
                
                with open(self.log_file, 'r') as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                            timestamp = entry.get('timestamp', '')
                            
                            # Only check new entries
                            if timestamp <= last_check_timestamp:
                                continue
                            
                            # Look for user_message
                            if entry.get('type') == 'user_message':
                                user_content = entry.get('content', '')
                                # Add to agent's conversation history
                                self.agent.add_user_message(user_content)
                                return  # Got user message, continue turn
                            
                            # Also check for control signals while waiting
                            if entry.get('type') == 'status':
                                status = entry.get('status')
                                if status == 'paused':
                                    self.paused = True
                                    return  # Exit waiting loop
                                elif status == 'archived':
                                    self.running = False
                                    return  # Exit waiting loop
                        
                        except json.JSONDecodeError:
                            continue
                
                last_check_timestamp = datetime.now().isoformat()
            
            except Exception:
                pass  # Ignore read errors
            
            # Sleep briefly before checking again
            time.sleep(0.5)
    
    def _run_loop(self):
        """Main agent loop - consume events and log them."""
        # Set thread-local agent log path for git commits
        set_agent_log_path(self.log_file)
        
        # Log initial status based on paused state
        if self.paused:
            self._log({'type': 'status', 'status': 'paused', 'message': 'Agent started (paused)', 'source': 'agent_runner._run_loop.initial_paused'})
            self.debug_logger.info("🟡 Agent starting in PAUSED state")
        else:
            self._log({'type': 'status', 'status': 'running', 'message': 'Agent started', 'source': 'agent_runner._run_loop.initial_running'})
            self.debug_logger.info("🟢 Agent starting in RUNNING state")
        
        initial_prompt = self.agent_config.get(
            'initial_prompt',
            'Start your task. Begin by getting oriented.'
        )
        
        while self.running:
            # Check for control signals and user messages
            self._check_control_signals()
            
            if self.paused:
                time.sleep(0.5)
                continue
            
            # If user message was injected, don't add another prompt
            if self.user_message_injected:
                initial_prompt = None
                self.user_message_injected = False
            
            try:
                # Consume events from agent generator
                waiting_for_user = False
                agent_finished = False
                for event in self.agent.run_forever(initial_prompt, max_turns=1):
                    signal = self._handle_event(event)
                    
                    if signal == 'wait_for_input':
                        # Mark that we'll wait, but DON'T break yet
                        # We need to consume remaining events (like tool_result)
                        waiting_for_user = True
                    
                    if signal == 'finished':
                        # Mark that agent is finished, but DON'T break yet
                        # We need to consume remaining events (like tool_result)
                        agent_finished = True
                
                # Flush any remaining content at turn end
                self._flush_text()
                self._flush_thinking()
                
                # Report cost to session tracker
                self._report_cost_to_tracker()
                
                # If agent marked as finished, wait for user message to resume
                if agent_finished:
                    self._log({
                        'type': 'status',
                        'status': 'finished',
                        'message': 'Agent finished. Send a message to resume.',
                        'source': 'agent_runner._run_loop.finished_waiting'
                    })
                    self._wait_for_user_message()
                    # User message was added by _wait_for_user_message
                    # Resume with continuation prompt
                    initial_prompt = "Continue your task."
                # If waiting for user input, poll for user_message in log
                elif waiting_for_user:
                    self._wait_for_user_message()
                    # User message was added by _wait_for_user_message, so pass None
                    initial_prompt = None
                else:
                    # After first turn, use continuation prompt
                    initial_prompt = "Continue your task."
            
            except ContextLengthExceeded as e:
                # Agent hit context limit
                self._log({
                    'type': 'status',
                    'status': 'archived',
                    'reason': 'context_limit',
                    'message': str(e),
                    'source': 'agent_runner._run_loop.context_limit'
                })
                self.running = False
                break
            
            except Exception as e:
                # Log error but don't kill the agent - wait for user to resume
                self._log({
                    'type': 'error',
                    'error': str(e),
                    'traceback': traceback.format_exc()
                })
                self._log({
                    'type': 'status',
                    'status': 'error_waiting',
                    'message': 'Agent encountered an error. Send a message to retry.',
                    'source': 'agent_runner._run_loop.error_recovery'
                })
                # Wait for user message to retry
                self._wait_for_user_message()
                # User message received, retry with continuation prompt
                initial_prompt = "Continue your task."
                continue
            
            # Small delay between turns
            time.sleep(1)
        
        # Log final stop
        self._log({'type': 'status', 'status': 'stopped', 'message': 'Agent stopped', 'source': 'agent_runner._run_loop.final_stop'})
    
    def start(self):
        """Start agent in background thread."""
        if self.running:
            return
        
        self.running = True
        # Don't override self.paused - respect start_paused setting
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop agent."""
        self.running = False
        # Thread will exit on next loop iteration
    
    def pause(self):
        """Pause agent (via log entry for consistency)."""
        self._log({
            'type': 'status',
            'status': 'paused',
            'message': 'Paused by user',
            'source': 'agent_runner.pause'
        })
    
    def resume(self):
        """Resume agent (via log entry for consistency)."""
        self._log({
            'type': 'status',
            'status': 'running',
            'message': 'Resumed by user',
            'source': 'agent_runner.resume'
        })
    
    def is_alive(self) -> bool:
        """Check if agent thread is still running."""
        return self.thread is not None and self.thread.is_alive()

