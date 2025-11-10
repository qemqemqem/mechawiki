"""
Context retrieval tool using memtool for multi-document expansion.

This tool provides intelligent context retrieval that automatically includes
related documents based on git history, markdown links, and semantic relationships.
"""
import os
from pathlib import Path
from typing import Optional, Literal, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

# Lazy import - only load when tool is actually used
_memtool_client = None


def _get_memtool_client():
    """Get or create memtool client singleton."""
    global _memtool_client
    
    if _memtool_client is None:
        try:
            from memtool.client import MemtoolClient
            _memtool_client = MemtoolClient(port=18861)
            logger.info("✓ Connected to memtool server on port 18861")
        except Exception as e:
            logger.error(f"Failed to connect to memtool server: {e}")
            raise ConnectionError(
                "memtool server not running. Start with: memtool server start --port 18861"
            )
    
    return _memtool_client


_index_ensured = False  # Track if we've already ensured index for this client

def _ensure_index_loaded():
    """
    Ensure memtool server has an index loaded for our client connection.
    
    CRITICAL: rpyc memtool connections are stateful per-client!
    The index only persists for the same client instance.
    This function uses the singleton client and only checks once.
    """
    global _index_ensured
    import os
    import toml
    from pathlib import Path
    
    # Already checked in this process
    if _index_ensured:
        return
    
    client = _get_memtool_client()  # Use the singleton
    
    # Check if index is already loaded ON THIS CLIENT
    try:
        status = client.status()
        if status['loaded']:
            _index_ensured = True
            return  # All good!
    except Exception as e:
        logger.warning(f"Could not check server status: {e}")
    
    # Index not loaded - need to load it
    logger.warning("⚠️  memtool index not loaded on this client, loading...")
    
    # Get wikicontent path from config
    try:
        config_path = Path(__file__).parent.parent.parent / "config.toml"
        config = toml.load(config_path)
        content_repo = Path(config['paths']['content_repo'])
    except Exception as e:
        logger.error(f"Could not load config: {e}")
        raise ConnectionError("Could not determine wikicontent path from config.toml")
    
    # memtool server doesn't care about our local cwd, so use absolute paths
    cache_path = str(content_repo / ".memtool_index.json")
    
    # Try to load cached index first
    if Path(cache_path).exists():
        try:
            logger.info("   Loading index from cache...")
            result = client.load_index(cache_path)
            logger.info(f"✓ Index loaded: {result['summary']['num_files']} files")
            _index_ensured = True
            return
        except Exception as e:
            logger.warning(f"   Failed to load cached index: {e}")
    
    # Build fresh index - use absolute path!
    logger.info(f"   Building fresh index from: {content_repo}")
    result = client.build_index(str(content_repo))
    summary = result['summary']
    logger.info(f"✓ Index built: {summary['num_files']} files, {summary['num_intervals']} intervals")
    
    # Save for next time
    client.save_index(cache_path)
    logger.info("✓ Index saved to cache")
    _index_ensured = True


def get_context(
    document: str,
    start_line: int = 1,
    end_line: int = 999999,
    expansion_mode: Literal["paragraph", "line", "section"] = "paragraph",
    padding: int = 2,
    return_metadata: bool = False
) -> str | Dict[str, Any]:
    """
    Get contextually expanded content for a document with automatic multi-document expansion.
    
    This tool queries the memtool server to retrieve not just the requested document,
    but also automatically includes related documents based on:
    - Markdown links in the document (e.g., [see castle](articles/castle.md))
    - Git history (documents edited together in the same commits)
    - Cross-references (documents that mention each other)
    - Temporal relationships (recently co-edited content)
    
    The memtool server maintains an in-memory index of the repository for fast queries
    and automatically expands context to natural boundaries (paragraphs, not arbitrary lines).
    
    ## How It Works
    
    1. **Query**: Request a document and line range
    2. **Discover**: memtool finds related documents via git blame and links
    3. **Expand**: Extends to natural boundaries (paragraphs) with padding
    4. **Return**: Combined text from all related documents
    
    ## memtool Server API
    
    The underlying RPC calls to memtool server:
    
    ```python
    # Step 1: Get context intervals (discovers related docs)
    context = client.get_context(document, start_line, end_line)
    # Returns: {"intervals": [...], "commits": [...]}
    # Intervals span multiple documents that are related
    
    # Step 2: Expand intervals to full text with smart boundaries
    expansion = client.expand_context(
        intervals=context["intervals"],
        mode="paragraph",  # Expand to paragraph boundaries
        pad=2              # Include 2 surrounding paragraphs
    )
    # Returns: {"snippets": [{"doc": "...", "preview": "..."}]}
    ```
    
    See memtool docs for full API: https://github.com/csheldondante/memtool
    
    Parameters
    ----------
    document : str
        Path to document relative to wikicontent root.
        Examples:
        - "articles/dracula.md"
        - "articles/castle.md"
        - "stories/tale-of-wonder.md"
        
    start_line : int, default=1
        Starting line number (1-indexed, inclusive).
        Use 1 to start from beginning of document.
        
    end_line : int, default=999999
        Ending line number (1-indexed, inclusive).
        Use 999999 (or any large number) to include entire document.
        
    expansion_mode : {"paragraph", "line", "section"}, default="paragraph"
        How to expand the context boundaries:
        - "paragraph": Expand to paragraph boundaries (recommended)
        - "line": Use exact line numbers (may cut mid-sentence)
        - "section": Expand to markdown section boundaries (##)
        
    padding : int, default=2
        Number of surrounding paragraphs/sections to include for context.
        Higher values give more context but increase token usage.
        - 0: No padding (just the exact boundaries)
        - 1: Include 1 paragraph before/after
        - 2: Include 2 paragraphs before/after (recommended)
        - 3+: Even more context
        
    return_metadata : bool, default=False
        If True, returns a dict with content + metadata.
        If False, returns just the content string (simpler for LLM).
        
    Returns
    -------
    str or dict
        If return_metadata=False (default):
            Combined text from requested document + related documents.
            Format: Each document's content separated by newlines.
            
        If return_metadata=True:
            Dictionary with:
            - "content": str - The combined text
            - "intervals": list - Intervals used (for provenance)
            - "num_docs": int - Number of documents included
            - "documents": list[str] - List of document paths included
            
    Raises
    ------
    ConnectionError
        If memtool server is not running on port 18861.
        Start with: memtool server start --port 18861
        
    FileNotFoundError
        If the requested document does not exist in the repository.
        
    Examples
    --------
    Basic usage (get article with related content):
    
    >>> content = get_context("articles/dracula.md")
    >>> print(content)
    '''
    # Count Dracula
    Ancient vampire from Transylvania...
    
    # Related: Dracula's Castle
    The castle stands in the Carpathian mountains...
    
    # Related: Jonathan Harker's Journey
    Jonathan traveled to meet Count Dracula...
    '''
    
    Get specific line range:
    
    >>> content = get_context("articles/dracula.md", start_line=50, end_line=100)
    # Returns lines 50-100 of dracula.md + related docs, expanded to paragraph boundaries
    
    With metadata for provenance tracking:
    
    >>> result = get_context("articles/dracula.md", return_metadata=True)
    >>> print(f"Included {result['num_docs']} documents:")
    >>> for doc in result['documents']:
    >>>     print(f"  - {doc}")
    >>> print(result['content'])
    
    Different expansion modes:
    
    >>> # Exact lines (may cut mid-sentence)
    >>> content = get_context("articles/dracula.md", expansion_mode="line", padding=0)
    
    >>> # Full sections (largest context)
    >>> content = get_context("articles/dracula.md", expansion_mode="section", padding=1)
    
    Notes
    -----
    - The memtool server must be running (started by start.sh)
    - Server maintains an in-memory index for fast queries (~5ms)
    - Index is automatically updated when files change
    - Related documents are found via git blame + markdown links
    - All queries are logged for debugging and analysis
    
    See Also
    --------
    read_article : Read a single article without expansion
    read_file : Read any file with line ranges
    find_articles : Search for articles by name
    """
    try:
        # Ensure index is loaded (self-healing)
        _ensure_index_loaded()
        
        client = _get_memtool_client()
        
        # Type coercion: LLMs often pass numbers as strings
        # memtool expects ints, so convert them
        start_line = int(start_line)
        end_line = int(end_line)
        padding = int(padding)
        
        # Step 1: Get context intervals (discovers related documents)
        logger.debug(f"Querying context for {document} lines {start_line}-{end_line}")
        context = client.get_context(document, start_line, end_line)
        
        if not context.get("intervals"):
            # No intervals found - could be nonexistent file or file with no indexable content
            logger.warning(f"No intervals found for {document}")
            
            # Provide helpful error message
            error_msg = (
                f"No content found for '{document}'. "
                f"This file may not exist, may be empty, or may not have been indexed. "
                f"Check the file path and try searching with find_articles tool."
            )
            
            return {"error": error_msg, "content": "", "intervals": [], "num_docs": 0} if return_metadata else ""
        
        # Step 2: Expand intervals to full text with smart boundaries
        logger.debug(f"Expanding {len(context['intervals'])} intervals with mode={expansion_mode}, pad={padding}")
        expansion = client.expand_context(
            context["intervals"],
            mode=expansion_mode,
            pad=padding
        )
        
        # Step 3: Extract text from snippets
        snippets = expansion.get("snippets", [])
        if not snippets:
            logger.warning(f"No snippets returned after expansion for {document}")
            error_msg = (
                f"Found intervals for '{document}' but expansion returned no text. "
                f"This may indicate an issue with the expansion mode or file encoding."
            )
            return {"error": error_msg, "content": "", "intervals": context["intervals"], "num_docs": 0} if return_metadata else ""
        
        # Combine all snippet text
        combined_text = "\n\n".join([snippet["preview"] for snippet in snippets])
        
        # Track which documents were included
        documents_included = list(set(interval["path"] for interval in context["intervals"]))
        
        logger.info(f"✓ Retrieved context for {document}: {len(snippets)} snippets from {len(documents_included)} documents")
        
        # Return based on metadata preference
        if return_metadata:
            return {
                "content": combined_text,
                "intervals": context["intervals"],
                "num_docs": len(documents_included),
                "documents": documents_included,
                "num_snippets": len(snippets)
            }
        else:
            # Simple string return (best for LLM consumption)
            return combined_text
            
    except ConnectionError:
        # Re-raise connection errors with helpful message
        raise
    except Exception as e:
        error_msg = f"Error retrieving context for {document}: {e}"
        logger.error(error_msg)
        if return_metadata:
            return {"error": error_msg}
        else:
            return f"Error: {error_msg}"


def close_memtool_client():
    """Close the memtool client connection (called on shutdown)."""
    global _memtool_client
    if _memtool_client is not None:
        try:
            _memtool_client.close()
            logger.info("✓ Closed memtool client")
        except Exception as e:
            logger.warning(f"Error closing memtool client: {e}")
        _memtool_client = None

