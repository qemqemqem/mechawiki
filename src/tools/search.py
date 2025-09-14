"""
Search tools for finding files across the content repository.
"""
import os
import re
import toml
from pathlib import Path
from typing import List

# Load config once at module level
try:
    _config = toml.load("config.toml")
    _content_repo_path = Path(_config["paths"]["content_repo"])
    _current_story = _config["story"]["current_story"]
    _articles_dir_name = _config["paths"]["articles_dir"]
    _images_dir_name = _config["paths"]["images_dir"]
    _songs_dir_name = _config["paths"]["songs_dir"]
except Exception as e:
    print(f"❌ Error loading config in search.py: {e}")
    _config = None
    _content_repo_path = None
    _current_story = None
    _articles_dir_name = "articles"
    _images_dir_name = "images"
    _songs_dir_name = "songs"


def _search_directory(directory: Path, search_string: str) -> List[str]:
    """Helper function to search for files in a specific directory.
    
    Parameters
    ----------
    directory : Path
        The directory to search in
    search_string : str
        The string to search for in file names
        
    Returns
    -------
    List[str]
        List of filenames that match the search criteria
    """
    if not directory.exists():
        return []
    
    search_lower = search_string.lower().strip()
    is_wildcard_search = (search_lower == "*")
    found_files = []
    
    for file_path in directory.iterdir():
        if file_path.is_file() and (is_wildcard_search or search_lower in file_path.name.lower()):
            found_files.append(file_path.name)
    
    return sorted(found_files)


def find_articles(search_string: str) -> List[str]:
    """Find article files whose title/name contains the search string.
    
    Searches only in the articles directory for markdown files.
    
    Parameters
    ----------
    search_string : str
        The string to search for in file names. Case-insensitive search.
        Can be a partial match (e.g., "wizard" will match "wizard-merlin.md").
        Use "*" to return all article files.
        
    Returns
    -------
    List[str]
        List of article filenames that contain the search string. Returns empty list
        if no matches found or if config could not be loaded.
        
    Examples
    --------
    >>> find_articles("wizard")
    ['wizard-merlin.md', 'wizard-spells.md']
    
    >>> find_articles("london")
    ['london.md', 'london-tale.md']
    
    >>> find_articles("*")
    ['all-articles.md', 'another-article.md', ...]
    """
    # Check if config was loaded successfully
    if _config is None or _content_repo_path is None:
        print(f"❌ Error: Could not load config.toml or required config values")
        return []
    
    if not search_string.strip():
        return []
    
    articles_dir = _content_repo_path / _articles_dir_name
    return _search_directory(articles_dir, search_string)


def find_images(search_string: str) -> List[str]:
    """Find image files whose title/name contains the search string.
    
    Searches only in the images directory for image files.
    
    Parameters
    ----------
    search_string : str
        The string to search for in file names. Case-insensitive search.
        Can be a partial match (e.g., "castle" will match "castle-ruins.png").
        Use "*" to return all image files.
        
    Returns
    -------
    List[str]
        List of image filenames that contain the search string. Returns empty list
        if no matches found or if config could not be loaded.
        
    Examples
    --------
    >>> find_images("castle")
    ['castle-ruins.png', 'haunted-castle.jpg']
    
    >>> find_images("wizard")
    ['wizard-hat.png', 'wizard-staff.jpg']
    
    >>> find_images("*")
    ['all-images.png', 'another-image.jpg', ...]
    """
    # Check if config was loaded successfully
    if _config is None or _content_repo_path is None:
        print(f"❌ Error: Could not load config.toml or required config values")
        return []
    
    if not search_string.strip():
        return []
    
    images_dir = _content_repo_path / _images_dir_name
    return _search_directory(images_dir, search_string)


def find_songs(search_string: str) -> List[str]:
    """Find song files whose title/name contains the search string.
    
    Searches only in the songs directory for audio files.
    
    Parameters
    ----------
    search_string : str
        The string to search for in file names. Case-insensitive search.
        Can be a partial match (e.g., "epic" will match "epic-battle.mp3").
        Use "*" to return all song files.
        
    Returns
    -------
    List[str]
        List of song filenames that contain the search string. Returns empty list
        if no matches found or if config could not be loaded.
        
    Examples
    --------
    >>> find_songs("battle")
    ['epic-battle.mp3', 'battle-cry.wav']
    
    >>> find_songs("wizard")
    ['wizard-song.mp3', 'wizard-melody.ogg']
    
    >>> find_songs("*")
    ['all-songs.mp3', 'another-song.wav', ...]
    """
    # Check if config was loaded successfully
    if _config is None or _content_repo_path is None:
        print(f"❌ Error: Could not load config.toml or required config values")
        return []
    
    if not search_string.strip():
        return []
    
    songs_dir = _content_repo_path / _songs_dir_name
    return _search_directory(songs_dir, search_string)


def find_files(search_string: str) -> List[str]:
    """Find files whose title/name contains the search string across all content types.
    
    This is a convenience function that searches across articles, images, and songs.
    For more specific searches, use find_articles(), find_images(), or find_songs().
    
    Parameters
    ----------
    search_string : str
        The string to search for in file names. Case-insensitive search.
        Can be a partial match (e.g., "wizard" will match "wizard-merlin.png").
        Use "*" to return all files across all content directories.
        
    Returns
    -------
    List[str]
        List of filenames that contain the search string. Returns empty list
        if no matches found or if config could not be loaded.
        
    Examples
    --------
    >>> find_files("wizard")
    ['wizard-merlin.md', 'wizard-hat.png', 'wizard-song.mp3']
    
    >>> find_files("castle")
    ['haunted-castle.md', 'castle-ruins.jpg']
    
    >>> find_files("*")
    ['all-files.md', 'all-images.png', 'all-songs.mp3', ...]
    """
    # Check if config was loaded successfully
    if _config is None or _content_repo_path is None:
        print(f"❌ Error: Could not load config.toml or required config values")
        return []
    
    if not search_string.strip():
        return []
    
    # Combine results from all content types
    all_files = []
    all_files.extend(find_articles(search_string))
    all_files.extend(find_images(search_string))
    all_files.extend(find_songs(search_string))
    
    return sorted(all_files)


if __name__ == "__main__":
    # Test the search functionality
    print("🧪 Testing search functions...")
    
    # Test find_articles
    print("\n📚 Testing find_articles:")
    results = find_articles("london")
    print(f"  Articles with 'london': {len(results)} found")
    if results:
        print(f"  First 3: {results[:3]}")
    
    results = find_articles("*")
    print(f"  All articles: {len(results)} found")
    
    # Test find_images
    print("\n🖼️ Testing find_images:")
    results = find_images("castle")
    print(f"  Images with 'castle': {len(results)} found")
    if results:
        print(f"  Results: {results}")
    
    results = find_images("*")
    print(f"  All images: {len(results)} found")
    
    # Test find_songs
    print("\n🎵 Testing find_songs:")
    results = find_songs("battle")
    print(f"  Songs with 'battle': {len(results)} found")
    if results:
        print(f"  Results: {results}")
    
    results = find_songs("*")
    print(f"  All songs: {len(results)} found")
    
    # Test find_files (convenience function)
    print("\n🔍 Testing find_files (all content types):")
    results = find_files("castle")
    print(f"  All files with 'castle': {len(results)} found")
    if results:
        print(f"  Results: {results}")
    
    results = find_files("*")
    print(f"  All files: {len(results)} found")
