"""
ReaderAgent for processing long stories chunk by chunk.

Uses the HighlightContent system to manage story windows efficiently.
"""
import sys
import os
import json
import re
import toml
import litellm
from pathlib import Path
from typing import Optional

# Add parent directory to sys.path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_agent.base_agent import BaseAgent, EndConversation
# from tools.images import create_image  # Too slow for dev
from tools.search import find_articles, find_images, find_songs, find_files
from tools.articles import read_article
from tools.files import edit_file
from agents.prompts.loader import build_agent_prompt
from utils.git import ensure_content_branch

# Load config
config = toml.load("config.toml")


class StoryWindow:
    """Manages the reading window through a long story."""
    
    def __init__(self, story_path: str, starting_position: Optional[int] = None):
        self.story_path = Path(story_path)
        self.story_text = ""
        self.current_position = starting_position if starting_position is not None else config["story"]["story_start"]
        self.chunk_size = config["story"]["chunk_size"]
        
        self._load_story()
    
    def _load_story(self) -> bool:
        """Load story text from file."""
        if not self.story_path.exists():
            raise FileNotFoundError(f"Story file not found: {self.story_path}")
        
        with open(self.story_path, 'r', encoding='utf-8') as f:
            self.story_text = f.read()
        
        return True
    
    def get_current_chunk(self, num_words: Optional[int] = None) -> str:
        """Get current story chunk without advancing position."""
        if not num_words:
            num_words = self.chunk_size
            
        words = self.story_text.split()
        start_word = self.current_position
        end_word = min(start_word + num_words, len(words))
        
        return " ".join(words[start_word:end_word])
    
    def advance(self, num_words: Optional[int] = None) -> str:
        """Advance the reading window and return the new chunk."""
        if not num_words:
            num_words = self.chunk_size
        
        # Get the chunk from current position
        chunk = self.get_current_chunk(num_words)
        
        # Advance position
        words = self.story_text.split()
        self.current_position = min(self.current_position + num_words, len(words))
        
        return chunk
    
    def get_position_info(self) -> dict:
        """Get current reading position information."""
        words = self.story_text.split()
        total_words = len(words)
        progress_percent = (self.current_position / total_words) * 100 if total_words > 0 else 0
        
        return {
            "current_position": self.current_position,
            "total_words": total_words, 
            "progress_percent": progress_percent,
            "is_complete": self.current_position >= total_words
        }
    
    def set_position(self, position: int) -> str:
        """Jump to a specific word position in the story."""
        words = self.story_text.split()
        total_words = len(words)
        
        # Clamp position to valid range
        position = max(0, min(position, total_words))
        
        old_position = self.current_position
        self.current_position = position
        
        # Get chunk at new position
        chunk = self.get_current_chunk()
        
        return chunk, old_position
    
    def grep_story(self, search_term: str, max_results: int = 10, context_words: int = 20) -> list:
        """
        Search the story using regex patterns.
        
        Returns list of matches with context.
        """
        words = self.story_text.split()
        results = []
        
        # Search through the text
        pattern = re.compile(search_term, re.IGNORECASE)
        
        # Find all matches in the full text
        for match in pattern.finditer(self.story_text):
            if len(results) >= max_results:
                break
                
            match_start = match.start()
            match_end = match.end()
            
            # Calculate word position (approximate)
            text_before_match = self.story_text[:match_start]
            word_position = len(text_before_match.split())
            
            # Get context
            start_word = max(0, word_position - context_words)
            end_word = min(len(words), word_position + context_words + 10)  # +10 for matched words
            
            context = " ".join(words[start_word:end_word])
            matched_text = match.group()
            
            results.append({
                "word_position": word_position,
                "matched_text": matched_text,
                "context": context
            })
        
        return results


class ReaderAgent(BaseAgent):
    """
    Agent that reads through long stories using a sliding window approach.
    
    Manages story content via HighlightContent system to prevent context bloat.
    """
    
    def __init__(self, story_file: str = "story.txt", agent_id: Optional[str] = None, agent_config: Optional[dict] = None, **kwargs):
        """Initialize the ReaderAgent with story reading tools.
        
        Args:
            story_file: Path to story file relative to content repo (default: "story.txt")
            agent_id: Agent ID for updating config (optional)
            agent_config: Agent configuration dict containing current_position (optional)
            **kwargs: Additional arguments passed to BaseAgent
        """
        
        # Store agent_id for config updates
        self.agent_id = agent_id
        
        # Load the story file
        story_path = Path(config["paths"]["content_repo"]) / story_file
        story_name = story_file  # Use filename as story name
        
        # Get starting position from agent config if available
        starting_position = None
        if agent_config and 'current_position' in agent_config:
            starting_position = agent_config['current_position']
        
        # Initialize story window with saved position
        self.story_window = StoryWindow(story_path, starting_position=starting_position)
        
        # Create tools using litellm helper with embedded functions
        tools = [
            {"type": "function", "function": litellm.utils.function_to_dict(self.advance), "_function": self.advance},
            {"type": "function", "function": litellm.utils.function_to_dict(self.get_status), "_function": self.get_status},
            {"type": "function", "function": litellm.utils.function_to_dict(self.go_to_position_in_story), "_function": self.go_to_position_in_story},
            {"type": "function", "function": litellm.utils.function_to_dict(self.grep_story), "_function": self.grep_story},
            # {"type": "function", "function": litellm.utils.function_to_dict(create_image), "_function": create_image},  # Too slow for dev
            {"type": "function", "function": litellm.utils.function_to_dict(find_articles), "_function": find_articles},
            {"type": "function", "function": litellm.utils.function_to_dict(find_images), "_function": find_images},
            {"type": "function", "function": litellm.utils.function_to_dict(find_songs), "_function": find_songs},
            {"type": "function", "function": litellm.utils.function_to_dict(find_files), "_function": find_files},
            {"type": "function", "function": litellm.utils.function_to_dict(read_article), "_function": read_article},
            {"type": "function", "function": litellm.utils.function_to_dict(edit_file), "_function": edit_file},
        ]
        
        # Load base system prompt from files and add story-specific context
        base_prompt = build_agent_prompt("reader", include_tools=True)
        system_prompt = f"""{base_prompt}

---

## Current Story Context

You are currently reading: **{story_name}**

The story content will be provided via the advance() tool using highlighted content.
Read systematically through the entire story, advancing the window as you go."""

        # Initialize base agent
        # Use model from kwargs if provided, otherwise use config
        model = kwargs.pop('model', config["agent"]["model"])
        super().__init__(
            model=model,
            system_prompt=system_prompt,
            tools=tools,
            **kwargs
        )
        
        # Set initial memory
        self.set_memory("story_name", story_name)
        self.set_memory("story_path", str(story_path))
        
        # Initialize pending content tracking
        self._pending_content = None
    
    def advance(self, num_words: Optional[int] = None):
        """
        Advance the story reading window forward and return the next chunk of text.
        
        This is your primary tool for progressing through the story. Each call moves 
        the reading position forward and returns the next chunk of story text.
        
        Parameters
        ----------
        num_words : int, optional
            Number of words to advance through the story. 
            Units: words (whitespace-separated tokens)
            Default: 5000 words (from config.toml story.chunk_size)
            
        Returns
        -------
        str
            The next chunk of story text, up to num_words in length
            
        Side Effects
        ------------
        - Updates current reading position in memory
        - Persists position to agents.json for resuming later
        - Advances cannot be undone (position only moves forward)
        
        Example
        -------
        advance()           # Advance by default chunk size (5000 words)
        advance(1000)       # Advance by exactly 1000 words
        advance(10000)      # Read a larger chunk (10000 words)
        """
        # Get new chunk
        chunk = self.story_window.advance(num_words)
        
        # Update memory with current position
        pos_info = self.story_window.get_position_info()
        self.update_memory({
            "current_position": pos_info["current_position"],
            "total_words": pos_info["total_words"],
            "progress_percent": pos_info["progress_percent"],
            "is_complete": pos_info["is_complete"]
        })
        
        # Persist current position to agents.json if we have an agent_id
        if self.agent_id:
            try:
                # Import here to avoid circular imports
                from server.config import agent_config
                
                # Update the agent's config with current position
                agent_config.update_agent(
                    self.agent_id,
                    {"config": {"current_position": pos_info["current_position"]}}
                )
                
            except Exception as e:
                # Don't fail the advance operation if config update fails
                # Just log it (agent can still continue reading)
                pass
        
        # Calculate start word for this chunk
        chunk_word_count = len(chunk.split()) if chunk.strip() else 0
        start_word = pos_info["current_position"] - chunk_word_count
        
        # Store content for deferred addition (after tool result is processed)
        self._pending_content = {
            'content': chunk,
            'start_word': start_word
        }
        
        # Return simple confirmation - the content will be added after tool execution
        return f"Advanced from word {start_word} to word {pos_info['current_position']} ({pos_info['progress_percent']:.1f}% complete)."
    
    def get_status(self):
        """
        Get current reading status and position information.
        
        Returns
        -------
        str
            Status report with position, progress, and story information
        """
        pos_info = self.story_window.get_position_info()
        story_name = self.get_memory("story_name", "unknown")
        
        status = f"""📖 Reading Status for "{story_name}":

Current Position: Word {pos_info['current_position']} of {pos_info['total_words']}
Progress: {pos_info['progress_percent']:.1f}% complete
Chunk Size: {self.story_window.chunk_size} words

Status: {"✅ Complete" if pos_info['is_complete'] else "🔄 In Progress"}

Use advance() to continue reading."""
        
        return status
    
    def go_to_position_in_story(self, position: int):
        """
        Jump to a specific word position in the story.
        
        This allows you to skip ahead or go back to a specific location in the story.
        Unlike advance(), this sets the reading position to an exact word number.
        
        Parameters
        ----------
        position : int
            The word position to jump to (0-indexed)
            Position will be clamped to valid range [0, total_words]
            
        Returns
        -------
        str
            Confirmation message with the chunk at the new position
            
        Side Effects
        ------------
        - Updates current reading position
        - Persists new position to agents.json
        - Returns a chunk at the new position via highlighted content
        
        Example
        -------
        go_to_position_in_story(0)       # Jump to the beginning
        go_to_position_in_story(10000)   # Jump to word 10000
        go_to_position_in_story(50000)   # Skip ahead to word 50000
        """
        chunk, old_position = self.story_window.set_position(position)
        
        # Update memory with new position
        pos_info = self.story_window.get_position_info()
        self.update_memory({
            "current_position": pos_info["current_position"],
            "total_words": pos_info["total_words"],
            "progress_percent": pos_info["progress_percent"],
            "is_complete": pos_info["is_complete"]
        })
        
        # Persist position to agents.json if we have an agent_id
        if self.agent_id:
            try:
                from server.config import agent_config
                
                agent_config.update_agent(
                    self.agent_id,
                    {"config": {"current_position": pos_info["current_position"]}}
                )
            except Exception as e:
                pass
        
        # Calculate chunk info for display
        chunk_word_count = len(chunk.split()) if chunk.strip() else 0
        
        # Store content for deferred addition
        self._pending_content = {
            'content': chunk,
            'start_word': pos_info["current_position"]
        }
        
        # Return confirmation
        return f"Jumped from word {old_position} to word {pos_info['current_position']} ({pos_info['progress_percent']:.1f}% complete)."
    
    def grep_story(self, search_term: str, max_results: int = 10, context_words: int = 20):
        """
        Search through the entire story using regex patterns.
        
        This powerful search tool lets you find specific text, phrases, or patterns 
        anywhere in the story without reading through it sequentially. Perfect for 
        finding mentions of characters, locations, or specific events.
        
        Parameters
        ----------
        search_term : str
            Regex pattern to search for (case-insensitive by default)
            Examples: "dragon", "Chapter \\d+", "said.*sadly"
        max_results : int, optional
            Maximum number of results to return (default: 10)
            Prevents overwhelming output for common terms
        context_words : int, optional
            Number of words to show before the match (default: 20)
            Context helps understand where in the story the match occurs
            
        Returns
        -------
        str
            Formatted list of matches with word positions and context
            
        Side Effects
        ------------
        None - this is a read-only operation that doesn't change position
        
        Example
        -------
        grep_story("Frodo")                    # Find all mentions of Frodo
        grep_story("Chapter \\d+", max_results=5)  # Find first 5 chapter headers
        grep_story("dragon.*fire", context_words=30)  # Find dragon/fire phrases with more context
        """
        results = self.story_window.grep_story(search_term, max_results, context_words)
        
        if not results:
            return f"No matches found for pattern: '{search_term}'"
        
        # Format results
        output = [f"Found {len(results)} match(es) for pattern: '{search_term}'\n"]
        
        for i, result in enumerate(results, 1):
            output.append(f"\n{i}. At word {result['word_position']}:")
            output.append(f"   Matched: '{result['matched_text']}'")
            output.append(f"   Context: ...{result['context']}...")
        
        if len(results) == max_results:
            output.append(f"\n(Showing first {max_results} results. Use max_results parameter to see more.)")
        
        return "\n".join(output)
    
    def process_pending_content(self):
        """Process any pending content after tool execution is complete."""
        if self._pending_content:
            self.advance_content(
                self._pending_content['content'], 
                self._pending_content['start_word']
            )
            self._pending_content = None
    
    def _post_tool_execution_hook(self):
        """Process any pending story content after tool execution."""
        self.process_pending_content()


def main():
    """Demo the ReaderAgent"""
    print("🚀 Starting ReaderAgent demo...")
    
    # Ensure we're on the correct content branch
    if not ensure_content_branch():
        print("❌ Failed to ensure correct content branch. Exiting.")
        return
    
    # Create the reader agent
    agent = ReaderAgent(stream=True)
    
    # Get initial status
    print("\n--- Initial Status ---")
    status = agent.get_status()
    print(status)
    
    # Run a reading session
    print("\n--- Starting Reading Session ---") 
    result = agent.run_forever(
        "Start reading the story. Use advance() to get the first chunk, then look up relevant articles. Use create_image() to create an image if you think the image would be cool (remember to provide a good name for the image).",
        max_turns=5
    )
    
    print(f"\n--- Session Result ---")
    print(result)


if __name__ == "__main__":
    main()