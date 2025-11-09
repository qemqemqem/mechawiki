# Real Agents Implementation Plan 🤖

## Overview

Transform MechaWiki from using `MockAgent` test agents to **real LLM-powered agents** that can read stories, write content, and create interactive experiences. Agents will run as background threads, log all activity to JSONL files, and integrate seamlessly with the existing UI.

## Architecture

### High-Level Structure

```
BaseAgent (base_agent/base_agent.py)
    ├── litellm completion API
    ├── Streaming support
    ├── Tool management
    ├── Memory/state tracking
    └── Conversation history
    
Specialized Agents (src/agents/)
    ├── reader_agent.py    - ReaderAgent(BaseAgent)
    ├── writer_agent.py    - WriterAgent(BaseAgent)
    ├── interactive_agent.py - InteractiveAgent(BaseAgent)
    └── [future] researcher_agent.py, recorder_agent.py

Agent Runner (NEW: src/agents/agent_runner.py)
    └── Wraps BaseAgent subclasses
    └── Writes to JSONL logs
    └── Integrates with Flask/SessionConfig
```

### Key Design Principles

1. **Log-First Architecture** - All agent activity is written to JSONL logs
2. **Tool-Based Actions** - Agents interact with the world through tools
3. **Streaming by Default** - Real-time token-by-token responses
4. **Session-Aware** - Agents operate within session context (git branch, etc.)
5. **BaseAgent Inheritance** - All agents share common infrastructure
6. **Configurable Prompts** - System prompts are agent-type specific but customizable

---

## Agent Types & Specializations

### 1. ReaderAgent

**Purpose**: Read through long stories chunk-by-chunk, create wiki articles, generate images

**Inherits From**: `BaseAgent` (already exists!)

**Special Components**:
- `StoryWindow` - Manages sliding window through story text
- Progress tracking (current word, total words, percentage)
- Chunk-based advancement

**Tools**:
- `advance(num_words=None)` - Advance reading window
- `get_status()` - Get current reading position
- `read_article(article_name)` - Read existing wiki article
- `write_article(article_name, content)` - Create/update wiki article
- `search_articles(query)` - Find existing articles
- `create_image(prompt, filename)` - Generate images for characters/locations
- `end(reason)` - Stop reading

**System Prompt Template**:
```python
You are a story reader processing "{story_name}" by advancing through it chunk by chunk.

Your mission: Read systematically, create comprehensive wiki articles about characters,
locations, themes, and plot points. Generate images for vivid descriptions.

{user_description}  # From agent.config.description

Use advance() to get each story chunk. After reading, decide what wiki articles to 
create or update. Focus on encyclopedic, structured content.
```

**State**:
- Story path, current position, chunk size
- Memory tracks progress and completion status

**Already Implemented**: ✅ `src/agents/reader_agent.py` exists with full implementation!

---

### 2. WriterAgent

**Purpose**: Take wiki content and write compelling prose stories

**Inherits From**: `BaseAgent` (needs to be created)

**Special Components**:
- Story output buffer
- Plot tracking
- Style/voice consistency

**Tools**:
- `read_article(article_name)` - Read wiki articles for story material
- `search_articles(query)` - Find relevant wiki content
- `write_story(content, append=True)` - Write to story file
- `edit_story(start_word, end_word, new_content)` - Edit existing story sections
- `get_story_status()` - Check current story length, progress
- `create_image(prompt, filename)` - Generate images for scenes
- `end(reason)` - Finish writing session

**System Prompt Template**:
```python
You are a story writer who crafts compelling narratives from wiki-style content.

Your mission: Read wiki articles about characters, locations, and events, then weave
them into engaging prose. Maintain narrative consistency and vivid descriptions.

{user_description}

Use read_article() and search_articles() to gather source material. Then use 
write_story() to create prose. You can edit earlier sections with edit_story().

Focus on: character development, vivid imagery, plot coherence, emotional resonance.
```

**State**:
- Current story path and length
- Memory tracks plot points, characters introduced, timeline

**Implementation**: NEW - Create `src/agents/writer_agent.py`

---

### 3. InteractiveAgent

**Purpose**: Create RPG-like interactive experiences with user choices

**Inherits From**: `BaseAgent` (needs to be created)

**Special Components**:
- Branching narrative support
- User choice tracking
- Session state management

**Tools**:
- `read_article(article_name)` - Get wiki context
- `search_articles(query)` - Find lore
- `send_prose(content)` - Send narrative text to user
- `request_user_input(prompt, choices=None)` - Ask user for input/decision
- `create_image(prompt, filename)` - Generate scene images
- `get_session_state()` - Check current story state
- `end(reason)` - End interactive session

**System Prompt Template**:
```python
You are an interactive storyteller creating RPG-like narrative experiences.

Your mission: Use wiki content as source material to craft branching narratives where
the user makes meaningful choices that affect the story.

{user_description}

Use send_prose() to describe scenes. Use request_user_input() to present choices.
Read wiki articles for lore consistency. Generate images for key moments.

Focus on: player agency, meaningful choices, atmospheric descriptions, consequences.
```

**State**:
- Interaction history (user choices made)
- Current narrative branch
- Memory tracks story state, character relationships, quest status

**Implementation**: NEW - Create `src/agents/interactive_agent.py`

---

## Event-Based Architecture ⭐

### Design Decision: Generators, Not Print Statements

All agents (BaseAgent and subclasses) are **generators that yield events**, not functions that print.

**Benefits:**
- ✅ Clean separation: agents produce events, AgentRunner logs them
- ✅ No monkey-patching or interception needed
- ✅ Easy to test (consume events in tests)
- ✅ Unified stream for logs and frontend (file-based for now)
- ✅ Following mockecy's proven pattern

### Event Types

Agents yield events that map directly to JSONL log entries:

```python
# Text streaming (accumulated then flushed)
{'type': 'text_token', 'content': 'The story begins'}

# Thinking/reasoning (separate from text)
{'type': 'thinking_start'}
{'type': 'thinking_token', 'content': 'I should create an article...'}
{'type': 'thinking_end'}

# Tool execution (blocking)
{'type': 'tool_call', 'tool': 'advance', 'args': {'num_words': 500}}
{'type': 'tool_result', 'tool': 'advance', 'result': {...}}

# Status changes
{'type': 'status', 'status': 'waiting_for_input', 'message': '...'}
{'type': 'status', 'status': 'paused'}  # Self-pause

# Errors (non-tool errors raise exceptions, tool errors become results)
# Tool error: {'type': 'tool_result', 'result': {'error': '...', 'success': False}}
# Agent error: raise Exception (AgentRunner catches and logs)
```

### Message Buffering Strategy

**Flush triggers** (A+C hybrid):
1. On **non-text_token events** (tool_call, status, etc.) - flush accumulated text
2. On **newline characters** (`\n`) - line-at-a-time for responsive UX
3. On **turn end** - flush any remaining text

**Why line-at-a-time?**
- With 3-10 agents running concurrently, per-token logging would overwhelm the system
- Line-by-line is a good compromise: responsive but not overwhelming
- Still preserves streaming feel for frontend

### Context Length Management

**Hard limit: 300,000 characters** to prevent API overrun costs.

**Check location:** BaseAgent before `litellm.completion()` call
**Action:** Raise `ContextLengthExceeded` exception
**AgentRunner response:** Log status=archived, stop agent

**Future:** Add auto-summarization when nearing limit (not v0)

## Agent Runner - Bridging BaseAgent to JSONL Logs

### Problem

`BaseAgent` needs to be refactored from CLI-style (print) to event-yielding generator.
MechaWiki needs:
1. All output in JSONL log files
2. Background thread execution
3. Integration with Flask session management
4. Pause/resume/archive support via log-based control

### Solution: Event-Yielding Agents + AgentRunner Consumer

Create `src/agents/agent_runner.py` that consumes events from BaseAgent:

```python
class ContextLengthExceeded(Exception):
    """Raised when agent context exceeds 300,000 characters."""
    pass


class AgentRunner:
    """
    Consumes events from BaseAgent generators and writes to JSONL.
    
    Simple event consumer - no interception or monkey-patching needed!
    """
    
    def __init__(self, agent_class, agent_id, agent_config, log_file, session_config):
        self.agent_id = agent_id
        self.agent_config = agent_config
        self.log_file = Path(log_file)
        self.session_config = session_config
        
        # Create the agent instance (ReaderAgent, WriterAgent, etc.)
        self.agent = agent_class(**self._build_agent_kwargs())
        
        # Control flags
        self.running = False
        self.paused = False
        self.thread = None
        self.last_log_check = None
        
        # Message accumulation
        self.accumulated_text = ""
        self.accumulated_thinking = ""
    
    def _build_agent_kwargs(self):
        """Build kwargs for agent initialization from config."""
        kwargs = {
            'model': self.agent_config.get('model', 'claude-3-5-haiku-20241022'),
            'stream': True
        }
        
        # Add agent-specific config (story path, etc.)
        if 'story' in self.agent_config:
            kwargs['story_name'] = self.agent_config['story']
        
        return kwargs
    
    def _log(self, log_entry):
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
    
    def _run_loop(self):
        """Main agent loop - consume events and log them."""
        self._log({'type': 'status', 'status': 'running', 'message': 'Agent started'})
        
        initial_prompt = self.agent_config.get('initial_prompt', 
                                               'Start your task. Begin by getting oriented.')
        
        while self.running:
            # Check for control signals
            self._check_control_signals()
            
            if self.paused:
                time.sleep(0.5)
                continue
            
            try:
                # Consume events from agent generator
                for event in self.agent.run_forever(initial_prompt, max_turns=1):
                    signal = self._handle_event(event)
                    
                    if signal == 'wait_for_input':
                        # Break turn, wait for user message in log
                        break
                
                # Flush any remaining content at turn end
                self._flush_text()
                self._flush_thinking()
                
                # After first turn, use continuation prompt
                initial_prompt = "Continue your task."
            
            except ContextLengthExceeded as e:
                # Agent hit context limit
                self._log({
                    'type': 'status',
                    'status': 'archived',
                    'reason': 'context_limit',
                    'message': str(e)
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
                raise
            
            # Small delay between turns
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
        self._log({'type': 'status', 'status': 'stopped'})
```

---

## Tools Implementation

### Common Tools (All Agents)

Already exist in `src/tools/`:
- ✅ `articles.py` - `read_article()`
- ✅ `search.py` - `find_articles()`, `find_images()`, `find_files()`
- ✅ `images.py` - `create_image()`

### Reader-Specific Tools

Already in `ReaderAgent` class:
- ✅ `advance()` - StoryWindow management
- ✅ `get_status()` - Progress info

Need to add:
- `write_article()` - Create/update wiki articles

### Writer-Specific Tools

Need to create in `src/tools/story.py`:
- `write_story(content, append=True)`
- `edit_story(start_word, end_word, new_content)`
- `get_story_status()`

### Interactive-Specific Tools

Need to create in `src/tools/interactive.py`:
- `wait_for_user()` - Pause and wait for user input (yields `waiting_for_input` status)
- `get_session_state()` - Check story state

**Future feature:** `wait_for_user(prompt, choices=[...])` for multiple choice
(See `notes/future_features.md`)

---

## Integration with Flask

### 1. Update AgentManager

```python
# src/server/agent_manager.py

from agents.agent_runner import AgentRunner
from agents.reader_agent import ReaderAgent
from agents.writer_agent import WriterAgent
from agents.interactive_agent import InteractiveAgent

AGENT_CLASSES = {
    'ReaderAgent': ReaderAgent,
    'WriterAgent': WriterAgent,
    'InteractiveAgent': InteractiveAgent
}

class AgentManager:
    def start_agent(self, agent_id, agent_type, log_file, session_config):
        """Start real agent using AgentRunner."""
        
        # Get agent config from session
        agent_config = session_config.get_agent(agent_id)
        
        # Get agent class
        agent_class = AGENT_CLASSES.get(agent_type)
        if not agent_class:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        # Create runner
        runner = AgentRunner(
            agent_class=agent_class,
            agent_id=agent_id,
            agent_config=agent_config,
            log_file=log_file,
            session_config=session_config
        )
        
        # Start
        runner.start()
        
        self._agents[agent_id] = runner
        return runner
```

### 2. No Changes Needed to API

The REST API already works with log-based architecture!
- Agents write to logs
- API reads logs for status
- Pause/resume writes to logs, runners read them

---

## JSONL Log Format

Already defined! Agents must write:

```jsonl
{"timestamp": "2025-11-08T...", "type": "status", "status": "running", "message": "..."}
{"timestamp": "...", "type": "tool_call", "tool": "read_article", "args": {"article_name": "london"}}
{"timestamp": "...", "type": "tool_result", "tool": "read_article", "result": "# London\n..."}
{"timestamp": "...", "type": "message", "role": "assistant", "content": "This story..."}
{"timestamp": "...", "type": "thinking", "content": "I should create an article about..."}
{"timestamp": "...", "type": "user_message", "content": "Yes, continue"}
```

---

## Implementation Phases

### Phase 0: Refactor BaseAgent to Event-Yielding ⏳

**Tasks**:
1. Refactor `BaseAgent.run_forever()` to be a generator
2. Yield `text_token`, `thinking_token`, `tool_call`, `tool_result` events
3. Add context length check before `litellm.completion()`
4. Handle tool errors as error results (not exceptions)
5. **Write unit tests** for event accumulation logic (critical!)

**Deliverable**: BaseAgent is event-based, tests pass

**Tests needed**:
```python
# tests/test_base_agent_events.py
def test_text_token_accumulation()
def test_thinking_token_separation()
def test_tool_call_flushes_text()
def test_newline_flushes()
def test_context_length_limit()
def test_tool_error_handling()
```

### Phase 1: AgentRunner + ReaderAgent Integration ⏳

**Tasks**:
1. Create `src/agents/agent_runner.py` (event consumer)
2. Implement message buffering with line-at-a-time flushing
3. Implement control signal checking (pause/resume)
4. Update `ReaderAgent` to use refactored BaseAgent
5. **Write unit tests** for AgentRunner accumulation

**Deliverable**: ReaderAgent runs via AgentRunner, logs to JSONL

**Tests needed**:
```python
# tests/test_agent_runner.py
def test_runner_accumulates_text()
def test_runner_flushes_on_newline()
def test_runner_flushes_on_tool_call()
def test_runner_handles_pause_resume()
def test_runner_handles_waiting_for_input()
```

### Phase 2: WriterAgent ⏳

**Tasks**:
1. Create `src/tools/story.py` with story tools
2. Create `src/agents/writer_agent.py`
3. Define WriterAgent system prompt
4. Integrate with AgentRunner

**Deliverable**: WriterAgent can write stories from wiki content

### Phase 3: InteractiveAgent ⏳

**Tasks**:
1. Create `src/tools/interactive.py` with `wait_for_user()` tool
2. Create `src/agents/interactive_agent.py`
3. Handle `waiting_for_input` status in AgentRunner (already done in Phase 1!)
4. Test user input flow through logs
5. Handle branching narrative state

**Deliverable**: InteractiveAgent creates interactive experiences

**Note**: Multiple choice for `wait_for_user()` is a future feature

### Phase 4: Polish & Testing ⏳

**Tasks**:
1. Test all agents with real LLM calls
2. Verify pause/resume works
3. Verify tool logging is complete
4. Test session management integration
5. Performance optimization

**Deliverable**: Production-ready real agents

---

## Configuration

### Agent Creation

When user creates agent via UI:

```python
# POST /api/agents/create
{
    "name": "Reader Agent 1",
    "type": "ReaderAgent",
    "config": {
        "description": "Read through Tales of Wonder and create character articles",
        "model": "claude-3-5-haiku-20241022",
        "story": "tales_of_wonder",
        "story_path": "/path/to/story.txt",
        "chunk_size": 500
    }
}
```

### Session Config Integration

Agents access session config for:
- Git branch (`session_config.get_config()['wikicontent_branch']`)
- Wikicontent path
- Story paths
- Model preferences

---

## Migration from MockAgent

### Backward Compatibility

`AgentRunner` will replace `MockAgent` in `agent_manager.py`:

```python
# Before
from agents.mock_agent import MockAgent
agent = MockAgent(agent_id, agent_type, log_file, wikicontent_path)

# After
from agents.agent_runner import AgentRunner
from agents.reader_agent import ReaderAgent
agent = AgentRunner(ReaderAgent, agent_id, agent_config, log_file, session_config)
```

### Testing Strategy

1. Keep `MockAgent` for fallback during development
2. Add `--use-mock` flag to `start.sh` for testing UI
3. Gradually migrate test agents to real agents
4. Remove `MockAgent` when all real agents are stable

---

## Open Questions

### 1. Token Budget & Context Management

**Question**: How to handle long conversations and context limits?

**Options**:
- A. Use BaseAgent's `advance_content()` system (archive old blocks)
- B. Implement summarization tool
- C. Reset conversation periodically with summary

**Recommendation**: Use BaseAgent's existing `advance_content()` for story readers. Implement summarization for writers/interactive.

### 2. Agent Persistence

**Question**: Should agents survive server restarts?

**Options**:
- A. Agents are ephemeral - restart from config on server start
- B. Serialize full agent state (messages, memory) to disk
- C. Agents can resume from last log position

**Recommendation**: Option C - Agents resume from last log position. Session config stores agent definitions, logs store history.

### 3. Concurrent Agents

**Question**: How many agents can run simultaneously?

**Current**: No limit (all run as threads)

**Issues**: 
- LLM API rate limits
- Cost control
- Resource usage

**Recommendation**: 
- Add `max_concurrent_agents` to session config
- Queue agents if limit reached
- Add cost tracking

### 4. Agent Communication

**Question**: Should agents be able to message each other?

**Future Feature**: Not in v0, but could be powerful:
- Researcher agent → Writer agent: "I found info about X"
- Reader agent → Interactive agent: "New character discovered"

**Implementation Idea**: Add `send_agent_message(target_agent_id, message)` tool

---

## Success Criteria

### Phase 1 Complete When:
- [x] ReaderAgent runs via AgentRunner
- [x] All output appears in JSONL logs
- [x] Pause/resume works
- [x] UI shows real agent activity

### Phase 2 Complete When:
- [ ] WriterAgent can write coherent multi-paragraph stories
- [ ] Stories reference wiki articles accurately
- [ ] Tool calls logged correctly

### Phase 3 Complete When:
- [ ] InteractiveAgent presents choices to user
- [ ] User input flows through logs correctly
- [ ] Branching narratives work

### Full Success When:
- [ ] All 3 agent types production-ready
- [ ] Documentation complete
- [ ] No MockAgent dependency
- [ ] Cost tracking implemented
- [ ] Performance acceptable (< 5s response time)

---

## Timeline Estimate

**Phase 0 (BaseAgent Refactor + Tests)**: 3-4 hours
**Phase 1 (AgentRunner + Tests)**: 2-3 hours
**Phase 2 (WriterAgent)**: 2-3 hours  
**Phase 3 (InteractiveAgent)**: 2-3 hours
**Phase 4 (Polish)**: 2-3 hours

**Total**: ~11-16 hours of focused development (includes testing!)

---

## Next Steps

1. **Read the code**: Review `src/agents/reader_agent.py` thoroughly
2. **Create AgentRunner**: Start with Phase 1
3. **Test with ReaderAgent**: Verify JSONL logging works
4. **Iterate**: Once Phase 1 works, move to Phase 2

**The foundation is already there - now we connect the pieces!** 🏰⚔️

