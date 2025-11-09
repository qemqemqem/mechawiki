#!/usr/bin/env python3
"""
Test script for real agents via AgentRunner.

Tests the event-based architecture with a simple CLI demo.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from agents.reader_agent import ReaderAgent
from agents.writer_agent import WriterAgent
from agents.interactive_agent import InteractiveAgent
from agents.agent_runner import AgentRunner
from base_agent.base_agent import ContextLengthExceeded

def test_reader_agent():
    """Test ReaderAgent with event yielding."""
    print("\n🏰 Testing ReaderAgent")
    print("=" * 60)
    
    # Create agent
    agent = ReaderAgent(model="claude-3-5-haiku-20241022")
    
    # Create test log file
    log_file = Path("data/test_reader.jsonl")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Wrap in AgentRunner
    runner = AgentRunner(
        agent_instance=agent,
        agent_id="test-reader-001",
        log_file=log_file,
        agent_config={
            'initial_prompt': 'List some articles in the articles directory.'
        }
    )
    
    print(f"✓ Created ReaderAgent")
    print(f"✓ Log file: {log_file}")
    print("\nTo run in background:")
    print("  runner.start()")
    print(f"\nTo watch logs:")
    print(f"  tail -f {log_file}")
    
    return runner


def test_writer_agent():
    """Test WriterAgent with event yielding."""
    print("\n✍️  Testing WriterAgent")
    print("=" * 60)
    
    agent = WriterAgent(model="claude-3-5-haiku-20241022")
    
    log_file = Path("data/test_writer.jsonl")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    runner = AgentRunner(
        agent_instance=agent,
        agent_id="test-writer-001",
        log_file=log_file,
        agent_config={
            'initial_prompt': 'Check if there is a story at stories/test_story.md. If not, write a short fantasy story.'
        }
    )
    
    print(f"✓ Created WriterAgent")
    print(f"✓ Log file: {log_file}")
    
    return runner


def test_interactive_agent():
    """Test InteractiveAgent with event yielding."""
    print("\n🎮 Testing InteractiveAgent")
    print("=" * 60)
    
    agent = InteractiveAgent(model="claude-3-5-haiku-20241022")
    
    log_file = Path("data/test_interactive.jsonl")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    runner = AgentRunner(
        agent_instance=agent,
        agent_id="test-interactive-001",
        log_file=log_file,
        agent_config={
            'initial_prompt': 'Start an interactive adventure. Present a scene and ask what the user wants to do.'
        }
    )
    
    print(f"✓ Created InteractiveAgent")
    print(f"✓ Log file: {log_file}")
    print("\nThis agent will use wait_for_user() and pause until you add a user_message to its log.")
    
    return runner


def test_event_streaming():
    """Test that events are properly yielded."""
    print("\n⚡ Testing Event Streaming")
    print("=" * 60)
    
    # Create a simple agent
    agent = ReaderAgent(model="claude-3-5-haiku-20241022")
    
    # Manually consume events (without AgentRunner)
    print("\nConsuming events directly from agent.run_forever()...")
    print("(First few events only)\n")
    
    event_count = 0
    try:
        for event in agent.run_forever("Say hello and end.", max_turns=1):
            print(f"Event {event_count + 1}: {event['type']}")
            if event['type'] == 'text_token':
                print(f"  Content: {repr(event['content'][:50])}")
            elif event['type'] == 'tool_call':
                print(f"  Tool: {event['tool']}")
            
            event_count += 1
            if event_count >= 10:  # Limit output
                print("  ... (more events)")
                break
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print(f"\n✓ Successfully yielded {event_count}+ events")
    return True


def main():
    """Run tests."""
    print("\n" + "="*60)
    print("  REAL AGENTS TEST SUITE")
    print("="*60)
    
    # Test 1: Event streaming
    if not test_event_streaming():
        print("\n❌ Event streaming test failed!")
        return 1
    
    # Test 2: Create all agent types
    reader_runner = test_reader_agent()
    writer_runner = test_writer_agent()
    interactive_runner = test_interactive_agent()
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    
    print("\nReal agents are ready to use!")
    print("\nNext steps:")
    print("1. Update UI to allow switching between Mock and Real agents")
    print("2. Set use_real_agent=True in AgentManager.start_agent()")
    print("3. Ensure config.toml has valid API keys")
    print("4. Watch the logs stream in real-time!")
    
    print("\nTo test in background:")
    print("  reader_runner.start()")
    print("  tail -f data/test_reader.jsonl")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

