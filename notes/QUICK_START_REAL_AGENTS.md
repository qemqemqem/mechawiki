# Quick Start: Real Agents 🚀

MechaWiki now uses **real LLM-powered agents** by default!

---

## ✅ Prerequisites

You need a Claude API key from Anthropic.

### Get Your API Key

1. Go to https://console.anthropic.com/
2. Create an account or sign in
3. Go to "API Keys"
4. Create a new key

### Add to Config

Edit `config.toml` (in the mechawiki root directory):

```toml
[anthropic]
api_key = "sk-ant-api03-YOUR-KEY-HERE"
```

---

## 🚀 Start with Real Agents

Just run the normal startup:

```bash
./start.sh
```

You'll see:
```
🏰 Starting MechaWiki...

Agent Mode: ⚡ REAL AGENTS (LLM-powered)

✓ Python 3 found: Python 3.12.x
✓ Node.js found: v20.x.x
...
✨ MechaWiki is running!

⚡ Real agents active - ensure config.toml has valid API keys!
```

The 3 demo agents will start **paused**:
- 🤖 Reader Agent 1 (ReaderAgent)
- ✍️ Writer Agent 1 (WriterAgent)
- 🎮 Interactive Agent 1 (InteractiveAgent)

**To activate them:** Click the ▶️ resume button in the UI.

**Why paused?** This prevents API usage until you're ready to watch them work!

---

## 🎭 Switch to Mock Agents

If you want to test without API calls:

**Run with the mock agents flag:**
```bash
USE_MOCK_AGENTS=true ./start.sh
```

Then restart:
```bash
./start.sh
```

---

## 📊 Watch Agents Work

### Via UI
Open http://localhost:5173 and watch the Command Center

### Via Logs
```bash
# Watch all agents
tail -f data/sessions/dev_session/logs/agent_*.jsonl

# Watch specific agent
tail -f data/sessions/dev_session/logs/agent_reader-001.jsonl
```

You'll see events streaming in real-time:
```jsonl
{"timestamp": "2025-11-09T...", "type": "status", "status": "running", ...}
{"timestamp": "2025-11-09T...", "type": "message", "role": "assistant", "content": "..."}
{"timestamp": "2025-11-09T...", "type": "tool_call", "tool": "read_article", ...}
{"timestamp": "2025-11-09T...", "type": "tool_result", ...}
```

---

## 🎮 Interact with Agents

### Pause/Resume
- Click pause button in UI
- Agent sees pause signal in its log
- Agent stops its loop (but stays alive)
- Click resume to continue

### Send Messages
- Type in the chat box at bottom of Agent View
- Message added to agent's log
- Agent picks it up on next turn

### Wait for Input (Interactive Agent)
- Interactive Agent uses `wait_for_user()` tool
- Agent yields `waiting_for_input` status
- You type a response
- Agent continues with your input

---

## 🔧 Troubleshooting

### "API key not found"
- Check `config.toml` has `[anthropic]` section with `api_key`
- Restart the server after adding the key

### "Context limit exceeded"
- Agent has processed too much content (300k chars)
- It will auto-archive itself
- This is by design to prevent cost overrun
- Future: Will add auto-summarization

### "Tool error"
- Agents handle tool errors gracefully
- Check logs for `{"error": "...", "success": false}`
- Agent sees the error and can retry or continue

### Agents not starting
- Check `backend.log` for errors
- Ensure all dependencies installed: `pip install -r requirements.txt`
- Check Python imports work: `python -c "from agents.reader_agent import ReaderAgent"`

---

## 📝 Next Steps

1. **Watch agents work** - Open UI and see them in action
2. **Create your own agent** - Use "New Agent" button
3. **Try Interactive Agent** - Send messages and get responses
4. **Read the docs** - See `notes/IMPLEMENTATION_COMPLETE.md`
5. **Write tests** - See `tests/test_*.py` stubs

---

## 🏰 You're Ready!

Real agents are now running. Hunt with purpose! ⚔️✨

