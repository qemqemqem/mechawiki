# Future Features 🔮

Features deferred from v0 but planned for future releases.

## Interactive Agent Enhancements

### Multiple Choice Options
**Status**: Deferred (v0 uses simple wait_for_user())

Allow InteractiveAgent to present structured choices:

```python
wait_for_user(
    prompt="What do you do?",
    choices=[
        {"id": "explore", "text": "Explore the castle"},
        {"id": "talk", "text": "Talk to the wizard"},
        {"id": "leave", "text": "Leave the area"}
    ]
)
```

**UI Impact:**
- Display choices as buttons in Agent View
- Store choice ID in user_message log entry
- Agent receives structured choice data

**Benefits:**
- Better UX than free text
- Agent can branch on specific choices
- Clearer intent tracking

---

## Context Management

### Auto-Summarization
**Status**: Planned (post-v0)

When agent context approaches 200k characters:
1. Trigger summarization tool
2. Agent generates summary of conversation
3. Compress old messages into summary
4. Continue with reduced context

**Implementation:**
```python
# When context > 200k chars
summary = agent.summarize_conversation(start_idx=0, end_idx=100)
# Replace old messages with summary
agent.messages = [
    system_message,
    {"role": "assistant", "content": f"[Summary of earlier conversation: {summary}]"},
    ...recent_messages
]
```

**Benefits:**
- Longer-running agents
- Cost reduction
- Maintain coherence over time

---

## Agent Communication

### Inter-Agent Messaging
**Status**: Future exploration

Allow agents to send messages to each other:

```python
# Tool: send_agent_message
send_agent_message(
    target_agent_id="writer-001",
    message="I found new character info: Merlin is actually 500 years old"
)
```

**Use Cases:**
- Researcher → Writer: "Found these sources"
- Reader → Interactive: "New character discovered"
- Writer → Reader: "Need more info about X"

**Challenges:**
- Message routing
- Context injection
- Loop prevention

---

## Researcher & Recorder Agents

### Researcher Agent
**Purpose**: Deep research and organization

**Tools:**
- Advanced search with ranking
- Cross-reference finding
- Taxonomy creation
- Similarity detection

**Deferred because:** Complex tool implementations needed

### Recorder Agent  
**Purpose**: Media management (images, audio)

**Tools:**
- Media cataloging
- Embedding generation
- Quality assessment
- Organization by theme/character

**Deferred because:** Needs media processing infrastructure

---

## Performance & Monitoring

### Cost Tracking
**Status**: Post-v0

Track LLM API costs per agent:
- Token usage logging
- Cost estimation per turn
- Budget warnings
- Agent-specific budgets

### Agent Analytics Dashboard
**Status**: Future

Visualizations:
- Agent activity timeline
- Tool usage heatmap
- Token usage graphs
- Success/error rates

---

## UI Enhancements

### Parallel Frontend Stream
**Status**: Optional optimization

Currently: `Agent → Log → LogManager → SSE → UI` (~100ms delay)

Future: `Agent → Split → [ Log file + Live SSE ] → UI` (instant)

**When to implement:** If log watching latency becomes noticeable in InteractiveAgent

### Agent Templates
**Status**: Future UX improvement

Pre-configured agent templates in Create Agent modal:
- "Story Reader - Tales of Wonder"
- "Character Writer - Fantasy Style"
- "Interactive DM - D&D Campaign"

**Benefits:**
- Faster agent creation
- Best practices baked in
- Lower learning curve

### Agent Restart
**Status**: Post-v0

UI button to restart archived agents:
- Resume from last log position
- Reset with fresh context
- Clone with different config

---

## Advanced Tool Features

### Async Tool Execution
**Status**: Future

Allow tools to run asynchronously:
```python
# Example: Image generation takes 30s
yield {'type': 'tool_call', 'tool': 'create_image', 'async': True}
# Agent continues with other actions
# Later: yield {'type': 'tool_result', 'tool': 'create_image', ...}
```

**Benefits:**
- Don't block on slow tools
- Better agent utilization
- More human-like multitasking

**Challenges:**
- Conversation history management
- Result ordering
- Error handling

### Tool Chaining
**Status**: Exploration

Allow tools to call other tools:
```python
# High-level tool
def research_and_write(topic):
    articles = find_articles(topic)
    for article in articles:
        content = read_article(article)
        # ... analyze ...
    return write_article(f"{topic}-summary", summary)
```

**Benefits:**
- Reduce token usage
- More reliable workflows
- Less agent reasoning needed

---

## Storage & Persistence

### Agent State Snapshots
**Status**: Future

Periodically save full agent state to disk:
- Conversation history
- Memory dict
- Tool state

**Use Case:** Server restarts, debugging, rollback

### Log Compression
**Status**: When logs grow large

Compress old log entries:
- Keep last N days uncompressed
- Compress rest with gzip
- Maintain index for fast access

---

**This list will grow as we use the system!** 🏰⚔️

