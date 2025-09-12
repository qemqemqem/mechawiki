#!/usr/bin/env python3
"""Test script to debug LangGraph agent tool usage."""

import asyncio
import toml
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain_anthropic import ChatAnthropic

async def test_agent():
    """Test the LangGraph agent with tools."""
    print("🤖 Testing LangGraph ReAct agent...")
    
    try:
        # Load config
        config = toml.load("config.toml")
        
        # Setup LLM
        llm = ChatAnthropic(
            model=config["agent"]["model"],
            temperature=config["agent"]["temperature"]
        )
        
        # Setup MCP client
        mcp_client = MultiServerMCPClient({
            "wiki_tools": {
                "command": ".venv/bin/python",
                "args": ["src/tools.py"],
                "transport": "stdio"
            }
        })
        
        # Get tools
        tools = await mcp_client.get_tools()
        print(f"✅ Loaded {len(tools)} tools")
        
        # Create agent
        checkpointer = InMemorySaver()
        agent = create_react_agent(
            model=llm,
            tools=tools,
            checkpointer=checkpointer
        )
        
        # Test with simple prompt
        print("🚀 Testing tool invocation...")
        response = agent.invoke(
            {"messages": [{"role": "user", "content": "Call the advance() function to get the first chunk of the story."}]},
            {"configurable": {"thread_id": "test"}}
        )
        
        print("✅ Agent response:")
        print(f"Final message: {response['messages'][-1].content}")
        
        # Print all messages to see the tool calls
        print("\n📝 All messages:")
        for i, msg in enumerate(response['messages']):
            print(f"{i+1}. {msg.__class__.__name__}: {str(msg)[:100]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        try:
            await mcp_client.close()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(test_agent())