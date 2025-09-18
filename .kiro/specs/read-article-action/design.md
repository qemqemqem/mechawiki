# Design Document

## Overview

The read_article action will be implemented as a new tool function that integrates with the existing agent framework. It will follow the same patterns established by the existing search tools (find_articles, find_images, etc.) and leverage the configuration system already in place.

The tool will provide agents with the ability to load complete article content by name, returning the full text in a structured response. This enables agents to access and process article content dynamically during their execution.

## Architecture

### Integration Points

The read_article tool will integrate with the existing system at several key points:

1. **Configuration System**: Uses the existing `config.toml` structure to locate the content repository and articles directory
2. **Tool Framework**: Follows the litellm tool pattern used by other agent tools
3. **Agent Integration**: Can be added to any agent's tool list, similar to existing search tools
4. **Error Handling**: Uses consistent error patterns with other tools in the system

### File Structure

```
src/tools/
├── search.py          # Existing search tools
├── images.py          # Existing image tools  
└── articles.py        # New module for article operations (including read_article)
```

## Components and Interfaces

### Core Function Signature

```python
def read_article(article_name: str) -> str:
    """
    Load and return the complete content of an article by name.
    
    Parameters
    ----------
    article_name : str
        Name of the article to load. Can include or exclude file extension.
        
    Returns
    -------
    str
        Complete article content, or error message if article not found
    """
```

### Configuration Dependencies

The tool will use the existing configuration structure:

- `config["paths"]["content_repo"]`: Base path to content repository
- `config["paths"]["articles_dir"]`: Subdirectory containing articles (default: "articles")

### Search Logic

The tool will implement flexible article name matching:

1. **Exact Match**: First try exact filename match
2. **Extension Inference**: If no extension provided, try common extensions (.md, .txt)
3. **Case Insensitive**: Perform case-insensitive matching
4. **Error Reporting**: Provide clear error messages with searched paths

## Data Models

### Input Model
- `article_name`: String representing the article filename or name
- Supports both with and without file extensions
- Case-insensitive matching

### Output Model
- **Success**: Complete article content as string
- **Error**: Descriptive error message indicating the specific failure reason

### Error Types
1. **File Not Found**: Article doesn't exist in the articles directory
2. **Permission Denied**: File exists but cannot be read due to permissions
3. **Read Error**: File exists but cannot be read due to encoding or corruption issues
4. **Configuration Error**: Config file missing or content repository path invalid

## Error Handling

### Error Response Format

All errors will be returned as descriptive strings that agents can process:

```python
# File not found example
"Error: Article 'wizard-story.md' not found. Searched in: /path/to/content/articles/"

# Permission error example  
"Error: Permission denied reading 'wizard-story.md'"

# Read error example
"Error: Unable to read 'wizard-story.md' - file may be corrupted or have encoding issues"
```

### Graceful Degradation

- If config cannot be loaded, return clear error message
- If content repository path is invalid, return path-specific error
- If articles directory doesn't exist, return directory-specific error

## Testing Strategy

### Unit Tests

1. **Successful Article Loading**
   - Test loading existing articles with various extensions
   - Test case-insensitive matching
   - Test extension inference

2. **Error Conditions**
   - Test file not found scenarios
   - Test permission denied scenarios
   - Test configuration errors
   - Test invalid content repository paths

3. **Edge Cases**
   - Test empty article files
   - Test articles with special characters in names
   - Test very large article files

### Integration Tests

1. **Agent Integration**
   - Test tool integration with ReaderAgent
   - Test tool execution through litellm framework
   - Test tool response handling

2. **Configuration Integration**
   - Test with different config.toml configurations
   - Test with missing configuration values
   - Test with invalid paths

### Manual Testing

1. **Real Content Testing**
   - Test with actual articles from the tales_of_wonder content
   - Test with various file formats and sizes
   - Test error scenarios with real file system

## Implementation Notes

### File Reading Strategy

- Use UTF-8 encoding by default with error handling for other encodings
- Read entire file content into memory (suitable for text articles)
- Handle both Unix and Windows line endings

### Performance Considerations

- File system operations are I/O bound but should be fast for text files
- No caching implemented initially - each call reads from disk
- Future enhancement could add optional caching for frequently accessed articles

### Security Considerations

- Path traversal protection: Only allow access to files within the configured articles directory
- No arbitrary file system access outside the content repository
- Validate article names to prevent directory traversal attacks