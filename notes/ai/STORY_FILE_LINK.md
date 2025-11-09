# Story File Link Feature

## Overview
Interactive and Writer agents that work with story files now display a clickable "📖 Story" link in their detail view that opens the story file in the Files pane.

## Implementation

### Backend Changes

#### 1. Log Watcher (`src/server/log_watcher.py`)
- Added `story_file` tracking in agent status cache
- **ReaderAgent**: Automatically set to `"story.txt"` when agent is created (hardcoded in ReaderAgent)
- **Writer/Interactive Agents**: Dynamically tracked when they use `add_to_story`, `write_story`, or `edit_story` tools
- The story file path is included in the agent status returned by `/api/agents`

```python
# ReaderAgent always uses story.txt
if agent_type == "ReaderAgent":
    self.agent_status[agent_id]["story_file"] = "story.txt"

# Track story file for interactive/writer agents
if entry_type == 'tool_call':
    tool = log_entry.get('tool')
    if tool in ['add_to_story', 'write_story', 'edit_story']:
        args = log_entry.get('args', {})
        filepath = args.get('filepath')
        if filepath:
            self.agent_status[agent_id]['story_file'] = filepath
```

#### 2. Reload Endpoint (`src/server/agents.py`)
- Added `POST /api/agents/<agent_id>/reload` endpoint
- Forces the log manager to re-read an agent's logs
- Useful for picking up story files from existing logs after server restart

### Frontend Changes

#### 1. Data Flow (`src/ui/src/App.jsx`)
- Added `onOpenFile={setSelectedFile}` callback to AgentsPane
- This allows agents to open files in the Files pane

#### 2. Props Passing (`src/ui/src/components/AgentsPane.jsx`)
- Added `onOpenFile` prop
- Passed through to AgentView component

#### 3. Story Link Display (`src/ui/src/components/agents/AgentView.jsx`)
- Added conditional story file link in agent info section
- Shows "📖 Story" button when `agent.story_file` exists
- Clicking opens the story file in the Files pane

```jsx
{agent.story_file && (
  <>
    {' • '}
    <button 
      className="story-link" 
      onClick={() => onOpenFile(agent.story_file)}
      title={`Open ${agent.story_file}`}
    >
      📖 Story
    </button>
  </>
)}
```

#### 4. Styling (`src/ui/src/components/agents/AgentView.css`)
- Added `.story-link` styling for inline button appearance
- Soft blue background with hover effects
- Rounded corners to match UI theme

## How It Works

### All Agents
1. **Agent is created**: Story file is specified in agents.json config (e.g., `"story_file": "story.txt"`)
2. **Backend reads config**: Log watcher gets story file from agent config immediately on startup
3. **API returns it**: `/api/agents` endpoint includes the story_file in agent data from the start
4. **UI displays link**: AgentView shows "📖 Story" button immediately (no waiting for first tool call)
5. **User clicks**: File opens in the Files pane on the right side

### Story File Assignments
- **ReaderAgent**: `story.txt` (the full Tales of Wonder story)
- **WriterAgent**: `stories/writer_story.md` (writer's output file)
- **InteractiveAgent**: `stories/interactive_adventure.md` (interactive adventure output)

## Testing

After restarting the server (or calling the reload endpoint):

```bash
# Check if story file is tracked
curl -s http://localhost:5000/api/agents | jq '.agents[] | select(.id == "interactive-001") | {id, story_file}'

# Manually reload an agent's logs
curl -X POST http://localhost:5000/api/agents/interactive-001/reload
```

## Notes

- Story file path is relative to wikicontent directory (e.g., `stories/interactive_adventure.md`)
- The Files pane automatically handles opening the file using the FileViewer component
- Works for any agent that uses file-writing tools (add_to_story, write_story, edit_story)
- The link only appears when a story file has been written to

