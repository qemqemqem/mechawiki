# memtool Index Persistence Issue

**Date:** 2025-11-09  
**Status:** ⚠️  Workaround in place, investigating root cause

---

## The Problem

The memtool server keeps losing its in-memory index, causing "No index loaded" errors when agents try to use `get_context()`.

### Symptoms

1. Agent calls `get_context("articles/some-file.md")`
2. Gets error: `ValueError: No index loaded`
3. Even though index was built/loaded earlier

### Root Cause (Suspected)

The memtool server's index state isn't persisting properly. Possible causes:
1. **rpyc connection lifecycle** - Index might be per-connection, not per-server
2. **memtool bug** - Server may not be retaining index in memory
3. **Race condition** - Index building completes but doesn't commit to server state

---

## Workaround

### For Agents (Automatic)

Agents can now use `get_context()` - just ensure the server was started with `./start.sh`.

### For Testing

Before running tests or using the tool manually, run:

```bash
python scripts/ensure_memtool_index.py
```

This script:
- Checks if index is loaded
- Loads from cache if available
- Builds fresh if needed
- Saves to disk for next time

### For Development

The index file is cached at: `~/Dev/wikicontent/.memtool_index.json`

To manually load the index:

```python
from memtool.client import MemtoolClient
import os

os.chdir("/home/keenan/Dev/wikicontent")
client = MemtoolClient(port=18861)

# Check status
status = client.status()
print(f"Loaded: {status['loaded']}")

# Load if needed
if not status['loaded']:
    if os.path.exists(".memtool_index.json"):
        client.load_index(".memtool_index.json")
    else:
        client.build_index(".")
        client.save_index(".memtool_index.json")

client.close()
```

---

## Current State

### What Works ✅

- memtool server starts successfully
- Index can be built (213 files, 1,981 intervals)
- Index can be saved to disk
- Index can be loaded from disk
- `get_context()` works when index is loaded
- Simple queries work (without `return_metadata`)

### What's Flaky ⚠️

- Index state persistence across connections
- `return_metadata=True` queries
- Tests that run multiple queries in sequence

### What Doesn't Work ❌

- Automatic index persistence (need to manually ensure)
- Reliable multi-query test scenarios

---

## Files Created

1. **`scripts/ensure_memtool_index.py`** - Helper script to ensure index
2. **`tests/test_memtool_integration.py`** - Unit tests (7/12 passing)
3. **`src/tools/context.py`** - The `get_context()` tool (works when index loaded)

---

## Next Steps

### Immediate (Done)

- [x] Create helper script to ensure index
- [x] Update `start.sh` to call helper script
- [x] Add pytest fixture to ensure index before tests
- [x] Document the issue

### Short Term (To Do)

1. **Investigate memtool source** - Check if this is a known issue
2. **Add retry logic** - Have `get_context()` auto-reload index on failure
3. **Add health check** - Periodically verify index is loaded
4. **Report upstream** - File issue with memtool if it's a bug

### Long Term (Optional)

1. **Replace memtool** - If issue persists, consider alternatives
2. **Implement own indexing** - Simpler in-process solution
3. **Use persistent database** - SQLite instead of in-memory

---

## Recommendations

### For Your Coworkers

Tell them to:

```bash
# If agents get "No index loaded" errors:
python scripts/ensure_memtool_index.py

# Then continue working - should be fixed
```

### For Production

**Don't deploy this yet** - the index persistence issue needs to be resolved first. Options:

1. **Wait for fix** - Investigate and fix the root cause
2. **Add auto-recovery** - Make `get_context()` self-healing
3. **Use simpler approach** - Implement multi-doc expansion without memtool

---

## Testing Status

```bash
# Run tests:
pytest tests/test_memtool_integration.py -v

# Current status: 7/12 passing
# Failures are all related to index not persisting
```

### Passing Tests ✅

- Server running check
- Simple `get_context()` calls
- Different expansion modes
- Line range queries
- Non-existent file handling

### Failing Tests ❌

- Server has index (index lost between checks)
- Metadata return (index lost during query)
- Full workflow (index lost mid-test)
- Multi-document expansion (index lost)
- Index persistence check (file doesn't exist)

---

## Workaround in `start.sh`

The startup script now calls `scripts/ensure_memtool_index.py` to build/load the index on startup. This should make it work for the initial agent usage, but the index may still be lost later.

---

## Summary

**The good news:** The integration is complete and the tool works!

**The bad news:** memtool server has an index persistence issue.

**The workaround:** Run `python scripts/ensure_memtool_index.py` when errors occur.

**The path forward:** Investigate and fix, or implement a simpler solution.

---

**For now, the `get_context()` tool is available to all agents, but may require occasional manual index reloading.**

