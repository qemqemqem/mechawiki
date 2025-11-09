# Agent Prompts Refactoring

## Summary

Refactored agent prompting system to use external markdown files instead of hardcoded strings. This improves maintainability and makes it easier to iterate on agent behavior without touching code.

## Implementation

### Directory Structure

```
src/agents/prompts/
├── loader.py                # Prompt loading utilities
├── project.md              # General MechaWiki project description
├── reader_agent.md         # ReaderAgent purpose and behavior
├── writer_agent.md         # WriterAgent purpose and behavior
├── interactive_agent.md    # InteractiveAgent purpose and behavior
└── tool_usage.md           # General tool usage guidelines
```

### Prompt Files

**project.md** (1,324 chars)
- Brief overview of MechaWiki system
- Explains agent ecosystem and content management
- Sets philosophical tone

**reader_agent.md** (1,809 chars)
- Purpose: Process long-form stories chunk-by-chunk
- Core responsibilities and expected behavior
- Tool usage patterns for reading workflow

**writer_agent.md** (2,091 chars)
- Purpose: Creative writing and content editing
- Story writing vs. editing patterns
- Wiki integration and consistency maintenance

**interactive_agent.md** (2,861 chars)
- Purpose: Create interactive storytelling experiences
- User engagement and choice presentation
- Critical wait_for_user() behavior documentation

**tool_usage.md** (1,577 chars)
- Core principles (read before edit, search before create)
- Common patterns and tool behavior notes
- Best practices for effective tool use

### Prompt Loader

**loader.py**
- `load_prompt_file(filename)` - Load individual markdown files
- `build_agent_prompt(agent_type, include_tools)` - Build complete system prompts

Combines prompts with `---` separators for clean structure.

### Agent Updates

Each agent class now:
1. Imports `build_agent_prompt` from prompts.loader
2. Calls `build_agent_prompt(agent_type, include_tools=True)` if no custom prompt provided
3. ReaderAgent appends story-specific context after base prompt

### Complete Prompt Sizes

- **ReaderAgent**: ~4,724 chars (+ story context)
- **WriterAgent**: ~5,006 chars
- **InteractiveAgent**: ~5,776 chars

Each includes:
- ✅ Project context
- ✅ Agent-specific guidance
- ✅ Tool usage best practices

## Testing

Created and ran test suite verifying:
- ✅ Individual prompt files load correctly
- ✅ Complete prompts contain all sections
- ✅ Agents initialize successfully with new prompts
- ✅ System prompts properly composed

## Benefits

**Maintainability**
- Edit prompts without touching Python code
- Version control friendly (clear diffs for prompt changes)
- Easy to iterate on agent behavior

**Consistency**
- Shared project context across all agents
- Common tool usage guidance
- Unified philosophical tone

**Clarity**
- Prompts are self-documenting markdown
- Agent behavior is explicit and discoverable
- New contributors can understand agent roles quickly

## Future Improvements

- Could add prompt versioning
- Could support loading custom prompts via config
- Could create specialized prompts for different story types
- Could add prompt templates for new agent types

---

Hunt with purpose! This refactor brings clarity and maintainability to agent behavior. 🎮⚔️

