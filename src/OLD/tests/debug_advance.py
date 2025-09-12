#!/usr/bin/env python3
"""Debug script to test advance function directly with MCP."""

import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient

async def debug_advance():
    """Test advance function with debug output."""
    print("🔍 Starting advance() debug test...")
    
    try:
        # Setup MCP client
        mcp_client = MultiServerMCPClient({
            "wiki_tools": {
                "command": ".venv/bin/python",
                "args": ["src/tools.py"],
                "transport": "stdio"
            }
        })
        
        print("📦 Getting tools...")
        tools = await mcp_client.get_tools()
        
        # Find advance tool
        advance_tool = next(t for t in tools if t.name == "advance")
        
        print("🚀 Calling advance() with default parameters...")
        result = await advance_tool.ainvoke({})
        print(f"📄 Result: {result}")
        
        print("\n🚀 Calling advance() with 50 words...")
        result2 = await advance_tool.ainvoke({"num_words": 50})
        print(f"📄 Result: {result2}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_advance())