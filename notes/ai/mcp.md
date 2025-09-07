# MCP Tool Description Best Practices

## Research Findings from Web Search

### FastMCP Docstring Standards
- **Type hints are crucial**: FastMCP leverages Python type hints and docstrings to automatically generate tool definitions
- **Google-style docstring format** is most common and recommended:
  ```python
  @mcp.tool()
  def tool_name(param1: type, param2: type) -> return_type:
      """Brief description of what the tool does.
      
      Args:
          param1: Description of first parameter
          param2: Description of second parameter
          
      Returns:
          Description of what is returned
      """
  ```

### Key Requirements Found
1. **Clear Tool Names**: Tool names should be descriptive and unambiguous
2. **Brief but Complete Descriptions**: First line should summarize tool purpose  
3. **Detailed Args Documentation**: Each parameter needs clear description
4. **Return Value Documentation**: Specify what the tool returns
5. **Context Usage Guidelines**: Include when/why to use the tool

### Current Limitations Discovered
- **FastMCP Parsing Issue**: There's an open GitHub issue (#226) about docstring parsing not working as expected
- **Security Annotations**: Tool annotations (readOnlyHint, destructiveHint) are untrusted hints - hosts must not rely on them for security
- **User Consent Required**: Hosts must obtain explicit user consent before invoking any tool

### Example Patterns from Research
**File Processing:**
```python
@mcp.tool()
def read_pdf(file_path: str) -> str:
    """Extract text content from PDF files for AI analysis.

    Args:
        file_path: Path to the PDF file (supports ~ for home directory)
        
    Returns:
        Extracted text content or error message
    """
```

**Data Analysis:**
```python
@mcp.tool()
def summarize_csv_file(filename: str) -> str:
    """ Summarize a CSV file by reporting its number of rows and columns.
    
    Args:
        filename: Name of the CSV file in the /data directory (e.g., 'sample.csv')
        
    Returns:
        A string describing the file's dimensions.
    """
```

### Security Best Practices Found
- **Treat tools as arbitrary code execution** - require appropriate caution
- **Validate all inputs rigorously** against protocol specification  
- **Include security vulnerability tests** for invalid inputs, path traversal, injection attempts
- **Tool descriptions are untrusted** unless from verified server

### MCP Ecosystem Growth
- Nearly 16,000 unique servers as of late 2024
- Explosive growth since Anthropic's introduction
- Standard format emerging across implementations