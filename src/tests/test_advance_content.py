"""Test script to demonstrate advance_content archiving behavior."""
import sys
sys.path.append('src')

from agent.base_agent import BaseAgent

def test_advance_content_archiving():
    """Test that advance_content properly archives old content blocks."""
    
    agent = BaseAgent()
    
    print("=== Testing advance_content archiving behavior ===\n")
    
    # Add first content block
    agent.advance_content("First story chunk goes here...", 0)
    print(f"After 1st advance_content call:")
    print(f"Total messages: {len(agent.messages)}")
    for i, msg in enumerate(agent.messages):
        if msg.get('_advance_content'):
            print(f"  Message {i}: advance content at word {msg.get('_start_word')}")
            print(f"    Content preview: {msg['content'][:50]}...")
    
    print()
    
    # Add second content block
    agent.advance_content("Second story chunk goes here...", 1000)
    print(f"After 2nd advance_content call:")
    print(f"Total messages: {len(agent.messages)}")
    for i, msg in enumerate(agent.messages):
        if msg.get('_advance_content'):
            print(f"  Message {i}: advance content at word {msg.get('_start_word')}")
            print(f"    Content preview: {msg['content'][:50]}...")
    
    print()
    
    # Add third content block (should archive the first one)
    agent.advance_content("Third story chunk goes here...", 2000)
    print(f"After 3rd advance_content call (should archive first):")
    print(f"Total messages: {len(agent.messages)}")
    for i, msg in enumerate(agent.messages):
        if msg.get('_advance_content'):
            print(f"  Message {i}: advance content at word {msg.get('_start_word')}")
            archived = "[Content removed" in msg['content']
            status = "ARCHIVED" if archived else "ACTIVE"
            print(f"    Status: {status}")
            print(f"    Content preview: {msg['content'][:50]}...")
    
    print()
    
    # Add fourth content block (should archive the second one)
    agent.advance_content("Fourth story chunk goes here...", 3000)
    print(f"After 4th advance_content call (should archive second):")
    print(f"Total messages: {len(agent.messages)}")
    for i, msg in enumerate(agent.messages):
        if msg.get('_advance_content'):
            print(f"  Message {i}: advance content at word {msg.get('_start_word')}")
            archived = "[Content removed" in msg['content']
            status = "ARCHIVED" if archived else "ACTIVE"
            print(f"    Status: {status}")
            print(f"    Content preview: {msg['content'][:50]}...")

if __name__ == "__main__":
    test_advance_content_archiving()