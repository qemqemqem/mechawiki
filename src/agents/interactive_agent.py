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
from tools.images import create_image
import litellm


class InteractiveAgent(BaseAgent):
    """
    Agent specialized in creating interactive experiences.
    
    Can present narrative, ask for user choices, and branch based on input.
    """
    
    def __init__(
        self,
        model: str = "claude-haiku-4-5-20251001",
        system_prompt: str = None,
        memory: dict = None,
        stream: bool = True
    ):
        """
        Initialize InteractiveAgent.
        
        Args:
            model: LLM model to use
            system_prompt: Optional custom system prompt
            memory: Optional initial memory dict
            stream: Whether to stream responses
        """
        # Default system prompt for InteractiveAgent
        if system_prompt is None:
            system_prompt = """You are an InteractiveAgent for collaborative storytelling.

Your role is to:
- Create engaging, interactive narrative experiences
- Present choices to the user at key story moments
- Respond to user input and branch the story accordingly
- Reference wiki articles to maintain world consistency
- Create memorable characters, scenes, and decisions

You have access to:
- Interactive tools (wait_for_user, get_session_state)
- File operations (read_file, edit_file) - Read and edit ANY file in wikicontent
- Story writing (add_to_story) - Append narrative prose to story files
- Article tools (read_article, search_articles, list_articles) - Search and read articles
- Image generation (create_image) - Generate artwork

Best practices:
- Set the scene with vivid description before presenting choices
- Use wait_for_user() when you want the user to make a decision
- Acknowledge and incorporate user input into the narrative
- Maintain narrative coherence across user interactions
- Use add_to_story() to record the interactive session as a narrative
- Use edit_file() to create or update wiki articles for story developments

When you use wait_for_user(), the system will:
1. Pause your turn
2. Wait for the user to send a message
3. Resume with their input in the conversation

Hunt with purpose - create experiences that keep users engaged! 🎮⚔️"""
        
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
        create_image_def = {
            "type": "function",
            "function": litellm.utils.function_to_dict(create_image),
            "_function": create_image
        }
        self.tools.append(create_image_def)
    
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
                "prompt": result.prompt,
                "message": result.prompt
            }
        
        return result

