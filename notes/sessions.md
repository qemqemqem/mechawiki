# Session Management

## Overview

MechaWiki uses **sessions** to organize agents and track which git branch of wikicontent they're working on.

## Structure

```
data/
└── sessions/
    └── dev_session/           # Default session
        ├── config.yaml        # Session configuration
        ├── agents.json        # Agents in this session
        └── logs/              # Agent log files
            ├── agent_reader-20250108120000.jsonl
            └── agent_writer-20250108120100.jsonl
```

## Session Config (`config.yaml`)

```yaml
session_name: dev_session
wikicontent_branch: tales_of_wonder/main
created_at: '2025-01-08T12:00:00'
```

**Fields:**
- `session_name`: Identifier for this session
- `wikicontent_branch`: Which git branch of ~/Dev/wikicontent this session uses
- `created_at`: When the session was created

## Agents Config (`agents.json`)

```json
{
  "agents": [
    {
      "id": "reader-20250108120000",
      "name": "Reader Agent 1",
      "type": "ReaderAgent",
      "status": "stopped",
      "created_at": "2025-01-08T12:00:00",
      "config": {
        "story": "tales_of_wonder",
        "chunk_size": 500
      },
      "log_file": "logs/agent_reader-20250108120000.jsonl"
    }
  ]
}
```

## Why Sessions?

1. **Git Branch Isolation** - Different sessions can work on different branches
2. **Workflow Separation** - Separate sessions for different projects/stories
3. **Clean Organization** - All session data (agents, logs) in one place
4. **Future Multi-User Support** - Each user could have their own session

## Default Session

The system creates a `dev_session` automatically on startup if it doesn't exist. It:
1. Detects the current git branch in ~/Dev/wikicontent
2. Creates `data/sessions/dev_session/`
3. Initializes `config.yaml` with the detected branch
4. Creates empty `agents.json`

## Future: Multiple Sessions

In the future, you could:
- Create different sessions for different stories
- Switch between sessions in the UI
- Archive old sessions
- Clone sessions to fork workflows

Example future structure:
```
data/sessions/
├── dev_session/          # Main development
├── dracula_session/      # Working on Dracula
├── tales_session/        # Working on Tales of Wonder
└── experimental/         # Testing new features
```

## Implementation

**Backend:** `src/server/config.py`
- `SessionConfig` class manages session state
- Automatically creates session structure
- Provides methods for agent management within sessions

**Current Limitation:** Only one session (`dev_session`) is active. Multi-session support is planned for future versions.

