"""
Unit tests for file operation tools' structured output.

Simple, focused tests on tool return values.
"""
import pytest
import tempfile
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestWriteArticleOutput:
    """Test write_article returns correct structure."""
    
    def test_returns_dict_with_required_fields(self, tmp_path):
        """Must return dict with file_path, lines_added, lines_removed."""
        # Setup
        import toml
        config_path = tmp_path / "config.toml"
        config_path.write_text(toml.dumps({
            "paths": {
                "content_repo": str(tmp_path / "content"),
                "articles_dir": "articles"
            }
        }))
        
        # Import and configure
        from src.tools import articles
        articles._config = toml.load(str(config_path))
        articles._content_repo_path = Path(articles._config["paths"]["content_repo"])
        articles._articles_dir_name = articles._config["paths"]["articles_dir"]
        
        # Execute
        result = articles.write_article("test", "line1\nline2\n")
        
        # Assert required fields
        assert isinstance(result, dict)
        assert "file_path" in result
        assert "lines_added" in result
        assert "lines_removed" in result
        assert isinstance(result["lines_added"], int)
        assert isinstance(result["lines_removed"], int)
    
    def test_calculates_lines_correctly_for_new_file(self, tmp_path):
        """New files should have lines_removed = 0."""
        import toml
        config_path = tmp_path / "config.toml"
        config_path.write_text(toml.dumps({
            "paths": {
                "content_repo": str(tmp_path / "content"),
                "articles_dir": "articles"
            }
        }))
        
        from src.tools import articles
        articles._config = toml.load(str(config_path))
        articles._content_repo_path = Path(articles._config["paths"]["content_repo"])
        articles._articles_dir_name = articles._config["paths"]["articles_dir"]
        
        result = articles.write_article("new-article", "# Title\n\nContent\n")
        
        # Content has 3 newlines, count('\n') + 1 = 4 lines
        assert result["lines_added"] == 4
        assert result["lines_removed"] == 0
    
    def test_calculates_lines_correctly_for_overwrite(self, tmp_path):
        """Overwriting should count removed lines."""
        import toml
        config_path = tmp_path / "config.toml"
        config_path.write_text(toml.dumps({
            "paths": {
                "content_repo": str(tmp_path / "content"),
                "articles_dir": "articles"
            }
        }))
        
        from src.tools import articles
        articles._config = toml.load(str(config_path))
        articles._content_repo_path = Path(articles._config["paths"]["content_repo"])
        articles._articles_dir_name = articles._config["paths"]["articles_dir"]
        
        # First write - 3 newlines = 4 lines
        articles.write_article("test", "old1\nold2\nold3\n")
        
        # Overwrite with shorter content - 2 newlines = 3 lines
        result = articles.write_article("test", "new1\nnew2\n")
        
        assert result["lines_added"] == 3
        assert result["lines_removed"] == 4
    
    def test_error_returns_string_not_dict(self):
        """Errors should return strings, not dicts."""
        from src.tools import articles
        
        # Force error by nulling config
        original = articles._config
        articles._config = None
        
        result = articles.write_article("test", "content")
        
        articles._config = original
        
        # Should be error string
        assert isinstance(result, str)
        assert "❌" in result or "Error" in result


class TestWriteStoryOutput:
    """Test write_story returns correct structure."""
    
    def test_returns_dict_with_required_fields(self, tmp_path, monkeypatch):
        """Must return dict with file_path, lines_added, lines_removed."""
        wikicontent = tmp_path / "wikicontent"
        wikicontent.mkdir()
        monkeypatch.setenv("WIKICONTENT_PATH", str(wikicontent))
        
        from src.tools.story import write_story
        
        result = write_story(
            content="Chapter 1\n",
            filepath="stories/test.md",
            append=False
        )
        
        assert isinstance(result, dict)
        assert result["success"] is True
        assert "file_path" in result
        assert "lines_added" in result
        assert "lines_removed" in result
        assert result["file_path"] == "stories/test.md"
    
    def test_append_doesnt_count_removed_lines(self, tmp_path, monkeypatch):
        """Append mode should have lines_removed = 0."""
        wikicontent = tmp_path / "wikicontent"
        stories = wikicontent / "stories"
        stories.mkdir(parents=True)
        
        # Create existing file
        (stories / "test.md").write_text("Existing\n")
        
        monkeypatch.setenv("WIKICONTENT_PATH", str(wikicontent))
        
        from src.tools.story import write_story
        
        result = write_story(
            content="New content\n",
            filepath="stories/test.md",
            append=True
        )
        
        assert result["lines_removed"] == 0
    
    def test_overwrite_counts_removed_lines(self, tmp_path, monkeypatch):
        """Overwrite mode should count removed lines."""
        wikicontent = tmp_path / "wikicontent"
        stories = wikicontent / "stories"
        stories.mkdir(parents=True)
        
        # Create existing file - 3 newlines = 4 lines
        (stories / "test.md").write_text("Line1\nLine2\nLine3\n")
        
        monkeypatch.setenv("WIKICONTENT_PATH", str(wikicontent))
        
        from src.tools.story import write_story
        
        result = write_story(
            content="New\n",
            filepath="stories/test.md",
            append=False
        )
        
        # 1 newline = 2 lines, removed 4 lines
        assert result["lines_added"] == 2
        assert result["lines_removed"] == 4


class TestEditStoryOutput:
    """Test edit_story returns correct structure."""
    
    def test_returns_dict_with_required_fields(self, tmp_path, monkeypatch):
        """Must return dict with file_path, lines_added, lines_removed."""
        wikicontent = tmp_path / "wikicontent"
        stories = wikicontent / "stories"
        stories.mkdir(parents=True)
        
        (stories / "test.md").write_text("Find this text\n")
        
        monkeypatch.setenv("WIKICONTENT_PATH", str(wikicontent))
        
        from src.tools.story import edit_story
        
        result = edit_story(
            filepath="stories/test.md",
            search="Find this",
            replace="Found and replaced"
        )
        
        assert isinstance(result, dict)
        assert result["success"] is True
        assert "file_path" in result
        assert "lines_added" in result
        assert "lines_removed" in result
    
    def test_calculates_line_changes(self, tmp_path, monkeypatch):
        """Should calculate line changes from search/replace."""
        wikicontent = tmp_path / "wikicontent"
        stories = wikicontent / "stories"
        stories.mkdir(parents=True)
        
        # Single line
        (stories / "test.md").write_text("Text\n")
        
        monkeypatch.setenv("WIKICONTENT_PATH", str(wikicontent))
        
        from src.tools.story import edit_story
        
        # Replace with multi-line
        result = edit_story(
            filepath="stories/test.md",
            search="Text",
            replace="Line1\nLine2\nLine3"
        )
        
        # Should detect 2 lines added
        assert result["lines_added"] == 2
        assert result["lines_removed"] == 0


class TestReadArticleOutput:
    """Test read_article returns correct structure."""
    
    def test_returns_dict_with_required_fields(self, tmp_path):
        """Must return dict with file_path and read flag."""
        import toml
        config_path = tmp_path / "config.toml"
        config_path.write_text(toml.dumps({
            "paths": {
                "content_repo": str(tmp_path / "content"),
                "articles_dir": "articles"
            }
        }))
        
        from src.tools import articles
        articles._config = toml.load(str(config_path))
        articles._content_repo_path = Path(articles._config["paths"]["content_repo"])
        articles._articles_dir_name = articles._config["paths"]["articles_dir"]
        
        # Create an article to read
        articles_dir = tmp_path / "content" / "articles"
        articles_dir.mkdir(parents=True)
        (articles_dir / "test.md").write_text("# Test\n\nContent\n")
        
        result = articles.read_article("test")
        
        assert isinstance(result, dict)
        assert "file_path" in result
        assert "content" in result
        assert result["read"] is True
        assert result["lines_added"] == 0
        assert result["lines_removed"] == 0
    
    def test_read_returns_content(self, tmp_path):
        """Read should return the file content."""
        import toml
        config_path = tmp_path / "config.toml"
        config_path.write_text(toml.dumps({
            "paths": {
                "content_repo": str(tmp_path / "content"),
                "articles_dir": "articles"
            }
        }))
        
        from src.tools import articles
        articles._config = toml.load(str(config_path))
        articles._content_repo_path = Path(articles._config["paths"]["content_repo"])
        articles._articles_dir_name = articles._config["paths"]["articles_dir"]
        
        # Create an article
        articles_dir = tmp_path / "content" / "articles"
        articles_dir.mkdir(parents=True)
        test_content = "# Test Article\n\nThis is test content.\n"
        (articles_dir / "test.md").write_text(test_content)
        
        result = articles.read_article("test")
        
        assert result["content"] == test_content


def test_all_tools_have_consistent_error_format():
    """All tools should return error dicts or strings for errors."""
    from src.tools import articles
    from src.tools.story import edit_story
    
    # Force errors
    original = articles._config
    articles._config = None
    
    article_error = articles.write_article("test", "content")
    read_error = articles.read_article("test")
    
    articles._config = original
    
    # write_story creates directories, so it doesn't error
    # Test edit_story with non-existent file instead
    edit_error = edit_story("this/file/does/not/exist.md", "search", "replace")
    
    # read_article returns dict with error field
    assert isinstance(read_error, dict) and "error" in read_error
    # write_article returns error string
    assert isinstance(article_error, str)
    # edit_story returns dict with success=False
    assert isinstance(edit_error, dict) and edit_error["success"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

