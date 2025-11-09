"""
AgentRunner - Consumes events from BaseAgent and writes to JSONL logs.

Bridges the event-yielding BaseAgent to MechaWiki's log-based architecture.
No monkey-patching needed - just a clean event consumer!
"""
import json
import time
import threading
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Import base agent and exception
import sys
sys.path.append(str(Path(__file__).parent.parent))
from base_agent.base_agent import BaseAgent, ContextLengthExceeded


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
        start_paused: bool = False
    ):
        """
        Initialize AgentRunner.
        
        Args:
            agent_instance: A BaseAgent subclass instance
            agent_id: Unique agent ID
            log_file: Path to JSONL log file
            agent_config: Optional agent configuration dict
            start_paused: If True, agent starts in paused state (default: False)
        """
        self.agent = agent_instance
        self.agent_id = agent_id
        self.log_file = Path(log_file)
        self.agent_config = agent_config or {}
        
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
        # Get current total cost from agent
        current_cost = self.agent.total_cost
        
        # Calculate incremental cost since last report
        incremental_cost = current_cost - self.last_reported_cost
        
        if incremental_cost > 0:
            # Report to session tracker
            try:
                # Import here to avoid circular imports
                from ..server.cost_tracker import get_cost_tracker
                tracker = get_cost_tracker()
                if tracker:
                    tracker.add_cost(self.agent_id, incremental_cost)
                    self.last_reported_cost = current_cost
            except Exception:
                # If tracker not available (e.g., running standalone), skip
                pass
    
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
            
            # Special handling for waiting_for_input
            if event_type == 'status' and event.get('status') == 'waiting_for_input':
                return 'wait_for_input'  # Signal to break turn
            
            # Special handling for finished
            if event_type == 'status' and event.get('status') == 'finished':
                return 'finished'  # Signal to finish agent
        
        return None
    
    def _check_control_signals(self):
        """Check log file for pause/resume/archive commands."""
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
                            elif status == 'running' and self.paused:
                                self.paused = False
                            elif status == 'archived':
                                self.running = False
                    
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
        # Log initial status based on paused state
        if self.paused:
            self._log({'type': 'status', 'status': 'paused', 'message': 'Agent started (paused)', 'source': 'agent_runner._run_loop.initial_paused'})
        else:
            self._log({'type': 'status', 'status': 'running', 'message': 'Agent started', 'source': 'agent_runner._run_loop.initial_running'})
        
        initial_prompt = self.agent_config.get(
            'initial_prompt',
            'Start your task. Begin by getting oriented.'
        )
        
        while self.running:
            # Check for control signals
            self._check_control_signals()
            
            if self.paused:
                time.sleep(0.5)
                continue
            
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
                
                # If agent marked as finished, stop running
                if agent_finished:
                    self.running = False
                    break
                
                # If waiting for user input, poll for user_message in log
                if waiting_for_user:
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
                # Other errors stop the agent
                self._log({
                    'type': 'error',
                    'error': str(e),
                    'traceback': traceback.format_exc()
                })
                # Don't raise - just log and stop
                self.running = False
                break
            
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

