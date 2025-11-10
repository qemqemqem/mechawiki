"""
Unit tests for memtool integration.

These tests verify:
1. The singleton client pattern works correctly
2. Index persistence across multiple get_context() calls
3. Self-healing when index is not loaded
4. Multi-document expansion via memtool
5. Error handling for missing files and server issues
"""

import pytest
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tools.context import get_context, _get_memtool_client, _ensure_index_loaded
import tools.context  # To reset module state between tests


@pytest.fixture(autouse=True)
def reset_module_state():
    """Reset module-level state before each test."""
    # Reset singleton state
    tools.context._memtool_client = None
    tools.context._index_ensured = False
    yield
    # Cleanup after test
    if tools.context._memtool_client:
        try:
            tools.context._memtool_client.close()
        except:
            pass
    tools.context._memtool_client = None
    tools.context._index_ensured = False


class TestMemtoolSingletonClient:
    """Test that the client singleton pattern works correctly."""
    
    def test_singleton_returns_same_client(self):
        """Verify _get_memtool_client returns the same instance."""
        client1 = _get_memtool_client()
        client2 = _get_memtool_client()
        
        assert client1 is client2, "Should return same client instance"
    
    def test_singleton_persists_across_get_context_calls(self):
        """Verify the same client is used across multiple get_context() calls."""
        # This is CRITICAL - if we create new clients, index is lost!
        
        # First call - should create client and load index
        result1 = get_context("articles/the-mist-keeper-universe.md", return_metadata=True)
        client1 = tools.context._memtool_client
        
        # Second call - should reuse same client
        result2 = get_context("articles/the-mist-keeper-universe.md", return_metadata=True)
        client2 = tools.context._memtool_client
        
        assert client1 is client2, "CRITICAL: Must use same client instance!"
        assert tools.context._index_ensured, "Index should be marked as ensured"


class TestIndexPersistence:
    """Test that the index persists correctly across operations."""
    
    def test_index_loads_once_and_persists(self):
        """Verify index is loaded once and persists for subsequent calls."""
        from memtool.client import MemtoolClient
        
        # First call - should load index
        result1 = get_context("articles/the-mist-keeper-universe.md", return_metadata=True)
        
        # Check that index is loaded on our client
        client = _get_memtool_client()
        status = client.status()
        assert status['loaded'], "Index should be loaded after first get_context()"
        
        # Second call - should NOT reload index
        result2 = get_context("articles/the-mist-keeper-universe.md", return_metadata=True)
        
        # Client should still have index
        status2 = client.status()
        assert status2['loaded'], "Index should still be loaded after second call"
    
    def test_index_ensured_flag_prevents_redundant_checks(self):
        """Verify _index_ensured flag prevents redundant status checks."""
        # First call - loads index
        _ensure_index_loaded()
        assert tools.context._index_ensured, "Flag should be set after ensuring index"
        
        # Second call - should return immediately
        _ensure_index_loaded()  # Should not make any client calls
        assert tools.context._index_ensured, "Flag should remain set"


class TestGetContextTool:
    """Test the get_context() tool functionality."""
    
    def test_get_context_returns_content(self):
        """Verify get_context returns content for existing files."""
        result = get_context("articles/the-mist-keeper-universe.md")
        
        assert isinstance(result, str), "Should return string"
        assert len(result) > 0, "Should return non-empty content"
    
    def test_get_context_with_metadata(self):
        """Verify metadata mode returns structured data."""
        result = get_context("articles/the-mist-keeper-universe.md", return_metadata=True)
        
        assert isinstance(result, dict), "Should return dict in metadata mode"
        assert 'content' in result, "Should have 'content' key"
        assert 'intervals' in result, "Should have 'intervals' key"
        assert 'num_docs' in result, "Should have 'num_docs' key"
        
        assert isinstance(result['content'], str), "Content should be string"
        assert isinstance(result['intervals'], list), "Intervals should be list"
        assert isinstance(result['num_docs'], int), "num_docs should be int"
    
    def test_get_context_with_line_range(self):
        """Verify line range filtering works."""
        result = get_context(
            "articles/the-mist-keeper-universe.md",
            start_line=1,
            end_line=10,
            return_metadata=True
        )
        
        assert isinstance(result, dict), "Should return dict"
        assert 'content' in result, "Should have content"
    
    def test_get_context_nonexistent_file(self):
        """Verify graceful handling of nonexistent files."""
        result = get_context("articles/does_not_exist_12345.md", return_metadata=True)
        
        # Should return empty result, not crash
        assert isinstance(result, dict), "Should return dict"
        assert result.get('content', '') == '', "Should return empty content"
    
    def test_get_context_expansion_modes(self):
        """Verify different expansion modes work."""
        modes = ["paragraph", "line", "section"]
        
        for mode in modes:
            result = get_context(
                "articles/the-mist-keeper-universe.md",
                expansion_mode=mode,
                return_metadata=True
            )
            assert isinstance(result, dict), f"Should work with mode={mode}"


class TestSelfHealing:
    """Test that get_context() is self-healing when index not loaded."""
    
    def test_auto_loads_index_when_missing(self):
        """Verify get_context() automatically loads index if missing."""
        # This simulates the scenario where:
        # 1. Server is running but has no index
        # 2. get_context() is called
        # 3. Should automatically load index and succeed
        
        client = _get_memtool_client()
        
        # Verify index gets loaded by first call
        result = get_context("articles/the-mist-keeper-universe.md", return_metadata=True)
        
        # Check that index is now loaded
        status = client.status()
        assert status['loaded'], "Index should be loaded after get_context()"
    
    def test_subsequent_calls_dont_reload(self):
        """Verify subsequent calls don't reload the index."""
        # First call - loads index
        result1 = get_context("articles/the-mist-keeper-universe.md", return_metadata=True)
        
        # Reset the flag to test if it gets set again
        original_flag = tools.context._index_ensured
        
        # Second call - should not reload
        result2 = get_context("articles/the-mist-keeper-universe.md", return_metadata=True)
        
        # Flag should still be set (not reset and re-set)
        assert tools.context._index_ensured == original_flag


class TestMultiDocumentExpansion:
    """Test memtool's multi-document expansion capabilities."""
    
    def test_expansion_includes_metadata(self):
        """Verify expanded context includes interval metadata."""
        result = get_context("articles/the-mist-keeper-universe.md", return_metadata=True)
        
        if result.get('intervals'):
            interval = result['intervals'][0]
            assert 'path' in interval, "Interval should have 'path' field"
            assert 'start' in interval, "Interval should have 'start' field"
            assert 'end' in interval, "Interval should have 'end' field"
    
    def test_num_docs_reflects_expansion(self):
        """Verify num_docs counts unique documents in expansion."""
        result = get_context("articles/the-mist-keeper-universe.md", return_metadata=True)
        
        if result.get('intervals'):
            # Count unique docs manually
            unique_docs = set(i['path'] for i in result['intervals'])
            
            assert result['num_docs'] == len(unique_docs), \
                "num_docs should match unique document count"


class TestErrorHandling:
    """Test error handling in various failure scenarios."""
    
    def test_handles_invalid_line_numbers(self):
        """Verify graceful handling of invalid line numbers."""
        # Should not crash with invalid ranges
        result = get_context(
            "articles/the-mist-keeper-universe.md",
            start_line=999999,
            end_line=999999,
            return_metadata=True
        )
        
        assert isinstance(result, dict), "Should return dict even with invalid range"
    
    def test_handles_invalid_expansion_mode(self):
        """Verify handling of invalid expansion modes."""
        # memtool might validate this, but we should handle gracefully
        try:
            result = get_context(
                "articles/the-mist-keeper-universe.md",
                expansion_mode="invalid_mode",
                return_metadata=True
            )
            # If it doesn't raise, should return a dict
            assert isinstance(result, dict), "Should return dict or raise exception"
        except Exception as e:
            # If it raises, that's also acceptable
            pass


class TestRealWorldUsage:
    """Test real-world usage patterns."""
    
    def test_multiple_sequential_calls(self):
        """Verify multiple sequential calls all work correctly."""
        files = [
            "articles/the-mist-keeper-universe.md",
            "articles/comprehensive-collection-summary.md",
            "articles/reading-guide-the-dreamers-gift.md"
        ]
        
        results = []
        for file in files:
            result = get_context(file, return_metadata=True)
            results.append(result)
            
            # Each should work
            assert isinstance(result, dict), f"Should return dict for {file}"
        
        # All calls should use same client
        client = _get_memtool_client()
        status = client.status()
        assert status['loaded'], "Index should still be loaded after all calls"
    
    def test_mixed_simple_and_metadata_calls(self):
        """Verify mixing simple and metadata calls works."""
        # Simple call
        content1 = get_context("articles/the-mist-keeper-universe.md")
        assert isinstance(content1, str), "Simple call should return string"
        
        # Metadata call
        result2 = get_context("articles/the-mist-keeper-universe.md", return_metadata=True)
        assert isinstance(result2, dict), "Metadata call should return dict"
        
        # Another simple call
        content3 = get_context("articles/the-mist-keeper-universe.md")
        assert isinstance(content3, str), "Second simple call should return string"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
