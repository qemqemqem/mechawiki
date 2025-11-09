# The Real Difference: Multi-Document Context Expansion

**Date:** 2025-11-09  
**Key Insight:** Both systems have "tools during generation" - but HOW the tools work is fundamentally different.

---

## You're Right! MechaWiki Already Does This:

```python
# MechaWiki BaseAgent
response = litellm.completion(
    model=self.model,
    messages=self.messages,
    tools=self.tools,  # ✅ Tools available during generation
    stream=True
)
```

Your agents CAN and DO call tools mid-generation:
- ✅ `read_article(article_name)` 
- ✅ `find_articles(search_string)`
- ✅ `read_file(filepath, start_line, end_line)`
- ✅ `search_content(query)`

**So what's the actual difference?**

---

## The Difference: Single-Doc vs Multi-Doc Expansion

### MechaWiki's Current Pattern (Explicit, Single-Document)

```python
# Agent thinks: "I need Dracula info"
tool_call("read_article", {"article_name": "dracula.md"})

# System returns:
{
    "content": "# Count Dracula\n\nAncient vampire...",  # ONLY dracula.md
    "file_path": "articles/dracula.md"
}

# Agent thinks: "I also need the castle info"
tool_call("read_article", {"article_name": "castle.md"})

# System returns:
{
    "content": "# Dracula's Castle\n\nLocated in Transylvania...",  # ONLY castle.md
    "file_path": "articles/castle.md"
}

# Result: Agent must know what to query and make multiple calls
```

**Characteristics:**
- ✅ **Explicit**: Agent decides what to read
- ✅ **Precise**: Gets exactly what it asks for
- ❌ **Single-document**: One file per query
- ❌ **Manual linking**: Agent must figure out related content
- ❌ **Multiple round-trips**: Separate tool call for each file

### AgenticMemory's Pattern (Automatic, Multi-Document)

```python
# Agent thinks: "I need Dracula info"
tool_call("query_kb", {"document": "characters/dracula.md"})

# System workflow:
1. memtool.get_context("characters/dracula.md")
   # Returns intervals across MULTIPLE documents:
   # - characters/dracula.md:1-100      (requested)
   # - locations/castle.md:1-80         (linked in dracula.md)
   # - events/arrival.md:50-100         (mentions Dracula)
   # - characters/jonathan.md:20-40     (co-edited with dracula.md)

2. memtool.expand_context(intervals, mode="paragraph", pad=2)
   # Expands to natural boundaries with padding

3. Returns combined text:
"""
# Count Dracula
Ancient vampire from Transylvania...

# Related: Dracula's Castle
The castle is located in the Carpathian mountains...

# Related: Jonathan Harker's Arrival
When Jonathan arrived at the castle, Dracula greeted him...
"""

# Result: Agent gets rich multi-document context in ONE call
```

**Characteristics:**
- ✅ **Automatic**: System finds related content
- ✅ **Multi-document**: Gets content from multiple files
- ✅ **Graph traversal**: Follows links, git history, co-occurrence
- ✅ **Smart expansion**: Paragraph boundaries, context padding
- ✅ **Single call**: Everything in one query

---

## Concrete Example: "Gandalf enters Rivendell"

### MechaWiki Flow (Current)

```
Agent: "I need Gandalf info"
→ find_articles("gandalf")
← ["gandalf.md"]

Agent: "Read it"
→ read_article("gandalf.md")
← "# Gandalf\nGrey wizard..."

Agent: "I need Rivendell info too"
→ find_articles("rivendell")
← ["rivendell.md"]

Agent: "Read it"
→ read_article("rivendell.md")
← "# Rivendell\nElven haven..."

Agent: "Now I can write"
→ Generates: "Gandalf entered the elven haven of Rivendell..."

Total tool calls: 4
Documents retrieved: 2 (explicitly requested)
```

### AgenticMemory Flow (Automatic Expansion)

```
Agent: "I need Gandalf info"
→ query_kb("characters/gandalf.md")

[System automatically]:
- Finds gandalf.md (requested)
- Finds rivendell.md (gandalf.md links to it)
- Finds council-of-elrond.md (gandalf was there)
- Finds grey-wizards.md (category match)
- Expands to paragraph boundaries
- Adds 2 paragraphs padding for context

← "# Gandalf\nGrey wizard of great power...\n\n# Rivendell\nElven haven where Gandalf often visits...\n\n# Council of Elrond\nGandalf spoke at the council..."

Agent: "Perfect, I have everything"
→ Generates: "Gandalf the Grey entered Rivendell, where he had spoken at the Council many times before..."

Total tool calls: 1
Documents retrieved: 4 (automatically expanded)
```

---

## The Algorithm Differences

### 1. **Discovery Mechanism**

**MechaWiki (Explicit):**
```python
# Agent must explicitly search/find
find_articles("wizard") → ["gandalf.md", "saruman.md"]
# Then decide which to read
read_article("gandalf.md")
```

**AgenticMemory (Automatic):**
```python
# System automatically finds related content
query_kb("gandalf.md") → Returns gandalf.md + all related docs
# Uses:
# - Markdown links in gandalf.md
# - Git blame (files edited together)
# - Cross-references
# - Temporal relationships
```

---

### 2. **Content Expansion**

**MechaWiki (Whole File or Line Range):**
```python
# Get whole file
read_article("dracula.md") → Entire file content

# OR get specific lines
read_file("articles/dracula.md", start_line=50, end_line=100)
→ Lines 50-100 exactly (might cut mid-sentence)
```

**AgenticMemory (Smart Boundaries):**
```python
# Request lines 50-100
query_kb("dracula.md", start=50, end=100)

# System expands to natural boundaries:
# - Finds paragraph containing line 50 → starts at line 45
# - Finds paragraph containing line 100 → ends at line 110
# - Adds padding (2 paragraphs before/after) → lines 30-125
# - Returns clean, readable text
```

---

### 3. **Relationship Discovery**

**MechaWiki:**
```python
# Agent must know/discover relationships
# "I read dracula.md, it mentions a castle, so I should search for castle"
read_article("dracula.md")
# Agent sees: "...his castle in Transylvania..."
# Agent decides: "I need castle info"
find_articles("castle")
read_article("castle.md")
```

**AgenticMemory:**
```python
# System automatically follows relationships
query_kb("dracula.md")
# memtool detects:
# - dracula.md contains [castle link](locations/castle.md)
# - dracula.md and castle.md were edited in same git commit
# - Both mention "Transylvania"
# → Automatically includes castle.md in response
```

---

### 4. **Provenance Tracking**

**MechaWiki (File-Level):**
```jsonl
{"type": "tool_call", "tool": "read_article", "args": {"article_name": "dracula.md"}}
{"type": "tool_result", "content": "...", "file_path": "articles/dracula.md"}
```
- Tracks: "Agent read dracula.md"
- Doesn't track: Which parts were actually used

**AgenticMemory (Interval-Level):**
```yaml
# context_pack.yaml
intervals:
  - doc: "characters/dracula.md"
    start: 1
    end: 50
    reason: "directly_requested"
  - doc: "locations/castle.md" 
    start: 20
    end: 80
    reason: "linked_from_dracula"
  - doc: "events/arrival.md"
    start: 100
    end: 150
    reason: "co_edited_with_dracula"
```
- Tracks: "Agent read lines 1-50 of dracula.md, lines 20-80 of castle.md, etc."
- Can reproduce: Use same intervals to get same context

---

## Visual Comparison

### MechaWiki: Agent-Driven Queries

```
┌──────────────┐
│    Agent     │  "I need Dracula info"
└──────┬───────┘
       │ query
       ↓
┌──────────────┐
│ read_article │  Returns: dracula.md content
│  (one file)  │
└──────────────┘

Agent: "I also need castle info"

┌──────────────┐
│ read_article │  Returns: castle.md content
│  (one file)  │
└──────────────┘

Agent: "And arrival event"

┌──────────────┐
│ read_article │  Returns: arrival.md content
│  (one file)  │
└──────────────┘

Total: 3 tool calls, 3 files, agent decides what's related
```

### AgenticMemory: System-Driven Expansion

```
┌──────────────┐
│    Agent     │  "I need Dracula info"
└──────┬───────┘
       │ query
       ↓
┌──────────────────────────────────┐
│         query_kb                 │
│  (multi-doc with expansion)      │
│                                  │
│  1. get_context("dracula.md")   │
│     → finds related docs         │
│  2. expand_context(intervals)    │
│     → smart boundaries           │
│  3. track intervals              │
│     → provenance                 │
│  4. return combined text         │
│                                  │
│  Returns:                        │
│  - dracula.md (requested)        │
│  - castle.md (linked)            │
│  - arrival.md (co-edited)        │
│  - transylvania.md (mentioned)   │
└──────────────────────────────────┘

Total: 1 tool call, 4 files, system decides what's related
```

---

## Why This Matters

### Scenario: "Tell me about Gandalf's staff"

**MechaWiki:**
```
Agent: find_articles("gandalf") → ["gandalf.md"]
Agent: read_article("gandalf.md") 
← "Gandalf is a wizard... has a staff..."

Agent: find_articles("staff")  → ["staff-of-gandalf.md"]
Agent: read_article("staff-of-gandalf.md")
← "Gandalf's staff is an ancient artifact..."

Agent: Generates response using both
```
**Result:** Works, but agent must know to search for "staff" separately

**AgenticMemory:**
```
Agent: query_kb("gandalf.md")

[System automatically includes]:
- gandalf.md (requested)
- staff-of-gandalf.md (linked from gandalf.md)
- istari.md (gandalf is an istari, staffs are mentioned)
- saruman.md (also has a staff, comparison context)

Agent: Generates response with rich context
```
**Result:** Agent gets comprehensive context without knowing all the pieces

---

## The Core Algorithmic Innovation

### It's Not:
- ❌ Tools during generation (MechaWiki has this)
- ❌ File reading (MechaWiki has this)
- ❌ Search (MechaWiki has this)

### It IS:
- ✅ **Automatic multi-document expansion** (not single file)
- ✅ **Graph traversal** (follow links, git history, co-occurrence)
- ✅ **Smart boundary expansion** (paragraphs, not arbitrary lines)
- ✅ **Interval-level provenance** (not just file-level)
- ✅ **Context packing** (related docs in one query)

---

## Can MechaWiki Achieve This?

**YES!** Two paths:

### Path A: Enhance Existing Tools (No memtool)

```python
def read_article_with_links(article_name: str) -> dict:
    """
    Read article + automatically include linked articles.
    
    Returns combined content from:
    1. Requested article
    2. All articles linked via [text](other-article.md)
    3. Recently co-edited articles (from git log)
    """
    # 1. Read main article
    main_content = read_article(article_name)
    
    # 2. Extract markdown links
    links = extract_markdown_links(main_content["content"])
    
    # 3. Read linked articles (limit to 5)
    linked_content = []
    for link in links[:5]:
        linked_article = read_article(link)
        if "content" in linked_article:
            linked_content.append({
                "source": link,
                "content": linked_article["content"][:500]  # Preview
            })
    
    # 4. Find co-edited articles (git blame/log)
    co_edited = find_co_edited_articles(article_name, limit=3)
    for article in co_edited:
        co_content = read_article(article)
        if "content" in co_content:
            linked_content.append({
                "source": article,
                "content": co_content["content"][:500],
                "reason": "recently_edited_together"
            })
    
    # 5. Combine
    combined = {
        "main": main_content,
        "related": linked_content,
        "total_docs": 1 + len(linked_content)
    }
    
    return combined
```

**Benefits:**
- ✅ Multi-document in one call
- ✅ Automatic link following
- ✅ Git-based relationships
- ✅ No external dependencies

**Limitations:**
- ❌ No sophisticated graph traversal
- ❌ No smart boundary expansion
- ❌ Manual implementation of relationships

---

### Path B: Integrate memtool (Full Solution)

```python
from memtool.client import MemtoolClient

class DualMemoryInterface:
    def __init__(self):
        self.kb_client = MemtoolClient(port=18861)
        
    def query_kb(self, document: str) -> str:
        # Full memtool pattern
        context = self.kb_client.get_context(document, 1, 999999)
        expansion = self.kb_client.expand_context(
            context["intervals"],
            mode="paragraph",
            pad=2
        )
        return "\n\n".join([s["preview"] for s in expansion["snippets"]])
```

**Benefits:**
- ✅ Full graph traversal
- ✅ Smart boundary expansion
- ✅ Interval-level provenance
- ✅ Battle-tested system

**Costs:**
- ❌ Requires memtool servers
- ❌ More setup complexity
- ❌ Learning curve

---

## Recommendation

**Start with Path A (Enhanced Tools) to validate the value:**

1. Create `read_article_with_related()` that includes linked articles
2. Add git-based co-editing detection
3. Track which articles were included (provenance)
4. Measure impact on agent quality

**If valuable, upgrade to Path B (memtool):**

1. Install memtool
2. Start memtool server alongside Flask
3. Migrate tools to use memtool
4. Get full graph traversal and provenance

---

## Key Takeaway

**You were right** - MechaWiki already has "tools during generation."

**The difference** is HOW the tools work:
- **MechaWiki**: One file per call, agent-driven discovery
- **AgenticMemory**: Multi-doc per call, system-driven expansion

**The innovation** is the **automatic multi-document context expansion algorithm**, not just tool availability.

You can implement this pattern with OR without memtool - it's the algorithmic approach that matters.

---

**The working code is understanding the difference between explicit single-doc queries vs automatic multi-doc expansion!** 🏰⚔️

