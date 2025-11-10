# memtool Type Coercion Bug: Not a memtool Bug!

## The Error

```
TypeError: '<' not supported between instances of 'int' and 'str'
```

When the agent called:
```json
{
  "document": "articles/the-mist-keeper-project.md",
  "start_line": "1",
  "end_line": "50",
  "expansion_mode": "paragraph",
  "padding": "1"
}
```

## Initial Diagnosis: "Is this a memtool bug?"

**No!** This is **our bug** in the integration layer.

## Root Cause

### The Problem

When LLMs call tools through `litellm.completion()` with function calling:
- The LLM generates JSON: `{"start_line": "1", "end_line": "50"}`
- JSON numbers can be represented as strings
- `litellm` passes these arguments **as-is** to our Python function
- Our function signature says `start_line: int`, but Python doesn't enforce type hints at runtime!
- We passed the string `"1"` directly to memtool's `get_context()`
- memtool expects integers, so it crashes when trying to compare `interval.end < start`

### The Type Flow

```
LLM → litellm → get_context("1") → memtool.get_context("1") → CRASH!
      (JSON)    (Python str)      (expects int)             ^^^ str vs int comparison
```

## The Fix

### Code Change

Added explicit type coercion in `src/tools/context.py`:

```python
def get_context(
    document: str,
    start_line: int = 1,     # Type hint doesn't enforce at runtime!
    end_line: int = 999999,
    expansion_mode: Literal["paragraph", "line", "section"] = "paragraph",
    padding: int = 2,
    return_metadata: bool = False
) -> str | Dict[str, Any]:
    try:
        # ... 
        
        # Type coercion: LLMs often pass numbers as strings
        # memtool expects ints, so convert them
        start_line = int(start_line)  # NEW
        end_line = int(end_line)      # NEW
        padding = int(padding)        # NEW
        
        # Now safe to pass to memtool
        context = client.get_context(document, start_line, end_line)
```

### Why This Works

1. **Handles strings**: `int("1")` → `1`
2. **Handles ints**: `int(1)` → `1` (no-op)
3. **Fails fast**: `int("abc")` → `ValueError` (caught by our try/except)

## Comprehensive Test Suite

Created `tests/test_memtool_type_coercion.py` with **7 tests**:

```
TestTypeCoercion (5 tests)
├─ test_string_line_numbers_from_llm          ✓
├─ test_integer_line_numbers_still_work       ✓
├─ test_mixed_types                           ✓
├─ test_metadata_mode_with_string_args        ✓
└─ test_exact_llm_call_from_error            ✓  (reproduces exact error)

TestInvalidTypes (2 tests)
├─ test_non_numeric_string                    ✓
└─ test_negative_line_numbers                 ✓
```

### Key Test

```python
def test_exact_llm_call_from_error(self):
    """
    Reproduce the exact LLM call that caused the error.
    
    From the user's error:
    {
      "document": "articles/the-mist-keeper-project.md",
      "start_line": "1",
      "end_line": "50",
      "expansion_mode": "paragraph",
      "padding": "1"
    }
    
    This should work, not raise TypeError!
    """
    result = get_context(
        document="articles/the-mist-keeper-project.md",
        start_line="1",  # STRING from LLM
        end_line="50",   # STRING from LLM
        expansion_mode="paragraph",
        padding="1"      # STRING from LLM
    )
    
    assert len(result) > 0, "Should return content"
    # ✓ PASSES NOW! No more TypeError
```

## Test Results

```bash
$ pytest tests/test_memtool_*.py -v

============================== 32 passed in 6.95s ===============================
```

**All 32 tests pass!** ✅
- 17 integration tests (singleton, persistence, functionality)
- 8 empty result tests (error messages, diagnostics)
- 7 type coercion tests (string handling, LLM compatibility) ⭐

## Before vs After

### Before (TypeError)

```python
# LLM calls with strings
get_context("articles/test.md", start_line="1", end_line="50")

# Passes strings to memtool
client.get_context(document, "1", "50")  # ❌ memtool crashes

# Error logged
TypeError: '<' not supported between instances of 'int' and 'str'
```

### After (Works!)

```python
# LLM calls with strings
get_context("articles/test.md", start_line="1", end_line="50")

# Converts to ints before passing to memtool
start_line = int("1")  # → 1
end_line = int("50")   # → 50
client.get_context(document, 1, 50)  # ✓ memtool works

# Returns content
"# Test Article\n\n..." (386KB of content)
```

## Why Not a memtool Bug?

memtool is **correctly** expecting integers for line numbers. The bug is in our integration layer:

1. **memtool API**: `get_context(document: str, start: int, end: int)` ✓ Correct
2. **Our wrapper**: Passed strings without conversion ❌ Our bug
3. **The fix**: Convert strings to ints in our wrapper ✓ Our responsibility

## Lessons Learned

1. **Type hints don't enforce** - Python doesn't validate types at runtime
2. **LLMs pass JSON** - Numbers in JSON can be strings or numbers
3. **Defensive programming** - Always coerce types at API boundaries
4. **Test real scenarios** - Unit tests should match actual LLM calls
5. **Integration layer responsibility** - Our job to adapt between LLM and library

## Related Pattern

This is a common issue when integrating LLM function calling with Python libraries:

```python
# Pattern: Always coerce types from LLM calls
def tool_wrapper(
    numeric_arg: int,  # Type hint is documentation, not enforcement!
    ...
):
    # Coerce at the boundary
    numeric_arg = int(numeric_arg)  # Handles both int and str
    
    # Now safe to use
    library.call(numeric_arg)
```

## How to Verify

```bash
# Run all memtool tests
pytest tests/test_memtool_*.py -v

# Test the exact failing scenario
python3 -c "
import sys
sys.path.insert(0, 'src')
from tools.context import get_context

# This now works!
result = get_context('articles/the-mist-keeper-project.md', 
                     start_line='1', end_line='50')
print(f'✓ Got {len(result)} chars')
"
```

Both should work without TypeErrors. ✅

## Conclusion

**Not a memtool bug!** This was an integration issue where we failed to convert LLM string arguments to integers before passing them to memtool. The fix is simple (explicit `int()` conversion) and fully tested (7 new tests, 32 total passing).

No bug report needed for memtool - they're doing everything correctly! 🎯

