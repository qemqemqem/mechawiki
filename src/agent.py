"""LangGraph agent for wiki generation."""
import toml
from typing import Dict, Any, Optional
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain_mcp_adapters.client import MCPClient
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

# Load config
config = toml.load("config.toml")

class WikiAgent:
    def __init__(self) -> None:
        self.config: Dict[str, Any] = config
        self.agent: Optional[Any] = None
        self.checkpointer: InMemorySaver = InMemorySaver()
        self._setup_agent()
    
    def _setup_agent(self) -> None:
        """Initialize the LangGraph agent with MCP tools."""
        
        # Setup LLM based on configured provider
        llm = self._create_llm()
        
        # Setup MCP client for tools
        mcp_client = MCPClient({
            "wiki_tools": {
                "command": "python",
                "args": ["src/tools.py"],
                "transport": "stdio"
            }
        })
        
        # Get tools from MCP server
        tools = mcp_client.get_tools()
        
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
- edit_article(title, search_text, replace_text): Edit existing articles

GUIDELINES:
- Follow specialized wiki standards (like fandom wikis) - be comprehensive
- Create articles for ANY named element or significant concept
- Use markdown linking: [Character Name](./character-name.md) 
- Include detailed descriptions, story context, and cross-references
- Update articles as you learn more about characters/locations
- Take your time - thorough documentation is the goal
- Don't advance too quickly - ensure you've captured all notable elements

Start by advancing to get the first chunk of the story, then begin creating articles for everything noteworthy you encounter."""

    def run_session(self, session_id: str = "main"):
        """Run an interactive wiki generation session."""
        config_dict = {"configurable": {"thread_id": session_id}}
        
        print(">�B WikiAgent starting session...")
        print(f"=� Processing: {self.config['story']['current_story']}")
        print("=� Type your instructions or 'quit' to exit\n")
        
        while True:
            user_input = input("\n=d You: ")
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("=� Wiki session ended.")
                break
            
            try:
                # Send message to agent
                response = self.agent.invoke(
                    {"messages": [{"role": "user", "content": user_input}]},
                    config_dict
                )
                
                # Display agent's response
                agent_message = response["messages"][-1]["content"]
                print(f"\n> WikiAgent: {agent_message}")
                
            except Exception as e:
                print(f"L Error: {str(e)}")
    
    def process_story_automatically(self, session_id: str = "auto"):
        """Automatically process the entire story and generate wiki."""
        config_dict = {"configurable": {"thread_id": session_id}}
        
        print(">�B WikiAgent starting automatic processing...")
        print(f"=� Processing: {self.config['story']['current_story']}")
        
        initial_prompt = """Begin reading and documenting the story. Start by advancing to get the first chunk, then systematically create wiki articles for every notable element you encounter. Continue until you've processed the entire story."""
        
        try:
            response = self.agent.invoke(
                {"messages": [{"role": "user", "content": initial_prompt}]},
                config_dict
            )
            
            agent_message = response["messages"][-1]["content"]
            print(f"\n> WikiAgent: {agent_message}")
            
        except Exception as e:
            print(f"L Error: {str(e)}")

if __name__ == "__main__":
    agent = WikiAgent()
    agent.run_session()