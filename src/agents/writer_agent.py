"""
WriterAgent - Writes and edits stories.

Inherits from BaseAgent and adds story writing tools.
"""
import sys
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Add parent to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from base_agent.base_agent import BaseAgent
from tools.files import read_file, edit_file, add_to_story, rename_story_file
from tools.articles import (
    read_article,
    search_articles,
    list_articles_in_directory
)
from tools.context import get_context
from tools.interactive import done, Finished
from agents.prompts.loader import build_agent_prompt
# from tools.images import create_image  # Too slow for dev
import litellm
import os


class WriterAgent(BaseAgent):
    """
    Agent specialized in writing stories and articles.
    
    Combines story writing tools with article management to create
    cohesive narratives from wiki content.
    """
    
    def __init__(
        self,
        model: str = "claude-haiku-4-5-20251001",
        story_file: str = "stories/writer_story.md",
        system_prompt: str = None,
        memory: dict = None,
        stream: bool = True,
        agent_id: str = None,
        agent_config: dict = None
    ):
        """
        Initialize WriterAgent.
        
        Args:
            model: LLM model to use
            story_file: Default story file for writing (default: "stories/writer_story.md")
            system_prompt: Optional custom system prompt
            memory: Optional initial memory dict
            stream: Whether to stream responses
            agent_id: Optional agent ID for updating config when renaming story
            agent_config: Optional agent configuration dict (for future state persistence)
        """
        self.story_file = story_file
        self.agent_id = agent_id  # Store agent ID for config updates
        logger.info(f"✍️ WriterAgent initialized: story_file={story_file}, agent_id={agent_id}")
        # Load system prompt from files if not provided
        if system_prompt is None:
            base_prompt = build_agent_prompt("writer", include_tools=True)
            # Add story file context
            system_prompt = f"""{base_prompt}

---

## Your Story File

**Your designated output file:** `{story_file}`

When you write new narrative content, use:
```
add_to_my_story(content="your prose here")
```

All your creative story writing will be appended to this file. This is where your narrative output lives!"""
        
        # Initialize base agent
        super().__init__(
            model=model,
            system_prompt=system_prompt,
            tools=[],  # Will add tools below
            memory=memory or {},
            stream=stream
        )
        
        # Add completion tools
        self._add_completion_tools()
        
        # Add rename tool
        self._add_rename_tool()
        
        # Add file operation tools
        self._add_file_tools()
        
        # Add article tools
        self._add_article_tools()
        
        # Add image tools
        self._add_image_tools()
    
    def _add_completion_tools(self):
        """Add completion/control flow tools."""
        # done
        done_def = {
            "type": "function",
            "function": litellm.utils.function_to_dict(done),
            "_function": done
        }
        self.tools.append(done_def)
    
    def _add_rename_tool(self):
        """Add rename story tool."""
        # Create the rename method bound to this instance
        def rename_my_story(new_filename: str):
            """
            Rename your story file to a new name.
            
            This will rename the actual file in wikicontent and update your agent 
            configuration. Use this when you want to give your story a better name.
            
            Parameters
            ----------
            new_filename : str
                New filename (e.g., "epic_adventure.md" or "stories/epic_adventure.md")
                If no directory is specified, the file stays in its current directory.
            
            Returns
            -------
            dict
                {"success": bool, "message": str, "old_file": str, "new_file": str}
                or {"success": bool, "error": str}
            
            Examples
            --------
            >>> rename_my_story("epic_adventure.md")
            {"success": True, "message": "Story renamed successfully", ...}
            """
            return self._rename_my_story_impl(new_filename)
        
        # Add to tools
        rename_def = {
            "type": "function",
            "function": litellm.utils.function_to_dict(rename_my_story),
            "_function": rename_my_story
        }
        self.tools.append(rename_def)
    
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
        
        # add_to_my_story - bound version of add_to_story for this agent
        def add_to_my_story(content: str):
            """
            Append narrative prose to YOUR story file.
            
            This writes to your designated story file automatically.
            Use this when continuing your narrative - it's your primary writing tool!
            
            Parameters
            ----------
            content : str
                The narrative prose to append
            
            Returns
            -------
            dict
                {
                    "success": bool,
                    "message": str,
                    "file_path": str,
                    "lines_added": int,
                    "lines_removed": int,
                    "mode": "append"
                }
            
            Examples
            --------
            >>> add_to_my_story("The wizard cast a powerful spell...")
            {"success": True, "message": "Appended to stories/tale.md", ...}
            """
            return add_to_story(content=content, filepath=self.story_file)
        
        add_to_my_story_def = {
            "type": "function",
            "function": litellm.utils.function_to_dict(add_to_my_story),
            "_function": add_to_my_story
        }
        self.tools.append(add_to_my_story_def)
    
    def _add_article_tools(self):
        """Add article search and reading tools."""
        # read_article
        read_article_def = {
            "type": "function",
            "function": litellm.utils.function_to_dict(read_article),
            "_function": read_article
        }
        self.tools.append(read_article_def)
        
        # get_context (multi-document expansion via memtool)
        get_context_def = {
            "type": "function",
            "function": litellm.utils.function_to_dict(get_context),
            "_function": get_context
        }
        self.tools.append(get_context_def)
        
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
    
    def _rename_my_story_impl(self, new_filename: str) -> dict:
        """
        Implementation of rename_my_story tool.
        
        Renames the story file and updates agent configuration.
        """
        try:
            # Parse new filename - if it's just a filename, keep current directory
            old_path = Path(self.story_file)
            new_path_input = Path(new_filename)
            
            # If new path has no directory, use old directory
            if len(new_path_input.parts) == 1:
                new_filepath = str(old_path.parent / new_filename)
            else:
                new_filepath = new_filename
            
            # Rename the actual file
            rename_result = rename_story_file(self.story_file, new_filepath)
            
            if not rename_result.get("success"):
                return rename_result
            
            # Update agent's story_file attribute
            old_story_file = self.story_file
            self.story_file = new_filepath
            
            # Update agents.json if we have an agent_id
            if self.agent_id:
                try:
                    # Import here to avoid circular imports
                    from server.config import agent_config
                    
                    # Update the agent's config
                    agent_config.update_agent(
                        self.agent_id,
                        {"config": {"story_file": new_filepath}}
                    )
                    
                    # Regenerate system prompt with new file path
                    base_prompt = build_agent_prompt("writer", include_tools=True)
                    self.system_prompt = f"""{base_prompt}

---

## Your Story File

**Your designated output file:** `{new_filepath}`

When you write new narrative content, use:
```
add_to_my_story(content="your prose here")
```

All your creative story writing will be appended to this file. This is where your narrative output lives!"""
                    
                except Exception as e:
                    # If we can't update agents.json, at least we renamed the file
                    return {
                        "success": True,
                        "message": f"Renamed file but couldn't update config: {str(e)}",
                        "old_file": old_story_file,
                        "new_file": new_filepath,
                        "warning": "Agent config not updated - restart may be needed"
                    }
            
            return {
                "success": True,
                "message": f"Story renamed successfully from {old_story_file} to {new_filepath}",
                "old_file": old_story_file,
                "new_file": new_filepath
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Error renaming story: {str(e)}"
            }
    
    def _execute_tool(self, tool_call: dict):
        """
        Override tool execution to handle Finished sentinel.
        
        When done() is called, it returns a Finished object.
        We need to convert this to a signal that AgentRunner recognizes.
        """
        result = super()._execute_tool(tool_call)
        
        # Check if result is Finished sentinel
        if isinstance(result, Finished):
            # Return a special dict that AgentRunner will recognize
            return {
                "_finished": True,
                "message": "Task completed"
            }
        
        return result

