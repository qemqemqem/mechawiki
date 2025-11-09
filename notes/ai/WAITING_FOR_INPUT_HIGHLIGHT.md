# Waiting for Input Highlight Implementation

## Overview
When an agent logs a "waiting_for_input" status, the UI now prominently displays this state with yellow highlighting and pulsing animations.

## Changes Made

### 1. CSS Color Update (`src/ui/src/App.css`)
- Changed `--status-waiting` color from `#D4A5A5` (pinkish amber) to `#F5C518` (bright yellow)
- Updated `.status-waiting` styling to use more prominent yellow glow
- Added new `urgentPulse` animation that pulses faster (1.5s) with larger scale (1.15x)
- Status bubble now has enhanced glow: `box-shadow: 0 0 16px rgba(245, 197, 24, 0.8)`

### 2. Agent Card Highlighting (`src/ui/src/components/agents/CommandCenter.jsx`)
- Added conditional class `agent-waiting` to agent cards when status is "waiting_for_input"
- Uses template literal: `className={card agent-card ${agent.status === 'waiting_for_input' ? 'agent-waiting' : ''}}`

### 3. Card Glow Animation (`src/ui/src/components/agents/CommandCenter.css`)
- Added `.agent-card.agent-waiting` styling with yellow background tint
- Card gets yellow border and glowing box shadow
- Added `cardGlow` animation that pulses the shadow intensity every 2 seconds
- Hover state enhances the glow effect

## How It Works

### Backend
1. Agent calls "waiting for input" and logs: `{"type": "status", "status": "waiting_for_input", ...}`
2. `LogManager._update_agent_status()` reads this from the log file
3. Status is cached and returned via `/api/agents` endpoint

### Frontend
1. `App.jsx` fetches agents every cycle (or through polling)
2. `CommandCenter` receives agent with `status: "waiting_for_input"`
3. Status indicator bubble gets `.status-waiting` class (yellow pulsing)
4. Agent card gets `.agent-waiting` class (yellow glow)
5. Status label shows "Waiting for input"

## Visual Result
- **Status Bubble**: Bright yellow with urgent pulsing animation (1.5s cycle)
- **Agent Card**: Yellow tint background with glowing yellow border
- **Overall Effect**: Immediately draws attention to agents needing input

## Testing
To test, an agent needs to:
1. Log a status entry with `waiting_for_input`
2. The UI should update within seconds to show yellow highlighting
3. Both the bubble and the entire card should pulse/glow

Example log entry:
```json
{"type": "status", "status": "waiting_for_input", "message": "What do you do?", "timestamp": "2025-11-08T18:54:09.438132"}
```

