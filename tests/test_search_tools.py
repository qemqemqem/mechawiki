"""
Tests for search tools (src/tools/search.py).
"""
import pytest
import toml
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools import search


class TestFindArticles:
    """Test find_articles functionality."""
    
    def test_finds_matching_articles(self, tmp_path):
        """Should find articles matching search term."""
        config_path = tmp_path / "config.toml"
        config_path.write_text(toml.dumps({
            "paths": {
                "content_repo": str(tmp_path / "content"),
                "articles_dir": "articles"
            },
            "story": {"current_story": "test"}
        }))
        
        articles_dir = tmp_path / "content" / "articles"
        articles_dir.mkdir(parents=True)
        
        (articles_dir / "wizard-merlin.md").write_text("# Merlin\n")
        (articles_dir / "wizard-gandalf.md").write_text("# Gandalf\n")
        (articles_dir / "castle.md").write_text("# Castle\n")
        
        # Configure module
        search._config = toml.load(str(config_path))
        search._content_repo_path = Path(search._config["paths"]["content_repo"])
        search._articles_dir_name = search._config["paths"]["articles_dir"]
        
        result = search.find_articles("wizard")
        
        assert len(result) == 2
        assert "wizard-merlin.md" in result
        assert "wizard-gandalf.md" in result
        assert "castle.md" not in result
    
    def test_wildcard_returns_all_articles(self, tmp_path):
        """Should return all articles when searching with *."""
        config_path = tmp_path / "config.toml"
        config_path.write_text(toml.dumps({
            "paths": {
                "content_repo": str(tmp_path / "content"),
                "articles_dir": "articles"
            },
            "story": {"current_story": "test"}
        }))
        
        articles_dir = tmp_path / "content" / "articles"
        articles_dir.mkdir(parents=True)
        
        (articles_dir / "article1.md").write_text("# Article 1\n")
        (articles_dir / "article2.md").write_text("# Article 2\n")
        (articles_dir / "article3.md").write_text("# Article 3\n")
        
        search._config = toml.load(str(config_path))
        search._content_repo_path = Path(search._config["paths"]["content_repo"])
        search._articles_dir_name = search._config["paths"]["articles_dir"]
        
        result = search.find_articles("*")
        
        assert len(result) == 3
        assert all(f"article{i}.md" in result for i in range(1, 4))
    
    def test_case_insensitive_search(self, tmp_path):
        """Should be case-insensitive."""
        config_path = tmp_path / "config.toml"
        config_path.write_text(toml.dumps({
            "paths": {
                "content_repo": str(tmp_path / "content"),
                "articles_dir": "articles"
            },
            "story": {"current_story": "test"}
        }))
        
        articles_dir = tmp_path / "content" / "articles"
        articles_dir.mkdir(parents=True)
        
        (articles_dir / "London.md").write_text("# London\n")
        
        search._config = toml.load(str(config_path))
        search._content_repo_path = Path(search._config["paths"]["content_repo"])
        search._articles_dir_name = search._config["paths"]["articles_dir"]
        
        result = search.find_articles("london")
        
        assert len(result) == 1
        assert "London.md" in result


class TestFindImages:
    """Test find_images functionality."""
    
    def test_finds_matching_images(self, tmp_path):
        """Should find images matching search term."""
        config_path = tmp_path / "config.toml"
        config_path.write_text(toml.dumps({
            "paths": {
                "content_repo": str(tmp_path / "content"),
                "images_dir": "images"
            },
            "story": {"current_story": "test"}
        }))
        
        images_dir = tmp_path / "content" / "images"
        images_dir.mkdir(parents=True)
        
        (images_dir / "castle-ruins.png").write_text("")
        (images_dir / "castle-hall.jpg").write_text("")
        (images_dir / "wizard.png").write_text("")
        
        search._config = toml.load(str(config_path))
        search._content_repo_path = Path(search._config["paths"]["content_repo"])
        search._images_dir_name = search._config["paths"]["images_dir"]
        
        result = search.find_images("castle")
        
        assert len(result) == 2
        assert "castle-ruins.png" in result
        assert "castle-hall.jpg" in result
    
    def test_wildcard_returns_all_images(self, tmp_path):
        """Should return all images when searching with *."""
        config_path = tmp_path / "config.toml"
        config_path.write_text(toml.dumps({
            "paths": {
                "content_repo": str(tmp_path / "content"),
                "images_dir": "images"
            },
            "story": {"current_story": "test"}
        }))
        
        images_dir = tmp_path / "content" / "images"
        images_dir.mkdir(parents=True)
        
        (images_dir / "image1.png").write_text("")
        (images_dir / "image2.jpg").write_text("")
        
        search._config = toml.load(str(config_path))
        search._content_repo_path = Path(search._config["paths"]["content_repo"])
        search._images_dir_name = search._config["paths"]["images_dir"]
        
        result = search.find_images("*")
        
        assert len(result) == 2


class TestFindSongs:
    """Test find_songs functionality."""
    
    def test_finds_matching_songs(self, tmp_path):
        """Should find songs matching search term."""
        config_path = tmp_path / "config.toml"
        config_path.write_text(toml.dumps({
            "paths": {
                "content_repo": str(tmp_path / "content"),
                "songs_dir": "songs"
            },
            "story": {"current_story": "test"}
        }))
        
        songs_dir = tmp_path / "content" / "songs"
        songs_dir.mkdir(parents=True)
        
        (songs_dir / "epic-battle.mp3").write_text("")
        (songs_dir / "battle-cry.wav").write_text("")
        (songs_dir / "peaceful-melody.ogg").write_text("")
        
        search._config = toml.load(str(config_path))
        search._content_repo_path = Path(search._config["paths"]["content_repo"])
        search._songs_dir_name = search._config["paths"]["songs_dir"]
        
        result = search.find_songs("battle")
        
        assert len(result) == 2
        assert "epic-battle.mp3" in result
        assert "battle-cry.wav" in result


class TestFindFiles:
    """Test find_files convenience function."""
    
    def test_finds_files_across_all_types(self, tmp_path):
        """Should find files across articles, images, and songs."""
        config_path = tmp_path / "config.toml"
        config_path.write_text(toml.dumps({
            "paths": {
                "content_repo": str(tmp_path / "content"),
                "articles_dir": "articles",
                "images_dir": "images",
                "songs_dir": "songs"
            },
            "story": {"current_story": "test"}
        }))
        
        content = tmp_path / "content"
        
        articles_dir = content / "articles"
        articles_dir.mkdir(parents=True)
        (articles_dir / "wizard-lore.md").write_text("# Wizard\n")
        
        images_dir = content / "images"
        images_dir.mkdir(parents=True)
        (images_dir / "wizard-hat.png").write_text("")
        
        songs_dir = content / "songs"
        songs_dir.mkdir(parents=True)
        (songs_dir / "wizard-song.mp3").write_text("")
        
        search._config = toml.load(str(config_path))
        search._content_repo_path = Path(search._config["paths"]["content_repo"])
        search._articles_dir_name = search._config["paths"]["articles_dir"]
        search._images_dir_name = search._config["paths"]["images_dir"]
        search._songs_dir_name = search._config["paths"]["songs_dir"]
        
        result = search.find_files("wizard")
        
        assert len(result) == 3
        assert "wizard-lore.md" in result
        assert "wizard-hat.png" in result
        assert "wizard-song.mp3" in result
    
    def test_returns_sorted_list(self, tmp_path):
        """Should return sorted list of files."""
        config_path = tmp_path / "config.toml"
        config_path.write_text(toml.dumps({
            "paths": {
                "content_repo": str(tmp_path / "content"),
                "articles_dir": "articles",
                "images_dir": "images",
                "songs_dir": "songs"
            },
            "story": {"current_story": "test"}
        }))
        
        content = tmp_path / "content"
        
        articles_dir = content / "articles"
        articles_dir.mkdir(parents=True)
        (articles_dir / "zebra.md").write_text("")
        (articles_dir / "aardvark.md").write_text("")
        
        images_dir = content / "images"
        images_dir.mkdir(parents=True)
        (images_dir / "monkey.png").write_text("")
        
        songs_dir = content / "songs"
        songs_dir.mkdir(parents=True)
        
        search._config = toml.load(str(config_path))
        search._content_repo_path = Path(search._config["paths"]["content_repo"])
        search._articles_dir_name = search._config["paths"]["articles_dir"]
        search._images_dir_name = search._config["paths"]["images_dir"]
        search._songs_dir_name = search._config["paths"]["songs_dir"]
        
        result = search.find_files("*")
        
        # Should be sorted alphabetically
        assert result[0] == "aardvark.md"
        assert result[-1] == "zebra.md"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

