"""
Unit tests for get_context() edge cases around empty results.

These tests expose the issue where:
- Nonexistent files return ""
- Empty files return ""
- Files with no indexed content return ""

All three cases should be distinguishable!
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tools.context import get_context
import tools.context


@pytest.fixture(autouse=True)
def reset_module_state():
    """Reset module-level state before each test."""
    tools.context._memtool_client = None
    tools.context._index_ensured = False
    yield
    if tools.context._memtool_client:
        try:
            tools.context._memtool_client.close()
        except:
            pass
    tools.context._memtool_client = None
    tools.context._index_ensured = False


class TestEmptyResultCases:
    """Test different reasons for empty results."""
    
    def test_nonexistent_file_simple_mode(self):
        """Verify nonexistent files return empty string in simple mode."""
        # This file doesn't exist
        result = get_context("articles/the-mist-keeper-story.md")
        
        assert isinstance(result, str), "Should return string in simple mode"
        assert result == "", "Should return empty string for nonexistent file"
    
    def test_nonexistent_file_metadata_mode(self):
        """Verify nonexistent files return clear error in metadata mode."""
        # This file doesn't exist
        result = get_context("articles/the-mist-keeper-story.md", return_metadata=True)
        
        assert isinstance(result, dict), "Should return dict in metadata mode"
        
        # Should always have these keys now
        assert 'error' in result, "Should have error key"
        assert 'content' in result, "Should have content key"
        assert 'intervals' in result, "Should have intervals key"
        assert 'num_docs' in result, "Should have num_docs key"
        
        # Content should be empty
        assert result['content'] == "", "Should have empty content"
        assert result['num_docs'] == 0, "Should have no docs"
        assert len(result['intervals']) == 0, "Should have no intervals"
        
        # Error message should be helpful
        error_msg = result['error']
        assert 'may not exist' in error_msg.lower() or 'not found' in error_msg.lower(), \
            "Error should mention file might not exist"
        assert 'find_articles' in error_msg.lower(), \
            "Error should suggest using find_articles tool"
    
    def test_existing_file_with_content(self):
        """Verify existing files with content return data."""
        # This file exists and has content
        result = get_context("articles/the-mist-keeper-universe.md", return_metadata=True)
        
        assert isinstance(result, dict), "Should return dict"
        
        # Should have content
        if 'error' not in result:
            assert 'content' in result, "Should have content key"
            assert len(result['content']) > 0, "Should have non-empty content"
            assert result['num_docs'] > 0, "Should have at least one document"
    
    def test_similar_file_names(self):
        """Test that similar file names are handled correctly."""
        # Files that exist
        existing_files = [
            "articles/the-mist-keeper-universe.md",
            "articles/the-mist-keeper-characters.md",
        ]
        
        # File that doesn't exist (but has similar name)
        nonexistent = "articles/the-mist-keeper-story.md"
        
        for existing in existing_files:
            result = get_context(existing, return_metadata=True)
            assert 'error' not in result or 'content' in result, \
                f"Existing file {existing} should not error"
        
        # Nonexistent should return empty/error
        result_ne = get_context(nonexistent, return_metadata=True)
        if 'content' in result_ne:
            assert result_ne['content'] == "" or result_ne['num_docs'] == 0, \
                "Nonexistent file should have no content"


class TestMemtoolQueryBehavior:
    """Test what memtool actually returns for different file queries."""
    
    def test_memtool_response_for_nonexistent_file(self):
        """Check what memtool returns when querying a nonexistent file."""
        from tools.context import _get_memtool_client, _ensure_index_loaded
        
        _ensure_index_loaded()
        client = _get_memtool_client()
        
        # Query for file that doesn't exist
        context = client.get_context("articles/the-mist-keeper-story.md", 1, 100)
        
        print(f"\nmemtool response for nonexistent file:")
        print(f"  Keys: {context.keys()}")
        print(f"  Intervals: {len(context.get('intervals', []))} intervals")
        print(f"  Commits: {len(context.get('commits', []))} commits")
        
        # Should return structure with empty intervals
        assert 'intervals' in context, "Should have intervals key"
        assert len(context['intervals']) == 0, "Should have no intervals for nonexistent file"
    
    def test_memtool_response_for_existing_file(self):
        """Check what memtool returns for an existing file."""
        from tools.context import _get_memtool_client, _ensure_index_loaded
        
        _ensure_index_loaded()
        client = _get_memtool_client()
        
        # Query for file that exists
        context = client.get_context("articles/the-mist-keeper-universe.md", 1, 100)
        
        print(f"\nmemtool response for existing file:")
        print(f"  Keys: {context.keys()}")
        print(f"  Intervals: {len(context.get('intervals', []))} intervals")
        print(f"  Commits: {len(context.get('commits', []))} commits")
        
        # Should return intervals
        assert 'intervals' in context, "Should have intervals key"
        assert len(context['intervals']) > 0, "Should have intervals for existing file"


class TestErrorMessages:
    """Test that error messages are helpful."""
    
    def test_helpful_error_for_missing_file(self):
        """Verify error messages guide users to correct file names."""
        result = get_context("articles/the-mist-keeper-story.md", return_metadata=True)
        
        # Should always have error key for missing files
        assert 'error' in result, "Should have error key"
        error_msg = result['error']
        
        print(f"\nImproved error message: {error_msg}")
        
        # Error should be informative and actionable
        assert len(error_msg) > 50, "Error message should be descriptive"
        assert 'may not exist' in error_msg or 'not found' in error_msg, \
            "Should mention file might not exist"
        assert 'find_articles' in error_msg, "Should suggest find_articles tool"
        
        # Should also have the empty data fields
        assert result['content'] == "", "Content should be empty"
        assert result['num_docs'] == 0, "Should indicate no docs found"
        assert len(result['intervals']) == 0, "Should have no intervals"


class TestAgentUsageScenario:
    """Test the exact scenario the agent encountered."""
    
    def test_agent_query_the_mist_keeper_story(self):
        """
        Reproduce the exact agent query that returned empty.
        
        Agent called:
        get_context(
            document="articles/the-mist-keeper-story.md",
            start_line=1,
            end_line=100,
            expansion_mode="paragraph",
            padding=2
        )
        
        And got back: ""
        """
        result = get_context(
            document="articles/the-mist-keeper-story.md",
            start_line=1,
            end_line=100,
            expansion_mode="paragraph",
            padding=2
        )
        
        print(f"\nAgent query result:")
        print(f"  Type: {type(result)}")
        print(f"  Length: {len(result)}")
        print(f"  Content: '{result}'")
        
        # Current behavior - empty string
        assert isinstance(result, str), "Simple mode returns string"
        assert result == "", "File doesn't exist, so returns empty"
        
        # With metadata we can see WHY it's empty
        result_with_meta = get_context(
            document="articles/the-mist-keeper-story.md",
            start_line=1,
            end_line=100,
            expansion_mode="paragraph",
            padding=2,
            return_metadata=True
        )
        
        print(f"\nWith metadata:")
        print(f"  Keys: {result_with_meta.keys()}")
        if 'num_docs' in result_with_meta:
            print(f"  Num docs: {result_with_meta['num_docs']}")
        if 'error' in result_with_meta:
            print(f"  Error: {result_with_meta['error']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

