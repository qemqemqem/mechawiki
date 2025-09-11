"""Main entry point for the WikiAgent system."""
import argparse
import asyncio
from typing import Any
from agent import WikiAgent

async def main() -> None:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(description="WikiAgent - Generate wikis from stories")
    parser.add_argument(
        "--session-id",
        default="auto", 
        help="Session ID for memory persistence"
    )
    parser.add_argument(
        "message",
        nargs="?",
        help="Special instructions to include in LLM context (e.g., 'add more images')"
    )
    
    args: Any = parser.parse_args()
    
    # Initialize and run agent
    agent: WikiAgent = WikiAgent()
    await agent.initialize()
    await agent.process_story(args.session_id, args.message)

if __name__ == "__main__":
    asyncio.run(main())