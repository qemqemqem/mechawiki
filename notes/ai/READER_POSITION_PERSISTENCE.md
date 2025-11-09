# Reader Agent Position Persistence ✅

## What Was Implemented

The **ReaderAgent** now **persists its reading position** to `agents.json` so it can resume from where it left off after a restart!

## Changes Made

### 1. StoryWindow Accepts Starting Position

```python
class StoryWindow:
    def __init__(self, story_path: str, starting_position: Optional[int] = None):
        self.current_position = starting_position if starting_position is not None else config["story"]["story_start"]
```

The `StoryWindow` can now be initialized with a saved position instead of always starting from the beginning.

### 2. ReaderAgent Loads Position from Config

```python
def __init__(self, story_file: str = "story.txt", agent_id: Optional[str] = None, agent_config: Optional[dict] = None, **kwargs):
    # Store agent_id for config updates
    self.agent_id = agent_id
    
    # Get starting position from agent config if available
    starting_position = None
    if agent_config and 'current_position' in agent_config:
        starting_position = agent_config['current_position']
    
    # Initialize story window with saved position
    self.story_window = StoryWindow(story_path, starting_position=starting_position)
```

When the agent starts, it checks if `agent_config` contains a `current_position` and uses that to initialize the story window.

### 3. ReaderAgent Saves Position on Advance

```python
def advance(self, num_words: Optional[int] = None):
    # ... advance logic ...
    
    # Persist current position to agents.json if we have an agent_id
    if self.agent_id:
        try:
            session_name = os.environ.get("SESSION_NAME", "dev_session")
            from server.config import SessionConfig
            session_config = SessionConfig(session_name)
            
            # Update the agent's config with current position
            session_config.update_agent(
                self.agent_id,
                {"config": {"current_position": pos_info["current_position"]}}
            )
        except Exception as e:
            # Don't fail the advance operation if config update fails
            pass
```

Every time the agent advances through the story, it **saves the new position** to `agents.json`.

### 4. AgentManager Passes Config to ReaderAgent

```python
# Add agent_id and agent_config for agents that need to persist state
if agent_type in ['WriterAgent', 'ReaderAgent']:
    init_params['agent_id'] = agent_id
    init_params['agent_config'] = agent_config
```

The agent manager now passes both `agent_id` and `agent_config` to ReaderAgent so it can load and save its position.

## How It Works

### First Run (Fresh Start)
1. ReaderAgent starts with no `current_position` in config
2. Defaults to `config["story"]["story_start"]` (usually 0)
3. Agent reads and calls `advance()`
4. Position saved to `agents.json`:
   ```json
   {
     "id": "reader-001",
     "config": {
       "story_file": "story.txt",
       "current_position": 500
     }
   }
   ```

### Restart (Resume)
1. ReaderAgent loads `current_position: 500` from config
2. Starts reading from word 500 instead of 0!
3. User sees: "Current Position: Word 500 of 50000"
4. Each `advance()` updates the position in config

## Manual Testing

### Test Plan

1. **Start a Reader Agent:**
   ```bash
   SESSION_NAME=tales_of_wonder ./start.sh
   ```

2. **Resume the reader agent and let it advance a few times:**
   - Open the UI at http://localhost:3000
   - Find the reader agent (e.g., `reader-001`)
   - Click "Resume" and watch it call `advance()` several times

3. **Check that position is saved:**
   ```bash
   cat data/sessions/tales_of_wonder/agents.json
   ```
   
   Look for:
   ```json
   {
     "id": "reader-001",
     "config": {
       "current_position": <some number> 
     }
   }
   ```

4. **Stop and restart the reader agent:**
   - In the UI, click "Archive" on the reader
   - Click "Reload Agent" button
   
5. **Verify it resumes from saved position:**
   - The agent should show the same position it was at before
   - Call `get_status()` and see: "Current Position: Word X" (where X matches the saved value)

## Race Condition Note

**Current Implementation:** Uses `SessionConfig.update_agent()` which does read-modify-write without file locking.

**Risk:** If multiple agents update config simultaneously, writes could be lost.

**Mitigation:** 
- Low risk in practice (agents don't update frequently)
- Pattern established by WriterAgent (already in use)
- For production: could add file locking using Python's `fcntl` or `filelock` library

**Future Enhancement:** Add proper file locking to `SessionConfig._load_agents()` and `_save_agents()`.

## Benefits

✅ **Persistence:** Reader agents remember their progress across restarts  
✅ **User-friendly:** No need to manually track reading position  
✅ **Consistent:** Uses same pattern as WriterAgent for config updates  
✅ **Backwards compatible:** Works with or without saved position  

## Hunt with Purpose! ⚡

Reader agents can now take on long-form stories over multiple sessions without losing their place. That's a tactical advantage in the battle against context bloat!

