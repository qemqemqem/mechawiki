"""Test ReaderAgent with updated create_image tool (with name parameter)."""
import sys
sys.path.append('src')

from ais.reader_agent import ReaderAgent

def test_reader_with_named_images():
    """Test that ReaderAgent can use create_image tool with name parameter."""
    print("🧪 Testing ReaderAgent with updated create_image tool...")
    
    # Create the reader agent
    agent = ReaderAgent(stream=True)
    
    # Run a reading session that uses create_image with name
    result = agent.run_forever(
        "Read the first section and create an image for an interesting character or scene, giving it a descriptive name like 'hasheesh-eater' or 'london-dream'.",
        max_turns=3
    )
    
    print(f"\n--- Session Result ---")
    print(result)

if __name__ == "__main__":
    test_reader_with_named_images()