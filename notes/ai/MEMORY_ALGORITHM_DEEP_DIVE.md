# Memory Management: The Core Algorithm

**Date:** 2025-11-09  
**Focus:** Deep dive into AgenticMemory's memory management patterns

---

## The Problem: Context Degradation in Long-Running Agents

As stories grow, agents face a fundamental challenge:

```
Turn 1:   "Dracula enters" → Agent has full context
Turn 50:  "Dracula enters again" → Which Dracula facts are relevant?
Turn 500: "Return to the castle" → Which castle? What happened there?
```

**Traditional approaches:**
1. **Load everything** → Context window explodes
2. **Load nothing** → Agent forgets critical details
3. **Load recent only** → Misses important early context
4. **Manual selection** → Doesn't scale

**The insight:** Agents need **dynamic, query-driven context retrieval** during generation, not static context loading before generation.

---

## AgenticMemory's Solution: The Dual Memory Architecture

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     STORYTELLER AGENT                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  LLM Generation (Streaming)                          │  │
│  │                                                       │  │
│  │  "Gandalf entered..."                               │  │
│  │  <I need context!>                                  │  │
│  │  [TOOL CALL: query_kb("characters/gandalf.md")]    │  │
│  │  [RESULT: "Grey wizard, has staff, friend to..."]  │  │
│  │  "...the grey wizard entered, staff raised..."     │  │
│  └──────────────────────────────────────────────────────┘  │
│         ↓                    ↑                               │
│    Tool Call            Tool Result                          │
│         ↓                    ↑                               │
└─────────┼────────────────────┼───────────────────────────────┘
          ↓                    ↑
┌─────────┼────────────────────┼───────────────────────────────┐
│         ↓    DUAL MEMORY     ↑                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  KB Server (port 18861)     Prompts Server (18862)  │  │
│  │                                                       │  │
│  │  memtool RPC               memtool RPC               │  │
│  │  ├─ get_context()          ├─ get_context()        │  │
│  │  ├─ expand_context()       ├─ expand_context()     │  │
│  │  └─ traverse_graph()       └─ traverse_graph()     │  │
│  └──────────────────────────────────────────────────────┘  │
│         ↓                    ↑                               │
└─────────┼────────────────────┼───────────────────────────────┘
          ↓                    ↑
┌─────────┼────────────────────┼───────────────────────────────┐
│    Git-backed Knowledge Base                                 │
│  kb/                          prompts/                       │
│  ├─ characters/               ├─ storyteller/               │
│  │  ├─ gandalf.md            │  ├─ overview.md             │
│  │  └─ frodo.md              │  └─ character_consistency.md│
│  ├─ locations/                └─ archivist/                 │
│  │  └─ rivendell.md              └─ kb_maintenance.md      │
│  └─ events/                                                  │
└──────────────────────────────────────────────────────────────┘
```

---

## The Core Algorithm: Interval-Based Context Retrieval

### Step 1: Get Context Intervals

When agent queries `"characters/gandalf.md"`:

```python
# Agent makes tool call
query_kb("characters/gandalf.md")

# DualMemoryInterface receives it
def query_kb(self, document: str, start: int = 1, end: int = 999999) -> str:
    # Step 1: Get context intervals from memtool
    context = self.kb_client.get_context(document, start, end)
    
    # Returns something like:
    # {
    #   "intervals": [
    #     {"doc": "characters/gandalf.md", "start": 1, "end": 50},
    #     {"doc": "characters/gandalf.md", "start": 100, "end": 150},  # Related section
    #     {"doc": "locations/rivendell.md", "start": 20, "end": 40},  # Linked doc
    #     {"doc": "events/council-of-elrond.md", "start": 1, "end": 30}  # Related event
    #   ],
    #   "metadata": {...}
    # }
```

**Key insight:** `get_context()` doesn't just return the requested document - it returns **intervals across multiple related documents** based on:
- Links between documents (git blame, cross-references)
- Temporal relationships (what was edited together)
- Semantic relationships (co-occurrence patterns)

### Step 2: Expand Intervals to Text

```python
    # Step 2: Expand intervals to actual text
    expansion = self.kb_client.expand_context(
        context["intervals"],
        mode="paragraph",  # Expand to paragraph boundaries
        pad=2              # Include 2 surrounding paragraphs for context
    )
    
    # Returns:
    # {
    #   "snippets": [
    #     {
    #       "doc": "characters/gandalf.md",
    #       "start": 1,
    #       "end": 65,  # Expanded from 50 to paragraph boundary
    #       "preview": "# Gandalf the Grey\n\nA wizard of great power..."
    #     },
    #     {
    #       "doc": "locations/rivendell.md",
    #       "start": 15,
    #       "end": 45,  # Expanded with padding
    #       "preview": "Rivendell is the elven haven where Gandalf often..."
    #     },
    #     ...
    #   ]
    # }
```

**Key insight:** Expansion is **smart** - it extends to natural boundaries (paragraphs, sections) and adds padding for context.

### Step 3: Track Intervals for Provenance

```python
    # Step 3: Extract text from snippets
    texts = [snippet["preview"] for snippet in expansion.get("snippets", [])]
    
    # Step 4: Track intervals for persistence
    self.kb_context_intervals.extend(context["intervals"])
    
    # Step 5: Return combined text to agent
    return "\n\n".join(texts)
```

**Key insight:** The system tracks **which intervals were used** for each turn. This enables:
- **Provenance tracking** - "Why did agent say X?" → "Because it read intervals Y and Z"
- **Context restoration** - Resume session with same context state
- **Debugging** - See exactly what KB content influenced each decision

---

## How This Gets Used During Generation

### The Agent's Perspective

```python
def generate(self, user_input: str) -> Generator[str, None, None]:
    """Generate story with dynamic context queries."""
    
    # 1. Add user message to conversation
    self.messages.append({"role": "user", "content": user_input})
    
    # 2. Start streaming generation with tools available
    response = litellm.completion(
        model=self.model,
        messages=[{"role": "system", "content": self.system_prompt}] + self.messages,
        tools=self._get_tools(),  # query_kb, query_prompts available
        stream=True
    )
    
    # 3. Process streaming chunks
    for chunk in response:
        delta = chunk.choices[0].delta
        
        # Agent produces tool call mid-generation!
        if hasattr(delta, 'tool_calls') and delta.tool_calls:
            tool_call = delta.tool_calls[0]
            
            # Execute tool (query KB)
            tool_result = self._execute_tool(tool_call.name, tool_call.args)
            
            # Add result to conversation
            self.messages.append({"role": "tool", "content": tool_result})
            
            # Continue generation with retrieved context!
            # LLM now has the KB info and continues writing
            
        # Agent produces narrative text
        elif hasattr(delta, 'content') and delta.content:
            yield delta.content  # Stream to user (tool calls hidden)
```

### The User's Perspective

```
User: "Gandalf enters Rivendell"

[Behind the scenes:]
1. LLM starts: "Gandalf entered..."
2. LLM realizes: "I need Gandalf details"
3. Tool call: query_kb("characters/gandalf.md")
4. memtool returns: Gandalf info + linked Rivendell info
5. LLM continues: "...the grey wizard entered the elven haven, staff raised..."
6. User sees clean narrative (no tool calls visible)

[What gets logged:]
- storyteller/reasoning.md: "Tool: query_kb(characters/gandalf.md), Result: 500 chars"
- storyteller/context_pack.yaml: Full list of intervals used
- storyteller/tool_calls.jsonl: Structured log of all tool interactions
```

---

## The Workspace Snapshot: Full Auditability

After each turn, the system commits a "workspace snapshot":

```
MetaCog/Workspace/sessions/session_1/blocks/0042/
├── storyteller/
│   ├── reasoning.md              # Human-readable thought log
│   ├── tool_calls.jsonl          # Structured tool call log
│   ├── context_pack.yaml         # Intervals used (full provenance)
│   └── prompt.txt                # Prompt used (if changed)
└── archivist/
    ├── reasoning.md              # Archivist's analysis
    ├── tool_calls.jsonl          # KB edits made
    └── applied_diffs.md          # Human-readable KB changes
```

**This enables:**
1. **Debugging** - "Why did agent say X?" → Check reasoning.md and context_pack.yaml
2. **Reproducibility** - Replay with same intervals
3. **Auditing** - Full trace of what KB content influenced output
4. **Learning** - Analyze patterns across many turns

---

## Comparison: AgenticMemory vs MechaWiki Memory

### AgenticMemory Pattern

```python
# Agent makes query
tool_call("query_kb", {"document": "characters/dracula.md"})

# System workflow:
1. memtool.get_context("characters/dracula.md")
   → Returns intervals across multiple docs
   
2. memtool.expand_context(intervals, mode="paragraph", pad=2)
   → Expands to natural boundaries
   
3. Track intervals for provenance
   self.kb_context_intervals.extend(intervals)
   
4. Return expanded text to agent
   return combined_text

# Result: Agent gets rich, multi-document context
# Provenance: Full record of what was retrieved
```

**Strengths:**
- ✅ **Multi-document context** - Gets related content automatically
- ✅ **Smart expansion** - Paragraph boundaries, padding
- ✅ **Provenance tracking** - Know exactly what was used
- ✅ **Graph traversal** - Follow links between documents
- ✅ **Context restoration** - Resume with same state

**Weaknesses:**
- ❌ Requires running memtool servers
- ❌ More complex setup
- ❌ RPC overhead (though likely minimal)

### MechaWiki Pattern

```python
# Agent makes tool call
tool_call("read_article", {"article_name": "dracula.md"})

# System workflow:
def read_article(article_name: str) -> str:
    path = wikicontent_path / "articles" / article_name
    return path.read_text()

# Result: Agent gets exact file requested
# Provenance: JSONL event logged
```

**Strengths:**
- ✅ **Simple** - Direct file system access
- ✅ **Fast** - No RPC calls
- ✅ **Transparent** - Easy to understand
- ✅ **Event logging** - JSONL tracks all operations

**Weaknesses:**
- ❌ **Single document only** - No automatic expansion
- ❌ **No relationship tracking** - Agent must know what to query
- ❌ **No context restoration** - Can't easily resume with same state
- ❌ **Limited provenance** - Know what was read, not why it was chosen

---

## The Memory Algorithm: Step by Step

### What Happens on Each Agent Turn

```
┌─────────────────────────────────────────────────────────────┐
│ TURN N: User says "Dracula enters the castle"              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 1. STORYTELLER: Start generation                           │
│    - messages: [...history, {"role": "user", "content": ...}]
│    - tools: [query_kb, query_prompts]                      │
│    - stream: True                                           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. LLM GENERATES (streaming):                              │
│    "Dracula entered..."                                     │
│    <realizes need context>                                  │
│    <emits tool call: query_kb("characters/dracula.md")>   │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. MEMORY SYSTEM: Execute tool call                        │
│    a) get_context("characters/dracula.md")                 │
│       → intervals: [dracula.md:1-100, castle.md:50-80, ...]│
│    b) expand_context(intervals, mode="paragraph", pad=2)   │
│       → texts: ["# Dracula\nAncient vampire...", ...]     │
│    c) Track intervals for provenance                       │
│    d) Return combined text to LLM                          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. LLM CONTINUES with retrieved context:                   │
│    "...the ancient vampire entered his castle..."          │
│    <still writing>                                          │
│    <realizes need location details>                        │
│    <emits tool call: query_kb("locations/castle.md")>     │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. MEMORY SYSTEM: Execute second tool call                 │
│    (same workflow as step 3)                               │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. LLM COMPLETES:                                          │
│    "...his castle in the Carpathian mountains."            │
│    <finish_reason: "stop">                                 │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. STORYTELLER: Write metacognition log                    │
│    metacognition/storyteller/block_N.md:                   │
│    - User input: "Dracula enters the castle"              │
│    - Tool 1: query_kb(characters/dracula.md) → 500 chars  │
│    - Tool 2: query_kb(locations/castle.md) → 300 chars    │
│    - Intervals used: [saved to context_pack.yaml]         │
│    - Output: "Dracula entered..."                          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 8. ARCHIVIST: Process story block                          │
│    a) Write story to sessions/session_1_block_N.md         │
│    b) Extract facts with LLM                               │
│    c) Update KB: kb/characters/dracula.md (if needed)      │
│    d) Write metacognition log                              │
│    e) Add to pending_blocks[]                              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 9. CHECK BATCH SIZE: len(pending_blocks) >= 5?            │
│    If yes → COMMIT:                                         │
│    - Story files (sessions/)                               │
│    - KB updates (kb/)                                      │
│    - Metacognition logs (metacognition/)                   │
│    - Commit message: "Story batch: blocks N to N+4"       │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Innovation: Context is Dynamic, Not Static

### Traditional Approach (MechaWiki currently)

```python
# Before generation: Load everything needed
context = []
context.append(read_article("dracula.md"))
context.append(read_article("castle.md"))
context.append(read_article("transylvania.md"))
# Problem: How do you know what to load?

# Generate with static context
messages = [
    {"role": "system", "content": system_prompt + "\n\n" + "\n\n".join(context)},
    {"role": "user", "content": user_input}
]
response = llm.completion(messages=messages)
```

**Problems:**
1. **Pre-selection** - Must guess what's needed before generation
2. **All or nothing** - Either load too much (context overflow) or too little (missing info)
3. **No adaptation** - Can't react to what LLM needs mid-generation
4. **Redundancy** - Same context loaded every turn even if not used

### AgenticMemory Approach (Dynamic)

```python
# During generation: Query as needed
tools = [query_kb_tool, query_prompts_tool]

response = llm.completion(
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ],
    tools=tools,
    stream=True
)

# LLM decides what to query, when to query it
# memtool returns rich, expanded context
# Process continues with retrieved info
```

**Benefits:**
1. **Just-in-time** - Load exactly what's needed when it's needed
2. **Adaptive** - LLM decides what context to fetch
3. **Rich expansion** - Get related content automatically
4. **Provenance** - Track exactly what was used

---

## The Full Memory Lifecycle

### Phase 1: Initial Creation

```
User writes story → Archivist extracts facts → KB grows

kb/
├── characters/
│   ├── dracula.md         (created turn 1)
│   ├── jonathan.md        (created turn 3)
│   └── mina.md            (created turn 5)
├── locations/
│   └── castle.md          (created turn 1)
└── events/
    └── arrival.md         (created turn 2)
```

### Phase 2: Context Retrieval (Any Turn)

```
User: "Jonathan explores the castle"

Storyteller queries: query_kb("characters/jonathan.md")

memtool returns intervals:
- characters/jonathan.md:1-100      (requested)
- characters/dracula.md:50-80       (related character)
- locations/castle.md:1-150         (mentioned location)
- events/arrival.md:20-40           (recent event)

Why these intervals?
- jonathan.md links to dracula.md (git blame shows co-editing)
- jonathan.md mentions "castle" (cross-reference)
- arrival.md involves both characters (temporal relationship)
```

### Phase 3: Workspace Snapshot (Every Turn)

```
After turn completes, snapshot workspace:

MetaCog/Workspace/sessions/session_1/blocks/0042/
├── storyteller/
│   ├── reasoning.md              # "User asked about Jonathan exploring..."
│   ├── tool_calls.jsonl          # {"tool": "query_kb", "doc": "jonathan.md", ...}
│   └── context_pack.yaml         # intervals: [jonathan.md:1-100, castle.md:1-150, ...]
└── archivist/
    ├── reasoning.md              # "Extracted: Jonathan's fear, castle layout..."
    ├── tool_calls.jsonl          # KB edits logged
    └── applied_diffs.md          # "Updated jonathan.md: added fear description"
```

### Phase 4: Batch Commit (Every N Turns)

```
After 5 turns, commit everything:

git commit -m "Story batch: Session 1 blocks 40-44

Processed 5 story blocks with KB updates.

Changes:
- sessions/: Added 5 story blocks
- kb/characters/: Updated jonathan.md, mina.md
- kb/locations/: Updated castle.md
- metacognition/: Added 10 logs (storyteller + archivist)
"
```

---

## Why This Matters: The Algorithm's Value

### 1. **Scalability**
- Works with 10 KB articles or 10,000 KB articles
- Agent only loads what it needs, when it needs it
- Context window stays manageable

### 2. **Consistency**
- Agent always has access to full KB via queries
- Can't "forget" important details (they're queryable)
- Reduces hallucinations (grounds responses in KB)

### 3. **Adaptability**
- LLM decides what context is relevant (not hardcoded)
- Can explore tangents (query unexpected articles)
- Responds to user questions about any KB topic

### 4. **Auditability**
- Every decision traced to specific KB intervals
- "Why did agent say X?" → Check context_pack.yaml
- Reproducible (can replay with same intervals)

### 5. **Collaboration**
- Multiple agents can query same KB
- KB is single source of truth
- Archivist maintains quality over time

---

## Implementation Path for MechaWiki

### Option A: Lightweight (No memtool)

Implement **query-on-demand** pattern without memtool:

```python
class SmartMemoryInterface:
    """Lightweight alternative to memtool."""
    
    def query_article(self, article_name: str) -> str:
        """Get article + linked articles."""
        # 1. Read requested article
        article_text = read_article(article_name)
        
        # 2. Extract links from article (markdown links)
        links = extract_markdown_links(article_text)
        
        # 3. Read linked articles
        linked_texts = [read_article(link) for link in links[:5]]  # Limit 5
        
        # 4. Combine
        return f"# {article_name}\n{article_text}\n\n## Related\n" + "\n\n".join(linked_texts)
    
    def query_recent(self, article_name: str) -> str:
        """Get article + recently edited related articles."""
        # 1. Get article
        article_text = read_article(article_name)
        
        # 2. Use git log to find recently co-edited articles
        recent_related = git_log_related(article_name, limit=5)
        
        # 3. Read those articles
        recent_texts = [read_article(name) for name in recent_related]
        
        # 4. Combine
        return f"# {article_name}\n{article_text}\n\n## Recently Related\n" + "\n\n".join(recent_texts)
```

**Benefits:**
- No external dependencies
- Use existing git/filesystem
- Simpler setup

**Limitations:**
- No sophisticated graph traversal
- Manual link detection
- Less sophisticated than memtool

### Option B: Full Integration (With memtool)

Install memtool and adopt full pattern:

```python
from memtool.client import MemtoolClient

class DualMemoryInterface:
    """Full memtool integration."""
    
    def __init__(self, kb_port=18861, prompts_port=18862):
        self.kb_client = MemtoolClient(port=kb_port)
        self.prompts_client = MemtoolClient(port=prompts_port)
        self.kb_context_intervals = []
        
    def query_kb(self, document: str) -> str:
        # Full memtool pattern
        context = self.kb_client.get_context(document, 1, 999999)
        expansion = self.kb_client.expand_context(
            context["intervals"],
            mode="paragraph",
            pad=2
        )
        texts = [s["preview"] for s in expansion["snippets"]]
        self.kb_context_intervals.extend(context["intervals"])
        return "\n\n".join(texts)
```

**Benefits:**
- Full power of memtool (graph traversal, smart expansion)
- Proven system (used in production)
- Complete provenance tracking

**Limitations:**
- Requires memtool servers running
- More complex setup
- Need to learn memtool API

---

## Recommendation

**Start with Option A (Lightweight)** to validate the pattern, then **migrate to Option B (Full)** if the benefits are clear.

The core insight isn't the technology (memtool vs filesystem) - it's the **algorithmic pattern**:

1. **Tools for memory queries** (not static context loading)
2. **Just-in-time retrieval** (during generation, not before)
3. **Multi-document expansion** (related content, not just exact match)
4. **Provenance tracking** (log what was retrieved)
5. **Workspace snapshots** (full audit trail)

You can implement this pattern with or without memtool. The pattern is what matters.

---

## Next Steps

1. **Study the pattern** - Understand dynamic query-on-demand
2. **Prototype lightweight version** - SmartMemoryInterface with link following
3. **Add to one agent** - Try with ReaderAgent first
4. **Track intervals** - Log what context was used
5. **Measure impact** - Does it improve consistency? Reduce hallucinations?
6. **Consider memtool** - If lightweight version proves valuable, upgrade to full system

The algorithm is the innovation. The tools are just implementation details.

---

**Hunt with Purpose! The working code is the memory pattern itself.** 🏰⚔️

