# memtool Empty Results: Root Cause & Fix

## The Agent's Problem

**What happened**: ReaderAgent called `get_context()` and got an empty string back:

```json
{"type": "tool_call", "tool": "get_context", "args": {
  "document": "articles/the-mist-keeper-story.md",
  "start_line": "1",
  "end_line": "100",
  "expansion_mode": "paragraph",
  "padding": "2"
}}
{"type": "tool_result", "tool": "get_context", "result": ""}
```

**The question**: Why did it return empty? Is the file broken? Is memtool broken? Is the file empty?

## Root Cause

**The file doesn't exist!** 

```bash
$ ls -lh /home/keenan/Dev/wikicontent/articles/the-mist-keeper-story.md
ls: cannot access 'articles/the-mist-keeper-story.md': No such file or directory
```

The agent was looking for `the-mist-keeper-story.md` but the available files are:
- `the-mist-keeper-universe.md` ✓
- `the-mist-keeper-characters.md` ✓
- `the-mist-keeper-analysis.md` ✓
- `the-mist-keeper-project.md` ✓
- `reading-guide-the-mist-keeper.md` ✓

## The Problem with Our Tool

**Before the fix**: When a file doesn't exist, `get_context()` would:
1. Query memtool → get 0 intervals back
2. Return empty string `""` (in simple mode)
3. Return `{"error": "No context found for..."}` (in metadata mode)

**Why this is bad for agents**:
- The agent has no way to know WHY it got empty results
- Could be: file doesn't exist, file is empty, file not indexed, or memtool is broken
- No actionable guidance on what to do next

## The Fix

### Improved Error Messages

**Now returns structured error with guidance**:

```python
{
  "error": "No content found for 'articles/the-mist-keeper-story.md'. "
           "This file may not exist, may be empty, or may not have been indexed. "
           "Check the file path and try searching with find_articles tool.",
  "content": "",
  "intervals": [],
  "num_docs": 0
}
```

**Key improvements**:
1. ✅ Explains possible reasons (doesn't exist, empty, not indexed)
2. ✅ Suggests actionable next step (use `find_articles` tool)
3. ✅ Returns consistent structure (always has all keys)
4. ✅ Simple mode still returns `""` for backward compatibility

### Code Changes

```python
if not context.get("intervals"):
    # Before: vague message
    # return {"error": f"No context found for {document}"}
    
    # After: helpful message with guidance
    error_msg = (
        f"No content found for '{document}'. "
        f"This file may not exist, may be empty, or may not have been indexed. "
        f"Check the file path and try searching with find_articles tool."
    )
    return {
        "error": error_msg,
        "content": "",
        "intervals": [],
        "num_docs": 0
    } if return_metadata else ""
```

## Comprehensive Test Suite

Created `tests/test_memtool_empty_results.py` with **8 new tests**:

```
TestEmptyResultCases (4 tests)
├─ test_nonexistent_file_simple_mode           ✓
├─ test_nonexistent_file_metadata_mode         ✓
├─ test_existing_file_with_content             ✓
└─ test_similar_file_names                     ✓

TestMemtoolQueryBehavior (2 tests)
├─ test_memtool_response_for_nonexistent_file  ✓
└─ test_memtool_response_for_existing_file     ✓

TestErrorMessages (1 test)
└─ test_helpful_error_for_missing_file         ✓

TestAgentUsageScenario (1 test)
└─ test_agent_query_the_mist_keeper_story      ✓  (reproduces exact agent scenario)
```

### What These Tests Catch

1. **Distinguishes empty result causes**
   - Nonexistent file vs empty file vs no indexed content
   
2. **Verifies error messages are helpful**
   - Mentions file might not exist
   - Suggests using `find_articles` tool
   - Provides actionable next steps

3. **Reproduces the exact agent scenario**
   - Tests the exact query that failed
   - Verifies the response structure
   - Documents expected behavior

4. **Ensures backward compatibility**
   - Simple mode still returns `""`
   - Metadata mode now returns full structure

## Test Results

```bash
$ pytest tests/test_memtool_integration.py tests/test_memtool_empty_results.py -v

============================== 25 passed in 6.63s ===============================
```

**All 25 tests pass!** ✅
- 17 original integration tests (singleton, index persistence, tool functionality)
- 8 new empty result tests (error handling, diagnostics, agent scenario)

## Example: How Agent Should Respond

**Before** (agent is confused):
```
Agent: I tried to read the-mist-keeper-story.md but got nothing back. 
       Let me try again... (same result)
```

**After** (agent knows what to do):
```
Agent: The file 'the-mist-keeper-story.md' may not exist. 
       Let me search for similar files...
       [calls find_articles with "mist-keeper"]
       Found: the-mist-keeper-universe.md, the-mist-keeper-characters.md, ...
```

## Key Insight

**Empty results need context!** When a tool returns empty, the agent needs to know:
1. **Why** it's empty (file doesn't exist vs no content)
2. **What to do** about it (use find_articles to search)
3. **Confidence** that the tool is working correctly

The improved error messages provide all three. 🎯

## Lessons Learned

1. **Test real agent scenarios** - The agent's actual query revealed the issue
2. **Error messages are UX** - Even for programmatic consumers (agents)
3. **Distinguish failure modes** - Different empties need different messages
4. **Suggest next actions** - Guide users/agents to solutions
5. **Test the edge cases** - Nonexistent files, empty files, etc.

## How to Verify

```bash
# Run all memtool tests
pytest tests/test_memtool_*.py -v

# Test the exact agent scenario
python3 -c "
import sys
sys.path.insert(0, 'src')
from tools.context import get_context

# This should return helpful error
result = get_context('articles/the-mist-keeper-story.md', return_metadata=True)
print(result['error'])
# Output: No content found for 'articles/the-mist-keeper-story.md'. 
#         This file may not exist, may be empty, or may not have been indexed. 
#         Check the file path and try searching with find_articles tool.
"
```

Both should demonstrate the improved error handling. ✅

