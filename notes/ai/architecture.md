# Architecture Notes

## LangGraph + FastMCP Integration

### LangGraph Lightweight Patterns
- **Simplest approach**: Use `create_react_agent` for single agent with tools
- Built-in state management and memory with `InMemorySaver`
- Avoids complex graph structures - just ReAct pattern
- Native MCP support via `langchain-mcp-adapters` library

### FastMCP for Custom Tools
- FastMCP creates MCP servers that LangGraph can consume
- Simple decorator pattern: `@mcp.tool()` for function definitions
- Transport options: `stdio` (local dev) or `http` (production)
- LangGraph connects via `MultiServerMCPClient`

### Benefits
- **State Management**: Story position + context articles automatically tracked
- **Memory**: Conversation/context persistence between iterations  
- **Tool Separation**: Clean MCP protocol boundary
- **Production Ready**: Well-documented, tested patterns

### Architecture
```
LangGraph Agent (create_react_agent)
    ↓ (MCP protocol)
FastMCP Server (advance, add_article, edit_article tools)
    ↓ (file operations)  
Content Directory (articles/, images/, songs/)
```

Context management: Keep last 15 linked articles in memory (~7.5k words total)

## Code Standards

### Typing Hints
- **All functions and methods must have complete type hints**
- Use `from typing import` for complex types: `Dict`, `List`, `Optional`, `Any`  
- Class attributes should be type-hinted in `__init__` methods
- Return types are mandatory for all functions
- This improves code clarity, IDE support, and catches type errors early

Example:
```python
def create_article(title: str, content: str) -> str:
    slug: str = slugify(title)  
    articles: List[Dict[str, str]] = load_articles()
    return f"Created {slug}.md"
```