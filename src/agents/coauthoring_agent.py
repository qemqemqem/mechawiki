"""
CoauthoringAgent - Collaborative storytelling agent.

Inherits from WriterAgent but uses wait_for_user() instead of done()
to enable continuous collaboration with the user.
"""
import sys
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Add parent to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from agents.writer_agent import WriterAgent
from tools.interactive import wait_for_user, get_session_state, WaitingForInput
from agents.prompts.loader import build_agent_prompt
import litellm


class CoauthoringAgent(WriterAgent):
    """
    Agent specialized in collaborative storytelling with users.
    
    Inherits all WriterAgent capabilities but replaces the done() tool
    with wait_for_user() to enable continuous collaboration.
    """
    
    def __init__(
        self,
        model: str = "claude-haiku-4-5-20251001",
        story_file: str = "stories/coauthoring_story.md",
        system_prompt: str = None,
        memory: dict = None,
        stream: bool = True,
        agent_id: str = None,
        agent_config: dict = None
    ):
        """
        Initialize CoauthoringAgent.
        
        Args:
            model: LLM model to use
            story_file: Default story file for coauthoring (default: "stories/coauthoring_story.md")
            system_prompt: Optional custom system prompt (defaults to coauthoring prompt)
            memory: Optional initial memory dict
            stream: Whether to stream responses
            agent_id: Optional agent ID for updating config when renaming story
            agent_config: Optional agent configuration dict (for future state persistence)
        """
        # Override system prompt before calling super().__init__
        if system_prompt is None:
            base_prompt = build_agent_prompt("coauthoring", include_tools=True)
            # Add story file context
            system_prompt = f"""{base_prompt}

---

## Your Story File

**Your designated output file:** `{story_file}`

When you write new narrative content, use:
```
add_to_my_story(content="your prose here")
```

All your creative story writing will be appended to this file. This is where your collaborative narrative output lives!"""
        
        # Call parent __init__ which will set up all WriterAgent tools
        # We pass story_file, agent_id, and other params to parent
        super().__init__(
            model=model,
            story_file=story_file,
            system_prompt=system_prompt,
            memory=memory,
            stream=stream,
            agent_id=agent_id,
            agent_config=agent_config
        )
        
        logger.info(f"🤝 CoauthoringAgent initialized: story_file={story_file}, agent_id={agent_id}")
    
    def _add_completion_tools(self):
        """
        Override to add wait_for_user() instead of done().
        
        This is called by WriterAgent.__init__ during tool setup.
        """
        # wait_for_user - the collaborative tool!
        wait_for_user_def = {
            "type": "function",
            "function": litellm.utils.function_to_dict(wait_for_user),
            "_function": wait_for_user
        }
        self.tools.append(wait_for_user_def)
        
        # get_session_state - helpful for tracking collaboration progress
        get_session_state_def = {
            "type": "function",
            "function": litellm.utils.function_to_dict(get_session_state),
            "_function": get_session_state
        }
        self.tools.append(get_session_state_def)
    
    def _execute_tool(self, tool_call: dict):
        """
        Override tool execution to handle WaitingForInput sentinel.
        
        When wait_for_user() is called, it returns a WaitingForInput object.
        We need to convert this to a signal that AgentRunner recognizes.
        """
        result = super(WriterAgent, self)._execute_tool(tool_call)
        
        # Check if result is WaitingForInput sentinel
        if isinstance(result, WaitingForInput):
            # Return a special dict that AgentRunner will recognize
            return {
                "_waiting_for_input": True,
                "message": "Waiting for user input"
            }
        
        return result

