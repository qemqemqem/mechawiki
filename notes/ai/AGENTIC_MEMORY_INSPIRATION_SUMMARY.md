# AgenticMemory Inspiration: Quick Summary

**Date:** 2025-11-09  
**See also:** [Full Comparison Document](./COMPARISON_AGENTIC_MEMORY.md)

---

## TL;DR: What Can We Learn?

Your friend's **AgenticMemory** project has several features that could level up MechaWiki's capabilities, especially around **memory management**, **provenance tracking**, and **prompt experimentation**.

---

## 🎯 Top 5 Features to Consider

### 1. ⭐⭐⭐ Dual Memory System (`memtool`)

**What it is:**  
Two RPC servers (KB + prompts) that provide interval-based context retrieval with automatic expansion.

**Why it matters:**
- Get related context automatically (not just exact file matches)
- Track what KB entries influenced each decision (provenance)
- Navigate knowledge graph during generation
- Save/restore context between sessions

**Example:**
```python
# Instead of reading files directly
article = read_file("characters/dracula.md")

# Use memtool for context expansion
context = memory.query_kb("characters/dracula.md")
# Returns: dracula.md + related locations + recent events + linked articles
```

**Effort:** Medium (2-3 days)  
**Impact:** 🔥 High - Much better context handling

---

### 2. ⭐⭐ Metacognition Logs

**What it is:**  
Structured markdown files showing agent reasoning traces after each turn.

**Why it matters:**
- **Debug agent decisions** - See exactly what context was used
- **Improve prompts** - Understand where agent gets confused
- **Audit trail** - Human-readable reasoning logs
- **Share with users** - Let them peek inside agent's mind

**Example:**
```markdown
# ReaderAgent Thoughts - 2025-11-09T10:30:00

Turn: 42
Action: advance(5000 words)

## Tool Calls
[Tool: advance(5000)]
[Search: "main characters"]
[Result: 15 articles found]

## Context Used
- articles/dracula.md (500 chars)
- articles/castle.md (300 chars)

## Decision
Created new article: "Count Dracula's Castle"
Reasoning: First detailed description of location, warrants dedicated article.
```

**Effort:** Low (1 day)  
**Impact:** Medium - Better debugging and transparency

---

### 3. ⭐⭐ Prompts as Git Submodule (A/B Testing)

**What it is:**  
Agent prompts live in a separate git repo, pulled into sessions as a submodule.

**Why it matters:**
- **A/B test prompts** - Try different prompt versions side-by-side
- **Centralized prompt library** - Share prompts across projects
- **Version control** - Track which prompt version produced which results
- **Rollback easily** - Switch prompt versions per session

**Workflow:**
```bash
# Create prompts repo (once)
git init agent-prompts/
# Add prompts for each agent type

# In each session
cd data/sessions/my_session/
git submodule add https://github.com/you/agent-prompts prompts

# Try different prompt versions
cd prompts/
git checkout experiment-concise-style  # Test concise writing
# vs
git checkout experiment-detailed-style # Test detailed writing

# Compare results across sessions!
```

**Effort:** Medium (2 days)  
**Impact:** 🔥 High - Enables systematic prompt experimentation

---

### 4. ⭐ Batch Commit Strategy

**What it is:**  
Commit every N operations (e.g., 5) instead of after every single change.

**Why it matters:**
- **Cleaner git history** - Logical groups instead of 100 tiny commits
- **Atomic operations** - Related changes committed together
- **Better performance** - Fewer git operations
- **Easier to review** - One commit = one batch of work

**Before:**
```
commit abc123: Created article dracula.md
commit def456: Updated article castle.md
commit ghi789: Created article transylvania.md
commit jkl012: Updated article dracula.md
commit mno345: Created image dracula.png
```

**After:**
```
commit xyz999: ReaderAgent batch: turns 1-5

Processed 5 story chunks:
- Created 3 articles (dracula.md, castle.md, transylvania.md)
- Updated 1 article (dracula.md)
- Generated 1 image (dracula.png)
```

**Effort:** Low (1 day)  
**Impact:** Medium - Much cleaner git history

---

### 5. ⭐ Archivist Agent (KB Maintenance)

**What it is:**  
Dedicated agent that periodically reviews the KB and maintains quality/consistency.

**Why it matters:**
- **Find duplicates** - "Dracula" vs "Count Dracula" → merge
- **Detect contradictions** - "Dracula has grey eyes" vs "Dracula has red eyes" → flag
- **Update links** - Add missing cross-references
- **Enhance quality** - Improve article structure over time

**Workflow:**
```
ReaderAgent advances 10 times → ArchivistAgent reviews KB → Commits improvements → Repeat
```

**What it does:**
1. Scans recent articles for quality issues
2. Uses LLM to analyze consistency
3. Suggests or makes improvements
4. Commits batch of fixes

**Effort:** Medium (3-4 days)  
**Impact:** 🔥 High - KB quality improves over time instead of degrading

---

## 🚀 Recommended Implementation Order

### Phase 1: Quick Wins (Week 1)
1. **Metacognition logs** (1 day) - Easy, high value for debugging
2. **Batch commits** (1 day) - Easy, cleaner git history

### Phase 2: Memory Upgrade (Week 2-3)
3. **Integrate memtool** (2-3 days) - Research + integrate dual memory interface
4. **Update agent tools** (1-2 days) - Replace direct file reads with `query_kb()`

### Phase 3: Advanced Features (Week 4+)
5. **Prompts as submodule** (2 days) - Enable A/B testing
6. **Archivist agent** (3-4 days) - KB maintenance
7. **UI enhancements** (ongoing) - Show metacognition, prompt versions, etc.

---

## 🎨 Design Philosophy Differences

### AgenticMemory: "Git is the Source of Truth"
- Everything versioned, full audit trail
- Batch commits create "audit bundles"
- Prompts as files (git submodules for A/B testing)
- Minimal stack (Python + LiteLLM + Git + memtool)
- Focus: **Provenance and reproducibility**

### MechaWiki: "Real-Time Observability"
- See everything as it happens in web UI
- Event-driven architecture (agents yield events)
- Multiple agents running concurrently
- Pause/resume/archive agent lifecycle
- Focus: **Control and experimentation**

**They're complementary!** AgenticMemory has better memory and provenance, MechaWiki has better UX and observability. We can combine the best of both.

---

## 🏆 What Makes MechaWiki Unique

Don't lose these differentiators:

1. ✅ **Web UI with real-time monitoring** (AgenticMemory is CLI-only)
2. ✅ **Multiple agent types** (Reader, Writer, Interactive vs just Storyteller/Archivist)
3. ✅ **Pause/resume agents** (AgenticMemory has no lifecycle control)
4. ✅ **File operations feed** (See all changes across agents)
5. ✅ **Event-driven architecture** (Clean separation of logic and I/O)
6. ✅ **Session management** (Multiple sessions in one project)
7. ✅ **Cost tracking** (Per-agent token usage)
8. ✅ **RPG theme** (Fun, engaging aesthetic)

---

## 📊 Effort vs Impact Matrix

```
High Impact │
            │  ⭐ Dual Memory     ⭐ Archivist
            │  ⭐ Prompts as      
            │     Submodule       
            │                     ⭐ Metacognition
Medium      │                     ⭐ Batch Commits
Impact      │                     
            │
Low Impact  │  
            │
            └─────────────────────────────────────
              Low Effort      Medium Effort    High Effort
```

---

## 🎯 Final Recommendation

**Start with quick wins:**
1. Add metacognition logs (1 day) - immediate debugging value
2. Implement batch commits (1 day) - cleaner git history

**Then level up memory:**
3. Integrate memtool (3-4 days) - significantly better context handling

**Then enable experimentation:**
4. Prompts as submodule (2 days) - A/B test prompt strategies
5. Add Archivist agent (3-4 days) - automated KB quality

**Total time investment:** 2-3 weeks for all features  
**Expected value:** 🔥 Significant improvement in agent intelligence and maintainability

---

## 📚 Resources

- **Full Comparison:** [COMPARISON_AGENTIC_MEMORY.md](./COMPARISON_AGENTIC_MEMORY.md)
- **AgenticMemory Location:** `~/Dev/AgenticMemory`
- **Key Files to Study:**
  - `agentic_memory/memory.py` - Dual memory interface
  - `agentic_memory/agents/storyteller.py` - Dynamic KB queries during generation
  - `agentic_memory/agents/archivist.py` - KB maintenance and batch commits
  - `ARCHITECTURE.md` - Design philosophy and patterns

---

**Hunt with Purpose!** Let's bring these battle-tested patterns into MechaWiki. 🏰⚔️

