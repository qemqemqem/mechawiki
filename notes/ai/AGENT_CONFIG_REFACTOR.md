# Agent Configuration Refactor

## Overview
Refactored the test agent initialization to use proper configuration files and let the normal initialization flow take over. Story files are now passed as configuration parameters instead of being hardcoded or detected dynamically.

## Key Changes

### 1. Agent Classes Accept Story File Parameters

#### ReaderAgent (`src/agents/reader_agent.py`)
- Now accepts `story_file` parameter (default: "story.txt")
- Story path is `content_repo / story_file`
- No longer hardcoded to read from `story.txt`

```python
def __init__(self, story_file: str = "story.txt", **kwargs):
```

#### WriterAgent (`src/agents/writer_agent.py`)
- Now accepts `story_file` parameter (default: "stories/writer_story.md")
- Stores it as `self.story_file` for use by the agent

```python
def __init__(
    self,
    model: str = "claude-haiku-4-5-20251001",
    story_file: str = "stories/writer_story.md",
    ...
):
```

#### InteractiveAgent (`src/agents/interactive_agent.py`)
- Now accepts `story_file` parameter (default: "stories/interactive_adventure.md")
- Stores it as `self.story_file` for use by the agent

```python
def __init__(
    self,
    model: str = "claude-haiku-4-5-20251001",
    story_file: str = "stories/interactive_adventure.md",
    ...
):
```

### 2. Agent Manager Passes Story Files (`src/server/agent_manager.py`)

```python
init_params = {
    'model': agent_config.get('model', 'claude-haiku-4-5-20251001'),
}

# Add story_file if specified in config
if 'story_file' in agent_config:
    init_params['story_file'] = agent_config['story_file']

agent_instance = agent_class(**init_params)
```

### 3. Test Initialization Refactored (`src/server/init_agents.py`)

The `init_test_agents()` function now:

1. **Cleans up dev_session directory**
   - Deletes all `*.jsonl` log files in the logs directory

2. **Writes proper agents.json**
   - Includes full agent configs with story files
   - Example:
   ```json
   {
     "id": "reader-001",
     "name": "Reader Agent 1",
     "type": "ReaderAgent",
     "config": {
       "description": "Reads stories and creates wiki articles",
       "initial_prompt": "...",
       "model": "claude-haiku-4-5-20251001",
       "story_file": "story.txt"
     },
     "created_at": "2025-11-08T...",
     "log_file": "logs/agent_reader-001.jsonl"
   }
   ```

3. **Writes config.yaml**
   - Session metadata with timestamp
   - Ensures clean initialization

4. **Normal initialization takes over**
   - `start_test_agents()` reads from `session_config.list_agents()`
   - Agent manager creates agents with proper configs
   - Log watcher tracks agents with story file info

### 4. Log Watcher Uses Config (`src/server/log_watcher.py`)

```python
def start_watching_agent(self, agent_id: str, log_file: str, agent_config: dict = None):
    """Start watching a specific agent's log.
    
    Args:
        agent_id: ID of the agent
        log_file: Path to agent's log file
        agent_config: Agent configuration dict (should contain 'story_file' key)
    """
    # Initialize status
    self.agent_status[agent_id] = {
        "status": "stopped",
        "last_action": None,
        "last_action_time": None,
        "story_file": None
    }
    
    # Get story file from agent config
    if agent_config and 'story_file' in agent_config:
        self.agent_status[agent_id]["story_file"] = agent_config['story_file']
```

- No longer detects story files dynamically from `add_to_story` calls
- Story file is set immediately from config when agent starts
- UI can display story link right away

### 5. Updated All Call Sites

- `src/server/app.py`: `log_manager.start_watching_agent(agent['id'], str(log_file), agent.get('config'))`
- `src/server/agents.py` (create): `log_manager.start_watching_agent(agent_id, str(log_file), config)`
- `src/server/agents.py` (reload): `log_manager.start_watching_agent(agent_id, str(log_file), agent.get('config'))`

## Benefits

1. **Clean Architecture**: Test initialization now follows the exact same path as production
2. **No Hardcoding**: Story files are configured, not hardcoded
3. **Declarative Config**: Everything is defined in agents.json
4. **Story Links Work Immediately**: UI shows story links without waiting for first tool call
5. **Easy to Add Agents**: Just update agents.json and restart

## Story File Assignments

| Agent Type | Story File |
|------------|-----------|
| ReaderAgent | `story.txt` (full Tales of Wonder) |
| WriterAgent | `stories/writer_story.md` |
| InteractiveAgent | `stories/interactive_adventure.md` |

## Testing

After server restart:
1. All agents should have story files in their details
2. UI should show "📖 Story" links immediately
3. Clicking story link should open the correct file in Files pane
4. Reader agent reads from Tales of Wonder
5. Writer/Interactive agents write to their respective story files

