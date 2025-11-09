"""
Mock Agent for UI testing.

Simulates agent behavior without actually using an LLM.
Generates random activity to test the UI components.
"""
import json
import random
import time
import threading
from datetime import datetime
from pathlib import Path
import sys
import os

# Add parent directory to sys.path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.articles import read_article
from tools.search import find_articles


class MockAgent:
    """Mock agent that generates random activity."""
    
    def __init__(self, agent_id: str, agent_type: str, log_file: Path, wikicontent_path: Path):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.log_file = log_file
        self.wikicontent_path = wikicontent_path
        self.running = False
        self.paused = False
        self.thread = None
        self.last_log_check = None
        
        # Agent behavior config
        self.actions = [
            ('read_article', 0.3),
            ('add_to_story', 0.25),
            ('search', 0.15),
            ('advance', 0.15 if agent_type == 'ReaderAgent' else 0),
            ('think', 0.1),
            ('talk', 0.05),
        ]
        
        # Should this agent wait for input sometimes?
        self.can_wait_for_input = (agent_type == 'InteractiveAgent')
    
    def _log(self, log_entry: dict):
        """Write a log entry to the log file."""
        log_entry['timestamp'] = datetime.now().isoformat()
        
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def _get_random_article(self) -> str:
        """Get a random article from wikicontent."""
        articles_dir = self.wikicontent_path / "articles"
        if not articles_dir.exists():
            return "london.md"
        
        articles = list(articles_dir.glob("*.md"))
        if not articles:
            return "london.md"
        
        return random.choice(articles).stem
    
    def _random_action(self):
        """Perform a random action."""
        # Check if paused
        if self.paused:
            time.sleep(1)
            return
        
        # Choose action
        actions = [a for a, w in self.actions if w > 0]
        weights = [w for a, w in self.actions if w > 0]
        action = random.choices(actions, weights=weights)[0]
        
        if action == 'read_article':
            self._action_read_article()
        elif action == 'add_to_story':
            self._action_add_to_story()
        elif action == 'search':
            self._action_search()
        elif action == 'advance':
            self._action_advance()
        elif action == 'think':
            self._action_think()
        elif action == 'talk':
            self._action_talk()
        
        # Occasionally wait for input (for Interactive agents)
        if self.can_wait_for_input and random.random() < 0.1:
            self._action_wait_for_input()
    
    def _action_read_article(self):
        """Simulate reading an article."""
        article = self._get_random_article()
        
        self._log({
            'type': 'tool_call',
            'tool': 'read_article',
            'args': {'article': article}
        })
        
        # Simulate delay
        time.sleep(random.uniform(0.5, 1.5))
        
        self._log({
            'type': 'tool_result',
            'tool': 'read_article',
            'result': {
                'file_path': f'articles/{article}.md',
                'length': random.randint(100, 1000)
            }
        })
    
    def _action_add_to_story(self):
        """Simulate writing/editing an article."""
        article = self._get_random_article()
        
        self._log({
            'type': 'tool_call',
            'tool': 'add_to_story',
            'args': {
                'article': article,
                'content': f'Updated content for {article}...'
            }
        })
        
        # Simulate delay
        time.sleep(random.uniform(1, 2))
        
        lines_added = random.randint(1, 30)
        lines_removed = random.randint(0, 10)
        
        self._log({
            'type': 'tool_result',
            'tool': 'add_to_story',
            'result': {
                'file_path': f'articles/{article}.md',
                'lines_added': lines_added,
                'lines_removed': lines_removed
            }
        })
    
    def _action_search(self):
        """Simulate searching for articles."""
        search_terms = ['london', 'castle', 'wizard', 'dragon', 'forest', 'magic']
        term = random.choice(search_terms)
        
        self._log({
            'type': 'tool_call',
            'tool': 'search',
            'args': {'query': term}
        })
        
        time.sleep(random.uniform(0.3, 0.8))
        
        self._log({
            'type': 'tool_result',
            'tool': 'search',
            'result': {
                'matches': random.randint(0, 5)
            }
        })
    
    def _action_advance(self):
        """Simulate advancing through story (Reader agent)."""
        words = random.randint(300, 600)
        
        self._log({
            'type': 'tool_call',
            'tool': 'advance',
            'args': {'num_words': words}
        })
        
        time.sleep(random.uniform(0.5, 1))
        
        self._log({
            'type': 'tool_result',
            'tool': 'advance',
            'result': {
                'words_read': words,
                'position': random.randint(1000, 5000),
                'progress': random.randint(10, 90)
            }
        })
    
    def _action_think(self):
        """Simulate thinking/reasoning."""
        thoughts = [
            "This passage describes an interesting character...",
            "I should create an image for this scene.",
            "Let me search for related articles to link...",
            "The description here is quite vivid.",
            "I notice a pattern in the narrative structure."
        ]
        
        self._log({
            'type': 'thinking',
            'content': random.choice(thoughts)
        })
        
        time.sleep(random.uniform(0.5, 1.5))
    
    def _action_talk(self):
        """Simulate assistant message."""
        messages = [
            "I've updated the article with new information.",
            "Found several related characters to document.",
            "Created an image for this location.",
            "Continuing to process the story...",
            "This section introduces an important plot point."
        ]
        
        self._log({
            'type': 'message',
            'role': 'assistant',
            'content': random.choice(messages)
        })
        
        time.sleep(random.uniform(0.5, 1))
    
    def _action_wait_for_input(self):
        """Simulate waiting for user input."""
        self._log({
            'type': 'status',
            'status': 'waiting_for_input',
            'message': 'What should I do next?'
        })
        
        # Actually pause and wait
        self.paused = True
        
        # Wait for user message (check log file)
        self._wait_for_user_message()
        
        # Resume
        self._log({
            'type': 'status',
            'status': 'running',
            'message': 'Continuing...'
        })
        
        self.paused = False
    
    def _wait_for_user_message(self):
        """Wait for a user message to appear in the log."""
        # In real implementation, this would be more sophisticated
        # For mock, just wait a bit then continue
        time.sleep(5)
    
    def start(self):
        """Start the mock agent."""
        if self.running:
            return
        
        self.running = True
        self.paused = False
        
        # Log startup
        self._log({
            'type': 'status',
            'status': 'running',
            'message': f'{self.agent_type} initialized'
        })
        
        # Start in background thread
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
    
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
                        
                        # Only check entries newer than our last check
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
            
            # Update last check timestamp
            self.last_log_check = datetime.now().isoformat()
            
        except Exception as e:
            # Silently ignore errors reading log file
            pass
    
    def _run_loop(self):
        """Main agent loop."""
        while self.running:
            try:
                # Check for control signals from log file
                self._check_control_signals()
                
                # If paused, just wait and check again
                if self.paused:
                    time.sleep(0.5)  # Check more frequently when paused
                    continue
                
                # Perform random action
                self._random_action()
                
                # Random delay between actions
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                print(f"Error in mock agent {self.agent_id}: {e}")
                time.sleep(1)
    
    def stop(self):
        """Stop the mock agent."""
        self.running = False
        
        self._log({
            'type': 'status',
            'status': 'stopped',
            'message': 'Agent stopped'
        })
    
    def pause(self):
        """Pause the agent."""
        self.paused = True
        
        self._log({
            'type': 'status',
            'status': 'paused',
            'message': 'Paused by user'
        })
    
    def resume(self):
        """Resume the agent."""
        self.paused = False
        
        self._log({
            'type': 'status',
            'status': 'running',
            'message': 'Resumed by user'
        })


def main():
    """Test the mock agent."""
    from pathlib import Path
    
    # Setup
    data_dir = Path(__file__).parent.parent.parent / "data"
    logs_dir = data_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = logs_dir / "agent_mock-test.jsonl"
    wikicontent_path = Path.home() / "Dev" / "wikicontent"
    
    # Create mock agent
    agent = MockAgent(
        agent_id="mock-test",
        agent_type="ReaderAgent",
        log_file=log_file,
        wikicontent_path=wikicontent_path
    )
    
    # Run for 30 seconds
    print(f"🤖 Starting mock agent... (log: {log_file})")
    agent.start()
    
    try:
        time.sleep(30)
    except KeyboardInterrupt:
        print("\n⏹️ Stopping...")
    
    agent.stop()
    print("✅ Done!")


if __name__ == '__main__':
    main()

