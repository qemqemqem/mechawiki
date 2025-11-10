"""
ToolTestAgent for rigorous tool testing and bug hunting.

This agent has access to ALL tools (except done) and systematically tests
them to find bugs and edge cases. Reports detailed bug reports via report_issue().
"""
import sys
import os
import toml
import litellm
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Add parent directory to sys.path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_agent.base_agent import BaseAgent
from tools.search import find_articles, find_images, find_songs, find_files
from tools.files import read_file, edit_file, add_to_story
from tools.articles import read_article, search_articles, list_articles_in_directory
from tools.context import get_context
from tools.interactive import wait_for_user, get_session_state, WaitingForInput
from agents.prompts.loader import build_agent_prompt
from utils.git import ensure_content_branch

# Load config
config = toml.load("config.toml")


class ToolTestAgent(BaseAgent):
    """
    Agent that rigorously tests ALL available tools to hunt down bugs.
    
    This agent has access to every tool in the system (except done) and
    systematically exercises them with various parameters, edge cases, and
    scenarios to find bugs. Uses report_issue() to file detailed bug reports.
    """
    
    def __init__(self, agent_id: Optional[str] = None, **kwargs):
        """Initialize the ToolTestAgent with ALL testing tools.
        
        Args:
            agent_id: Agent ID for identification (optional)
            **kwargs: Additional arguments passed to BaseAgent
        """
        
        # Store agent_id for identification
        self.agent_id = agent_id or "tool-test-agent"
        
        logger.info(f"🧪 ToolTestAgent initialized: id={self.agent_id}")
        
        # Initialize base agent first (to get report_issue)
        system_prompt = build_agent_prompt("tool_test", include_tools=True)
        model = kwargs.pop('model', config["agent"]["model"])
        super().__init__(
            model=model,
            system_prompt=system_prompt,
            tools=[],  # Will add below
            **kwargs
        )
        
        # Now add ALL the tools for comprehensive testing
        self._add_search_tools()
        self._add_file_tools()
        self._add_article_tools()
        self._add_context_tools()
        self._add_interactive_tools()
        
        # Set initial memory
        self.set_memory("agent_type", "tool_test")
        self.set_memory("test_status", "not_started")
        self.set_memory("bugs_found", 0)
    
    def _add_search_tools(self):
        """Add search/discovery tools."""
        search_funcs = [find_articles, find_images, find_songs, find_files]
        for func in search_funcs:
            self.tools.append({
                "type": "function",
                "function": litellm.utils.function_to_dict(func),
                "_function": func
            })
    
    def _add_file_tools(self):
        """Add file operation tools."""
        file_funcs = [read_file, edit_file, add_to_story]
        for func in file_funcs:
            self.tools.append({
                "type": "function",
                "function": litellm.utils.function_to_dict(func),
                "_function": func
            })
    
    def _add_article_tools(self):
        """Add article management tools."""
        article_funcs = [read_article, search_articles, list_articles_in_directory]
        for func in article_funcs:
            self.tools.append({
                "type": "function",
                "function": litellm.utils.function_to_dict(func),
                "_function": func
            })
    
    def _add_context_tools(self):
        """Add context retrieval tools."""
        self.tools.append({
            "type": "function",
            "function": litellm.utils.function_to_dict(get_context),
            "_function": get_context
        })
    
    def _add_interactive_tools(self):
        """Add interactive tools for testing collaborative features."""
        interactive_funcs = [wait_for_user, get_session_state]
        for func in interactive_funcs:
            self.tools.append({
                "type": "function",
                "function": litellm.utils.function_to_dict(func),
                "_function": func
            })
    
    def _execute_tool(self, tool_call: dict):
        """
        Override tool execution to handle WaitingForInput sentinel.
        
        When wait_for_user() is called during testing, convert to signal.
        """
        result = super()._execute_tool(tool_call)
        
        # Check if result is WaitingForInput sentinel
        if isinstance(result, WaitingForInput):
            return {
                "_waiting_for_input": True,
                "message": "Test paused - waiting for user input to continue testing"
            }
        
        return result


def main():
    """Demo the ToolTestAgent"""
    print("🚀 Starting ToolTestAgent demo...")
    
    # Ensure we're on the correct content branch
    if not ensure_content_branch():
        print("❌ Failed to ensure correct content branch. Exiting.")
        return
    
    # Create the tool test agent
    agent = ToolTestAgent(stream=True)
    
    # Run a testing session
    print("\n--- Starting Tool Testing Session ---")
    result = agent.run_forever(
        "Test the get_context tool. Start by finding some articles, then test get_context with different parameters.",
        max_turns=10
    )
    
    print(f"\n--- Session Result ---")
    print(result)


if __name__ == "__main__":
    main()

