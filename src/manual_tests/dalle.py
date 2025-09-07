#!/usr/bin/env python3
"""Manual test script for DALL-E image generation API."""

import os
import requests
from openai import OpenAI
from pathlib import Path

def test_dalle_generation():
    """Test DALL-E image generation with a simple prompt."""
    
    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY environment variable not set")
        print("Set it with: export OPENAI_API_KEY='your-key-here'")
        return False
    
    print(f"🔑 API key found: {api_key[:8]}...{api_key[-4:]}")
    
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        
        # Test prompt: bird wizard
        prompt = "A wise owl wizard wearing a pointed hat and robes, holding a magical staff, perched on ancient spell books, fantasy art style"
        
        print(f"🎨 Generating image with prompt: {prompt}")
        print("⏳ This may take 10-30 seconds...")
        
        # Generate image
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )
        
        # Get image URL and download it
        image_url = response.data[0].url
        print(f"✅ Image generated successfully!")
        print(f"🔗 URL: {image_url}")
        
        # Download and save image
        print("📥 Downloading image...")
        image_response = requests.get(image_url)
        image_response.raise_for_status()
        
        # Save to src/manual_tests/dalle_image.png
        output_file = Path("src/manual_tests/dalle_image.png")
        with open(output_file, 'wb') as f:
            f.write(image_response.content)
        
        print(f"💾 Image saved to: {output_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error generating image: {e}")
        return False

if __name__ == "__main__":
    print("🧙‍♂️ DALL-E Bird Wizard Test")
    print("=" * 50)
    
    success = test_dalle_generation()
    
    if success:
        print("\n✅ DALL-E API test PASSED - Image generation working!")
    else:
        print("\n❌ DALL-E API test FAILED - Check API key and connection")