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


def read_article(article_name: str):
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
    dict or str
        Dict with file_path, content, and read flag for successful reads.
        Error message string if the article is not found or if config could not be loaded.
        
    Examples
    --------
    >>> read_article("wizard-merlin")
    {"file_path": "articles/wizard-merlin.md", "content": "# Wizard...", "read": True, ...}
    
    >>> read_article("london.md")
    {"file_path": "articles/london.md", "content": "# London...", "read": True, ...}
    
    >>> read_article("castle")
    {"file_path": "articles/haunted-castle.md", "content": "# Haunted...", "read": True, ...}
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
        
        # Get relative path from content repo
        rel_path = found_file.relative_to(_content_repo_path)
        
        # Return structured data for log watcher
        return {
            "file_path": str(rel_path),
            "content": content,
            "lines_added": 0,
            "lines_removed": 0,
            "read": True,
            "message": f"📖 Read article: {found_file.name}"
        }
    
    except Exception as e:
        return f"❌ Error reading article '{found_file.name}': {str(e)}"


def write_article(article_name: str, content: str):
    """
    Write content to an article file.
    
    Parameters
    ----------
    article_name : str
        Name of the article (with or without .md extension)
    content : str
        Content to write to the article
    
    Returns
    -------
    dict or str
        Success dict with file_path and line counts, or error message string
    """
    if _config is None or _content_repo_path is None:
        return "❌ Error: Could not load config.toml"
    
    if not article_name.strip():
        return "❌ Error: Article name cannot be empty"
    
    articles_dir = _content_repo_path / _articles_dir_name
    articles_dir.mkdir(parents=True, exist_ok=True)
    
    # Add .md extension if not present
    if not article_name.endswith('.md'):
        article_name += '.md'
    
    file_path = articles_dir / article_name
    
    # Check if file exists to calculate diff
    lines_removed = 0
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            old_content = f.read()
        lines_removed = old_content.count('\n') + 1
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        lines_added = content.count('\n') + 1
        
        # Return structured data for log watcher
        return {
            "file_path": f"{_articles_dir_name}/{article_name}",
            "lines_added": lines_added,
            "lines_removed": lines_removed,
            "message": f"✅ Successfully wrote to {article_name}"
        }
    except Exception as e:
        return f"❌ Error writing article: {str(e)}"


def search_articles(query: str) -> str:
    """
    Search for articles by name containing the query string.
    
    Parameters
    ----------
    query : str
        Search term (case-insensitive)
    
    Returns
    -------
    str
        List of matching article names
    """
    if _config is None or _content_repo_path is None:
        return "❌ Error: Could not load config.toml"
    
    articles_dir = _content_repo_path / _articles_dir_name
    
    if not articles_dir.exists():
        return f"❌ Error: Articles directory not found: {articles_dir}"
    
    query = query.lower()
    matches = []
    
    for file_path in articles_dir.iterdir():
        if file_path.is_file() and query in file_path.name.lower():
            matches.append(file_path.name)
    
    if not matches:
        return f"No articles found matching '{query}'"
    
    return "Matching articles:\n" + "\n".join(f"- {name}" for name in sorted(matches))


def list_articles_in_directory(directory: Optional[str] = None) -> str:
    """
    List all article files in the articles directory.
    
    Parameters
    ----------
    directory : str, optional
        Subdirectory within articles to list (if articles are organized in folders)
    
    Returns
    -------
    str
        List of article names
    """
    if _config is None or _content_repo_path is None:
        return "❌ Error: Could not load config.toml"
    
    articles_dir = _content_repo_path / _articles_dir_name
    if directory:
        articles_dir = articles_dir / directory
    
    if not articles_dir.exists():
        return f"❌ Error: Directory not found: {articles_dir}"
    
    articles = []
    for file_path in articles_dir.iterdir():
        if file_path.is_file() and file_path.name.endswith('.md'):
            articles.append(file_path.name)
    
    if not articles:
        return f"No articles found in {articles_dir}"
    
    return f"Articles in {articles_dir.name}:\n" + "\n".join(f"- {name}" for name in sorted(articles))


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
