"""LangGraph agent for wiki generation."""
import toml
from typing import Dict, Any, Optional, List, TypedDict, Annotated
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import add_messages
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

# Load config
config = toml.load("config.toml")

# Define the WikiAgent state schema (must match tools.py)
class WikiAgentState(TypedDict):
    """State schema for WikiAgent - contains persistent story state"""
    messages: Annotated[list, add_messages]
    remaining_steps: int  # Required by create_react_agent
    story_info: Dict[str, Any]  # Contains position, text, complete status
    linked_articles: List[Dict[str, str]]

class WikiAgent:
    def __init__(self) -> None:
        self.config: Dict[str, Any] = config
        self.agent: Optional[Any] = None
        self.checkpointer: InMemorySaver = InMemorySaver()
    
    async def initialize(self) -> None:
        """Initialize the agent asynchronously."""
        await self._setup_agent()
    
    async def _setup_agent(self) -> None:
        """Initialize the LangGraph agent with MCP tools and custom state injection."""
        
        # Setup LLM based on configured provider
        llm = self._create_llm()
        
        # Setup MCP client for tools with environment variables
        import os
        mcp_client = MultiServerMCPClient({
            "wiki_tools": {
                "command": ".venv/bin/python",
                "args": ["src/tools.py"],
                "transport": "stdio",
                "env": {
                    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
                    "PATH": os.getenv("PATH", ""),
                    # Inherit other important environment variables
                    "PYTHONPATH": os.getenv("PYTHONPATH", ""),
                }
            }
        })
        
        # Get tools from MCP server
        mcp_tools = await mcp_client.get_tools()
        self.mcp_tools = mcp_tools
        
        # Create system prompt
        system_prompt = self._create_system_prompt()
        
        # Create custom graph with state injection (like our test)
        self.agent = self._create_custom_agent(llm, mcp_tools, system_prompt)
        
    def _create_llm(self) -> Any:
        """Create LLM instance based on configured provider."""
        provider: str = self.config["agent"]["llm_provider"].lower()
        model: str = self.config["agent"]["model"]
        temperature: float = self.config["agent"]["temperature"]
        
        if provider == "anthropic":
            return ChatAnthropic(
                model=model,
                temperature=temperature
            )
        elif provider == "openai":
            return ChatOpenAI(
                model=model,
                temperature=temperature
            )
        elif provider == "together":
            # Using OpenAI-compatible interface
            return ChatOpenAI(
                model=model,
                temperature=temperature,
                base_url="https://api.together.xyz/v1"
            )
        elif provider == "replicate":
            raise NotImplementedError("Replicate LLM support not yet implemented")
        else:
            raise ValueError(
                f"Unsupported LLM provider: {provider}. "
                f"Supported: anthropic, openai, together, replicate"
            )
    
    def _create_system_prompt(self, user_message: Optional[str] = None) -> str:
        """Create the system prompt for the wiki agent.

        If provided, user_message is included as prioritized special instructions
        that the agent should follow throughout the entire session.
        """
        base = f"""You are a specialized wiki writer agent reading through "{self.config['story']['current_story']}" and creating comprehensive wiki-style documentation.

Your task is to read through the story section by section and create detailed wiki articles about:
- Characters (major and minor)
- Locations (cities, buildings, landmarks) 
- Objects and artifacts
- Events and concepts
- Anything notable that would merit a wiki page

TOOLS AVAILABLE:
- advance(num_words): Move forward/backward in the story (-2000 to +2000 words)
- add_article(title, content): Create a new wiki article in markdown
- edit_article(title, edit_block): Edit existing articles using Aider-style search/replace
- create_image(art_prompt): Generate artwork for articles

GUIDELINES:
- Follow specialized wiki standards (like fandom wikis) - be comprehensive
- Create articles for ANY named element or significant concept
- Use markdown linking: [Character Name](./character-name.md) 
- Include detailed descriptions, story context, and cross-references
- Update articles as you learn more about characters/locations
- Take your time - thorough documentation is the goal
- Don't advance too quickly - ensure you've captured all notable elements"""
        
        if user_message:
            base += f"""

SPECIAL INSTRUCTIONS (PRIORITIZE THESE):
- The user requests: {user_message}
- Treat these as high-priority constraints/preferences across all steps.
- If ambiguous or conflicting, ask clarifying questions before proceeding.
- Prefer these instructions over defaults where conflicts arise."""

        return base
    
    def _create_custom_agent(self, llm: Any, tools: List[Any], system_prompt: str) -> Any:
        """Create a custom StateGraph agent with proper state injection (based on our test)."""
        from langgraph.graph import StateGraph, END
        from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
        from langchain_core.runnables import RunnableConfig
        import json
        import sys
        sys.path.append('src')
        from tools import _advance_impl
        
        # Bind tools to LLM
        llm_with_tools = llm.bind_tools(tools)
        
        # Limit how many past messages are sent to the LLM each turn
        message_window: int = int(self.config.get("agent", {}).get("message_window", 12))
        
        def call_model(state: WikiAgentState, config: RunnableConfig):
            """Call the LLM."""
            history = state["messages"]
            # Step budget guard: stop gracefully if out of steps
            remaining = state.get("remaining_steps", 1_000_000)
            if remaining <= 0:
                return {
                    "messages": [AIMessage(content="Stopping: step budget exhausted (remaining_steps=0).")],
                    "remaining_steps": 0
                }
            # Always include system prompt for the model input and window the history
            system_message = AIMessage(content=system_prompt)
            trimmed_history = history[-message_window:] if message_window > 0 else history
            llm_messages = [system_message] + trimmed_history
            # Log prompt size being sent to the LLM
            def _msg_len(m):
                try:
                    c = getattr(m, "content", "")
                    if isinstance(c, str):
                        return len(c)
                    if isinstance(c, list):
                        total = 0
                        for part in c:
                            if isinstance(part, dict) and "text" in part:
                                total += len(str(part.get("text", "")))
                            else:
                                total += len(str(part))
                        return total
                    return len(str(c))
                except Exception:
                    return 0
            total_chars = sum(_msg_len(m) for m in llm_messages)
            approx_tokens = max(1, total_chars // 4)  # rough heuristic
            from collections import Counter
            type_counts = Counter(type(m).__name__ for m in llm_messages)
            print(
                f"🧠 LLM call -> msgs:{len(llm_messages)} chars:{total_chars} ~tokens:{approx_tokens} window:{message_window} types:{dict(type_counts)}",
                file=sys.stderr,
                flush=True,
            )
            
            response = llm_with_tools.invoke(llm_messages, config=config)
            # Decrement step budget after a model turn
            return {"messages": [response], "remaining_steps": max(0, remaining - 1)}
        
        def should_continue(state: WikiAgentState):
            """Check if we should continue or call tools."""
            # Stop if out of steps
            if state.get("remaining_steps", 1) <= 0:
                return END
            last_message = state["messages"][-1]
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                return "tools"
            return END
        
        async def call_tools(state: WikiAgentState, config: RunnableConfig):
            """Custom tool node that properly handles MCP tools with state injection."""
            last_message = state["messages"][-1]
            tool_messages = []
            state_updates = {}
            
            print(f"🔧 Custom tool node called with {len(last_message.tool_calls)} tool calls")
            
            for tool_call in last_message.tool_calls:
                tool_name = tool_call["name"]
                print(f"🔧 Processing tool call: {tool_name}")
                
                if tool_name == "advance":
                    # INJECT POSITION FROM STATE - this is our proven working solution
                    args = tool_call["args"].copy()
                    current_position = state.get("story_info", {}).get("position", 0)
                    
                    print(f"🔧 Injecting position {current_position} into advance call")
                    
                    # Call the internal implementation directly with injected position
                    result = _advance_impl(
                        num_words=args.get("num_words"),
                        current_position=current_position
                    )
                    
                    # Extract data for state update
                    content = result.get("content", str(result))
                    new_position = result.get("position", current_position) 
                    story_info = result.get("story_info", {"position": new_position})
                    
                    # Update state with new story info
                    state_updates["story_info"] = story_info
                    print(f"🔧 Updating story position: {current_position} -> {new_position}")
                    
                    tool_messages.append(ToolMessage(
                        content=content,
                        tool_call_id=tool_call["id"]
                    ))
                else:
                    # Other tools - handle normally through MCP
                    tool = next((t for t in tools if t.name == tool_name), None)
                    if tool:
                        result = await tool.ainvoke(tool_call["args"], config=config)
                        tool_messages.append(ToolMessage(
                            content=str(result),
                            tool_call_id=tool_call["id"]
                        ))
                    else:
                        tool_messages.append(ToolMessage(
                            content=f"Error: Tool {tool_name} not found",
                            tool_call_id=tool_call["id"]
                        ))
            
            print(f"🔧 Final state updates: {state_updates}")
            return {"messages": tool_messages, **state_updates}
        
        # Build the graph  
        workflow = StateGraph(WikiAgentState)
        workflow.add_node("agent", call_model)
        workflow.add_node("tools", call_tools)
        
        workflow.set_entry_point("agent")
        workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
        workflow.add_edge("tools", "agent")
        
        # Compile with checkpointer
        return workflow.compile(checkpointer=self.checkpointer)
    
    def _scan_existing_articles(self) -> List[Dict[str, str]]:
        """Scan for existing articles and return them as a list."""
        from pathlib import Path
        import re
        
        story_name = self.config["story"]["current_story"]
        articles_dir = Path(self.config["paths"]["content_dir"]) / story_name / self.config["paths"]["articles_dir"]
        
        existing_articles = []
        
        if articles_dir.exists():
            for article_file in articles_dir.glob("*.md"):
                # Extract slug from filename
                slug = article_file.stem
                
                # Try to extract title from file content
                try:
                    with open(article_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Look for markdown title (# Title)
                        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                        if title_match:
                            title = title_match.group(1).strip()
                        else:
                            # Fallback to slug converted to title
                            title = slug.replace('-', ' ').title()
                except Exception:
                    # Fallback to slug converted to title
                    title = slug.replace('-', ' ').title()
                
                existing_articles.append({
                    'title': title,
                    'slug': slug, 
                    'path': str(article_file)
                })
        
        # Sort by title for consistent ordering
        return sorted(existing_articles, key=lambda x: x['title'])
    
    async def process_story(self, session_id: str = "auto", user_message: str = None) -> None:
        """Process the entire story and generate wiki automatically."""
        config_dict: Dict[str, Any] = {
            "configurable": {"thread_id": session_id},
            # Very high cap to support long-running tool loops
            "recursion_limit": 1_000_000,
        }
        
        print("🧙‍♂️ WikiAgent starting processing...")
        print(f"📖 Processing: {self.config['story']['current_story']}")
        if user_message:
            print(f"💬 User message: {user_message}")
        print("🚀 Running in automatic mode...")
        
        # Ensure tools/agent are ready; rebuild agent with embedded user instructions if provided
        if not getattr(self, "mcp_tools", None) or not getattr(self, "agent", None):
            await self._setup_agent()
        if user_message:
            llm = self._create_llm()
            system_prompt = self._create_system_prompt(user_message=user_message)
            self.agent = self._create_custom_agent(llm, self.mcp_tools, system_prompt)
        
        # Build initial prompt with optional user message
        base_prompt = """You are a wiki creation agent. You MUST use the provided tools to process the story. The story "Tales of Wonder" is already loaded.

Available tools (you MUST use these):
- advance(num_words) - Move through the story (starts at beginning)
- add_article(title, content) - Create comprehensive wiki pages
- edit_article(title, edit_block) - Update existing wiki pages
- create_image(art_prompt) - Generate artwork for characters, locations, and scenes
- exit_when_complete() - Call when finished

IMPORTANT: Create images for major story elements! Use create_image() to generate artwork for:
- Main characters (portraits, action scenes)  
- Important locations (landscapes, buildings)
- Key objects (magical items, weapons)
- Dramatic scenes (battles, important events)"""

        # User instructions are embedded in the system prompt already

        # Scan for existing articles and add to prompt
        existing_articles = self._scan_existing_articles()
        if existing_articles:
            base_prompt += f"""

📚 EXISTING ARTICLES IN CONTEXT: {len(existing_articles)} articles are already loaded into your context:"""
            for article in existing_articles:
                base_prompt += f"\n  • {article['title']} ({article['slug']}.md)"
            base_prompt += """

You can reference and edit these existing articles as needed. They contain information that may be relevant to new content you encounter in the story."""
        
        base_prompt += """

Start by calling advance() to begin reading the story from the beginning."""

        initial_prompt: str = base_prompt
        
        try:
            # Print existing articles info (already scanned above)
            if existing_articles:
                print(f"📚 Found {len(existing_articles)} existing articles - loading some of them into context")
                # for article in existing_articles:
                #     print(f"  • {article['title']} ({article['slug']}.md)")
            
            # Initialize state with pre-loaded articles
            max_steps = int(self.config.get("agent", {}).get("max_steps", 1_000_000))
            initial_state = {
                "messages": [{"role": "user", "content": initial_prompt}],
                "remaining_steps": max_steps,
                "story_info": {},  # Will be populated by advance() tool
                "linked_articles": existing_articles[:10]
            }
            
            response = await self.agent.ainvoke(initial_state, config_dict)
            
            agent_message: str = response["messages"][-1].content
            print(f"\n🤖 WikiAgent: {agent_message}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    agent = WikiAgent()
    agent.process_story()
