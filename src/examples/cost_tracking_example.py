#!/usr/bin/env python3
"""
Example: Using Cost Tracking with BaseAgent

This example shows how to monitor LLM costs during agent execution.
Cost tracking is automatic - no setup required!
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.base_agent.base_agent import BaseAgent
import logging

# Enable info logging to see cost logs
logging.basicConfig(level=logging.INFO, format='%(message)s')

def main():
    print("=== Cost Tracking Example ===\n")
    
    # Create agent - cost tracking is automatic!
    agent = BaseAgent(
        model="claude-haiku-4-5-20251001",
        system_prompt="You are a helpful assistant.",
        stream=False  # Non-streaming for simpler example
    )
    
    print("Running agent with 3 turns...\n")
    
    # Run the agent
    for event in agent.run_forever(
        initial_message="Tell me a short joke about programming.", 
        max_turns=3
    ):
        if event['type'] == 'text_token':
            print(event['content'], end='', flush=True)
    
    print("\n\n=== Cost Statistics ===\n")
    
    # Get cost stats
    stats = agent.get_cost_stats()
    
    print(f"Total Cost:              ${stats['total_cost']:.6f}")
    print(f"Total Tokens:            {stats['total_tokens']:,}")
    print(f"  - Prompt Tokens:       {stats['total_prompt_tokens']:,}")
    print(f"  - Completion Tokens:   {stats['total_completion_tokens']:,}")
    print(f"Turn Count:              {stats['turn_count']}")
    print(f"Average Cost Per Turn:   ${stats['average_cost_per_turn']:.6f}")
    
    print("\n✅ Cost tracking complete!")

if __name__ == "__main__":
    main()

