"""
Tests for article reading and searching tools (src/tools/articles.py).
"""
import pytest
import toml
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools import articles


class TestReadArticle:
    """Test read_article functionality."""
    
    def test_reads_article_successfully(self, tmp_path):
        """Should read article content."""
        # Setup config
        config_path = tmp_path / "config.toml"
        config_path.write_text(toml.dumps({
            "paths": {
                "content_repo": str(tmp_path / "content"),
                "articles_dir": "articles"
            }
        }))
        
        # Create article
        articles_dir = tmp_path / "content" / "articles"
        articles_dir.mkdir(parents=True)
        
        test_article = articles_dir / "wizard.md"
        test_article.write_text("# Wizard\n\nMerlin was a powerful wizard.\n")
        
        # Configure module
        articles._config = toml.load(str(config_path))
        articles._content_repo_path = Path(articles._config["paths"]["content_repo"])
        articles._articles_dir_name = articles._config["paths"]["articles_dir"]
        
        # Test
        result = articles.read_article("wizard")
        
        assert isinstance(result, dict)
        assert "content" in result
        assert "Wizard" in result["content"]
        assert "Merlin" in result["content"]
    
    def test_reads_article_with_md_extension(self, tmp_path):
        """Should handle .md extension."""
        config_path = tmp_path / "config.toml"
        config_path.write_text(toml.dumps({
            "paths": {
                "content_repo": str(tmp_path / "content"),
                "articles_dir": "articles"
            }
        }))
        
        articles_dir = tmp_path / "content" / "articles"
        articles_dir.mkdir(parents=True)
        
        test_article = articles_dir / "castle.md"
        test_article.write_text("# Castle\n\nA haunted castle.\n")
        
        articles._config = toml.load(str(config_path))
        articles._content_repo_path = Path(articles._config["paths"]["content_repo"])
        articles._articles_dir_name = articles._config["paths"]["articles_dir"]
        
        result = articles.read_article("castle.md")
        
        assert isinstance(result, dict)
        assert "Castle" in result["content"]
        assert "haunted" in result["content"]
    
    def test_case_insensitive_search(self, tmp_path):
        """Should be case-insensitive."""
        config_path = tmp_path / "config.toml"
        config_path.write_text(toml.dumps({
            "paths": {
                "content_repo": str(tmp_path / "content"),
                "articles_dir": "articles"
            }
        }))
        
        articles_dir = tmp_path / "content" / "articles"
        articles_dir.mkdir(parents=True)
        
        test_article = articles_dir / "London.md"
        test_article.write_text("# London\n\nA great city.\n")
        
        articles._config = toml.load(str(config_path))
        articles._content_repo_path = Path(articles._config["paths"]["content_repo"])
        articles._articles_dir_name = articles._config["paths"]["articles_dir"]
        
        result = articles.read_article("london")
        
        assert isinstance(result, dict)
        assert "London" in result["content"]
    
    def test_partial_match(self, tmp_path):
        """Should support partial matching."""
        config_path = tmp_path / "config.toml"
        config_path.write_text(toml.dumps({
            "paths": {
                "content_repo": str(tmp_path / "content"),
                "articles_dir": "articles"
            }
        }))
        
        articles_dir = tmp_path / "content" / "articles"
        articles_dir.mkdir(parents=True)
        
        test_article = articles_dir / "wizard-merlin.md"
        test_article.write_text("# Wizard Merlin\n\nMerlin.\n")
        
        articles._config = toml.load(str(config_path))
        articles._content_repo_path = Path(articles._config["paths"]["content_repo"])
        articles._articles_dir_name = articles._config["paths"]["articles_dir"]
        
        result = articles.read_article("wizard")
        
        assert isinstance(result, dict)
        assert "Merlin" in result["content"]
    
    def test_returns_error_for_nonexistent_article(self, tmp_path):
        """Should return error dict for missing article."""
        config_path = tmp_path / "config.toml"
        config_path.write_text(toml.dumps({
            "paths": {
                "content_repo": str(tmp_path / "content"),
                "articles_dir": "articles"
            }
        }))
        
        articles_dir = tmp_path / "content" / "articles"
        articles_dir.mkdir(parents=True)
        
        articles._config = toml.load(str(config_path))
        articles._content_repo_path = Path(articles._config["paths"]["content_repo"])
        articles._articles_dir_name = articles._config["paths"]["articles_dir"]
        
        result = articles.read_article("does-not-exist")
        
        assert isinstance(result, dict)
        assert "error" in result
        assert "not found" in result["error"].lower()


class TestSearchArticles:
    """Test search_articles functionality."""
    
    def test_finds_matching_articles(self, tmp_path):
        """Should find articles matching search term."""
        config_path = tmp_path / "config.toml"
        config_path.write_text(toml.dumps({
            "paths": {
                "content_repo": str(tmp_path / "content"),
                "articles_dir": "articles"
            }
        }))
        
        articles_dir = tmp_path / "content" / "articles"
        articles_dir.mkdir(parents=True)
        
        (articles_dir / "wizard-merlin.md").write_text("# Merlin\n")
        (articles_dir / "wizard-gandalf.md").write_text("# Gandalf\n")
        (articles_dir / "castle.md").write_text("# Castle\n")
        
        articles._config = toml.load(str(config_path))
        articles._content_repo_path = Path(articles._config["paths"]["content_repo"])
        articles._articles_dir_name = articles._config["paths"]["articles_dir"]
        
        result = articles.search_articles("wizard")
        
        assert "wizard-merlin.md" in result
        assert "wizard-gandalf.md" in result
        assert "castle.md" not in result
    
    def test_case_insensitive_search(self, tmp_path):
        """Should be case-insensitive."""
        config_path = tmp_path / "config.toml"
        config_path.write_text(toml.dumps({
            "paths": {
                "content_repo": str(tmp_path / "content"),
                "articles_dir": "articles"
            }
        }))
        
        articles_dir = tmp_path / "content" / "articles"
        articles_dir.mkdir(parents=True)
        
        (articles_dir / "London.md").write_text("# London\n")
        
        articles._config = toml.load(str(config_path))
        articles._content_repo_path = Path(articles._config["paths"]["content_repo"])
        articles._articles_dir_name = articles._config["paths"]["articles_dir"]
        
        result = articles.search_articles("london")
        
        assert "London.md" in result
    
    def test_returns_message_when_no_matches(self, tmp_path):
        """Should return message when no articles match."""
        config_path = tmp_path / "config.toml"
        config_path.write_text(toml.dumps({
            "paths": {
                "content_repo": str(tmp_path / "content"),
                "articles_dir": "articles"
            }
        }))
        
        articles_dir = tmp_path / "content" / "articles"
        articles_dir.mkdir(parents=True)
        
        articles._config = toml.load(str(config_path))
        articles._content_repo_path = Path(articles._config["paths"]["content_repo"])
        articles._articles_dir_name = articles._config["paths"]["articles_dir"]
        
        result = articles.search_articles("nonexistent")
        
        assert "No articles found" in result


class TestListArticlesInDirectory:
    """Test list_articles_in_directory functionality."""
    
    def test_lists_all_articles(self, tmp_path):
        """Should list all articles in directory."""
        config_path = tmp_path / "config.toml"
        config_path.write_text(toml.dumps({
            "paths": {
                "content_repo": str(tmp_path / "content"),
                "articles_dir": "articles"
            }
        }))
        
        articles_dir = tmp_path / "content" / "articles"
        articles_dir.mkdir(parents=True)
        
        (articles_dir / "article1.md").write_text("# Article 1\n")
        (articles_dir / "article2.md").write_text("# Article 2\n")
        (articles_dir / "article3.md").write_text("# Article 3\n")
        
        articles._config = toml.load(str(config_path))
        articles._content_repo_path = Path(articles._config["paths"]["content_repo"])
        articles._articles_dir_name = articles._config["paths"]["articles_dir"]
        
        result = articles.list_articles_in_directory()
        
        assert "article1.md" in result
        assert "article2.md" in result
        assert "article3.md" in result
    
    def test_returns_message_when_no_articles(self, tmp_path):
        """Should return message when directory is empty."""
        config_path = tmp_path / "config.toml"
        config_path.write_text(toml.dumps({
            "paths": {
                "content_repo": str(tmp_path / "content"),
                "articles_dir": "articles"
            }
        }))
        
        articles_dir = tmp_path / "content" / "articles"
        articles_dir.mkdir(parents=True)
        
        articles._config = toml.load(str(config_path))
        articles._content_repo_path = Path(articles._config["paths"]["content_repo"])
        articles._articles_dir_name = articles._config["paths"]["articles_dir"]
        
        result = articles.list_articles_in_directory()
        
        assert "No articles found" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

