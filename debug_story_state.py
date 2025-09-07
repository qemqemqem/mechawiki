#!/usr/bin/env python3
"""Debug the story state issue."""

import sys
sys.path.insert(0, 'src')

# Import and test the story loading
import toml
from pathlib import Path

# Load config
config = toml.load("config.toml")

class StoryState:
    def __init__(self) -> None:
        self.current_position: int = 0
        self.story_text: str = ""
    
    def load_story(self, story_name: str) -> bool:
        """Load story text from file."""
        story_path = Path(config["paths"]["content_dir"]) / story_name / f"{story_name}.txt"
        print(f"Looking for story at: {story_path}")
        print(f"Path exists: {story_path.exists()}")
        if story_path.exists():
            with open(story_path, 'r', encoding='utf-8') as f:
                self.story_text = f.read()
            return True
        return False
    
    def advance_story(self, num_words: int) -> str:
        """Advance story position and return new chunk."""
        print(f"advance_story called with {num_words} words")
        print(f"Current position: {self.current_position}")
        print(f"Story length: {len(self.story_text.split())} words")
        
        # Apply guardrails
        min_advance: int = config["story"]["min_advance"]
        max_advance: int = config["story"]["max_advance"]
        original_num_words = num_words
        num_words = max(min_advance, min(num_words, max_advance))
        
        print(f"Original: {original_num_words}, after guardrails: {num_words}")
        
        old_position = self.current_position
        self.current_position += num_words
        
        print(f"Position after advance: {self.current_position}")
        
        # Don't go past end of story
        total_words = len(self.story_text.split())
        if self.current_position >= total_words:
            print(f"Hit end of story! Position {self.current_position} >= {total_words}")
            self.current_position = total_words
            return "END_OF_STORY"
        
        print("Getting current chunk...")
        return self.get_current_chunk()
    
    def get_current_chunk(self, num_words: int = 1000) -> str:
        """Get current story chunk."""
        words = self.story_text.split()
        start_word = self.current_position
        end_word = min(start_word + num_words, len(words))
        
        print(f"Getting chunk from word {start_word} to {end_word}")
        
        return " ".join(words[start_word:end_word])

# Test
story_state = StoryState()
story_name = config["story"]["current_story"]

print(f"Loading story: {story_name}")
success = story_state.load_story(story_name)
print(f"Load success: {success}")

if success:
    print(f"\nStory loaded: {len(story_state.story_text)} chars")
    print(f"First 100 chars: {story_state.story_text[:100]}")
    
    print(f"\nTesting advance with default chunk_size: {config['story']['chunk_size']}")
    result = story_state.advance_story(config["story"]["chunk_size"])
    print(f"Result: {result[:100]}...")