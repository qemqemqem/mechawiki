"""
InteractiveAgent - Creates interactive experiences with user.

Combines storytelling with user interaction, pausing for input at key moments.
"""
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from base_agent.base_agent import BaseAgent
from tools.interactive import wait_for_user, get_session_state, WaitingForInput
from tools.files import read_file, edit_file, add_to_story
from tools.articles import (
    read_article,
    search_articles,
    list_articles_in_directory
)
from agents.prompts.loader import build_agent_prompt
# from tools.images import create_image  # Too slow for dev
import litellm


class InteractiveAgent(BaseAgent):
    """
    Agent specialized in creating interactive experiences.
    
    Can present narrative, ask for user choices, and branch based on input.
    """
    
    def __init__(
        self,
        model: str = "claude-haiku-4-5-20251001",
        story_file: str = "stories/interactive_adventure.md",
        system_prompt: str = None,
        memory: dict = None,
        stream: bool = True,
        agent_id: str = None,
        agent_config: dict = None
    ):
        """
        Initialize InteractiveAgent.
        
        Args:
            model: LLM model to use
            story_file: Default story file for interactive adventures (default: "stories/interactive_adventure.md")
            system_prompt: Optional custom system prompt
            memory: Optional initial memory dict
            stream: Whether to stream responses
            agent_id: Optional agent ID for updating config
            agent_config: Optional agent configuration dict (for future state persistence)
        """
        self.story_file = story_file
        self.agent_id = agent_id  # Store agent ID for config updates
        # Load system prompt from files if not provided
        if system_prompt is None:
            system_prompt = build_agent_prompt("interactive", include_tools=True)
        
        # Initialize base agent
        super().__init__(
            model=model,
            system_prompt=system_prompt,
            tools=[],  # Will add tools below
            memory=memory or {},
            stream=stream
        )
        
        # Add interactive tools
        self._add_interactive_tools()
        
        # Add file operation tools
        self._add_file_tools()
        
        # Add article tools
        self._add_article_tools()
        
        # Add image tools
        self._add_image_tools()
    
    def _add_interactive_tools(self):
        """Add interactive tools."""
        # wait_for_user
        wait_for_user_def = {
            "type": "function",
            "function": litellm.utils.function_to_dict(wait_for_user),
            "_function": wait_for_user
        }
        self.tools.append(wait_for_user_def)
        
        # get_session_state
        get_session_state_def = {
            "type": "function",
            "function": litellm.utils.function_to_dict(get_session_state),
            "_function": get_session_state
        }
        self.tools.append(get_session_state_def)
    
    def _add_file_tools(self):
        """Add general file operation tools."""
        # read_file
        read_file_def = {
            "type": "function",
            "function": litellm.utils.function_to_dict(read_file),
            "_function": read_file
        }
        self.tools.append(read_file_def)
        
        # edit_file
        edit_file_def = {
            "type": "function",
            "function": litellm.utils.function_to_dict(edit_file),
            "_function": edit_file
        }
        self.tools.append(edit_file_def)
        
        # add_to_story
        add_to_story_def = {
            "type": "function",
            "function": litellm.utils.function_to_dict(add_to_story),
            "_function": add_to_story
        }
        self.tools.append(add_to_story_def)
    
    def _add_article_tools(self):
        """Add article search and reading tools."""
        # read_article
        read_article_def = {
            "type": "function",
            "function": litellm.utils.function_to_dict(read_article),
            "_function": read_article
        }
        self.tools.append(read_article_def)
        
        # search_articles
        search_articles_def = {
            "type": "function",
            "function": litellm.utils.function_to_dict(search_articles),
            "_function": search_articles
        }
        self.tools.append(search_articles_def)
        
        # list_articles_in_directory
        list_articles_def = {
            "type": "function",
            "function": litellm.utils.function_to_dict(list_articles_in_directory),
            "_function": list_articles_in_directory
        }
        self.tools.append(list_articles_def)
    
    def _add_image_tools(self):
        """Add image generation tools."""
        # Too slow for dev - commenting out for now
        # create_image_def = {
        #     "type": "function",
        #     "function": litellm.utils.function_to_dict(create_image),
        #     "_function": create_image
        # }
        # self.tools.append(create_image_def)
        pass
    
    def _execute_tool(self, tool_call: dict):
        """
        Override tool execution to handle WaitingForInput sentinel.
        
        When wait_for_user() is called, it returns a WaitingForInput object.
        We need to convert this to a status event signal.
        """
        result = super()._execute_tool(tool_call)
        
        # Check if result is WaitingForInput sentinel
        if isinstance(result, WaitingForInput):
            # Return a special dict that AgentRunner will recognize
            # But also yield the status event from BaseAgent
            return {
                "_waiting_for_input": True,
                "message": "Waiting for user input"
            }
        
        return result

