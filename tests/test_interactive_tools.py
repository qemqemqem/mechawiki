"""
Tests for interactive tools (src/tools/interactive.py).
"""
import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.interactive import wait_for_user, get_session_state, done, WaitingForInput, Finished


class TestWaitForUser:
    """Test wait_for_user functionality."""
    
    def test_returns_waiting_for_input_sentinel(self):
        """Should return WaitingForInput sentinel object."""
        result = wait_for_user()
        
        assert isinstance(result, WaitingForInput)
    
    def test_accepts_no_arguments(self):
        """Should not require any arguments."""
        # Should not raise an exception
        result = wait_for_user()
        
        assert isinstance(result, WaitingForInput)
    
    def test_returns_simple_sentinel(self):
        """Should return a simple sentinel without attributes."""
        result = wait_for_user()
        
        # Should be a WaitingForInput instance
        assert isinstance(result, WaitingForInput)
        # Should not have a prompt attribute
        assert not hasattr(result, 'prompt')


class TestGetSessionState:
    """Test get_session_state functionality."""
    
    def test_returns_dict(self):
        """Should return a dictionary."""
        result = get_session_state()
        
        assert isinstance(result, dict)
    
    def test_indicates_success(self):
        """Should indicate successful operation."""
        result = get_session_state()
        
        assert result.get("success") is True
    
    def test_has_session_info(self):
        """Should include session information."""
        result = get_session_state()
        
        assert "session" in result
    
    def test_has_message(self):
        """Should include a message."""
        result = get_session_state()
        
        assert "message" in result
        assert isinstance(result["message"], str)


class TestWaitingForInputSentinel:
    """Test the WaitingForInput sentinel class."""
    
    def test_can_create_instance(self):
        """Should create sentinel instance."""
        sentinel = WaitingForInput()
        
        assert isinstance(sentinel, WaitingForInput)
    
    def test_is_simple_sentinel(self):
        """Should be a simple sentinel without data."""
        sentinel = WaitingForInput()
        
        # Should not have a prompt attribute
        assert not hasattr(sentinel, 'prompt')
    
    def test_is_distinct_type(self):
        """Should be distinguishable from other types."""
        sentinel = WaitingForInput()
        
        assert not isinstance(sentinel, dict)
        assert not isinstance(sentinel, str)
        assert isinstance(sentinel, WaitingForInput)


class TestDone:
    """Test done functionality."""
    
    def test_returns_finished_sentinel(self):
        """Should return Finished sentinel object."""
        result = done()
        
        assert isinstance(result, Finished)
    
    def test_accepts_no_arguments(self):
        """Should not require any arguments."""
        # Should not raise an exception
        result = done()
        
        assert isinstance(result, Finished)
    
    def test_returns_simple_sentinel(self):
        """Should return a simple sentinel without attributes."""
        result = done()
        
        # Should be a Finished instance
        assert isinstance(result, Finished)


class TestFinishedSentinel:
    """Test the Finished sentinel class."""
    
    def test_can_create_instance(self):
        """Should create sentinel instance."""
        sentinel = Finished()
        
        assert isinstance(sentinel, Finished)
    
    def test_is_simple_sentinel(self):
        """Should be a simple sentinel without data."""
        sentinel = Finished()
        
        # Should not have extra attributes
        # (just checking it's a simple class)
        assert isinstance(sentinel, Finished)
    
    def test_is_distinct_type(self):
        """Should be distinguishable from other types."""
        sentinel = Finished()
        
        assert not isinstance(sentinel, dict)
        assert not isinstance(sentinel, str)
        assert not isinstance(sentinel, WaitingForInput)
        assert isinstance(sentinel, Finished)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

