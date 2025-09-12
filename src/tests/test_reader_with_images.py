"""Test ReaderAgent with create_image tool."""
import sys
sys.path.append('src')

from ais.reader_agent import ReaderAgent

def test_reader_with_images():
    """Test that ReaderAgent can use create_image tool."""
    print("🧪 Testing ReaderAgent with create_image tool...")
    
    # Create the reader agent
    agent = ReaderAgent(stream=True)
    
    # Run a reading session that might use create_image
    result = agent.run_forever(
        "Read the first section and then create an image for an interesting character or scene you encounter.",
        max_turns=4
    )
    
    print(f"\n--- Session Result ---")
    print(result)

if __name__ == "__main__":
    test_reader_with_images()