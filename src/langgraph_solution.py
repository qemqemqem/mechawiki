#!/usr/bin/env python3
"""LangGraph-native solution for WikiAgent with proper state management."""

from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_anthropic import ChatAnthropic
import toml
from pathlib import Path
import re

# Load config
config = toml.load("config.toml")

class WikiAgentState(TypedDict):
    """Shared state that persists across all graph nodes."""
    messages: List[Dict[str, Any]]  # Chat history
    story_position: int  # Current reading position in story
    story_text: str  # Full story content (loaded once)
    story_length: int  # Total words in story
    linked_articles: List[Dict[str, str]]  # Articles in context
    current_chunk: str  # Most recent story chunk
    articles_created: int  # Track progress
    images_created: int  # Track progress
    completed: bool  # Whether processing is done

def load_story_node(state: WikiAgentState) -> WikiAgentState:
    """Load the story text into state (runs once)."""
    if state.get("story_text"):
        return state  # Already loaded
    
    story_name = config["story"]["current_story"]
    story_path = Path(config["paths"]["content_dir"]) / story_name / f"{story_name}.txt"
    
    if story_path.exists():
        with open(story_path, 'r', encoding='utf-8') as f:
            story_text = f.read() + "\n\nEND_OF_STORY"
        
        state["story_text"] = story_text
        state["story_length"] = len(story_text.split())
        state["story_position"] = 0
        print(f"📚 Loaded story: {story_name} ({state['story_length']} words)")
    else:
        state["story_text"] = ""
        state["story_length"] = 0
        print(f"❌ Failed to load story: {story_name}")
    
    return state

def advance_story_node(state: WikiAgentState) -> WikiAgentState:
    """Advance through the story and update current chunk."""
    if not state.get("story_text"):
        return state
    
    # Get advance amount (default or from LLM request)
    num_words = config["story"]["chunk_size"]  # Could be dynamic
    
    # Calculate new position
    old_position = state.get("story_position", 0)
    new_position = old_position + num_words
    
    # Get chunk from old position
    words = state["story_text"].split()
    start_word = old_position
    end_word = min(start_word + num_words, len(words))
    
    chunk = " ".join(words[start_word:end_word])
    
    # Update state
    state["story_position"] = min(new_position, len(words))
    state["current_chunk"] = chunk
    
    # Check if complete
    if state["story_position"] >= len(words):
        state["completed"] = True
    
    print(f"📍 Advanced to position {state['story_position']}/{len(words)}")
    return state

def create_article_node(state: WikiAgentState) -> WikiAgentState:
    """Create wiki article and update articles context."""
    # This would be called by LLM with specific article data
    # For now, just increment counter
    state["articles_created"] = state.get("articles_created", 0) + 1
    return state

def llm_reasoning_node(state: WikiAgentState) -> WikiAgentState:
    """LLM analyzes current chunk and decides what to do."""
    llm = ChatAnthropic(
        model=config["agent"]["model"],
        temperature=config["agent"]["temperature"]
    )
    
    # Create context-aware prompt
    chunk = state.get("current_chunk", "")
    position = state.get("story_position", 0)
    total = state.get("story_length", 0)
    
    if not chunk:
        state["messages"].append({"role": "assistant", "content": "No story content available."})
        return state
    
    # Build prompt with current context
    system_prompt = f"""You are processing a story. Current position: {position}/{total} words.

Current text chunk:
{chunk}

Based on this content, you should:
1. Identify notable elements (characters, locations, objects, events)
2. Decide whether to create articles, advance the story, or complete

Respond with your analysis and next action."""

    # Get LLM response
    try:
        response = llm.invoke([{"role": "user", "content": system_prompt}])
        state["messages"].append({
            "role": "assistant", 
            "content": response.content
        })
    except Exception as e:
        state["messages"].append({
            "role": "assistant",
            "content": f"Error in LLM reasoning: {e}"
        })
    
    return state

def should_continue(state: WikiAgentState) -> str:
    """Determine next action based on state."""
    if state.get("completed", False):
        return END
    
    if not state.get("current_chunk"):
        return "advance_story"
    
    # Simple logic - could be more sophisticated
    articles_count = state.get("articles_created", 0)
    if articles_count < 5:  # Create more articles
        return "create_article"
    else:  # Continue reading
        return "advance_story"

def create_wiki_agent_graph() -> StateGraph:
    """Create the LangGraph state graph for WikiAgent."""
    
    # Initialize graph with state schema
    graph = StateGraph(WikiAgentState)
    
    # Add nodes
    graph.add_node("load_story", load_story_node)
    graph.add_node("advance_story", advance_story_node)
    graph.add_node("create_article", create_article_node)
    graph.add_node("llm_reasoning", llm_reasoning_node)
    
    # Define flow
    graph.set_entry_point("load_story")
    graph.add_edge("load_story", "advance_story")
    graph.add_edge("advance_story", "llm_reasoning")
    graph.add_conditional_edges(
        "llm_reasoning",
        should_continue,
        {
            "advance_story": "advance_story",
            "create_article": "create_article",
            END: END
        }
    )
    graph.add_edge("create_article", "llm_reasoning")
    
    return graph

async def main():
    """Run the LangGraph WikiAgent with proper state management."""
    print("🚀 LangGraph WikiAgent with State Management")
    
    # Create graph
    graph = create_wiki_agent_graph()
    
    # Use memory checkpointer (could be persistent in production)
    checkpointer = MemorySaver()
    
    # Compile with checkpointer
    app = graph.compile(checkpointer=checkpointer)
    
    # Initialize state
    initial_state = {
        "messages": [],
        "story_position": 0,
        "story_text": "",
        "story_length": 0,
        "linked_articles": [],
        "current_chunk": "",
        "articles_created": 0,
        "images_created": 0,
        "completed": False
    }
    
    # Run the graph
    config_dict = {"configurable": {"thread_id": "wiki_session"}}
    
    try:
        result = await app.ainvoke(initial_state, config_dict)
        print(f"\n✅ WikiAgent completed!")
        print(f"📊 Final state:")
        print(f"  • Story position: {result.get('story_position', 0)}/{result.get('story_length', 0)}")
        print(f"  • Articles created: {result.get('articles_created', 0)}")
        print(f"  • Completed: {result.get('completed', False)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())