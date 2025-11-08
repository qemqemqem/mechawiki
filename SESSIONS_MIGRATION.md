# Session Management Migration ✅

## What Changed

We've implemented **session-based architecture** to better organize agents and track git branch state.

### Before
```
data/
├── agents.json          # Global agents
└── logs/                # All logs together
    └── agent_*.jsonl
```

### After
```
data/
└── sessions/
    └── dev_session/     # Per-session organization
        ├── config.yaml  # Tracks git branch!
        ├── agents.json  # Session's agents
        └── logs/        # Session's logs
            └── agent_*.jsonl
```

## Key Benefits

1. ✅ **Git Branch Tracking** - Each session knows which wikicontent branch it uses
2. ✅ **Clean Separation** - All session data in one place
3. ✅ **Future-Ready** - Easy to add multiple sessions later
4. ✅ **Better Organization** - Clear ownership of agents and logs

## Session Config Example

`data/sessions/dev_session/config.yaml`:
```yaml
session_name: dev_session
wikicontent_branch: tales_of_wonder/main  # Auto-detected from git!
created_at: '2025-01-08T12:00:00'
```

## Implementation Details

**Backend Changes:**
- `src/server/config.py` - New `SessionConfig` class (was `AgentConfig`)
- Automatically detects git branch on session creation
- All agent operations now session-scoped

**New Dependency:**
- Added `pyyaml` to `requirements.txt` for config.yaml support

**Auto-Migration:**
- `start.sh` creates session structure automatically
- Old `data/agents.json` and `data/logs/` (if they exist) are ignored
- Fresh start with new structure

## Current State

- **One Session**: `dev_session` (default)
- **Auto-Created**: On first run by backend
- **Git Branch**: Auto-detected from `~/Dev/wikicontent`

## Future Enhancements

Could add:
- Multiple sessions (different stories/branches)
- Session switching in UI
- Session cloning
- Session archival

## Testing

After restart, verify:
1. `data/sessions/dev_session/` exists
2. `config.yaml` shows correct git branch
3. New agents appear in `data/sessions/dev_session/agents.json`
4. Logs go to `data/sessions/dev_session/logs/`

## Migration Notes

- **No manual migration needed** - Fresh session created automatically
- Old data (if any) in `data/agents.json` won't interfere
- All new agents use the session structure

---

**This change makes MechaWiki more organized and ready for future multi-session workflows!** 🏰⚔️

