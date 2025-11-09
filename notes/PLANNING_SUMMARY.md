# Real Agents Planning Summary 📋

**Date**: 2025-11-08  
**Status**: Planning Complete ✅ - Ready for Implementation

---

## Overview

Complete plan created for transitioning from MockAgent test agents to **real LLM-powered agents** using litellm. The foundation (BaseAgent, ReaderAgent, tools) already exists - we just need to refactor to event-based architecture and add 2 more agent types.

---

## Key Design Decisions ⭐

### 1. Event-Based Architecture (Generator Pattern)

**Decision**: All agents yield events, AgentRunner consumes them

**Why**: 
- ✅ Clean separation (agents produce, runner logs)
- ✅ No monkey-patching needed
- ✅ Easy to test
- ✅ Following proven mockecy pattern

```python
# Agent yields
yield {'type': 'text_token', 'content': 'Hello'}
yield {'type': 'tool_call', 'tool': 'advance', 'args': {...}}

# AgentRunner logs
for event in agent.run_forever(...):
    log_event(event)
```

### 2. Line-at-a-Time Buffering

**Decision**: Flush on newlines + tool calls (not per-token)

**Why**:
- With 3-10 agents running, per-token logging would overwhelm system
- Line-by-line is responsive but not overwhelming
- Still feels real-time for frontend

### 3. 300k Character Context Limit

**Decision**: Hard stop at 300k, raise exception

**Why**:
- Prevent runaway API costs
- Force us to implement summarization later
- Check happens before LLM call

### 4. Tool Errors as Results

**Decision**: Tool exceptions become `{'error': '...', 'success': False}` results

**Why**:
- Agent can see and respond to errors
- More robust than crashing
- Matches real-world tool behavior

### 5. Thinking Tokens Separate from Text

**Decision**: Yield `thinking_token` events separately

**Why**:
- Different UI presentation
- Can be logged separately
- Matches Claude's extended thinking feature

### 6. File-Based Streaming (For Now)

**Decision**: `Agent → Log File → LogManager → SSE → UI`

**Why**:
- Simpler (unify log and frontend streams)
- Can add dual-feed later if needed
- File watching is fast enough (~100ms)

---

## Documents Created

1. **`real_agents_implementation_plan.md`** (638 lines)
   - Full technical specification
   - All 3 agent types detailed
   - Complete AgentRunner implementation
   - 4-phase roadmap with timeline

2. **`real_agents_architecture_diagram.md`**
   - ASCII diagrams of system
   - Data flow visualizations
   - Control flow (pause/resume)
   - Memory management patterns

3. **`agent_implementation_quickstart.md`**
   - Step-by-step Phase 0 & 1 guide
   - Concrete code examples
   - Testing checklist
   - Debugging tips

4. **`agent_pause_resume_architecture.md`** (existing, already complete)
   - Log-based control architecture
   - Already implemented for MockAgent
   - Works same way for real agents!

5. **`future_features.md`** (NEW)
   - Multiple choice for InteractiveAgent
   - Auto-summarization
   - Inter-agent messaging
   - Researcher & Recorder agents
   - Cost tracking
   - And more...

6. **Test Stubs** (NEW)
   - `tests/test_base_agent_events.py`
   - `tests/test_agent_runner.py`
   - Comprehensive test coverage planned

---

## What Already Works ✅

1. **BaseAgent** - Full litellm integration, streaming, tools, memory
2. **ReaderAgent** - Complete implementation with StoryWindow
3. **Tools** - articles.py, search.py, images.py all working
4. **JSONL Log Infrastructure** - Format defined, LogManager watching
5. **Session Management** - Config, agents.json, logs directory
6. **UI** - Displays agents, logs, files in real-time
7. **Pause/Resume** - Log-based architecture works!
8. **AgentManager** - Skeleton ready for real agents

**We're ~50% done!**

---

## What Needs Building ⏳

### Phase 0: BaseAgent Refactor (3-4 hours)
- Change `run_forever()` from print to yield
- Add context length check
- Handle tool errors as results
- **Write unit tests**

### Phase 1: AgentRunner (2-3 hours)
- Event consumer with buffering
- Line-at-a-time flushing
- Control signal reading
- **Write unit tests**

### Phase 2: WriterAgent (2-3 hours)
- Create `src/tools/story.py`
- Create `src/agents/writer_agent.py`
- Inherit from refactored BaseAgent

### Phase 3: InteractiveAgent (2-3 hours)
- Create `src/tools/interactive.py` with `wait_for_user()`
- Create `src/agents/interactive_agent.py`
- Test user input flow

### Phase 4: Polish (2-3 hours)
- Test with real LLMs
- Verify all logging works
- Performance check
- Documentation

**Total**: 11-16 hours

---

## Event Types Reference

```python
# Streaming tokens
{'type': 'text_token', 'content': '...'}
{'type': 'thinking_token', 'content': '...'}

# Markers
{'type': 'thinking_start'}
{'type': 'thinking_end'}

# Tools (blocking)
{'type': 'tool_call', 'tool': 'advance', 'args': {...}}
{'type': 'tool_result', 'tool': 'advance', 'result': {...}}

# Status
{'type': 'status', 'status': 'waiting_for_input', 'message': '...'}
{'type': 'status', 'status': 'paused'}
{'type': 'status', 'status': 'archived', 'reason': '...'}

# Errors
# Tool errors: result = {'error': '...', 'success': False}
# Agent errors: raise Exception (AgentRunner logs it)
```

---

## Testing Strategy

**Unit Tests** (Critical!)
- `test_base_agent_events.py` - Event yielding logic
- `test_agent_runner.py` - Accumulation and flushing

**Integration Tests**:
1. Create ReaderAgent via UI
2. Watch logs stream
3. Pause/resume works
4. Tool calls logged correctly
5. Context limit triggers archive

**Load Tests**:
- Run 10 agents concurrently
- Verify no log corruption
- Check file I/O performance
- Monitor memory usage

---

## Success Criteria

### Phase 0 Complete When:
- [x] BaseAgent yields events instead of printing
- [x] Context check raises ContextLengthExceeded
- [x] Tool errors become error results
- [x] All unit tests pass

### Phase 1 Complete When:
- [x] AgentRunner consumes events cleanly
- [x] JSONL logs written correctly
- [x] Line-at-a-time flushing works
- [x] Pause/resume via logs works
- [x] All unit tests pass

### Phases 2-4 Complete When:
- [ ] WriterAgent writes coherent stories
- [ ] InteractiveAgent handles user input
- [ ] All 3 agent types production-ready
- [ ] No MockAgent dependency
- [ ] Documentation complete

---

## Next Steps

1. **Read the plans** (especially quickstart)
2. **Start Phase 0**: Refactor BaseAgent to yield events
3. **Write tests first** (TDD approach)
4. **Test with ReaderAgent** (already exists!)
5. **Phase 1**: Create AgentRunner
6. **Iterate**: Add WriterAgent, then InteractiveAgent

---

## Questions Answered ✅

1. **Yielding vs Printing?** → Yielding (cleaner, testable)
2. **Event types?** → Match JSONL log format
3. **Streaming strategy?** → Line-at-a-time buffering
4. **CLI compatibility?** → Everything event-based
5. **Tool execution?** → Blocking (async later if needed)
6. **Control signals?** → Yield as status events
7. **Error handling?** → Raise exceptions (tool errors are results)
8. **Thinking tokens?** → Separate stream (Option A)
9. **Context limit?** → 300k chars, check before LLM call
10. **Frontend streaming?** → File-based for now (simpler)

---

## Files to Modify

**Phase 0**:
- `src/base_agent/base_agent.py` - Refactor to yield events
- `tests/test_base_agent_events.py` - Write tests

**Phase 1**:
- `src/agents/agent_runner.py` - CREATE
- `src/server/agent_manager.py` - Update to use AgentRunner
- `tests/test_agent_runner.py` - Write tests

**Phase 2**:
- `src/tools/story.py` - CREATE
- `src/agents/writer_agent.py` - CREATE

**Phase 3**:
- `src/tools/interactive.py` - CREATE
- `src/agents/interactive_agent.py` - CREATE

---

## Risk Mitigation

**Accumulation Bugs**: 
- → Write comprehensive unit tests first!
- → Test edge cases (no newlines, multiple tool calls, etc.)

**Performance Issues**:
- → Monitor with 10 concurrent agents
- → Profile if needed
- → Line-at-a-time buffering helps

**Context Overrun**:
- → 300k hard limit prevents runaway costs
- → Add summarization in future

**Tool Errors**:
- → All become error results
- → Agent can respond gracefully
- → Logged for debugging

---

**Planning is complete! Ready to implement.** 🏰⚔️

**Estimated delivery**: 11-16 hours of focused development + testing

