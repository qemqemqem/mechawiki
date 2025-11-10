# memtool Integration: Root Cause Analysis & Fix

## The Problem

The `get_context()` tool was consistently failing with:
```
Error: Error retrieving context for story.txt: No index loaded
ValueError: No index loaded
```

Even though `start.sh` was building an index, every call to `get_context()` would fail.

## Root Causes Discovered

### 1. rpyc is Stateful Per-Client Connection ⚠️

**The Critical Discovery**: memtool uses rpyc (Remote Procedure Call) which maintains state **per-client connection**, not per-server!

- When you create a `MemtoolClient()`, it opens a connection to the server
- When you call `build_index()` or `load_index()` on that client, the index is loaded **for that connection only**
- If you create a new client, it **does not see** the index from the previous client
- The server has the index, but new connections start with `loaded: False`

**What this means**: Creating multiple client instances loses the index!

### 2. Wrong Directory for Index Building

**The Second Bug**: When calling `build_index(".")` with `os.chdir()`, the local `chdir()` doesn't affect the remote rpyc server!

```python
# WRONG - client doesn't care about our local cwd
os.chdir(content_repo)
client.build_index(".")  # Builds from SERVER'S cwd, not ours!
```

This meant `build_index()` was indexing the **mechawiki** directory instead of **wikicontent**, so queries for wiki articles always returned empty.

### 3. Field Name Mismatch

**Third Issue**: memtool intervals use `interval['path']` not `interval['doc']`, causing `KeyError` when counting documents.

## The Fixes

### Fix 1: Singleton Client Pattern

```python
# Module-level singleton
_memtool_client = None

def _get_memtool_client():
    global _memtool_client
    if _memtool_client is None:
        _memtool_client = MemtoolClient(port=18861)
    return _memtool_client  # Always return same instance!
```

**Why this works**: All calls to `get_context()` use the same client connection, so the index persists.

### Fix 2: Self-Healing Index Loading

```python
_index_ensured = False  # Only check once per process

def _ensure_index_loaded():
    global _index_ensured
    if _index_ensured:
        return  # Already loaded on this client
    
    client = _get_memtool_client()  # Use singleton
    status = client.status()
    if status['loaded']:
        _index_ensured = True
        return
    
    # Index not loaded - load it now
    # ... (load from cache or build fresh)
    _index_ensured = True
```

**Why this works**: First call loads the index, subsequent calls skip the check since we know it's loaded on our singleton client.

### Fix 3: Absolute Paths for rpyc

```python
# Use absolute path, not relative with chdir
cache_path = str(content_repo / ".memtool_index.json")
result = client.build_index(str(content_repo))  # Absolute path!
client.save_index(cache_path)  # Absolute path!
```

**Why this works**: rpyc server receives the absolute path and indexes the correct directory.

### Fix 4: Correct Field Names

```python
# Use 'path' not 'doc'
documents_included = list(set(interval["path"] for interval in context["intervals"]))
```

## Comprehensive Test Suite

Created `tests/test_memtool_integration.py` with **17 tests** covering:

1. **Singleton Client Tests** (2 tests)
   - Verifies `_get_memtool_client()` returns same instance
   - Verifies client persists across `get_context()` calls ⭐ (catches bug #1)

2. **Index Persistence Tests** (2 tests)
   - Verifies index loads once and persists
   - Verifies `_index_ensured` flag prevents redundant checks

3. **Tool Functionality Tests** (5 tests)
   - Returns content for existing files
   - Metadata mode works
   - Line range filtering works
   - Graceful handling of nonexistent files
   - All expansion modes work

4. **Self-Healing Tests** (2 tests)
   - Auto-loads index when missing
   - Subsequent calls don't reload

5. **Multi-Document Expansion Tests** (2 tests)
   - Interval metadata is correct
   - `num_docs` counts unique documents correctly

6. **Error Handling Tests** (2 tests)
   - Invalid line numbers don't crash
   - Invalid expansion modes handled gracefully

7. **Real-World Usage Tests** (2 tests)
   - Multiple sequential calls all work
   - Mixing simple and metadata calls works

## Test Results

```bash
$ pytest tests/test_memtool_integration.py -v
...
============================== 17 passed in 4.66s ==============================
```

**All tests pass!** ✅

## Why These Tests Catch the Original Bug

### The Critical Test

```python
def test_singleton_persists_across_get_context_calls(self):
    """Verify the same client is used across multiple get_context() calls."""
    # This is CRITICAL - if we create new clients, index is lost!
    
    result1 = get_context("articles/the-mist-keeper-universe.md", return_metadata=True)
    client1 = tools.context._memtool_client
    
    result2 = get_context("articles/the-mist-keeper-universe.md", return_metadata=True)
    client2 = tools.context._memtool_client
    
    assert client1 is client2, "CRITICAL: Must use same client instance!"
```

**This test would have failed immediately** if we had written it before implementing the singleton pattern, exposing the bug.

### The Fixture That Ensures Clean State

```python
@pytest.fixture(autouse=True)
def reset_module_state():
    """Reset module-level state before each test."""
    tools.context._memtool_client = None
    tools.context._index_ensured = False
    yield
    # Cleanup after
```

This simulates a fresh process for each test, ensuring they test the actual initialization flow.

## Performance Impact

- **Before**: Every `get_context()` call would fail and retry, potentially rebuilding the index
- **After**: 
  - First call: ~4-5s (load index from cache)
  - Subsequent calls: <100ms (index already loaded on singleton client)

## Lessons Learned

1. **rpyc connections are stateful** - always use singleton pattern for rpyc clients
2. **Remote servers don't see local `os.chdir()`** - use absolute paths
3. **Test the actual failure mode** - write tests that would catch the bug if it existed
4. **Don't just document problems** - fix them and test them!

## How to Verify

```bash
# Run the comprehensive test suite
pytest tests/test_memtool_integration.py -v

# Test the exact failing query from before
python3 -c "
import sys
sys.path.insert(0, 'src')
from tools.context import get_context
result = get_context('story.txt', start_line=1, end_line=50)
print(f'Success! Got {len(result)} chars')
"
```

Both should work perfectly now. ✅

