"""
Unit tests for file feed integration.

Tests the flow from tool execution to file event extraction:
1. Tools return structured data
2. Log watcher detects file operations
3. File events are correctly formatted
"""
import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime

# Add parent to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.articles import write_article
from src.tools.story import write_story, edit_story
from src.server.log_watcher import LogManager


class TestToolStructuredOutput:
    """Test that file operation tools return structured data."""
    
    def test_write_article_returns_dict_on_success(self, tmp_path):
        """write_article should return dict with file_path and line counts."""
        # Setup temp config
        import toml
        config_path = tmp_path / "config.toml"
        config_path.write_text(toml.dumps({
            "paths": {
                "content_repo": str(tmp_path / "wikicontent"),
                "articles_dir": "articles"
            }
        }))
        
        # Reload articles module with new config
        import importlib
        from src.tools import articles
        articles._config = toml.load(str(config_path))
        articles._content_repo_path = Path(articles._config["paths"]["content_repo"])
        articles._articles_dir_name = articles._config["paths"]["articles_dir"]
        
        # Execute
        result = articles.write_article(
            "test-article",
            "# Test\n\nThis is a test article.\n"
        )
        
        # Assert structure
        assert isinstance(result, dict), "Should return dict on success"
        assert "file_path" in result
        assert "lines_added" in result
        assert "lines_removed" in result
        assert "message" in result
        
        # Assert values
        assert result["file_path"] == "articles/test-article.md"
        assert result["lines_added"] == 4  # 3 newlines = 4 lines
        assert result["lines_removed"] == 0  # New file
        assert "✅" in result["message"]
    
    def test_write_article_returns_string_on_error(self):
        """write_article should return error string on failure."""
        # This should fail with invalid config
        import src.tools.articles as articles
        original_config = articles._config
        articles._config = None
        
        result = articles.write_article("test", "content")
        
        # Restore
        articles._config = original_config
        
        assert isinstance(result, str)
        assert "❌" in result or "ERROR" in result.upper()
    
    def test_write_story_returns_dict_on_success(self, tmp_path, monkeypatch):
        """write_story should return dict with file_path and line counts."""
        # Setup
        wikicontent = tmp_path / "wikicontent"
        wikicontent.mkdir()
        monkeypatch.setenv("WIKICONTENT_PATH", str(wikicontent))
        
        # Execute
        result = write_story(
            content="# Chapter 1\n\nOnce upon a time.\n",
            filepath="stories/tale.md",
            append=False
        )
        
        # Assert
        assert isinstance(result, dict)
        assert result["success"] is True
        assert "file_path" in result
        assert result["file_path"] == "stories/tale.md"
        assert result["lines_added"] == 4  # 3 newlines = 4 lines
        assert result["lines_removed"] == 0
    
    def test_write_story_append_mode(self, tmp_path, monkeypatch):
        """write_story in append mode should calculate lines correctly."""
        # Setup
        wikicontent = tmp_path / "wikicontent"
        stories_dir = wikicontent / "stories"
        stories_dir.mkdir(parents=True)
        
        # Write initial content
        story_file = stories_dir / "tale.md"
        story_file.write_text("# Chapter 1\n\nFirst line.\n")
        
        monkeypatch.setenv("WIKICONTENT_PATH", str(wikicontent))
        
        # Execute append
        result = write_story(
            content="\n# Chapter 2\n\nSecond line.\n",
            filepath="stories/tale.md",
            append=True
        )
        
        # Assert
        assert result["success"] is True
        assert result["lines_added"] == 5  # 4 newlines = 5 lines
        assert result["lines_removed"] == 0  # Append doesn't remove
    
    def test_edit_story_returns_dict_on_success(self, tmp_path, monkeypatch):
        """edit_story should return dict with file_path and line counts."""
        # Setup
        wikicontent = tmp_path / "wikicontent"
        stories_dir = wikicontent / "stories"
        stories_dir.mkdir(parents=True)
        
        story_file = stories_dir / "tale.md"
        story_file.write_text("The wizard was old.\nHe lived alone.\n")
        
        monkeypatch.setenv("WIKICONTENT_PATH", str(wikicontent))
        
        # Execute
        result = edit_story(
            filepath="stories/tale.md",
            search="old",
            replace="ancient and wise"
        )
        
        # Assert
        assert isinstance(result, dict)
        assert result["success"] is True
        assert "file_path" in result
        assert result["file_path"] == "stories/tale.md"
        assert result["occurrences"] == 1


class TestLogWatcherFileDetection:
    """Test that LogManager correctly detects and extracts file operations."""
    
    def test_is_file_operation_detects_write_article(self):
        """Should detect write_article as file operation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_manager = LogManager(Path(tmpdir))
            
            log_entry = {
                "type": "tool_result",
                "tool": "write_article",
                "result": {
                    "file_path": "articles/test.md",
                    "lines_added": 10,
                    "lines_removed": 0
                }
            }
            
            assert log_manager._is_file_operation(log_entry) is True
    
    def test_is_file_operation_detects_write_story(self):
        """Should detect write_story as file operation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_manager = LogManager(Path(tmpdir))
            
            log_entry = {
                "type": "tool_result",
                "tool": "write_story",
                "result": {"file_path": "stories/tale.md"}
            }
            
            assert log_manager._is_file_operation(log_entry) is True
    
    def test_is_file_operation_detects_create_image(self):
        """Should detect create_image as file operation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_manager = LogManager(Path(tmpdir))
            
            log_entry = {
                "type": "tool_result",
                "tool": "create_image",
                "result": {"file_path": "images/wizard.png"}
            }
            
            assert log_manager._is_file_operation(log_entry) is True
    
    def test_is_file_operation_ignores_non_file_tools(self):
        """Should not detect non-file tools."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_manager = LogManager(Path(tmpdir))
            
            log_entry = {
                "type": "tool_result",
                "tool": "some_other_tool",
                "result": "some result"
            }
            
            assert log_manager._is_file_operation(log_entry) is False
    
    def test_is_file_operation_requires_tool_result_type(self):
        """Should only detect tool_result events."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_manager = LogManager(Path(tmpdir))
            
            log_entry = {
                "type": "tool_call",  # Not tool_result
                "tool": "write_article"
            }
            
            assert log_manager._is_file_operation(log_entry) is False
    
    def test_is_file_operation_detects_add_to_my_story(self):
        """Should detect add_to_my_story (writer agent tool) as file operation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_manager = LogManager(Path(tmpdir))
            
            log_entry = {
                "type": "tool_result",
                "tool": "add_to_my_story",
                "result": {
                    "file_path": "stories/my_story.md",
                    "lines_added": 15,
                    "lines_removed": 0
                }
            }
            
            assert log_manager._is_file_operation(log_entry) is True
    
    def test_is_file_operation_detects_rename_my_story(self):
        """Should detect rename_my_story (writer agent tool) as file operation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_manager = LogManager(Path(tmpdir))
            
            log_entry = {
                "type": "tool_result",
                "tool": "rename_my_story",
                "result": {
                    "old_path": "stories/old_name.md",
                    "new_path": "stories/new_name.md"
                }
            }
            
            assert log_manager._is_file_operation(log_entry) is True
    
    def test_extract_file_event_from_write_article(self):
        """Should extract complete file event from write_article result."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_manager = LogManager(Path(tmpdir))
            
            log_entry = {
                "type": "tool_result",
                "tool": "write_article",
                "result": {
                    "file_path": "articles/test.md",
                    "lines_added": 42,
                    "lines_removed": 5,
                    "message": "Success"
                },
                "timestamp": "2025-11-09T12:00:00"
            }
            
            file_event = log_manager._extract_file_event("agent_writer-001", log_entry)
            
            assert file_event is not None
            assert file_event["type"] == "file_changed"
            assert file_event["agent_id"] == "agent_writer-001"
            assert file_event["file_path"] == "articles/test.md"
            assert file_event["action"] == "write_article"
            assert file_event["changes"]["added"] == 42
            assert file_event["changes"]["removed"] == 5
            assert file_event["timestamp"] == "2025-11-09T12:00:00"
    
    def test_extract_file_event_handles_string_result(self):
        """Should return None for string results (error cases)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_manager = LogManager(Path(tmpdir))
            
            log_entry = {
                "type": "tool_result",
                "tool": "write_article",
                "result": "❌ Error: File not found"
            }
            
            file_event = log_manager._extract_file_event("agent_writer-001", log_entry)
            
            assert file_event is None
    
    def test_extract_file_event_handles_missing_file_path(self):
        """Should return None if file_path is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_manager = LogManager(Path(tmpdir))
            
            log_entry = {
                "type": "tool_result",
                "tool": "write_article",
                "result": {
                    "lines_added": 10,
                    "lines_removed": 0
                    # Missing file_path
                }
            }
            
            file_event = log_manager._extract_file_event("agent_writer-001", log_entry)
            
            assert file_event is None
    
    def test_extract_file_event_from_add_to_my_story(self):
        """Should extract file event from add_to_my_story (writer agent tool)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_manager = LogManager(Path(tmpdir))
            
            log_entry = {
                "type": "tool_result",
                "tool": "add_to_my_story",
                "result": {
                    "success": True,
                    "file_path": "stories/my_story.md",
                    "lines_added": 20,
                    "lines_removed": 0,
                    "mode": "append"
                },
                "timestamp": "2025-11-09T12:00:00"
            }
            
            file_event = log_manager._extract_file_event("agent_writer-001", log_entry)
            
            assert file_event is not None
            assert file_event["type"] == "file_changed"
            assert file_event["agent_id"] == "agent_writer-001"
            assert file_event["file_path"] == "stories/my_story.md"
            assert file_event["action"] == "add_to_my_story"
            assert file_event["changes"]["added"] == 20
            assert file_event["changes"]["removed"] == 0
    
    def test_extract_file_event_from_rename_my_story(self):
        """Should extract file event from rename_my_story using new_path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_manager = LogManager(Path(tmpdir))
            
            log_entry = {
                "type": "tool_result",
                "tool": "rename_my_story",
                "result": {
                    "success": True,
                    "message": "Story renamed successfully",
                    "old_path": "stories/old_name.md",
                    "new_path": "stories/epic_adventure.md"
                },
                "timestamp": "2025-11-09T12:00:00"
            }
            
            file_event = log_manager._extract_file_event("agent_writer-001", log_entry)
            
            assert file_event is not None
            assert file_event["type"] == "file_changed"
            assert file_event["agent_id"] == "agent_writer-001"
            assert file_event["file_path"] == "stories/epic_adventure.md"
            assert file_event["action"] == "rename_my_story"
            assert file_event["changes"]["added"] == 0
            assert file_event["changes"]["removed"] == 0


class TestEndToEndFileTracking:
    """Test complete flow from tool to file event."""
    
    def test_write_article_logged_and_detected(self, tmp_path, monkeypatch):
        """Complete flow: write_article → log → detect."""
        # Setup temp environment
        wikicontent = tmp_path / "wikicontent"
        wikicontent.mkdir()
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()
        
        import toml
        config_path = tmp_path / "config.toml"
        config_path.write_text(toml.dumps({
            "paths": {
                "content_repo": str(wikicontent),
                "articles_dir": "articles"
            }
        }))
        
        # Reload articles module
        from src.tools import articles
        articles._config = toml.load(str(config_path))
        articles._content_repo_path = Path(articles._config["paths"]["content_repo"])
        articles._articles_dir_name = articles._config["paths"]["articles_dir"]
        
        # Create log manager
        log_manager = LogManager(logs_dir)
        
        # Execute tool
        tool_result = articles.write_article(
            "test-article",
            "# Test\n\nContent here.\n"
        )
        
        # Simulate log entry (what AgentRunner would create)
        log_entry = {
            "type": "tool_result",
            "tool": "write_article",
            "result": tool_result,
            "timestamp": datetime.now().isoformat()
        }
        
        # Process through log manager
        assert log_manager._is_file_operation(log_entry) is True
        file_event = log_manager._extract_file_event("test_agent", log_entry)
        
        # Verify file event
        assert file_event is not None
        assert file_event["type"] == "file_changed"
        assert file_event["agent_id"] == "test_agent"
        assert file_event["file_path"] == "articles/test-article.md"
        assert file_event["changes"]["added"] == 4  # 3 newlines = 4 lines
        assert file_event["changes"]["removed"] == 0
        
        # Verify actual file was created
        article_path = wikicontent / "articles" / "test-article.md"
        assert article_path.exists()
        assert "Test" in article_path.read_text()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

