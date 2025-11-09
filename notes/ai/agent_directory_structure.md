# Agent Directory Structure

## Overview

Each agent now has its own dedicated directory in `wikicontent/agents/{agent-id}/` with subdirectories based on the agent type.

## Directory Structure by Agent Type

### All Agents
Every agent gets:
```
agents/{agent-id}/
└── scratchpad/        # For tracking thoughts and working notes
```

### ReaderAgent
```
agents/{agent-id}/
└── scratchpad/
```

### WriterAgent
```
agents/{agent-id}/
├── scratchpad/
├── stories/
│   └── story.md      # Auto-created with initial template
└── subplots/         # For tracking subplot documents
```

### InteractiveAgent
```
agents/{agent-id}/
├── scratchpad/
└── stories/
    └── story.md      # Auto-created with initial template
```

## Implementation

### When Directories Are Created

1. **New Agent Creation**: When a new agent is created via the API (`/api/agents/create`), the directory structure is automatically created before the agent starts.

2. **Server Startup**: When the server starts and loads existing agents from `agents.json`, it ensures all agents have their proper directory structure (creates missing directories without overwriting existing content).

### Code Locations

- **New Agent Creation**: `src/server/agents.py` - `_setup_agent_directories()`
- **Existing Agent Initialization**: `src/server/init_agents.py` - `_ensure_agent_directories()`

### Story Files

For WriterAgent and InteractiveAgent types, a `story.md` file is automatically created in their `stories/` directory with an initial template:

```markdown
# {agent-id} Story

Your story begins here...
```

This file is only created if it doesn't already exist, so existing story files are never overwritten.

## Usage Examples

### Writer Agent
Can maintain multiple subplot documents in `subplots/`:
- `subplots/romance_arc.md`
- `subplots/mystery_thread.md`
- `subplots/character_development.md`

### All Agents
Can use `scratchpad/` for:
- `scratchpad/observations.md`
- `scratchpad/todo.md`
- `scratchpad/planning.md`

## Migration

All existing agents have been migrated to the new directory structure. The directories were created automatically when running the test, and will be maintained/created automatically going forward.

