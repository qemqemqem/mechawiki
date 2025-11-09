"""
Tests for interactive tools (src/tools/interactive.py).
"""
import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.interactive import wait_for_user, get_session_state, WaitingForInput


class TestWaitForUser:
    """Test wait_for_user functionality."""
    
    def test_returns_waiting_for_input_sentinel(self):
        """Should return WaitingForInput sentinel object."""
        result = wait_for_user()
        
        assert isinstance(result, WaitingForInput)
    
    def test_includes_custom_prompt(self):
        """Should include custom prompt in sentinel."""
        custom_prompt = "What do you want to do next?"
        result = wait_for_user(custom_prompt)
        
        assert result.prompt == custom_prompt
    
    def test_has_default_prompt(self):
        """Should have default prompt."""
        result = wait_for_user()
        
        assert result.prompt == "What would you like to do?"
    
    def test_different_prompts_create_different_objects(self):
        """Should create distinct objects for different prompts."""
        result1 = wait_for_user("Prompt 1")
        result2 = wait_for_user("Prompt 2")
        
        assert result1.prompt != result2.prompt


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
    
    def test_can_create_with_custom_prompt(self):
        """Should create sentinel with custom prompt."""
        sentinel = WaitingForInput("Custom prompt")
        
        assert sentinel.prompt == "Custom prompt"
    
    def test_has_default_prompt(self):
        """Should have default prompt."""
        sentinel = WaitingForInput()
        
        assert "Waiting" in sentinel.prompt or "waiting" in sentinel.prompt
    
    def test_is_distinct_type(self):
        """Should be distinguishable from other types."""
        sentinel = WaitingForInput()
        
        assert not isinstance(sentinel, dict)
        assert not isinstance(sentinel, str)
        assert isinstance(sentinel, WaitingForInput)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

