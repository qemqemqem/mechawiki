#!/usr/bin/env python3
"""Test script to debug MCP tools."""

import asyncio
import sys
from langchain_mcp_adapters.client import MultiServerMCPClient

async def test_mcp_tools():
    """Test MCP tools to debug issues."""
    print("🔧 Testing MCP tools...")
    
    try:
        # Setup MCP client
        mcp_client = MultiServerMCPClient({
            "wiki_tools": {
                "command": ".venv/bin/python",
                "args": ["src/tools.py"],
                "transport": "stdio"
            }
        })
        
        print("📦 Getting tools from MCP server...")
        tools = await mcp_client.get_tools()
        
        print(f"✅ Found {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description[:60]}...")
        
        # Test advance tool
        print("\n🚀 Testing advance() tool...")
        for tool in tools:
            if tool.name == "advance":
                try:
                    result = await tool.ainvoke({"num_words": 100})
                    print(f"✅ advance() result: {result[:200]}...")
                    break
                except Exception as e:
                    print(f"❌ advance() failed: {e}")
                    # Let's see the full error
                    import traceback
                    traceback.print_exc()
        
        print("\n🧪 Test complete!")
        
    except Exception as e:
        print(f"❌ Error testing tools: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean shutdown
        try:
            await mcp_client.close()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(test_mcp_tools())