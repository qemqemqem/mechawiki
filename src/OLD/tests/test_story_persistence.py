#!/usr/bin/env python3
"""Test story state persistence across MCP server calls."""

import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient

async def test_story_persistence():
    """Test if story state persists across multiple tool calls."""
    print("🔍 Testing story state persistence...")
    
    # Setup MCP client
    mcp_client = MultiServerMCPClient({
        "wiki_tools": {
            "command": ".venv/bin/python",
            "args": ["src/tools.py"],
            "transport": "stdio"
        }
    })
    
    tools = await mcp_client.get_tools()
    advance_tool = next(t for t in tools if t.name == "advance")
    
    print("\n🚀 Call 1: advance(100)")
    result1 = await advance_tool.ainvoke({"num_words": 100})
    print(f"Result 1: {result1[:100]}...")
    
    print("\n🚀 Call 2: advance(100) - should continue from word 100")
    result2 = await advance_tool.ainvoke({"num_words": 100}) 
    print(f"Result 2: {result2[:100]}...")
    
    print("\n🚀 Call 3: advance(100) - should continue from word 200")
    result3 = await advance_tool.ainvoke({"num_words": 100})
    print(f"Result 3: {result3[:100]}...")
    
    # Check if positions are advancing
    if "word 100" in result1 and "word 200" in result2 and "word 300" in result3:
        print("\n✅ Story state persists - positions are advancing correctly")
        return True
    elif "word 100" in result1 and "word 100" in result2 and "word 100" in result3:
        print("\n❌ Story state NOT persisting - each call resets to same position")
        return False
    else:
        print("\n⚠️ Unclear results - positions may have other issues")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_story_persistence())
    print(f"\nPersistence test: {'PASS' if success else 'FAIL'}")