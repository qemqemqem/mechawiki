"""
Article reading tools for loading complete article content by name.
"""
import os
import toml
from pathlib import Path
from typing import Optional

# Load config once at module level
try:
    _config = toml.load("config.toml")
    _content_repo_path = Path(_config["paths"]["content_repo"])
    _current_story = _config["story"]["current_story"]
    _articles_dir_name = _config["paths"]["articles_dir"]
except Exception as e:
    print(f"❌ Error loading config in articles.py: {e}")
    _config = None
    _content_repo_path = None
    _current_story = None
    _articles_dir_name = "articles"


def _normalize_path(path: Path, base_path: Path) -> Optional[Path]:
    """Normalize and validate a path to prevent directory traversal attacks.
    
    Parameters
    ----------
    path : Path
        The path to normalize and validate
    base_path : Path
        The base directory that the path must be within
        
    Returns
    -------
    Optional[Path]
        The normalized path if valid, None if path traversal detected
    """
    try:
        # Resolve the path and check if it's within the base directory
        resolved_path = path.resolve()
        resolved_base = base_path.resolve()
        
        # Check if the resolved path is within the base directory
        try:
            resolved_path.relative_to(resolved_base)
            return resolved_path
        except ValueError:
            # Path is outside the base directory
            return None
    except (OSError, ValueError):
        return None


def _find_article_file(articles_dir: Path, article_name: str) -> Optional[Path]:
    """Find an article file using flexible matching logic.
    
    Parameters
    ----------
    articles_dir : Path
        Directory to search for articles
    article_name : str
        Name of the article to find
        
    Returns
    -------
    Optional[Path]
        Path to the found article file, or None if not found
    """
    if not articles_dir.exists():
        return None
    
    # Common text file extensions to try
    extensions = ['.md', '.txt']
    
    # First try exact match
    exact_match = articles_dir / article_name
    if exact_match.is_file():
        return _normalize_path(exact_match, articles_dir)
    
    # If no extension provided, try adding common extensions
    if '.' not in article_name:
        for ext in extensions:
            candidate = articles_dir / (article_name + ext)
            if candidate.is_file():
                return _normalize_path(candidate, articles_dir)
    
    # Try case-insensitive matching
    article_name_lower = article_name.lower()
    
    try:
        for file_path in articles_dir.iterdir():
            if file_path.is_file():
                # Check exact case-insensitive match
                if file_path.name.lower() == article_name_lower:
                    return _normalize_path(file_path, articles_dir)
                
                # If no extension in search term, try case-insensitive with extensions
                if '.' not in article_name:
                    name_without_ext = file_path.stem.lower()
                    if name_without_ext == article_name_lower and file_path.suffix in extensions:
                        return _normalize_path(file_path, articles_dir)
    except (OSError, PermissionError):
        # Directory listing failed, but we can still return None
        pass
    
    return None


def read_article(article_name: str) -> str:
    """Load and return the complete content of an article by name.
    
    Searches for articles in the configured content repository using flexible
    name matching including exact match, extension inference, and case-insensitive
    matching. Includes comprehensive error handling and path traversal protection.
    
    Parameters
    ----------
    article_name : str
        Name of the article to load. Can include or exclude file extension.
        Supports case-insensitive matching and automatic extension detection
        for .md and .txt files.
        
    Returns
    -------
    str
        Complete article content, or error message if article cannot be loaded.
        
    Examples
    --------
    >>> read_article("london.md")
    "# London\\n\\nThe capital city of England..."
    
    >>> read_article("london")  # Extension inferred
    "# London\\n\\nThe capital city of England..."
    
    >>> read_article("LONDON")  # Case-insensitive
    "# London\\n\\nThe capital city of England..."
    
    >>> read_article("nonexistent")
    "Error: Article 'nonexistent' not found. Searched in: /path/to/articles/"
    """
    # Validate input
    if not article_name or not article_name.strip():
        return "Error: Article name cannot be empty"
    
    article_name = article_name.strip()
    
    # Check if config was loaded successfully
    if _config is None or _content_repo_path is None:
        return "Error: Could not load config.toml or required configuration values"
    
    # Validate content repository path
    if not _content_repo_path.exists():
        return f"Error: Content repository path does not exist: {_content_repo_path}"
    
    # Build articles directory path
    articles_dir = _content_repo_path / _current_story / _articles_dir_name
    
    # Check if articles directory exists
    if not articles_dir.exists():
        return f"Error: Articles directory does not exist: {articles_dir}"
    
    # Find the article file
    article_path = _find_article_file(articles_dir, article_name)
    
    if article_path is None:
        return f"Error: Article '{article_name}' not found. Searched in: {articles_dir}"
    
    # Read the article content
    try:
        with open(article_path, 'r', encoding='utf-8') as file:
            content = file.read()
            return content
    except PermissionError:
        return f"Error: Permission denied reading '{article_path.name}'"
    except UnicodeDecodeError:
        # Try with different encoding
        try:
            with open(article_path, 'r', encoding='latin-1') as file:
                content = file.read()
                return content
        except Exception:
            return f"Error: Unable to read '{article_path.name}' - file may have encoding issues"
    except FileNotFoundError:
        return f"Error: Article file '{article_path.name}' was found but then disappeared"
    except OSError as e:
        return f"Error: Unable to read '{article_path.name}' - {str(e)}"
    except Exception as e:
        return f"Error: Unexpected error reading '{article_path.name}' - {str(e)}"


if __name__ == "__main__":
    # Test the article reading functionality
    print("🧪 Testing read_article function...")
    
    # Test with existing article
    print("\n📚 Testing with existing article:")
    result = read_article("london.md")
    if result.startswith("Error:"):
        print(f"  ❌ {result}")
    else:
        print(f"  ✅ Successfully loaded article ({len(result)} characters)")
        print(f"  First 100 characters: {result[:100]}...")
    
    # Test extension inference
    print("\n🔍 Testing extension inference:")
    result = read_article("london")
    if result.startswith("Error:"):
        print(f"  ❌ {result}")
    else:
        print(f"  ✅ Successfully loaded article with inferred extension ({len(result)} characters)")
    
    # Test case-insensitive matching
    print("\n🔤 Testing case-insensitive matching:")
    result = read_article("LONDON")
    if result.startswith("Error:"):
        print(f"  ❌ {result}")
    else:
        print(f"  ✅ Successfully loaded article with case-insensitive match ({len(result)} characters)")
    
    # Test non-existent article
    print("\n❌ Testing non-existent article:")
    result = read_article("nonexistent-article")
    print(f"  Expected error: {result}")
    
    # Test empty article name
    print("\n❌ Testing empty article name:")
    result = read_article("")
    print(f"  Expected error: {result}")
    
    # Test with whitespace
    print("\n🔍 Testing article name with whitespace:")
    result = read_article("  london  ")
    if result.startswith("Error:"):
        print(f"  ❌ {result}")
    else:
        print(f"  ✅ Successfully handled whitespace in article name ({len(result)} characters)")