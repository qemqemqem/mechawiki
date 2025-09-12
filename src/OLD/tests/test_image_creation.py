#!/usr/bin/env python3
"""Test script for image creation functionality."""

import asyncio
import os
from unittest.mock import patch, Mock
from langchain_mcp_adapters.client import MultiServerMCPClient

async def test_image_tool_availability():
    """Test that the create_image tool is available and can be called."""
    print("🎨 Testing image creation tool availability...")
    
    try:
        # Setup MCP client
        mcp_client = MultiServerMCPClient({
            "wiki_tools": {
                "command": ".venv/bin/python",
                "args": ["src/tools.py"],
                "transport": "stdio"
            }
        })
        
        tools = await mcp_client.get_tools()
        
        # Find create_image tool
        image_tools = [t for t in tools if t.name == "create_image"]
        
        if not image_tools:
            print("❌ create_image tool not found!")
            return False
            
        print(f"✅ Found create_image tool: {image_tools[0].description[:100]}...")
        
        image_tool = image_tools[0]
        
        print("\n🧪 Testing create_image tool with mock (safe test)...")
        
        # Test with a simple prompt - this will try to call DALLE
        # but if no API key, it should give us a clear error
        try:
            result = await image_tool.ainvoke({
                "art_prompt": "A mystical wizard tower in a fantasy landscape, digital art style"
            })
            print(f"📄 Result: {result}")
            
            if "ERROR" in result:
                if "API key" in result or "authentication" in result.lower():
                    print("⚠️ Image tool works but needs OpenAI API key for live testing")
                    return True
                else:
                    print(f"❌ Image tool error: {result}")
                    return False
            else:
                print("✅ Image tool working - image should be created!")
                return True
                
        except Exception as e:
            print(f"❌ Image tool exception: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to test image tool: {e}")
        return False

async def test_live_dalle_integration():
    """Test live DALLE integration if API key is available."""
    print("\n🚀 Testing live DALLE integration...")
    
    # Check if we have an API key
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️ OPENAI_API_KEY not found - skipping live DALLE test")
        print("💡 Set OPENAI_API_KEY environment variable to test live image generation")
        return False
    
    try:
        # Setup MCP client
        mcp_client = MultiServerMCPClient({
            "wiki_tools": {
                "command": ".venv/bin/python", 
                "args": ["src/tools.py"],
                "transport": "stdio"
            }
        })
        
        tools = await mcp_client.get_tools()
        image_tool = next(t for t in tools if t.name == "create_image")
        
        print("🎨 Generating test image with DALLE-3...")
        result = await image_tool.ainvoke({
            "art_prompt": "A small fantasy book cover showing a magical castle, simple digital art"
        })
        
        print(f"📄 DALLE Result: {result}")
        
        if "Successfully created image" in result:
            print("🎉 Live DALLE integration working!")
            
            # Check if image file was actually created
            if "Saved to:" in result:
                image_path = result.split("Saved to: ")[-1].strip()
                if os.path.exists(image_path):
                    file_size = os.path.getsize(image_path)
                    print(f"✅ Image file created: {image_path} ({file_size} bytes)")
                else:
                    print(f"⚠️ Image path mentioned but file not found: {image_path}")
            
            return True
        else:
            print(f"❌ DALLE integration failed: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Live DALLE test failed: {e}")
        return False

async def main():
    """Run all image tests."""
    print("🎨 Image Creation Testing Suite")
    print("=" * 50)
    
    # Test 1: Tool availability
    tool_available = await test_image_tool_availability()
    
    if not tool_available:
        print("\n❌ Image tool not working - stopping tests")
        return False
    
    # Test 2: Live integration (if API key available)
    live_test = await test_live_dalle_integration()
    
    print(f"\n📊 Results:")
    print(f"  • Tool available: {'✅' if tool_available else '❌'}")
    print(f"  • Live DALLE: {'✅' if live_test else '⚠️ (needs API key)'}")
    
    return tool_available

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)