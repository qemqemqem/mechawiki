"""
Unit tests for get_context() type coercion.

LLMs often pass numbers as strings in function calls.
Our tool should handle this gracefully.
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


class TestTypeCoercion:
    """Test that get_context handles type coercion from LLM calls."""
    
    def test_string_line_numbers_from_llm(self):
        """
        Verify string line numbers are converted to ints.
        
        When LLMs call tools through litellm, they often pass:
        - start_line: "1" (string)
        - end_line: "50" (string)
        
        But memtool expects integers!
        """
        # This is what the LLM actually passes
        result = get_context(
            document="articles/the-mist-keeper-project.md",
            start_line="1",  # STRING, not int!
            end_line="50",   # STRING, not int!
            expansion_mode="paragraph",
            padding="1"      # STRING, not int!
        )
        
        # Should work, not crash with TypeError
        assert isinstance(result, str), "Should return string in simple mode"
        assert len(result) > 0, "Should return content"
        print(f"\n✓ Successfully handled string arguments, got {len(result)} chars")
    
    def test_integer_line_numbers_still_work(self):
        """Verify integer line numbers still work (backward compatibility)."""
        result = get_context(
            document="articles/the-mist-keeper-project.md",
            start_line=1,   # INT
            end_line=50,    # INT
            expansion_mode="paragraph",
            padding=1       # INT
        )
        
        assert isinstance(result, str), "Should return string"
        assert len(result) > 0, "Should return content"
        print(f"\n✓ Integer arguments work, got {len(result)} chars")
    
    def test_mixed_types(self):
        """Verify mixed string/int arguments work."""
        result = get_context(
            document="articles/the-mist-keeper-project.md",
            start_line="1",    # STRING
            end_line=50,       # INT (mixed!)
            expansion_mode="paragraph",
            padding=1
        )
        
        assert isinstance(result, str), "Should return string"
        assert len(result) > 0, "Should return content"
        print(f"\n✓ Mixed types work, got {len(result)} chars")
    
    def test_metadata_mode_with_string_args(self):
        """Verify metadata mode works with string arguments."""
        result = get_context(
            document="articles/the-mist-keeper-project.md",
            start_line="1",
            end_line="50",
            expansion_mode="paragraph",
            padding="1",
            return_metadata=True  # Request metadata
        )
        
        assert isinstance(result, dict), "Should return dict in metadata mode"
        assert 'content' in result, "Should have content"
        assert len(result['content']) > 0, "Should have content"
        print(f"\n✓ Metadata mode with strings works: {result['num_docs']} docs")
    
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
            start_line="1",
            end_line="50",
            expansion_mode="paragraph",
            padding="1"
        )
        
        print(f"\n✓ EXACT LLM CALL WORKS! Got {len(result)} chars")
        assert isinstance(result, str), "Should return string"
        assert len(result) > 0, "Should have content"
        
        # Should NOT raise:
        # TypeError: '<' not supported between instances of 'int' and 'str'


class TestInvalidTypes:
    """Test handling of truly invalid types."""
    
    def test_non_numeric_string(self):
        """Verify non-numeric strings are handled gracefully."""
        try:
            result = get_context(
                document="articles/the-mist-keeper-project.md",
                start_line="abc",  # Invalid!
                end_line="50"
            )
            # If it doesn't raise, it should return error
            assert 'error' in str(result).lower() or result == "", \
                "Should handle invalid input gracefully"
        except ValueError:
            # Raising ValueError is also acceptable
            pass
    
    def test_negative_line_numbers(self):
        """Verify negative line numbers are handled."""
        result = get_context(
            document="articles/the-mist-keeper-project.md",
            start_line="-1",  # Negative
            end_line="50"
        )
        
        # Should not crash - may return empty or error
        assert isinstance(result, str), "Should return string"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

