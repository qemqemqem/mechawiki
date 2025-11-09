# Agent Implementation Quick Start 🚀

## TL;DR

You already have **ReaderAgent working!** Now we need to:
1. Create `AgentRunner` to wrap it and write JSONL logs
2. Replace `MockAgent` with real agents in `AgentManager`
3. Add 2 more agent types (Writer, Interactive)

**Estimated time for Phase 1: 2-3 hours**

---

## What You Already Have ✅

### Working Components

1. **✅ BaseAgent** (`src/base_agent/base_agent.py`)
   - Full litellm integration
   - Streaming support
   - Tool execution
   - Memory management
   - Conversation history

2. **✅ ReaderAgent** (`src/agents/reader_agent.py`)
   - Complete implementation
   - StoryWindow for chunk management
   - Tools: `advance()`, `get_status()`, `read_article()`, etc.
   - Ready to use!

3. **✅ Tools** (`src/tools/`)
   - `articles.py` - read_article()
   - `search.py` - find_articles(), find_images()
   - `images.py` - create_image()

4. **✅ Log-Based Infrastructure**
   - JSONL log format defined
   - LogManager watching files
   - SSE streaming to UI
   - Session management

5. **✅ Flask Integration**
   - AgentManager skeleton
   - API endpoints for control
   - Pause/resume via logs

### What's Missing

1. **⏳ AgentRunner** - Wrapper to bridge BaseAgent → JSONL logs
2. **⏳ WriterAgent** - New agent class
3. **⏳ InteractiveAgent** - New agent class
4. **⏳ Story tools** - write_story(), edit_story()
5. **⏳ Interactive tools** - send_prose(), request_user_input()

---

## Phase 0: Refactor BaseAgent to Event-Yielding

### Goal

Make `BaseAgent.run_forever()` a **generator that yields events** instead of printing.

### Step 1: Refactor BaseAgent

Edit `src/base_agent/base_agent.py` - change `run_forever()` from:

```python
def run_forever(self, initial_message, max_turns=3):
    # ... code ...
    print(content, end="", flush=True)  # ❌ Old way
```

To:

```python
def run_forever(self, initial_message, max_turns=3):
    # ... code ...
    yield {'type': 'text_token', 'content': content}  # ✅ New way
```

**Full refactor needed in `_handle_streaming_response()` and tool execution!**

### Step 2: Add Context Length Check

Before `litellm.completion()` call:

```python
def _get_context_length(self):
    """Calculate total characters in conversation."""
    return sum(len(str(msg.get('content', ''))) for msg in self.messages)

def run_forever(self, initial_message, max_turns=3):
    # ... add user message ...
    
    while True:
        # Check context limit BEFORE LLM call
        if self._get_context_length() > 300000:
            raise ContextLengthExceeded(
                f"Context is {self._get_context_length()} chars (limit: 300,000)"
            )
        
        # Now call LLM...
```

### Step 3: Write Tests!

See `tests/test_base_agent_events.py` for test stubs.

**Run tests**: `pytest tests/test_base_agent_events.py -v`

---

## Phase 1: AgentRunner Implementation

### Goal

Create `AgentRunner` that **consumes events** from BaseAgent and writes JSONL logs.

### Step 1: Create AgentRunner Class

Create `src/agents/agent_runner.py`:

```python
"""
AgentRunner - Consumes events from BaseAgent and writes JSONL logs.

Simple event consumer - no monkey-patching needed!
"""
import json
import time
import threading
import traceback
from datetime import datetime
from pathlib import Path


class ContextLengthExceeded(Exception):
    """Raised when agent context exceeds 300,000 characters."""
    pass


class AgentRunner:
    """Consumes events from BaseAgent and writes to JSONL."""
    
    def __init__(self, agent_class, agent_id, agent_config, log_file, session_config):
        self.agent_class = agent_class
        self.agent_id = agent_id
        self.agent_config = agent_config
        self.log_file = Path(log_file)
        self.session_config = session_config
        
        # Control state
        self.running = False
        self.paused = False
        self.thread = None
        self.last_log_check = None
        
        # Message accumulation (line-at-a-time buffering)
        self.accumulated_text = ""
        self.accumulated_thinking = ""
        
        # Create agent instance
        self.agent = self._create_agent()
    
    def _create_agent(self):
        """Create the agent instance with proper kwargs."""
        # Build kwargs from config
        kwargs = {
            'model': self.agent_config.get('model', 'claude-3-5-haiku-20241022'),
            'stream': True
        }
        
        # Agent-specific config
        if 'story' in self.agent_config:
            kwargs['story_name'] = self.agent_config['story']
        if 'story_path' in self.agent_config:
            kwargs['story_path'] = self.agent_config['story_path']
        
        return self.agent_class(**kwargs)
    
    def _log(self, log_entry):
        """Write JSONL log entry."""
        log_entry['timestamp'] = datetime.now().isoformat()
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
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
    
    def _handle_event(self, event):
        """Process a single event from the agent."""
        event_type = event['type']
        
        if event_type == 'text_token':
            self.accumulated_text += event['content']
            # Flush on newlines (line-at-a-time)
            if '\n' in event['content']:
                self._flush_text()
        
        elif event_type == 'thinking_token':
            self.accumulated_thinking += event['content']
            if '\n' in event['content']:
                self._flush_thinking()
        
        elif event_type == 'thinking_start':
            pass  # Just a marker
        
        elif event_type == 'thinking_end':
            self._flush_thinking()
        
        elif event_type in ['tool_call', 'tool_result', 'status']:
            # Flush accumulated content first
            self._flush_text()
            self._flush_thinking()
            # Log event immediately
            self._log(event)
            
            # Special handling for waiting_for_input
            if event_type == 'status' and event.get('status') == 'waiting_for_input':
                return 'wait_for_input'  # Signal to break turn
        
        return None
    
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
    
    def _run_loop(self):
        """Main agent loop - consume events and log them."""
        self._log({'type': 'status', 'status': 'running', 'message': 'Agent started'})
        
        initial_prompt = self.agent_config.get('initial_prompt', 
                                               'Start your task. Begin by getting oriented.')
        
        while self.running:
            self._check_control_signals()
            
            if self.paused:
                time.sleep(0.5)
                continue
            
            try:
                # Consume events from agent generator
                for event in self.agent.run_forever(initial_prompt, max_turns=1):
                    signal = self._handle_event(event)
                    
                    if signal == 'wait_for_input':
                        break  # Break turn, wait for user message
                
                # Flush any remaining content at turn end
                self._flush_text()
                self._flush_thinking()
                
                initial_prompt = "Continue your task."
            
            except ContextLengthExceeded as e:
                self._log({
                    'type': 'status',
                    'status': 'archived',
                    'reason': 'context_limit',
                    'message': str(e)
                })
                self.running = False
                break
            
            except Exception as e:
                self._log({
                    'type': 'error',
                    'error': str(e),
                    'traceback': traceback.format_exc()
                })
                raise
            
            time.sleep(1)
    
    def start(self):
        """Start agent in background thread."""
        if self.running:
            return
        
        self.running = True
        self.paused = False
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop agent."""
        self.running = False
        self._log({
            'type': 'status',
            'status': 'stopped',
            'message': 'Agent stopped'
        })
```

### Step 2: Update AgentManager

Edit `src/server/agent_manager.py`:

```python
# Add imports
from agents.agent_runner import AgentRunner
from agents.reader_agent import ReaderAgent

# Define agent class registry
AGENT_CLASSES = {
    'ReaderAgent': ReaderAgent,
    # 'WriterAgent': WriterAgent,  # Future
    # 'InteractiveAgent': InteractiveAgent,  # Future
}

class AgentManager:
    # ... existing code ...
    
    def start_agent(self, agent_id: str, agent_type: str, log_file: Path, 
                    session_config) -> AgentRunner:
        """Start a new agent instance."""
        # Check if already running
        if agent_id in self._agents:
            logger.warning(f"Agent {agent_id} is already running")
            return self._agents[agent_id]
        
        # Get agent class
        agent_class = AGENT_CLASSES.get(agent_type)
        if not agent_class:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        # Get agent config
        agent_config = session_config.get_agent(agent_id)
        if not agent_config:
            raise ValueError(f"Agent {agent_id} not found in session config")
        
        # Create runner
        runner = AgentRunner(
            agent_class=agent_class,
            agent_id=agent_id,
            agent_config=agent_config,
            log_file=log_file,
            session_config=session_config
        )
        runner.start()
        
        self._agents[agent_id] = runner
        logger.info(f"✅ Started agent: {agent_id}")
        return runner
```

### Step 2: Write Tests!

See `tests/test_agent_runner.py` for test stubs.

**Run tests**: `pytest tests/test_agent_runner.py -v`

### Step 3: Test It!

```bash
# 1. Make sure you have API keys in config.toml
# 2. Run unit tests
pytest tests/ -v

# 3. Restart server
./start.sh

# 4. Create a ReaderAgent via UI
# 5. Watch the logs!
tail -f data/sessions/dev_session/logs/agent_reader-*.jsonl

# You should see proper JSONL entries:
# {"timestamp": "...", "type": "status", "status": "running", ...}
# {"timestamp": "...", "type": "message", "role": "assistant", "content": "..."}
# {"timestamp": "...", "type": "tool_call", "tool": "advance", ...}
```

---

## Phase 2 Preview: WriterAgent

After Phase 1 works, create `src/agents/writer_agent.py`:

```python
from base_agent.base_agent import BaseAgent
import litellm
from tools.articles import read_article
from tools.search import find_articles
from tools.story import write_story, edit_story  # NEW tools

class WriterAgent(BaseAgent):
    """Agent that writes stories from wiki content."""
    
    def __init__(self, **kwargs):
        # Create tools
        tools = [
            {"type": "function", "function": litellm.utils.function_to_dict(read_article)},
            {"type": "function", "function": litellm.utils.function_to_dict(find_articles)},
            {"type": "function", "function": litellm.utils.function_to_dict(write_story)},
            {"type": "function", "function": litellm.utils.function_to_dict(edit_story)},
        ]
        
        system_prompt = f"""You are a story writer who crafts compelling narratives 
from wiki-style content.

Read wiki articles, then write engaging prose. Focus on character development, 
vivid imagery, and plot coherence."""
        
        super().__init__(
            model=kwargs.get('model', 'claude-3-5-haiku-20241022'),
            system_prompt=system_prompt,
            tools=tools,
            **kwargs
        )
```

Then add to `AGENT_CLASSES` in `agent_manager.py`.

---

## Testing Checklist

### Phase 1 Success Criteria

- [ ] Create test ReaderAgent via UI
- [ ] Agent appears as "running" in Command Center
- [ ] Log file shows JSONL entries
- [ ] Can see tool calls in Agent View
- [ ] Pause button actually pauses agent
- [ ] Resume button resumes agent
- [ ] Archive button stops agent cleanly

### Debugging Tips

1. **Agent not starting?**
   - Check `backend.log` for errors
   - Verify config.toml has API keys
   - Check agent config in `data/sessions/dev_session/agents.json`

2. **No logs appearing?**
   - Check if log file is being created
   - Verify LogManager is watching the file
   - Check file permissions

3. **Pause/resume not working?**
   - Check if `_check_control_signals()` is being called
   - Verify status entries are being written to log
   - Check timestamp comparison logic

---

## Next Steps After Phase 1

1. **Add Tool Logging** - Intercept `_execute_tool()` to log calls/results
2. **Add Message Logging** - Intercept print() to log assistant messages
3. **Create WriterAgent** - Follow the pattern
4. **Create InteractiveAgent** - Add special user input handling
5. **Remove MockAgent** - No longer needed!

---

## Key Files to Modify

```
src/agents/
├── agent_runner.py          ← CREATE (Phase 1)
├── reader_agent.py          ← Already exists!
├── writer_agent.py          ← CREATE (Phase 2)
└── interactive_agent.py     ← CREATE (Phase 3)

src/server/
└── agent_manager.py         ← UPDATE (add AGENT_CLASSES)

src/tools/
├── story.py                 ← CREATE (Phase 2)
└── interactive.py           ← CREATE (Phase 3)
```

---

## Resources

- **Main Plan**: `notes/real_agents_implementation_plan.md`
- **Architecture**: `notes/real_agents_architecture_diagram.md`
- **Pause/Resume**: `notes/agent_pause_resume_architecture.md`
- **Existing Code**: `src/agents/reader_agent.py` (your template!)
- **BaseAgent**: `src/base_agent/base_agent.py` (already solid)

---

**You're 50% there! The foundation is rock-solid. Now just connect the pieces.** 🏰⚔️

