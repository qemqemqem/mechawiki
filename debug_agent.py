"""Debug script to understand conversation state issues."""
import sys
import os
import json

# Add src to path
sys.path.append('src')

from agent.base_agent import BaseAgent, HighlightContent

def debug_highlight():
    """Debug HighlightContent test."""
    
    agent = BaseAgent()
    
    # Add initial user message
    agent.add_user_message("Hello")
    print("After user message:")
    for i, msg in enumerate(agent.messages):
        print(f"  {i}: {msg}")
    
    # Test highlight_content
    agent.highlight_content("This is test content")
    print("\nAfter highlight_content:")
    for i, msg in enumerate(agent.messages):
        print(f"  {i}: {msg}")

if __name__ == "__main__":
    debug_highlight()