"""
ReaderAgent for processing long stories chunk by chunk.

Uses the HighlightContent system to manage story windows efficiently.
"""
import sys
import os
import json
import toml
import litellm
from pathlib import Path
from typing import Optional

# Add parent directory to sys.path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.base_agent import BaseAgent, EndConversation

# Load config
config = toml.load("config.toml")


class StoryWindow:
    """Manages the reading window through a long story."""
    
    def __init__(self, story_path: str):
        self.story_path = Path(story_path)
        self.story_text = ""
        self.current_position = config["story"]["story_start"]
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


class ReaderAgent(BaseAgent):
    """
    Agent that reads through long stories using a sliding window approach.
    
    Manages story content via HighlightContent system to prevent context bloat.
    """
    
    def __init__(self, **kwargs):
        """Initialize the ReaderAgent with story reading tools."""
        
        # Load the configured story
        story_name = config["story"]["current_story"]
        story_path = Path(config["paths"]["content_dir"]) / story_name / f"{story_name}.txt"
        
        # Initialize story window
        self.story_window = StoryWindow(story_path)
        
        # Create tools using litellm helper
        tools = [
            {"type": "function", "function": litellm.utils.function_to_dict(self.advance)},
            {"type": "function", "function": litellm.utils.function_to_dict(self.get_status)},
        ]
        
        # Define available functions
        available_functions = {
            "advance": self.advance,
            "get_status": self.get_status,
        }
        
        # Enhanced system prompt for story reading
        system_prompt = f"""You are a story reader agent processing "{story_name}".

Your mission: Read through the story chunk by chunk, analyzing and understanding the content.

Available tools:
- advance(num_words): Move the reading window forward by specified words (default {config['story']['chunk_size']})
- get_status(): Get current reading position and progress information
- end(reason): End the reading session

The current story section will be provided via the advance() tool using highlighted content.
Focus on understanding the narrative, characters, settings, and notable story elements.

When you advance, the story content becomes available for analysis. Pay attention to:
- Character introductions and development
- Setting descriptions and world-building
- Plot progression and key events
- Notable objects, concepts, or themes

Read systematically through the entire story, advancing the window as you go."""

        # Initialize base agent
        super().__init__(
            model=config["agent"]["model"],
            system_prompt=system_prompt,
            tools=tools,
            available_functions=available_functions,
            **kwargs
        )
        
        # Set initial memory
        self.set_memory("story_name", story_name)
        self.set_memory("story_path", str(story_path))
        
        # Initialize pending content tracking
        self._pending_content = None
    
    def advance(self, num_words: Optional[int] = None):
        """
        Advance the story reading window.
        
        Parameters
        ----------
        num_words : int, optional
            Number of words to advance (default uses config chunk_size)
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
        
        # Calculate start word for this chunk
        chunk_word_count = len(chunk.split()) if chunk.strip() else 0
        start_word = pos_info["current_position"] - chunk_word_count
        
        # Store content for deferred addition (after tool result is processed)
        self._pending_content = {
            'content': chunk,
            'start_word': start_word
        }
        
        # Return simple confirmation - the content will be added after tool execution
        return f"Advanced to word {pos_info['current_position']} ({pos_info['progress_percent']:.1f}% complete)."
    
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
    
    def process_pending_content(self):
        """Process any pending content after tool execution is complete."""
        if self._pending_content:
            self.advance_content(
                self._pending_content['content'], 
                self._pending_content['start_word']
            )
            self._pending_content = None
    
    def run_forever(self, initial_message: str, max_turns: int = 3):
        """Override to handle pending content after tool execution."""
        # Add initial message
        self.add_user_message(initial_message)
        
        turn = 0
        while True:
            turn += 1
            
            # Check turn limit
            if max_turns is not None and turn > max_turns:
                return "Max turns reached"
            
            print(f"\n--- Agent Turn {turn} ---")
            
            # Make LLM call
            response = litellm.completion(
                model=self.model,
                messages=self.messages,
                tools=self.tools if self.tools else None,
                tool_choice="auto" if self.tools else None,
                stream=self.stream
            )
            
            # Handle response based on streaming mode
            if self.stream:
                collected_content, tool_calls = self._handle_streaming_response(response)
            else:
                collected_content, tool_calls = self._handle_non_streaming_response(response)
            
            # Check for tool calls
            if tool_calls and any(tc.get("id") for tc in tool_calls):
                valid_tool_calls = [tc for tc in tool_calls if tc.get("id")]
                print(f"\n--- Executing {len(valid_tool_calls)} tool calls ---")
                
                # Add assistant message
                assistant_message = {
                    "role": "assistant",
                    "content": collected_content if collected_content else None,
                    "tool_calls": valid_tool_calls
                }
                self.messages.append(assistant_message)
                
                # Execute each tool call
                for tool_call in valid_tool_calls:
                    function_name = tool_call["function"]["name"]
                    function_args = json.loads(tool_call["function"]["arguments"])
                    
                    print(f"Calling {function_name} with args: {function_args}")
                    
                    # Execute tool (can be overridden by subclasses)
                    raw_result = self._execute_tool(tool_call)
                    
                    # Check if tool returned EndConversation signal
                    if isinstance(raw_result, EndConversation):
                        print(f"Agent called end() - terminating conversation")
                        return "Conversation ended by agent"
                    
                    # Regular result
                    result_content = str(raw_result)
                    print(f"Result: {raw_result}")
                    
                    # Add function result to conversation
                    self.messages.append({
                        "tool_call_id": tool_call["id"],
                        "role": "tool", 
                        "name": function_name,
                        "content": result_content
                    })
                
                # Process any pending content after all tool results are added
                self.process_pending_content()
                
            else:
                # No tool calls - add assistant message and continue
                if collected_content:
                    self.messages.append({
                        "role": "assistant", 
                        "content": collected_content
                    })
                
                # Continue loop regardless - only exit on turn limit


def main():
    """Demo the ReaderAgent"""
    print("🚀 Starting ReaderAgent demo...")
    
    # Create the reader agent
    agent = ReaderAgent(stream=True)
    
    # Get initial status
    print("\n--- Initial Status ---")
    status = agent.get_status()
    print(status)
    
    # Run a reading session
    print("\n--- Starting Reading Session ---") 
    result = agent.run_forever(
        "Start reading the story. Use advance() to get the first chunk, then analyze what you read.",
        max_turns=5
    )
    
    print(f"\n--- Session Result ---")
    print(result)


if __name__ == "__main__":
    main()