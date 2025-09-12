"""Test automatic tool description generation."""
import sys
sys.path.append('src')

from ais.reader_agent import ReaderAgent

def test_auto_tool_descriptions():
    """Test that BaseAgent automatically generates tool descriptions."""
    print("🧪 Testing automatic tool description generation...")
    
    # Create the reader agent
    agent = ReaderAgent(stream=False)
    
    print("Generated System Prompt:")
    print("=" * 60)
    print(agent.system_prompt)
    print("=" * 60)
    
    # Also test the tool description generation directly
    print("\nDirect tool descriptions:")
    print(agent._generate_tools_description())

if __name__ == "__main__":
    test_auto_tool_descriptions()