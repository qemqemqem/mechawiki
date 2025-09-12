#!/usr/bin/env python3
"""Minimal MCP tools for testing advance function."""

import os
# Turn off FastMCP splash screen
os.environ["FASTMCP_NO_SPLASH"] = "1"

import toml
from pathlib import Path
from typing import Dict, Any, Optional
from fastmcp import FastMCP

# Load config
config = toml.load("config.toml")

class StoryState:
    """Manages the loaded story text and navigation."""
    def __init__(self):
        self.story_text = ""
        self.story_words = []
        self.current_position = 0
        self.linked_articles = []
        
    def load_story(self, story_name: str) -> bool:
        """Load a story from the content directory."""
        story_path = Path(config["paths"]["content_dir"]) / story_name / f"{story_name}.txt"
        
        try:
            with open(story_path, 'r', encoding='utf-8') as f:
                self.story_text = f.read().strip()
            self.story_words = self.story_text.split()
            return True
        except Exception as e:
            print(f"Error loading story: {e}")
            return False

# Initialize story state and load the current story
story_state = StoryState()
current_story = config["story"]["current_story"]
if not story_state.load_story(current_story):
    print(f"❌ Warning: Could not load story '{current_story}'")
else:
    print(f"✅ Loaded story: {current_story} ({len(story_state.story_text)} characters)")
    print(f"📊 Total words: {len(story_state.story_text.split())}")
    print(f"📍 Initial position: {story_state.current_position}")

# Initialize FastMCP server
mcp = FastMCP("WikiAgent")

def _advance_impl(num_words: Optional[int] = None, current_position: int = 0) -> Dict[str, Any]:
    """Internal implementation of advance that accepts position parameter."""
    # Handle default parameter
    if num_words is None or num_words == 0:
        num_words = config["story"]["chunk_size"]
    
    print(f"🐛 advance() called - num_words: {num_words}, current_position: {current_position}")
    
    # Validate range
    num_words = max(config["story"]["min_advance"], min(num_words, config["story"]["max_advance"]))
    
    # Calculate new position
    new_pos = current_position + num_words
    new_pos = max(0, min(new_pos, len(story_state.story_words)))
    
    # Get chunk of words to show
    if new_pos > current_position:
        # Moving forward - show words from current to new position
        start_pos = current_position
        end_pos = new_pos
    else:
        # Moving backward - show words from new to current position
        start_pos = new_pos
        end_pos = current_position
    
    chunk_words = story_state.story_words[start_pos:end_pos]
    chunk = ' '.join(chunk_words)
    
    # Update story info
    story_info = {"position": new_pos}
    
    # Prepare result message
    chunk_words_count = len(chunk.split()) if chunk.strip() else 0
    result_content = f"Showing words {start_pos} - {end_pos} ({chunk_words_count} words)\n\n{chunk}"
    
    print(f"🐛 advance() returning - old_pos: {current_position}, new_pos: {new_pos}")
    
    return {
        "position": new_pos,
        "content": result_content,
        "story_info": story_info
    }

@mcp.tool()
def advance(num_words: Optional[int] = None) -> Dict[str, Any]:
    """Navigate through the story by advancing or rewinding by specified words.
    
    Args:
        num_words: Number of words to advance (positive) or rewind (negative)
                  If not provided, uses default chunk size from config (1000).
                  Range: -2000 to +2000
    
    Returns:
        Dict with updated story state and current chunk content.
        
    Note: Current position will be injected by the LangGraph agent using
    a custom tool node that calls the internal implementation.
    """
    # This is the public interface that LLMs see - no position parameter
    # The LangGraph agent will intercept calls and use _advance_impl directly
    return _advance_impl(num_words=num_words, current_position=0)

@mcp.tool()
def add_article(title: str, content: str) -> str:
    """Create a new wiki article (placeholder)."""
    return f"Article '{title}' would be created with content: {content[:100]}..."

if __name__ == "__main__":
    mcp.run()