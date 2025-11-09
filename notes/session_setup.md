# Session Setup

## Quick Start

To create a new session, just set the `SESSION_NAME` environment variable when running `start.sh`:

```bash
SESSION_NAME=tales_of_wonder ./start.sh
```

If the session doesn't exist, you'll be guided through an interactive setup wizard!

## How It Works

### 1. Automatic Detection
When you run `start.sh` with a new session name, it checks if `data/sessions/<session_name>` exists.

### 2. Setup Wizard
If the session doesn't exist (and isn't `dev_session`), the setup wizard launches automatically:

```
🏰 MechaWiki Session Setup: tales_of_wonder
======================================================================

Let's configure your new session!

This wizard will help you set up:
  • Session directory structure
  • Wikicontent branch configuration
  • Initial session settings
```

### 3. Configuration Questions

The wizard asks:

1. **Wikicontent Branch**: Which branch should this session track?
   - Auto-detects your current branch as the default
   - Shows all available branches
   - You can select from the list or type a custom branch name

2. **Description** (optional): A human-readable description of this session

3. **Confirmation**: Review and confirm before creating

### 4. Session Created!

The wizard creates:
```
data/sessions/tales_of_wonder/
├── config.yaml      # Session config with branch info
├── agents.json      # Empty agents list (ready for agents!)
└── logs/            # Directory for agent logs
```

## Examples

### Development Session (auto-cleaned)
```bash
# Default - gets wiped on every start
./start.sh
```

### Persistent Story Session
```bash
# Create a new session for your story project
SESSION_NAME=tales_of_wonder ./start.sh

# On first run, wizard asks questions
# On subsequent runs, just loads the session
SESSION_NAME=tales_of_wonder ./start.sh
```

### Multiple Sessions
```bash
# Fantasy story session
SESSION_NAME=dragon_quest ./start.sh

# Horror story session
SESSION_NAME=haunted_manor ./start.sh

# Analysis session
SESSION_NAME=lotr_analysis ./start.sh
```

## Session Config Example

After setup, `data/sessions/tales_of_wonder/config.yaml`:

```yaml
session_name: tales_of_wonder
wikicontent_branch: tales_of_wonder/main
created_at: '2025-01-09T15:30:00'
description: My epic fantasy story project
```

## Features

✅ **Interactive**: Friendly CLI wizard guides you through setup
✅ **Smart Defaults**: Auto-detects git branch from wikicontent
✅ **Branch Selection**: Shows all available branches
✅ **Skip for dev_session**: Development session skips wizard (gets auto-cleaned)
✅ **One-Time Setup**: Only runs when session doesn't exist
✅ **Safe**: Asks for confirmation before creating

## Workflow

### First Time
```bash
$ SESSION_NAME=tales_of_wonder ./start.sh
📋 Session 'tales_of_wonder' doesn't exist yet.
Running setup wizard...

[wizard runs, you answer questions]

✨ Session 'tales_of_wonder' created successfully!

[MechaWiki starts normally]
```

### Subsequent Times
```bash
$ SESSION_NAME=tales_of_wonder ./start.sh
🏰 Starting MechaWiki...
Session: tales_of_wonder
[continues normally - no wizard]
```

## Technical Details

### Setup Script
- Located at: `setup_session.py`
- Written in Python for portability
- Uses YAML for config, JSON for agents
- Integrates with git to detect branches

### start.sh Integration
- Checks if session directory exists
- Runs setup script if needed
- Validates setup completed successfully
- Continues with normal startup

### Session Structure Created
```python
{
    'session_name': 'tales_of_wonder',
    'wikicontent_branch': 'tales_of_wonder/main',
    'created_at': '2025-01-09T15:30:00',
    'description': 'Optional description'  # if provided
}
```

## Tips

**Hunt with Purpose!** 🎯
- Use descriptive session names
- One session per story/project
- `dev_session` is for quick testing (gets wiped!)
- All other sessions persist between runs

**Master the Fundamentals!** 🛡️
- The wizard auto-detects your git branch
- You can create custom branches before setup
- Session tracks the branch it was created with
- Agents in the session will use that branch

**One Quest at a Time!** ⚔️
- Create the session first
- Then add agents through the UI
- Let agents work on their configured branch
- Keep each session focused on one goal

