"""LangGraph agent for wiki generation."""
import toml
from typing import Dict, Any, Optional
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

# Load config
config = toml.load("config.toml")

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
        
        # Setup MCP client for tools
        mcp_client = MultiServerMCPClient({
            "wiki_tools": {
                "command": ".venv/bin/python",
                "args": ["src/tools.py"],
                "transport": "stdio"
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
- Don't advance too quickly - ensure you've captured all notable elements

Start by advancing to get the first chunk of the story, then begin creating articles for everything noteworthy you encounter."""
    
    async def process_story(self, session_id: str = "auto") -> None:
        """Process the entire story and generate wiki automatically."""
        config_dict: Dict[str, Any] = {"configurable": {"thread_id": session_id}}
        
        print("🧙‍♂️ WikiAgent starting processing...")
        print(f"📖 Processing: {self.config['story']['current_story']}")
        print("🚀 Running in automatic mode...")
        
        initial_prompt: str = """You are a wiki creation agent. You MUST use the provided tools to process the story. The story "Tales of Wonder" is already loaded.

CRITICAL: You MUST call the advance() function RIGHT NOW to begin reading the story. Do not explain or hesitate - just call advance() immediately.

Available tools (you MUST use these):
- advance(num_words) - Call this NOW to start reading
- add_article(title, content) - Create comprehensive wiki pages
- edit_article(title, edit_block) - Update existing wiki pages
- create_image(art_prompt) - Generate artwork for characters, locations, and scenes
- exit_when_complete() - Call when finished

IMPORTANT: Create images for major story elements! Use create_image() to generate artwork for:
- Main characters (portraits, action scenes)  
- Important locations (landscapes, buildings)
- Key objects (magical items, weapons)
- Dramatic scenes (battles, important events)

Your first action: Call advance() with num_words=1000 to get the first chunk of the story. Do this NOW."""
        
        try:
            response = await self.agent.ainvoke(
                {"messages": [{"role": "user", "content": initial_prompt}]},
                config_dict
            )
            
            agent_message: str = response["messages"][-1].content
            print(f"\n🤖 WikiAgent: {agent_message}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    agent = WikiAgent()
    agent.process_story()