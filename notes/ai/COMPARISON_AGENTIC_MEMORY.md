# AgenticMemory vs MechaWiki: Comparative Analysis

**Date:** 2025-11-09  
**Purpose:** Analyze architectural and feature differences between AgenticMemory and MechaWiki

---

## Executive Summary

Both projects are AI-powered storytelling systems with agent-based architectures, but they differ significantly in their **scope**, **memory architecture**, **user experience paradigm**, and **operational model**.

**AgenticMemory** is a **CLI-based storytelling engine** focused on narrative generation with deep git-based memory and context tracking via the `memtool` system. It's designed for **single-user interactive storytelling** with full provenance tracking.

**MechaWiki** is a **web-based multi-agent platform** designed for **wiki generation, story analysis, and interactive experiences**. It provides real-time monitoring, multiple agent types, and a full UI for managing agent lifecycles.

---

## Core Architectural Differences

### 1. Memory System

#### AgenticMemory: `memtool` + Dual Memory Interface
- **Technology:** Uses two separate `memtool` RPC servers running on ports 18861 (KB) and 18862 (prompts)
- **Pattern:** `get_context()` → `expand_context()` for retrieving intervals
- **Persistence:** Git-based interval tracking with provenance
- **Context Query:** Agents query KB **during generation** using LiteLLM tool calls
- **Tracking:** Saves interval history for session restoration
- **Git Integration:** Deep git integration - every commit is an "audit bundle"

**Key Code:**
```python
# DualMemoryInterface connects to two memtool servers
memory = DualMemoryInterface(kb_port=18861, prompts_port=18862)
memory.connect()

# Query KB and get expanded text
kb_text = memory.query_kb("characters/gandalf.md")

# Tracks intervals for persistence
memory.save_context(output_path)
```

#### MechaWiki: File-Based Tools
- **Technology:** Direct filesystem operations (read/write/search)
- **Pattern:** Agents use tools to manipulate files in `~/Dev/wikicontent`
- **Persistence:** JSONL logs track all agent actions, git commits for content
- **Context Query:** Static file reads, search tools for discovery
- **Tracking:** Event-based logging to JSONL files
- **Git Integration:** Content repo is separate, commits are manual or agent-initiated

**Key Code:**
```python
# BaseAgent provides tool execution framework
tools = [read_article_tool, write_article_tool, search_tool, etc.]
agent = BaseAgent(tools=tools)

# Tools execute directly on filesystem
def read_article(article_name: str) -> str:
    return (wikicontent_path / "articles" / article_name).read_text()
```

**Analysis:**
- AgenticMemory's `memtool` approach provides **stronger provenance** and **context expansion** capabilities
- MechaWiki's direct file approach is **simpler** and **more transparent** but lacks interval-based context tracking
- AgenticMemory has better **knowledge graph traversal** (if `memtool` supports it)
- MechaWiki has better **real-time monitoring** of file operations

---

### 2. Agent Architecture

#### AgenticMemory: Two-Agent System

**Storyteller Agent:**
- Generates narrative using streaming LiteLLM
- Queries KB mid-generation using tool calls
- Writes thought logs to `metacognition/storyteller/`
- Maintains conversation history

**Archivist Agent:**
- Extracts facts from story blocks
- Updates KB wiki articles (creates/edits markdown files)
- Commits changes in batches (every N blocks)
- Writes thought logs to `metacognition/archivist/`

**Agent Interaction:**
```
User → Storyteller (generates story) → Archivist (extracts facts, updates KB) → Git Commit
```

**Strengths:**
- Clear separation of concerns (generate vs. maintain)
- Batch commits reduce git noise
- Both agents write "metacognition" logs (reasoning traces)
- Archivist uses LLM to analyze story and update KB

#### MechaWiki: Three-Agent System + UI

**ReaderAgent:**
- Processes stories chunk-by-chunk (advances through text)
- Creates wiki articles as it reads
- Generates images for content
- Tracks reading position (persistent state)

**WriterAgent:**
- Takes wiki content and generates narrative prose
- Inverse of ReaderAgent

**InteractiveAgent:**
- Creates RPG-like interactive experiences
- User becomes part of the story

**Agent Interaction:**
```
AgentRunner wraps agent → Yields events → Logged to JSONL → UI displays real-time
```

**Strengths:**
- **Multiple agent types** for different workflows
- **Real-time monitoring** via web UI (see thinking, tool calls, messages)
- **Pause/resume/archive** functionality
- **AgentRunner** provides event-driven architecture
- **File feed** shows all file operations chronologically
- Agents can be created, paused, resumed, and archived via UI

---

### 3. User Interface

#### AgenticMemory: CLI (Terminal-based)

**Interaction Pattern:**
```bash
$ agentic-memory run --story-repo ~/my-story

You: Gandalf enters Rivendell
Story: [streaming narrative appears]
[Archivist processing...]
OK KB updated
```

**Characteristics:**
- Rich terminal UI using `typer` + `rich` libraries
- Streaming text output (clean narrative, tool calls hidden)
- Simple, focused workflow
- No visual monitoring of agent state
- Manual session management

**Commands:**
- `agentic-memory init-story <path>` - Create new story project
- `agentic-memory run --story-repo <path>` - Start interactive session

#### MechaWiki: Web UI (React + Flask)

**Interaction Pattern:**
- Open browser to `localhost:5173`
- See all agents in left pane (with status indicators)
- Click agent to view details (messages, thinking, tool calls)
- Chat with agents in real-time
- Right pane shows file feed (all file operations across agents)
- Click files to view/edit with Monaco editor

**Characteristics:**
- **RPG-inspired theme** (dark fantasy aesthetic)
- **Real-time SSE updates** (agent events stream to browser)
- **Multi-agent orchestration** (see all agents at once)
- **Visual state management** (●running, ◉waiting, ◐paused)
- **File operations feed** with diff summaries
- **Agent lifecycle management** (create/pause/resume/archive)
- **Session-based** (multiple sessions, each with own agents)

**Analysis:**
- AgenticMemory is **focused on the storytelling experience** (direct, immersive)
- MechaWiki is **focused on observability and control** (monitor, manage, intervene)
- AgenticMemory is better for **solo writing sessions**
- MechaWiki is better for **experimentation and debugging**

---

### 4. Configuration & Project Structure

#### AgenticMemory: Story-Centric Projects

**Project Structure:**
```
my-story-project/
├── kb/                    # Knowledge base
│   ├── characters/
│   ├── locations/
│   ├── events/
│   └── ...
├── prompts/               # Agent prompts (can be git submodule)
│   ├── storyteller/
│   │   └── overview.md
│   └── archivist/
│       └── overview.md
├── sessions/              # Generated story blocks
├── metacognition/         # Agent thought logs
│   ├── storyteller/
│   └── archivist/
└── config.yaml           # Story configuration
```

**Config File (config.yaml):**
```yaml
story_repo: /path/to/story
session_name: "Session 1"
kb_server_port: 18861
prompts_server_port: 18862
storyteller_model: "claude-haiku-4-5-20251001"
archivist_model: "claude-sonnet-4-5-20250929"
temperature: 0.7
max_tokens: 2000
archivist_batch_size: 5
```

**Key Features:**
- Each story is a **separate git repository**
- Prompts can be a **git submodule** (for A/B testing across stories)
- Requires two `memtool` servers running
- Configuration is per-story (not global)

#### MechaWiki: Engine-Centric with Sessions

**Project Structure:**
```
mechawiki/
├── src/
│   ├── agents/           # Agent implementations
│   ├── server/           # Flask backend
│   ├── ui/              # React frontend
│   └── tools/           # Agent tools
├── data/
│   └── sessions/
│       ├── dev_session/
│       │   ├── config.yaml      # Session config
│       │   ├── agents.json      # Active agents
│       │   └── logs/           # JSONL logs
│       └── tales_of_wonder/
│           └── ...
└── config.toml          # Global configuration
```

**Config File (config.toml):**
```toml
[agent]
llm_provider = "anthropic"
model = "claude-haiku-4-5-20251001"
temperature = 1.0
max_steps = 1000000

[paths]
content_repo = "/home/user/Dev/wikicontent"
content_branch = "tales_of_wonder/main"

[story]
chunk_size = 5000
current_story = "tales_of_wonder"
```

**Key Features:**
- **Single engine** manages multiple sessions
- **Content repository** is separate (wikicontent)
- **Session isolation** (each session has own agents, config, logs)
- **Branch-based** content management (sessions map to git branches)
- **Global config** + per-session config

**Analysis:**
- AgenticMemory: **One story = one project = one repo**
- MechaWiki: **One engine = many sessions = one content repo with branches**
- AgenticMemory approach is **cleaner for individual stories**
- MechaWiki approach is **better for managing multiple concurrent workflows**

---

### 5. Git Integration & Provenance

#### AgenticMemory: Audit Bundle Commits

**Commit Strategy:**
- **One commit per N story blocks** (batch commits)
- Each commit is an "audit bundle" containing:
  1. Story append to `sessions/`
  2. KB updates to `kb/`
  3. Storyteller thoughts to `metacognition/storyteller/`
  4. Archivist thoughts to `metacognition/archivist/`

**Commit Message:**
```
Story batch: Session 1 blocks 1-5

Processed 5 story blocks with KB updates, session files, and metacognition logs.

Session: Session 1
Blocks: 1-5
```

**Key Features:**
- **Full provenance** - every decision is logged
- **Metacognition logs** show agent reasoning
- **Git history is source of truth**
- **Prompts can be versioned as submodules** (for A/B testing)
- Uses GitPython for commits

#### MechaWiki: Agent-Initiated Commits

**Commit Strategy:**
- Agents have access to git tools (if provided)
- JSONL logs track all actions (complete audit trail)
- Content repo commits are separate from session data
- No automatic batch commits (agents decide when to commit)

**Log Format (JSONL):**
```jsonl
{"type": "tool_call", "tool": "read_article", "args": {...}, "timestamp": ...}
{"type": "tool_result", "result": "...", "timestamp": ...}
{"type": "message", "role": "assistant", "content": "...", "timestamp": ...}
```

**Key Features:**
- **Event-based logging** to JSONL files
- **File operations tracked** in real-time
- **Backend watches JSONL logs** (via LogWatcher)
- **No automatic commit strategy** (more flexible)

**Analysis:**
- AgenticMemory has **stronger git discipline** (batch commits, audit bundles)
- MechaWiki has **more flexible git usage** (agents can commit or not)
- AgenticMemory is better for **audit/provenance use cases**
- MechaWiki is better for **experimentation** (agents control commits)

---

## Feature Comparison Matrix

| Feature | AgenticMemory | MechaWiki |
|---------|---------------|-----------|
| **Interface** | CLI (terminal) | Web UI (React + Flask) |
| **Agent Types** | 2 (Storyteller, Archivist) | 3 (Reader, Writer, Interactive) |
| **Real-time Monitoring** | ❌ No | ✅ Yes (SSE streaming) |
| **Pause/Resume Agents** | ❌ No | ✅ Yes |
| **Memory System** | memtool (RPC servers) | Direct filesystem |
| **Context Tracking** | Interval-based | File-based |
| **Git Integration** | Deep (audit bundles) | Light (agent-controlled) |
| **Metacognition Logs** | ✅ Yes (markdown files) | ✅ Yes (JSONL events) |
| **Streaming Output** | ✅ Yes (to terminal) | ✅ Yes (to UI) |
| **Tool Calls During Generation** | ✅ Yes (LiteLLM) | ✅ Yes (BaseAgent) |
| **Multi-Session Support** | ❌ One story per project | ✅ Multiple sessions |
| **File Operations Feed** | ❌ No | ✅ Yes |
| **Agent Creation UI** | ❌ No (init-story command) | ✅ Yes (web UI) |
| **Cost Tracking** | ❌ No | ✅ Yes (per agent) |
| **Image Generation** | ❌ No | ✅ Yes (DALL-E) |
| **Story Position Tracking** | ❌ No | ✅ Yes (ReaderAgent) |
| **A/B Testing Prompts** | ✅ Yes (git submodules) | ❌ No |
| **Batch Commits** | ✅ Yes (configurable) | ❌ No |
| **Prompts as Submodule** | ✅ Yes | ❌ No |

---

## Design Philosophy Differences

### AgenticMemory

**Philosophy:**
- **"Git is the source of truth"** - Everything versioned, full audit trail
- **Minimal stack** - No frameworks, just Python + LiteLLM + Git + memtool
- **Single elegant mechanism** - Audit bundle commits
- **Prompts as files** - Read from repo, history proves what was used
- **Session isolation** - One branch per session
- **Offline audit** - Can analyze git history to understand agent decisions

**Design Goals (from ARCHITECTURE.md):**
- Single elegant mechanism (all provenance in Git)
- Session isolation (branches)
- Prompts as files (git submodules)
- Minimal stack (no LangChain/LangGraph)

### MechaWiki

**Philosophy:**
- **"Real-time observability"** - See everything as it happens
- **RPG-inspired UX** - Fun, engaging, thematic
- **Event-driven architecture** - Agents yield events, runners consume them
- **Multi-agent orchestration** - Multiple agents running concurrently
- **Pause/resume/archive** - Full lifecycle control
- **XP Programming values** - "Swift and decisive", "Working code", "Strong defenses"

**Design Goals (from README.md):**
- Real-time monitoring with beautiful UI
- Multiple agent types for different workflows
- Session-based management
- Full audit trail via JSONL logs
- Focus on developer experience (observability)

**Analysis:**
- AgenticMemory prioritizes **provenance and reproducibility**
- MechaWiki prioritizes **observability and control**
- AgenticMemory is **git-first** (everything committed)
- MechaWiki is **event-first** (everything logged, commits optional)

---

## What MechaWiki Can Learn from AgenticMemory

### 1. ⭐ **Dual Memory System (memtool integration)**

**Feature:** Two separate memory servers (KB + prompts) with interval-based context retrieval

**Value:**
- **Better context expansion** - Get related content automatically
- **Provenance tracking** - Know what KB entries influenced decisions
- **Graph-based memory** - Navigate knowledge graph during generation
- **Session restoration** - Save/load interval history

**Implementation Path:**
1. Install `memtool` as dependency
2. Add `DualMemoryInterface` wrapper class
3. Update agent tools to use `query_kb()` instead of direct file reads
4. Track intervals in agent state
5. Optional: Start memtool servers alongside Flask server

**Effort:** Medium (2-3 days)  
**Impact:** High (significantly better context handling)

---

### 2. ⭐ **Metacognition Logs (Agent Reasoning Traces)**

**Feature:** Structured markdown files showing agent thought process

**Value:**
- **Debugging** - Understand why agent made decisions
- **Prompt engineering** - See what context agent used
- **Audit trail** - Human-readable reasoning logs
- **Learning** - Study agent behavior patterns

**Current State:** MechaWiki has JSONL events but no structured "thought logs"

**Implementation Path:**
1. Add `metacognition/` directory to session structure
2. After each agent turn, write markdown file with:
   - Timestamp, block/turn number
   - User input (if any)
   - Tool calls made (with descriptions)
   - Context retrieved (KB queries, search results)
   - LLM response (final output)
3. Reference from UI (add "View Reasoning" button)

**Example:**
```markdown
# ReaderAgent Thoughts - 2025-11-09T10:30:00

Session: tales_of_wonder
Turn: 42

## User Input
[advance command]

## Tool Calls
[Tool: advance(5000 words)]
[Search: "main characters"]
[Result: Found 15 articles]

## Context Retrieved
- KB: characters/dracula.md (500 chars)
- KB: locations/castle.md (300 chars)

## Response
Created article: "Count Dracula's Castle"
Generated image: castle-exterior.png
```

**Effort:** Low (1 day)  
**Impact:** Medium (better debugging and understanding)

---

### 3. ⭐ **Batch Commit Strategy**

**Feature:** Commit every N operations (batched) instead of one-by-one

**Value:**
- **Cleaner git history** - Logical groups instead of noise
- **Atomic operations** - Related changes committed together
- **Performance** - Fewer git operations
- **Audit bundles** - One commit = one logical unit of work

**Implementation Path:**
1. Add `pending_operations` counter to AgentRunner
2. Add `batch_size` config option (default: 5)
3. After each operation, check if `len(pending_operations) >= batch_size`
4. If yes, commit with message: "Agent batch: {agent_id} ops {start}-{end}"
5. Include in commit:
   - File changes
   - JSONL log updates
   - Metacognition logs (if implemented)

**Effort:** Low (1 day)  
**Impact:** Medium (cleaner git history, better for reviews)

---

### 4. ⭐⭐ **Prompts as Git Submodule (A/B Testing)**

**Feature:** Agent prompts stored in separate repo, pulled as submodule

**Value:**
- **Centralized prompt library** - One repo, many stories
- **A/B testing** - Pin different prompt versions per session
- **Prompt evolution** - Track prompt changes over time
- **Collaboration** - Share prompts across team/projects

**Implementation Path:**
1. Create separate `agent-prompts` repo:
   ```
   agent-prompts/
   ├── reader/
   │   ├── overview.md
   │   └── image_guidance.md
   ├── writer/
   │   └── overview.md
   └── interactive/
       └── overview.md
   ```
2. In each session, add as submodule:
   ```bash
   cd data/sessions/my_session/
   git submodule add https://github.com/you/agent-prompts prompts
   ```
3. Update agent initialization to read from `session_path/prompts/{agent_type}/`
4. Create branches in prompts repo for experiments:
   ```bash
   # In agent-prompts repo
   git checkout -b experiment-concise-style
   # Edit prompts
   git commit -m "Try more concise writing style"
   
   # In session
   cd data/sessions/my_session/prompts
   git checkout experiment-concise-style
   ```

**Benefits:**
- **Version control prompts** separately from code
- **Pin specific prompt versions** per session
- **Compare sessions** with different prompts
- **Rollback prompts** easily

**Effort:** Medium (2 days)  
**Impact:** High (enables systematic prompt experimentation)

---

### 5. **Archivist-Style KB Maintenance Agent**

**Feature:** Dedicated agent that reviews content and maintains consistency

**Value:**
- **KB cleanup** - Consolidate duplicate articles
- **Consistency checks** - Find contradictions
- **Link maintenance** - Update cross-references
- **Quality improvement** - Enhance article structure

**Current State:** MechaWiki agents write directly to KB, no maintenance phase

**Implementation Path:**
1. Create `ArchivistAgent` class (similar to AgenticMemory)
2. Add tools: `review_article()`, `merge_articles()`, `check_consistency()`
3. Run periodically (e.g., after every 10 ReaderAgent advances)
4. Use LLM to:
   - Find duplicate/similar articles → merge
   - Find contradictions → flag or resolve
   - Update links → add missing cross-references
   - Enhance articles → add sections, improve structure

**Workflow:**
```
ReaderAgent runs 10 times → ArchivistAgent reviews KB → Commits changes → Repeat
```

**Effort:** Medium (3-4 days)  
**Impact:** High (better KB quality over time)

---

### 6. **Story Project Init Command**

**Feature:** CLI command to create new story project with template structure

**Value:**
- **Onboarding** - Easy to start new stories
- **Consistency** - All stories have same structure
- **Documentation** - Generated README with instructions
- **Templates** - Include example prompts, config

**Implementation Path:**
1. Add CLI command (or web UI button): `mechawiki init-story <name>`
2. Create directory structure:
   ```
   data/sessions/<name>/
   ├── config.yaml      (template)
   ├── agents.json      (empty)
   ├── prompts/         (git submodule)
   ├── metacognition/   (empty)
   └── README.md        (generated)
   ```
3. Initialize git branch in wikicontent: `<name>/main`
4. Copy example prompts
5. Open UI to new session

**Effort:** Low (1 day)  
**Impact:** Low (nice-to-have, improves onboarding)

---

## What AgenticMemory Could Learn from MechaWiki

### 1. **Web UI with Real-Time Monitoring**
- See agent state visually (running, paused, waiting)
- View tool calls, messages, thinking in real-time
- File operations feed
- Monaco editor for viewing/editing files

### 2. **Pause/Resume/Archive Agent Lifecycle**
- Pause agent mid-execution
- Resume from exact state
- Archive completed agents
- Create new agents on the fly

### 3. **Multiple Agent Types**
- ReaderAgent (analyze stories)
- WriterAgent (generate from wiki)
- InteractiveAgent (RPG experiences)
- Extensible architecture for new types

### 4. **Event-Driven Agent Architecture**
- Agents yield events (not print statements)
- AgentRunner consumes events
- Decouples agent logic from I/O
- Better for testing and observability

### 5. **Session Management**
- Multiple sessions in one project
- Each session isolated (agents, logs, config)
- Easy to switch between sessions
- Development session with auto-cleanup

### 6. **Cost Tracking**
- Per-agent cost tracking
- Total tokens (prompt + completion)
- Average cost per turn
- Useful for optimization

---

## Recommendations for MechaWiki

### Priority 1: High Value, Low/Medium Effort

1. **Metacognition Logs** (1 day) - Add structured reasoning traces
2. **Batch Commit Strategy** (1 day) - Cleaner git history
3. **Cost Tracking Enhancement** - Already exists, just expose in UI

### Priority 2: High Value, Medium Effort

4. **Dual Memory System** (2-3 days) - Integrate memtool for better context
5. **Prompts as Git Submodule** (2 days) - Enable A/B testing
6. **Archivist Agent** (3-4 days) - KB maintenance and quality

### Priority 3: Nice-to-Have

7. **Story Init Command** (1 day) - Better onboarding
8. **Enhanced Prompt Management UI** - Visual prompt editor
9. **Context Window Visualization** - Show what's in agent memory

---

## Conclusion

**AgenticMemory** and **MechaWiki** solve similar problems with different approaches:

| Aspect | AgenticMemory | MechaWiki |
|--------|---------------|-----------|
| **Focus** | Storytelling provenance | Agent observability |
| **Interface** | CLI (immersive) | Web UI (control center) |
| **Memory** | memtool (interval-based) | Filesystem (direct) |
| **Git** | Audit bundles (strict) | Flexible (agent-controlled) |
| **Sessions** | One story = one repo | One engine = many sessions |

**Key Takeaways:**

1. **memtool integration** would significantly improve MechaWiki's context handling
2. **Metacognition logs** would make debugging much easier
3. **Batch commits** + **prompts as submodules** would enable better experimentation
4. **Archivist agent** would improve KB quality over time
5. MechaWiki's **event-driven architecture** and **real-time UI** are unique strengths

**Strategic Direction:**

- Keep MechaWiki's **multi-agent orchestration** and **web UI** (core differentiators)
- Adopt AgenticMemory's **memory patterns** and **git discipline** (proven approaches)
- Add **archivist-style maintenance** (KB quality)
- Enable **prompt experimentation** (A/B testing)

---

**Next Steps:**

1. Review this document with team
2. Prioritize features to adopt
3. Create implementation tickets
4. Start with quick wins (metacognition logs, batch commits)
5. Plan larger integrations (memtool, archivist agent)

