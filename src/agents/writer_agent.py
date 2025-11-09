"""
WriterAgent - Writes and edits stories.

Inherits from BaseAgent and adds story writing tools.
"""
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from base_agent.base_agent import BaseAgent
from tools.files import read_file, edit_file, add_to_story
from tools.articles import (
    read_article,
    search_articles,
    list_articles_in_directory
)
# from tools.images import create_image  # Too slow for dev
import litellm


class WriterAgent(BaseAgent):
    """
    Agent specialized in writing stories and articles.
    
    Combines story writing tools with article management to create
    cohesive narratives from wiki content.
    """
    
    def __init__(
        self,
        model: str = "claude-haiku-4-5-20251001",
        system_prompt: str = None,
        memory: dict = None,
        stream: bool = True
    ):
        """
        Initialize WriterAgent.
        
        Args:
            model: LLM model to use
            system_prompt: Optional custom system prompt
            memory: Optional initial memory dict
            stream: Whether to stream responses
        """
        # Default system prompt for WriterAgent
        if system_prompt is None:
            system_prompt = """You are a creative WriterAgent for a collaborative storytelling wiki.

Your role is to:
- Write engaging stories and narrative prose
- Edit existing story and article content for coherence and quality
- Reference wiki articles to maintain consistency with established lore
- Create new wiki articles as needed for characters, locations, and concepts
- Weave together narrative and reference material

You have access to:
- File operations (read_file, edit_file) - Read and edit ANY file in wikicontent
- Story writing (add_to_story) - Append narrative prose to story files
- Article tools (read_article, search_articles, list_articles) - Search and read articles

Best practices:
- Use add_to_story() for writing new narrative content that flows sequentially
- Use edit_file() with search/replace blocks for surgical edits to existing content
- Use read_file() to check file contents before editing
- Check existing articles before writing to maintain consistency
- Write story content in a narrative, flowing style
- Create supporting wiki articles for important story elements
- Use markdown formatting appropriately

Stay the course - write with clarity, energy, and purpose! 🏰✍️"""
        
        # Initialize base agent
        super().__init__(
            model=model,
            system_prompt=system_prompt,
            tools=[],  # Will add tools below
            memory=memory or {},
            stream=stream
        )
        
        # Add file operation tools
        self._add_file_tools()
        
        # Add article tools
        self._add_article_tools()
        
        # Add image tools
        self._add_image_tools()
    
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

