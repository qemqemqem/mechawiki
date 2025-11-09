# Report Issue Tool Implementation

## Overview

Implemented a new built-in tool `report_issue(issue_str)` that is automatically available to **all agents** in the system. This tool allows LLMs to report bugs or impossible tasks they encounter.

## Implementation Details

### Location
- **File**: `src/base_agent/base_agent.py`
- **Method**: `_add_report_issue_tool()`
- **Initialized**: In `BaseAgent.__init__()` alongside the built-in `end()` tool

### Tool Signature

```python
def report_issue(issue_str: str):
    """Report a bug or issue encountered during operation.
    
    Call this tool when you believe you have encountered a bug in the system,
    or when the system prompt has instructed you to do something that is 
    impossible or cannot be completed with the available tools.
    
    Parameters
    ----------
    issue_str : str
        Description of the issue, bug, or impossible task encountered
    """
```

### Return Value

```
"Issue logged successfully. The developer will review this report. Please carry on as best as possible despite this issue."
```

## Availability

The tool is automatically available to **all agents** that inherit from `BaseAgent`:

- ✅ **BaseAgent** - All base agents
- ✅ **ReaderAgent** - Story reading agents
- ✅ **WriterAgent** - Story writing agents
- ✅ **InteractiveAgent** - Interactive experience agents
- ✅ **Future agents** - Any new agents that inherit from BaseAgent

## Logging

The tool is **automatically logged** via the existing AgentRunner logging system:

1. When an agent calls `report_issue(issue_str="some issue")`, a tool_call event is yielded
2. AgentRunner logs this to the agent's JSONL log file with:
   - `type: "tool_call"`
   - `tool: "report_issue"`
   - `args: {"issue_str": "..."}`
   - `timestamp: ...`
3. The tool result is also logged with `type: "tool_result"`

**No special logging implementation was needed** - the existing infrastructure handles it automatically.

## Example Usage

An LLM agent might call this tool like:

```json
{
  "type": "tool_call",
  "tool": "report_issue",
  "args": {
    "issue_str": "System prompt instructs me to use find_articles tool with parameter 'category', but the tool schema shows it only accepts 'query' parameter. This appears to be a mismatch in the documentation."
  }
}
```

The agent would receive:

```
"Issue logged successfully. The developer will review this report. Please carry on as best as possible despite this issue."
```

And can then continue operation despite the problem.

## Testing

Verified that all agent types have access to the tool:
- Tested BaseAgent ✅
- Tested ReaderAgent ✅  
- Tested WriterAgent ✅
- Tested InteractiveAgent ✅

All tests passed successfully - the tool is available and functional in all agents.

