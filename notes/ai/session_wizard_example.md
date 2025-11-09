# Session Setup Wizard - Example Run

## Command
```bash
SESSION_NAME=tales_of_wonder ./start.sh
```

## Expected Flow

### 1. Initial Detection
```
🏰 Starting MechaWiki...

Session: tales_of_wonder
Agent Mode: ⚡ REAL AGENTS (LLM-powered)

📋 Session 'tales_of_wonder' doesn't exist yet.
Running setup wizard...
```

### 2. Wizard Launch
```
======================================================================
  🏰 MechaWiki Session Setup: tales_of_wonder
======================================================================

Let's configure your new session!

This wizard will help you set up:
  • Session directory structure
  • Wikicontent branch configuration
  • Initial session settings

📍 Available branches in wikicontent:
   Current branch: tales_of_wonder/main

📂 Which branch should this session use?
  1. main
  2. tales_of_wonder/main (default)
  3. dracula/analysis
  4. feature/new-story

Press Enter for default, or enter a number [1-4]: [Enter]
```

### 3. Optional Description
```
📝 Session description (optional, press Enter to skip):
[My epic fantasy story project]: My epic fantasy story project
```

### 4. Confirmation
```
======================================================================
  Session Configuration Summary
======================================================================
  Session Name:   tales_of_wonder
  Branch:         tales_of_wonder/main
  Description:    My epic fantasy story project
  Location:       /home/keenan/Dev/mechawiki/data/sessions/tales_of_wonder

✅ Create this session? [Y/n]: y
```

### 5. Creation
```
🚀 Creating session structure...
✓ Created config.yaml
✓ Created agents.json

✨ Session 'tales_of_wonder' created successfully!

======================================================================
  🎉 Ready to hunt!
======================================================================

Your session 'tales_of_wonder' is configured and ready.
The startup script will now continue launching MechaWiki.
```

### 6. Normal Startup Continues
```
⚠️  config.toml not found!
Creating from example...
✓ Created config.toml - please edit with your API keys

✓ Created session directories for: tales_of_wonder

🚀 Starting Flask backend (port 5000)...
Backend PID: 12345
✓ Backend started successfully

🚀 Starting Vite frontend (port 5173)...
Frontend PID: 12346
✓ Frontend started successfully

✨ MechaWiki is running!

📍 Backend:  http://localhost:5000
📍 Frontend: http://localhost:5173 << Click here to open the UI

Press Ctrl+C to stop all servers
```

## Second Run (Session Already Exists)
```bash
SESSION_NAME=tales_of_wonder ./start.sh
```

```
🏰 Starting MechaWiki...

Session: tales_of_wonder
Agent Mode: ⚡ REAL AGENTS (LLM-powered)

[No wizard - session exists, continues normally]

✓ Python 3 found: Python 3.10.12
✓ Node.js found: v20.10.0
✓ npm found: 10.2.3

...
```

## Created Structure
```
data/sessions/tales_of_wonder/
├── config.yaml
│   session_name: tales_of_wonder
│   wikicontent_branch: tales_of_wonder/main
│   created_at: '2025-01-09T15:30:00'
│   description: My epic fantasy story project
│
├── agents.json
│   {
│     "agents": []
│   }
│
└── logs/
    (empty, ready for agent logs)
```

## Key Features

**Swift and Decisive!** ⚡
- One command creates everything
- Smart defaults (detects current git branch)
- Confirms before creating
- Continues seamlessly to startup

**Hunt with Purpose!** 🎯
- Wizard only runs once per session
- Subsequent runs skip wizard entirely
- Session data persists between runs
- Each session tracks its own branch

**Master the Fundamentals!** 🛡️
- Clean directory structure
- YAML config for readability
- JSON for agents (easy to parse)
- Logs directory ready for action

