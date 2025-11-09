"""
Prompt loading utilities for agents.

Loads markdown prompt files and combines them into system prompts.
"""
from pathlib import Path
from typing import List


def load_prompt_file(filename: str) -> str:
    """Load a single prompt file from the prompts directory.
    
    Args:
        filename: Name of the markdown file (e.g., "project.md")
        
    Returns:
        Content of the prompt file
        
    Raises:
        FileNotFoundError: If the prompt file doesn't exist
    """
    prompts_dir = Path(__file__).parent
    filepath = prompts_dir / filename
    
    if not filepath.exists():
        raise FileNotFoundError(f"Prompt file not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read().strip()


def build_agent_prompt(agent_type: str, include_tools: bool = True) -> str:
    """Build a complete system prompt for an agent.
    
    Args:
        agent_type: Type of agent ("reader", "writer", "interactive")
        include_tools: Whether to include tool usage guidelines
        
    Returns:
        Complete system prompt combining project, agent-specific, and tool guidance
    """
    # Load core prompt components
    project_context = load_prompt_file("project.md")
    agent_specific = load_prompt_file(f"{agent_type}_agent.md")
    
    # Start building the prompt
    parts = [project_context, agent_specific]
    
    # Add story structure guide for writer agents
    if agent_type == "writer":
        story_structure = load_prompt_file("story_structure_guide.md")
        parts.append(story_structure)
    
    # Add tool usage guidelines if requested
    if include_tools:
        tool_guidance = load_prompt_file("tool_usage.md")
        parts.append(tool_guidance)
    
    # Combine with clear separators
    return "\n\n---\n\n".join(parts)

