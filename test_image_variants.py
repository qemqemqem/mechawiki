"""Test image creation with similar prompts to test unique filename generation."""
import sys
sys.path.append('src')

from tools.images import create_image

def test_image_variants():
    print("🧪 Testing image variants...")
    
    # Test 1: Slightly different prompt
    print("\n--- Test 1: Similar but different prompt ---")
    result1 = create_image("A majestic castle on a hill at dawn, fantasy art style", "landscape")
    print(result1)
    
    # Test 2: Different orientation 
    print("\n--- Test 2: Same prompt, different orientation ---")
    result2 = create_image("A majestic castle on a hill at sunset, fantasy art style", "portrait")
    print(result2)

if __name__ == "__main__":
    test_image_variants()