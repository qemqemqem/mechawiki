"""Test ReaderAgent with automatic tool descriptions."""
import sys
sys.path.append('src')

from ais.reader_agent import ReaderAgent

def test_reader_with_auto_tools():
    """Test that ReaderAgent works with auto-generated tool descriptions."""
    print("🧪 Testing ReaderAgent with auto-generated tool descriptions...")
    
    # Create the reader agent
    agent = ReaderAgent(stream=True)
    
    # Run a short reading session
    result = agent.run_forever(
        "Start reading and create an image if you find something interesting.",
        max_turns=2
    )
    
    print(f"\n--- Session Result ---")
    print(result)

if __name__ == "__main__":
    test_reader_with_auto_tools()