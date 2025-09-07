"""Aider-style search/replace diffing utilities with fuzzy matching."""
import re
from typing import Optional, Tuple, List
from dataclasses import dataclass

@dataclass
class EditResult:
    """Result of an edit operation."""
    success: bool
    message: str
    new_content: Optional[str] = None

class SearchReplaceError(Exception):
    """Error in search/replace operation."""
    pass

def parse_search_replace_block(edit_text: str) -> Tuple[str, str]:
    """Parse Aider-style search/replace block.
    
    Expected format:
    <<<<<<< SEARCH
    text to find
    =======
    text to replace with  
    >>>>>>> REPLACE
    
    Args:
        edit_text: The search/replace block text
        
    Returns:
        Tuple of (search_text, replace_text)
        
    Raises:
        SearchReplaceError: If format is invalid
    """
    # Remove leading/trailing whitespace but preserve internal formatting
    edit_text = edit_text.strip()
    
    # Check for search block markers
    search_pattern = r'<{7}\s*SEARCH\s*\n(.*?)\n={7}\s*\n(.*?)\n>{7}\s*REPLACE'
    match = re.search(search_pattern, edit_text, re.DOTALL)
    
    if not match:
        raise SearchReplaceError(
            "Invalid search/replace format. Expected:\n"
            "<<<<<<< SEARCH\n"
            "text to find\n"
            "=======\n"
            "text to replace\n" 
            ">>>>>>> REPLACE"
        )
    
    search_text = match.group(1)
    replace_text = match.group(2)
    
    return search_text, replace_text

def apply_search_replace(content: str, search_text: str, replace_text: str, 
                        max_retries: int = 2) -> EditResult:
    """Apply search/replace with fuzzy matching retry logic.
    
    Args:
        content: Original file content
        search_text: Text to search for
        replace_text: Text to replace with
        max_retries: Number of retry attempts with increasing fuzziness
        
    Returns:
        EditResult with success/failure info
    """
    
    # Attempt 1: Exact match
    if search_text in content:
        # Check for multiple matches - this could be ambiguous
        match_count = content.count(search_text)
        if match_count > 1:
            return EditResult(
                success=False,
                message=f"Ambiguous edit: found {match_count} exact matches for search text. "
                       "Please make search text more specific."
            )
        
        new_content = content.replace(search_text, replace_text, 1)
        return EditResult(
            success=True,
            message="Edit applied successfully (exact match)",
            new_content=new_content
        )
    
    # Attempt 2: Normalized whitespace match  
    if max_retries >= 1:
        normalized_search = normalize_whitespace(search_text)
        normalized_content = normalize_whitespace(content)
        
        if normalized_search in normalized_content:
            # Find the original text boundaries by looking for the pattern
            # This is a simple approach - could be more sophisticated
            try:
                # Try to find approximate match location
                lines = content.split('\n')
                search_lines = search_text.split('\n')
                
                # Look for sequence of lines that approximately match
                for i in range(len(lines) - len(search_lines) + 1):
                    candidate_lines = lines[i:i + len(search_lines)]
                    candidate_text = '\n'.join(candidate_lines)
                    
                    if normalize_whitespace(candidate_text) == normalized_search:
                        # Found approximate match - replace this section
                        before = '\n'.join(lines[:i])
                        after = '\n'.join(lines[i + len(search_lines):])
                        
                        if before and not before.endswith('\n'):
                            before += '\n'
                        if after and not after.startswith('\n'):
                            after = '\n' + after
                            
                        new_content = before + replace_text + after
                        return EditResult(
                            success=True,
                            message="Edit applied successfully (fuzzy whitespace match)",
                            new_content=new_content
                        )
                        
            except Exception as e:
                pass  # Fall through to failure case
    
    # All attempts failed
    return EditResult(
        success=False,
        message=f"Could not find search text in content. Tried exact match and normalized whitespace. "
                f"Search text preview: {repr(search_text[:50])}..."
    )

def normalize_whitespace(text: str) -> str:
    """Normalize whitespace for fuzzy matching.
    
    Args:
        text: Input text
        
    Returns:
        Text with normalized whitespace
    """
    # Replace multiple whitespace with single space, strip lines
    lines = [line.strip() for line in text.split('\n')]
    # Remove empty lines for comparison
    lines = [line for line in lines if line]
    return ' '.join(lines)

def apply_search_replace_block(content: str, edit_block: str, 
                              max_retries: int = 2) -> EditResult:
    """Parse and apply an Aider-style search/replace block.
    
    Args:
        content: Original file content
        edit_block: Search/replace block text
        max_retries: Number of retry attempts
        
    Returns:
        EditResult with success/failure info
    """
    try:
        search_text, replace_text = parse_search_replace_block(edit_block)
        return apply_search_replace(content, search_text, replace_text, max_retries)
        
    except SearchReplaceError as e:
        return EditResult(
            success=False,
            message=f"Parse error: {str(e)}"
        )