# Branch-Based Configuration Migration

**Date:** November 9, 2025  
**Status:** ✅ COMPLETE

## Summary

Migrated from session-based data management to branch-based configuration. All agent data now lives in the wikicontent repository alongside the content it manages.

## What Changed

### Removed
- `data/sessions/` directory structure
- `SESSION_NAME` environment variable
- `dev_session` special handling and cleanup logic
- `setup_session.py` script
- `SessionConfig` class

### Added
- `agents/` directory in wikicontent repository
- `content_branch` setting in config.toml
- `agents_dir` path configuration
- `AgentConfig` class (simpler, no session concept)

### Migrated
- All data from `data/sessions/tales_of_wonder/` → `wikicontent/agents/`
  - `agents.json`
  - `costs.log`
  - All log files in `logs/`

## New Structure

```
wikicontent/
├── articles/          # Wiki content
├── stories/           # Story content  
├── images/            # Generated images
└── agents/            # Agent data (per branch)
    ├── agents.json    # Agent configurations
    ├── costs.log      # Cost tracking
    └── logs/          # Agent JSONL logs
        ├── agent_reader-001.jsonl
        ├── agent_writer-001.jsonl
        └── agent_interactive-001.jsonl
```

## Configuration

All configuration is now in `config.toml`:

```toml
[paths]
content_repo = "/home/keenan/Dev/wikicontent"
content_branch = "tales_of_wonder/main"
agents_dir = "agents"

[agent]
use_mock_agents = false
```

## Branch Isolation

Different branches in wikicontent can have completely different:
- Agent configurations
- Agent logs
- Cost tracking
- Wiki content

To switch projects:
1. Checkout different branch in wikicontent
2. Update `content_branch` in config.toml
3. Restart MechaWiki

## Benefits

1. **Simpler Mental Model**: No more session vs branch confusion
2. **Git-Based Isolation**: Use branches for project separation
3. **Unified Repository**: Content and agent data together
4. **No Special Cases**: No more dev_session cleanup logic
5. **Easier Backups**: Everything in one git repository

## Files Modified

### Core Server Files
- `src/server/config.py` - Complete refactor (SessionConfig → AgentConfig)
- `src/server/app.py` - Use agent_config instead of session_config
- `src/server/agents.py` - Updated all references
- `src/server/init_agents.py` - Removed dev_session handling

### Agent Files  
- `src/agents/reader_agent.py` - Updated config imports
- `src/agents/writer_agent.py` - Updated config imports

### Scripts
- `start.sh` - Removed SESSION_NAME and dev_session cleanup
- `config.toml` - Added content_branch and agents_dir settings

### Documentation
- `README.md` - Updated to reflect branch-based approach
- Removed references to session management

### Deleted
- `data/` directory (entirely)
- `setup_session.py` script

## Migration for Other Branches

If you have other sessions in `data/sessions/`, migrate them:

```bash
# For each session
cd wikicontent
git checkout your-branch
mkdir -p agents/logs
cp ~/mechawiki/data/sessions/your-session/agents.json agents/
cp ~/mechawiki/data/sessions/your-session/costs.log agents/
cp ~/mechawiki/data/sessions/your-session/logs/* agents/logs/
git add agents/
git commit -m "Migrate agent data to branch"
```

## Testing

✅ Files migrated successfully  
✅ All Python imports updated  
✅ start.sh simplified  
✅ Documentation updated  
✅ data/ directory removed  

Ready to test with: `./start.sh`

## Philosophy

This change embodies our XP values:
- **"The Working Code"** - Simpler code, fewer special cases
- **"Swift and Decisive"** - Clear mental model, faster understanding
- **"Stay the Course"** - Git branches already provide isolation
- **"Hunt with Purpose"** - One clear way to manage projects

