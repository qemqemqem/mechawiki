# Debug Logging Patterns

## Overview

All agents now have comprehensive debug logging that writes to `agents/debug_logs/{agent-id}.log`. These logs are cleared on startup and capture all Python logging for debugging purposes.

## Logger Setup

Every agent and base class should have:

```python
import logging

logger = logging.getLogger(__name__)
```

## Logging Levels

- **DEBUG**: Tool calls, context length checks, routine operations
- **INFO**: Agent initialization, state changes, important milestones
- **WARNING**: Repairs, malformed input, recoverable errors
- **ERROR**: Tool failures, unrecoverable errors, exceptions

## Common Patterns

### Agent Initialization
```python
logger.info(f"🤖 BaseAgent initialized: model={model}, stream={stream}, tools={len(self.tools)}")
logger.info(f"📖 ReaderAgent initialized: story={story_file}, starting_position={starting_position}")
logger.info(f"✍️ WriterAgent initialized: story_file={story_file}, agent_id={agent_id}")
logger.info(f"🎮 InteractiveAgent initialized: story_file={story_file}, agent_id={agent_id}")
```

### Tool Execution
```python
logger.debug(f"🔧 Executing tool: {function_name}({function_args})")
logger.debug(f"✅ Tool {function_name} completed successfully")
logger.error(f"❌ Tool {function_name} raised exception: {e}")
```

### Context Management
```python
logger.debug(f"📏 Context length: {context_length} chars ({len(self.messages)} messages)")
logger.error(f"❌ Context length exceeded: {context_length} chars (limit: 300,000)")
```

### Story/Content Operations
```python
logger.debug(f"📖 Advanced story: position={pos}/{total} ({percent:.1f}%)")
logger.debug(f"📝 Processing pending content: start_word={start_word}, length={length} chars")
```

### Control Signals
```python
logger.info(f"🏁 Tool {function_name} returned EndConversation signal")
```

### Error Handling
```python
logger.warning(f"⚠️ Malformed JSON in tool call {function_name}: {e}")
logger.warning(f"🔧 Repaired conversation history: rearranged X, added Y, removed Z")
logger.debug(f"✅ Conversation history validated: {len(messages)} messages, no repairs needed")
```

## Emoji Guide

- 🤖 BaseAgent operations
- 📖 Reader agent (reading, story position)
- ✍️ Writer agent (writing operations)
- 🎮 Interactive agent (interactive features)
- 🔧 Tool execution
- 📦 Tool results
- 🔄 Status changes
- 💬 User messages
- ⏸️ Pause signals
- ▶️ Resume signals
- 📦 Archive signals
- 🟢 Running state
- 🟡 Paused state
- 📏 Context/length measurements
- 📝 Content processing
- 🏁 Completion/end signals
- ✅ Success operations
- ❌ Errors
- ⚠️ Warnings

## AgentRunner Debug Logging

AgentRunner sets up per-agent debug loggers:

```python
def _setup_debug_logging(self):
    """Set up per-agent debug log file handler."""
    from ..server.config import agent_config
    
    # Create a logger specific to this agent
    debug_logger = logging.getLogger(f"agent.{self.agent_id}")
    debug_logger.setLevel(logging.DEBUG)
    
    # Create file handler
    debug_log_file = agent_config.debug_logs_dir / f"{self.agent_id}.log"
    file_handler = logging.FileHandler(debug_log_file, mode='a')
    file_handler.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    debug_logger.addHandler(file_handler)
    
    return debug_logger
```

### AgentRunner Event Logging

```python
# Agent state
self.debug_logger.info("🟢 Agent starting in RUNNING state")
self.debug_logger.info("🟡 Agent starting in PAUSED state")

# Tool calls and results
self.debug_logger.debug(f"🔧 Tool call: {event.get('tool')}({event.get('args', {})})")
self.debug_logger.debug(f"📦 Tool result: {result_preview}...")

# Control signals
self.debug_logger.info("⏸️ Received PAUSE signal from control log")
self.debug_logger.info("▶️ Received RESUME signal from control log")
self.debug_logger.info("📦 Received ARCHIVE signal - shutting down")

# User messages
self.debug_logger.info(f"💬 User message injected: {user_content[:100]}...")
```

## File Locations

- **Server logs**: `agents/debug_logs/server.log`
- **Agent logs**: `agents/debug_logs/{agent-id}.log`
- **Examples**: 
  - `agents/debug_logs/reader-agent-005.log`
  - `agents/debug_logs/writer-agent-001.log`
  - `agents/debug_logs/interactive-001.log`

## Startup Behavior

The `start.sh` script clears all debug logs on startup:

```bash
# Clear debug logs on startup
DEBUG_LOGS_DIR="$AGENTS_DIR/debug_logs"
if [ -d "$DEBUG_LOGS_DIR" ]; then
    echo "🧹 Clearing debug logs..."
    rm -f "$DEBUG_LOGS_DIR"/*.log
    echo "✓ Debug logs cleared"
```

And prints where logs will be written:

```
📋 Debug logs will be written to:
   Server:  /path/to/wikicontent/agents/debug_logs/server.log
   Agents:  /path/to/wikicontent/agents/debug_logs/{agent-id}.log
```

## Best Practices

1. **Use appropriate log levels** - DEBUG for routine operations, INFO for milestones, WARNING for issues, ERROR for failures
2. **Include context** - Add relevant variables, IDs, counts, etc.
3. **Use emojis consistently** - Makes logs easier to scan visually
4. **Keep messages concise** - One line per log entry when possible
5. **Log state changes** - Initialization, transitions, completions
6. **Log errors with details** - Include error messages, stack traces when needed
7. **Don't log sensitive data** - API keys, user passwords, etc.
8. **Log at decision points** - Help future debugging by showing why decisions were made

## Examples from Real Logs

From `reader-agent-006.log`:

```
2025-11-09 12:58:44 - agent.reader-agent-006 - INFO - 🔍 Debug logging initialized for agent: reader-agent-006
2025-11-09 12:58:44 - agent.reader-agent-006 - INFO - 🟢 Agent starting in RUNNING state
2025-11-09 12:58:45 - agent.reader-agent-006 - DEBUG - 🔧 Tool call: get_status({})
2025-11-09 12:58:45 - agent.reader-agent-006 - DEBUG - 📦 Tool result: 📖 Reading Status for "story.txt": ...
2025-11-09 12:58:48 - agent.reader-agent-006 - DEBUG - 🔧 Tool call: advance({'num_words': 5000})
2025-11-09 12:58:48 - agent.reader-agent-006 - DEBUG - 📦 Tool result: Advanced from word 0 to word 5000 (12.1% complete)....
2025-11-09 12:59:04 - agent.reader-agent-006 - INFO - 💬 User message injected: please start editing now...
```

Clean, readable, informative! 🎯

