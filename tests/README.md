# MechaWiki Tests

Unit tests for the MechaWiki agent system.

## Running Tests

### Run all tests
```bash
pytest tests/
```

### Run specific test file
```bash
pytest tests/test_file_feed_integration.py -v
```

### Run with coverage
```bash
pytest tests/ --cov=src --cov-report=html
```

## Test Files

### `test_file_tools_output.py`
Tests that file operation tools (`write_article`, `write_story`, `edit_story`) return structured data with the correct format:
- `file_path`: relative path to modified file
- `lines_added`: number of lines added
- `lines_removed`: number of lines removed

**Why these tests matter:** The Files Feed UI depends on this structured data to display file changes. If tools return plain strings, the feed won't detect changes.

### `test_file_feed_integration.py`
End-to-end tests for the file tracking system:
1. Tools execute and return structured data
2. LogManager detects file operations from log entries
3. File events are correctly formatted for UI consumption

**What it tests:**
- Tool → Log entry → File event pipeline
- Log watcher's file operation detection
- File event extraction from tool results

### `test_base_agent_events.py`
Tests for BaseAgent event generation and tool execution.

### `test_agent_runner.py`
Tests for AgentRunner's event consumption and JSONL logging.

## Writing Tests

### Test Structure
Follow the "hunt with purpose" philosophy:
- **One assertion per test** (when possible)
- **Clear test names** that describe what's being tested
- **Arrange-Act-Assert** structure

### Example
```python
def test_write_article_returns_dict_on_success(self, tmp_path):
    """write_article should return dict with file_path and line counts."""
    # Arrange: setup test environment
    setup_test_config(tmp_path)
    
    # Act: execute the tool
    result = write_article("test", "content\n")
    
    # Assert: verify structure
    assert isinstance(result, dict)
    assert "file_path" in result
    assert result["lines_added"] > 0
```

## Test Coverage Goals

Our shield wall against bugs:
- ✅ Tool structured output format
- ✅ Tool line counting accuracy
- ✅ Tool error handling (strings vs dicts)
- ✅ Log watcher file operation detection
- ✅ File event extraction
- 🎯 BaseAgent tool execution
- 🎯 AgentRunner event logging

## Running in CI/CD

Add to your CI pipeline:
```yaml
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest tests/ --junitxml=test-results.xml
```

## Debugging Failed Tests

### Verbose output
```bash
pytest tests/ -v -s
```

### Run one test
```bash
pytest tests/test_file_tools_output.py::TestWriteArticleOutput::test_returns_dict_with_required_fields -v
```

### Drop into debugger on failure
```bash
pytest tests/ --pdb
```

## Test Philosophy (XP Style)

**"Strong defenses win campaigns"** - Test first, then implement
- Write failing tests to define behavior
- Make them pass with minimal code
- Refactor with confidence

**"Track the bugs before they track you"** - Catch issues early
- Test edge cases and error conditions
- Use fixtures to avoid test duplication
- Keep tests fast and focused

**"Your tests are your early warning system"**
- If a test breaks, something real broke
- Tests document expected behavior
- Green tests = confidence to ship

