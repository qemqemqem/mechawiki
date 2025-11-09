#!/usr/bin/env python3
"""
Simple focused test: Create artificial logs, load agent, verify history.
"""
import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.reader_agent import ReaderAgent
from agents.agent_runner import AgentRunner


def test_agent_loads_history_from_log():
    """
    Create an artificial log with conversation history.
    Load an agent with that log.
    Verify the agent's conversation history matches the log.
    """
    
    print("\n" + "="*70)
    print("🧪 Test: Agent History Loading from Artificial Log")
    print("="*70)
    
    # Step 1: Create artificial log with conversation history
    print("\n📝 Step 1: Creating artificial log file...")
    
    log_entries = [
        {"type": "status", "status": "running", "message": "Agent started"},
        {"type": "message", "role": "assistant", "content": "Hello! I'll help you read the story."},
        {"type": "tool_call", "tool": "find_articles", "args": {"search_string": "london"}},
        {"type": "tool_result", "tool": "find_articles", "result": ["london.md", "tales.md"]},
        {"type": "message", "role": "assistant", "content": "Found 2 articles about London."},
        {"type": "user_message", "content": "Great, please continue."},
        {"type": "message", "role": "assistant", "content": "I'll advance through the story now."},
        {"type": "tool_call", "tool": "advance", "args": {"num_words": 1000}},
        {"type": "tool_result", "tool": "advance", "result": "Advanced from 0 to 1000"},
        {"type": "message", "role": "assistant", "content": "The story begins with a mysterious journey."},
    ]
    
    # Create temporary log file
    temp_log = tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False)
    for entry in log_entries:
        entry['timestamp'] = datetime.now().isoformat()
        temp_log.write(json.dumps(entry) + '\n')
    temp_log.close()
    log_path = Path(temp_log.name)
    
    print(f"   ✓ Created log file: {log_path}")
    print(f"   ✓ Added {len(log_entries)} log entries")
    print(f"   ✓ Entries include: messages, tool calls, tool results, user message")
    
    # Step 2: Create agent and load it with the log file
    print("\n🤖 Step 2: Creating agent and loading history...")
    
    agent = ReaderAgent(model="claude-haiku-4-5-20251001")
    print(f"   ✓ Created ReaderAgent")
    print(f"   ✓ Agent messages before loading: {len(agent.messages)}")
    
    # Create AgentRunner - this triggers history loading
    runner = AgentRunner(
        agent_instance=agent,
        agent_id="test-agent",
        log_file=log_path,
        start_paused=True
    )
    
    print(f"   ✓ Created AgentRunner (this loads history)")
    print(f"   ✓ Agent messages after loading: {len(agent.messages)}")
    
    # Step 3: Verify the history
    print("\n✅ Step 3: Verifying conversation history...")
    
    success = True
    
    # Check that messages were loaded
    if len(agent.messages) == 0:
        print("   ❌ FAIL: No messages loaded!")
        success = False
    else:
        print(f"   ✓ Loaded {len(agent.messages)} messages")
    
    # Check for expected message types
    assistant_msgs = [m for m in agent.messages if m['role'] == 'assistant']
    user_msgs = [m for m in agent.messages if m['role'] == 'user']
    tool_msgs = [m for m in agent.messages if m['role'] == 'tool']
    
    print(f"\n   Message breakdown:")
    print(f"   - Assistant messages: {len(assistant_msgs)}")
    print(f"   - User messages: {len(user_msgs)}")
    print(f"   - Tool messages: {len(tool_msgs)}")
    
    # Verify we have the expected content
    print(f"\n   Checking for expected content...")
    
    # Check for first assistant message
    has_hello = any("Hello" in str(m.get('content', '')) for m in assistant_msgs)
    if has_hello:
        print(f"   ✓ Found initial greeting")
    else:
        print(f"   ❌ Missing initial greeting")
        success = False
    
    # Check for tool calls
    has_tool_calls = any('tool_calls' in m for m in assistant_msgs)
    if has_tool_calls:
        print(f"   ✓ Found assistant messages with tool calls")
    else:
        print(f"   ❌ Missing tool calls")
        success = False
    
    # Check for user message
    has_user_msg = len(user_msgs) > 0
    if has_user_msg:
        print(f"   ✓ Found user message")
        user_content = user_msgs[0].get('content', '')
        if "continue" in user_content.lower():
            print(f"   ✓ User message content matches: '{user_content}'")
        else:
            print(f"   ⚠️  User message content unexpected: '{user_content}'")
    else:
        print(f"   ❌ Missing user message")
        success = False
    
    # Check for tool results
    if len(tool_msgs) > 0:
        print(f"   ✓ Found {len(tool_msgs)} tool result messages")
        # Check that tool results reference correct tools
        tool_names = [m.get('name') for m in tool_msgs]
        print(f"   ✓ Tools used: {tool_names}")
    else:
        print(f"   ❌ Missing tool results")
        success = False
    
    # Show actual message sequence
    print(f"\n   Full message sequence:")
    for i, msg in enumerate(agent.messages):
        role = msg['role']
        content = str(msg.get('content', ''))[:60]
        has_tools = 'tool_calls' in msg
        tool_name = msg.get('name', '')
        
        if has_tools:
            tool_count = len(msg['tool_calls'])
            print(f"   {i+1}. [{role}] {content}... (+{tool_count} tool call(s))")
        elif role == 'tool':
            print(f"   {i+1}. [{role}/{tool_name}] {content}...")
        else:
            print(f"   {i+1}. [{role}] {content}...")
    
    # Cleanup
    log_path.unlink()
    
    # Final result
    print("\n" + "="*70)
    if success:
        print("✅ SUCCESS: Agent correctly loaded conversation history from log!")
        print("="*70)
        return True
    else:
        print("❌ FAILED: Agent did not correctly load history")
        print("="*70)
        return False


if __name__ == '__main__':
    try:
        success = test_agent_loads_history_from_log()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

