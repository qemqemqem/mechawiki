#!/usr/bin/env python3
"""
Script to create a ReaderAgent and display its auto-generated system prompt.

This helps verify that the automatic tool description generation is working correctly.
"""
import sys
import os

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ais.reader_agent import ReaderAgent


def main():
    """Create a ReaderAgent and display its system prompt."""
    print("🔍 Creating ReaderAgent and inspecting system prompt...")
    print("=" * 80)
    
    # Create the reader agent
    agent = ReaderAgent(stream=False)
    
    print("📋 SYSTEM PROMPT:")
    print("-" * 40)
    print(agent.system_prompt)
    print("-" * 40)
    
    print(f"\n📊 STATISTICS:")
    print(f"   - System prompt length: {len(agent.system_prompt)} characters")
    print(f"   - Number of tools: {len(agent.tools)}")
    print(f"   - Available functions: {list(agent.available_functions.keys())}")
    
    print(f"\n🔧 RAW TOOL DESCRIPTIONS:")
    print("-" * 40)
    print(agent._generate_tools_description())
    print("-" * 40)
    
    print("\n✅ System prompt inspection complete!")


if __name__ == "__main__":
    main()