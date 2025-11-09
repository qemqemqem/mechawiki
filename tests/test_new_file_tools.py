"""
Tests for the new general-purpose file tools (read_file, edit_file, add_to_story).
"""
import pytest
import tempfile
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.files import read_file, edit_file, add_to_story


class TestReadFile:
    """Test read_file functionality."""
    
    def test_reads_file_successfully(self, tmp_path, monkeypatch):
        """Should read file content."""
        wikicontent = tmp_path / "wikicontent"
        articles = wikicontent / "articles"
        articles.mkdir(parents=True)
        
        test_file = articles / "test.md"
        test_file.write_text("# Test\n\nContent here\n")
        
        monkeypatch.setenv("WIKICONTENT_PATH", str(wikicontent))
        
        result = read_file("articles/test.md")
        
        assert "content" in result
        assert result["content"] == "# Test\n\nContent here\n"
    
    def test_reads_file_with_line_range(self, tmp_path, monkeypatch):
        """Should read specific line range."""
        wikicontent = tmp_path / "wikicontent"
        stories = wikicontent / "stories"
        stories.mkdir(parents=True)
        
        test_file = stories / "story.md"
        test_file.write_text("Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n")
        
        monkeypatch.setenv("WIKICONTENT_PATH", str(wikicontent))
        
        result = read_file("stories/story.md", start_line=2, end_line=4)
        
        assert "content" in result
        assert result["content"] == "Line 2\nLine 3\nLine 4"
    
    def test_returns_error_for_nonexistent_file(self, tmp_path, monkeypatch):
        """Should return error dict for missing file."""
        wikicontent = tmp_path / "wikicontent"
        wikicontent.mkdir()
        
        monkeypatch.setenv("WIKICONTENT_PATH", str(wikicontent))
        
        result = read_file("does/not/exist.md")
        
        assert "error" in result
        assert "not found" in result["error"].lower()


class TestEditFile:
    """Test edit_file with Aider-style diffs."""
    
    def test_creates_new_file_with_empty_search(self, tmp_path, monkeypatch):
        """Empty SEARCH block should create new file."""
        wikicontent = tmp_path / "wikicontent"
        wikicontent.mkdir()
        
        monkeypatch.setenv("WIKICONTENT_PATH", str(wikicontent))
        
        diff = """<<<<<<< SEARCH
=======
# New Article

This is brand new content.
>>>>>>> REPLACE"""
        
        result = edit_file("articles/new.md", diff)
        
        assert result["success"] is True
        assert result["file_path"] == "articles/new.md"
        assert result["lines_added"] > 0
        
        # Verify file was created
        new_file = wikicontent / "articles" / "new.md"
        assert new_file.exists()
        assert "New Article" in new_file.read_text()
    
    def test_edits_existing_file(self, tmp_path, monkeypatch):
        """Should apply search/replace to existing file."""
        wikicontent = tmp_path / "wikicontent"
        articles = wikicontent / "articles"
        articles.mkdir(parents=True)
        
        test_file = articles / "wizard.md"
        test_file.write_text("# Wizard\n\nMerlin was a wizard.\n")
        
        monkeypatch.setenv("WIKICONTENT_PATH", str(wikicontent))
        
        diff = """<<<<<<< SEARCH
Merlin was a wizard.
=======
Merlin was a powerful wizard.
>>>>>>> REPLACE"""
        
        result = edit_file("articles/wizard.md", diff)
        
        assert result["success"] is True
        assert "powerful wizard" in test_file.read_text()
    
    def test_multiple_search_replace_blocks(self, tmp_path, monkeypatch):
        """Should handle multiple search/replace blocks."""
        wikicontent = tmp_path / "wikicontent"
        articles = wikicontent / "articles"
        articles.mkdir(parents=True)
        
        test_file = articles / "story.md"
        test_file.write_text("Line 1\nLine 2\nLine 3\n")
        
        monkeypatch.setenv("WIKICONTENT_PATH", str(wikicontent))
        
        diff = """<<<<<<< SEARCH
Line 1
=======
Line ONE
>>>>>>> REPLACE
<<<<<<< SEARCH
Line 3
=======
Line THREE
>>>>>>> REPLACE"""
        
        result = edit_file("articles/story.md", diff)
        
        assert result["success"] is True
        content = test_file.read_text()
        assert "Line ONE" in content
        assert "Line THREE" in content
        assert "Line 2" in content  # Unchanged
    
    def test_returns_error_for_search_not_found(self, tmp_path, monkeypatch):
        """Should return error when search text doesn't exist."""
        wikicontent = tmp_path / "wikicontent"
        articles = wikicontent / "articles"
        articles.mkdir(parents=True)
        
        test_file = articles / "test.md"
        test_file.write_text("Some content\n")
        
        monkeypatch.setenv("WIKICONTENT_PATH", str(wikicontent))
        
        diff = """<<<<<<< SEARCH
This text does not exist
=======
Replacement
>>>>>>> REPLACE"""
        
        result = edit_file("articles/test.md", diff)
        
        assert result["success"] is False
        assert "error" in result
        assert "not found" in result["error"].lower()
    
    def test_returns_error_for_invalid_diff_format(self, tmp_path, monkeypatch):
        """Should return error for malformed diff."""
        wikicontent = tmp_path / "wikicontent"
        wikicontent.mkdir()
        
        monkeypatch.setenv("WIKICONTENT_PATH", str(wikicontent))
        
        result = edit_file("test.md", "This is not a valid diff format")
        
        assert result["success"] is False
        assert "error" in result


class TestAddToStory:
    """Test add_to_story functionality."""
    
    def test_appends_content_to_file(self, tmp_path, monkeypatch):
        """Should append content to end of file."""
        wikicontent = tmp_path / "wikicontent"
        stories = wikicontent / "stories"
        stories.mkdir(parents=True)
        
        story_file = stories / "tale.md"
        story_file.write_text("Chapter 1\n\nThe beginning.\n")
        
        monkeypatch.setenv("WIKICONTENT_PATH", str(wikicontent))
        
        result = add_to_story("\nChapter 2\n\nThe middle.\n", "stories/tale.md")
        
        assert result["success"] is True
        assert result["file_path"] == "stories/tale.md"
        assert result["mode"] == "append"
        assert result["lines_added"] > 0
        
        # Verify content was appended
        content = story_file.read_text()
        assert "Chapter 1" in content
        assert "Chapter 2" in content
        assert content.endswith("The middle.\n")
    
    def test_creates_file_if_not_exists(self, tmp_path, monkeypatch):
        """Should create file if it doesn't exist."""
        wikicontent = tmp_path / "wikicontent"
        wikicontent.mkdir()
        
        monkeypatch.setenv("WIKICONTENT_PATH", str(wikicontent))
        
        result = add_to_story("# New Story\n\nOnce upon a time...\n", "stories/new.md")
        
        assert result["success"] is True
        
        # Verify file was created
        new_file = wikicontent / "stories" / "new.md"
        assert new_file.exists()
        assert "Once upon a time" in new_file.read_text()
    
    def test_returns_dict_with_line_counts(self, tmp_path, monkeypatch):
        """Should return structured output."""
        wikicontent = tmp_path / "wikicontent"
        wikicontent.mkdir()
        
        monkeypatch.setenv("WIKICONTENT_PATH", str(wikicontent))
        
        result = add_to_story("Line 1\nLine 2\n", "test.md")
        
        assert isinstance(result, dict)
        assert result["success"] is True
        assert "lines_added" in result
        assert "lines_removed" in result
        assert result["lines_removed"] == 0  # Always 0 for append
        assert result["lines_added"] == 3  # 2 newlines + 1


class TestToolIntegration:
    """Test tools working together."""
    
    def test_edit_then_read(self, tmp_path, monkeypatch):
        """Should be able to edit then read back."""
        wikicontent = tmp_path / "wikicontent"
        wikicontent.mkdir()
        
        monkeypatch.setenv("WIKICONTENT_PATH", str(wikicontent))
        
        # Create file
        diff = """<<<<<<< SEARCH
=======
# Article

Initial content.
>>>>>>> REPLACE"""
        
        edit_result = edit_file("test.md", diff)
        assert edit_result["success"] is True
        
        # Read it back
        read_result = read_file("test.md")
        assert "content" in read_result
        assert "Initial content" in read_result["content"]
    
    def test_add_to_story_then_edit(self, tmp_path, monkeypatch):
        """Should be able to append then edit."""
        wikicontent = tmp_path / "wikicontent"
        wikicontent.mkdir()
        
        monkeypatch.setenv("WIKICONTENT_PATH", str(wikicontent))
        
        # Add initial content
        add_result = add_to_story("Chapter 1\nThe hero awoke.\n", "story.md")
        assert add_result["success"] is True
        
        # Add more
        add_result2 = add_to_story("Chapter 2\nThe villain appeared.\n", "story.md")
        assert add_result2["success"] is True
        
        # Edit it
        diff = """<<<<<<< SEARCH
The hero awoke.
=======
The hero awoke with a start.
>>>>>>> REPLACE"""
        
        edit_result = edit_file("story.md", diff)
        assert edit_result["success"] is True
        
        # Verify
        read_result = read_file("story.md")
        content = read_result["content"]
        assert "awoke with a start" in content
        assert "villain appeared" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

