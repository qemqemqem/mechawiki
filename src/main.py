"""Main entry point for the WikiAgent system."""
import argparse
from typing import Any
from agent import WikiAgent

def main() -> None:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(description="WikiAgent - Generate wikis from stories")
    parser.add_argument(
        "--mode", 
        choices=["interactive", "auto"], 
        default="interactive",
        help="Run mode: interactive chat or automatic processing"
    )
    parser.add_argument(
        "--session-id",
        default="main", 
        help="Session ID for memory persistence"
    )
    
    args: Any = parser.parse_args()
    
    # Initialize agent
    agent: WikiAgent = WikiAgent()
    
    # Run based on mode
    if args.mode == "interactive":
        agent.run_session(args.session_id)
    else:
        agent.process_story_automatically(args.session_id)

if __name__ == "__main__":
    main()