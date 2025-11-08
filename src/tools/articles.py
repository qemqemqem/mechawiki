"""
Article reading tools for accessing article content from the content repository.
"""
import os
import toml
from pathlib import Path
from typing import Optional

# Load config once at module level
try:
    _config = toml.load("config.toml")
    _content_repo_path = Path(_config["paths"]["content_repo"])
    _articles_dir_name = _config["paths"]["articles_dir"]
except Exception as e:
    print(f"❌ Error loading config in articles.py: {e}")
    _config = None
    _content_repo_path = None
    _articles_dir_name = "articles"


def read_article(article_name: str) -> str:
    """Read the contents of an article file.
    
    Searches for an article by name (with or without .md extension) and returns its contents.
    The search is case-insensitive and will match partial names.
    
    Parameters
    ----------
    article_name : str
        The name of the article to read. Can be with or without .md extension.
        Case-insensitive search. Can be a partial match.
        
    Returns
    -------
    str
        The contents of the article file. Returns an error message if the article
        is not found or if config could not be loaded.
        
    Examples
    --------
    >>> read_article("wizard-merlin")
    "# Wizard Merlin\n\nMerlin was a powerful wizard..."
    
    >>> read_article("london.md")
    "# London\n\nLondon is a great city..."
    
    >>> read_article("castle")
    "# Haunted Castle\n\nThe castle stood on the hill..."
    """
    # Check if config was loaded successfully
    if _config is None or _content_repo_path is None:
        return "❌ Error: Could not load config.toml or required config values"
    
    if not article_name.strip():
        return "❌ Error: Article name cannot be empty"
    
    articles_dir = _content_repo_path / _articles_dir_name
    
    if not articles_dir.exists():
        return f"❌ Error: Articles directory not found: {articles_dir}"
    
    # Normalize the article name
    article_name = article_name.strip()
    search_name = article_name.lower()
    
    # If no extension provided, assume .md
    if not article_name.endswith('.md'):
        article_name += '.md'
        search_name += '.md'
    
    # Search for the article file
    found_file = None
    for file_path in articles_dir.iterdir():
        if file_path.is_file() and file_path.name.lower() == search_name:
            found_file = file_path
            break
    
    # If exact match not found, try partial match
    if found_file is None:
        for file_path in articles_dir.iterdir():
            if file_path.is_file() and search_name.replace('.md', '') in file_path.name.lower():
                found_file = file_path
                break
    
    if found_file is None:
        return f"❌ Error: Article '{article_name}' not found in {articles_dir}"
    
    try:
        with open(found_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return content
    
    except Exception as e:
        return f"❌ Error reading article '{found_file.name}': {str(e)}"


if __name__ == "__main__":
    # Test the article reading functionality
    print("🧪 Testing article reading functions...")
    
    # Test reading an article
    print("\n📚 Testing read_article:")
    
    # Try to read a common article name
    test_names = ["london", "wizard", "castle", "test"]
    
    for name in test_names:
        print(f"\n  Testing '{name}':")
        content = read_article(name)
        if content.startswith("❌"):
            print(f"    {content}")
        else:
            # Show first 100 characters
            preview = content[:100].replace('\n', ' ')
            print(f"    ✅ Found article, preview: {preview}...")
            print(f"    Full length: {len(content)} characters")
