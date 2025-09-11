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
        """Initialize the LangGraph agent with MCP tools."""
        
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
        tools = await mcp_client.get_tools()
        
        # Create system prompt
        system_prompt = self._create_system_prompt()
        
        # Create ReAct agent with tools and memory
        self.agent = create_react_agent(
            model=llm,
            tools=tools,
            state_schema=WikiAgentState,
            checkpointer=self.checkpointer,
            prompt=system_prompt
        )
        
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
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for the wiki agent."""
        return f"""You are a specialized wiki writer agent reading through "{self.config['story']['current_story']}" and creating comprehensive wiki-style documentation.

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
    
    async def process_story(self, session_id: str = "auto", user_message: str = None) -> None:
        """Process the entire story and generate wiki automatically."""
        config_dict: Dict[str, Any] = {"configurable": {"thread_id": session_id}}
        
        print("🧙‍♂️ WikiAgent starting processing...")
        print(f"📖 Processing: {self.config['story']['current_story']}")
        if user_message:
            print(f"💬 User message: {user_message}")
        print("🚀 Running in automatic mode...")
        
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

        if user_message:
            base_prompt += f"""

🚨 SPECIAL REQUEST FROM USER - PLEASE PAY ATTENTION: {user_message}

This is a specific instruction from the user about how to approach this wiki creation task. Make sure to keep this request in mind throughout the entire process."""

        initial_prompt: str = base_prompt
        
        try:
            # Initialize state with empty story_info and linked_articles
            initial_state = {
                "messages": [{"role": "user", "content": initial_prompt}],
                "remaining_steps": 25,  # Default for create_react_agent
                "story_info": {},  # Will be populated by advance() tool
                "linked_articles": []
            }
            
            response = await self.agent.ainvoke(initial_state, config_dict)
            
            agent_message: str = response["messages"][-1].content
            print(f"\n🤖 WikiAgent: {agent_message}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    agent = WikiAgent()
    agent.process_story()