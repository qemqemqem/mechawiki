#!/usr/bin/env python3
"""
Unit tests for agent history loading from log files.
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


def create_test_log_file(entries):
    """Create a temporary log file with test entries."""
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False)
    
    for entry in entries:
        entry['timestamp'] = datetime.now().isoformat()
        temp_file.write(json.dumps(entry) + '\n')
    
    temp_file.close()
    return Path(temp_file.name)


def test_empty_history():
    """Test agent with no existing log file."""
    print("\n🧪 Test 1: Empty history (no log file)")
    
    # Create agent
    agent = ReaderAgent(model="claude-haiku-4-5-20251001")
    
    # Create runner with non-existent log file
    runner = AgentRunner(
        agent_instance=agent,
        agent_id="test-001",
        log_file=Path("/tmp/nonexistent_log.jsonl"),
        start_paused=True
    )
    
    assert len(agent.messages) == 0, f"Expected 0 messages, got {len(agent.messages)}"
    print("✅ PASS: Agent starts with empty history when no log file exists")


def test_simple_message_history():
    """Test loading simple assistant and user messages."""
    print("\n🧪 Test 2: Simple message history")
    
    log_entries = [
        {"type": "status", "status": "running", "message": "Agent started"},
        {"type": "message", "role": "assistant", "content": "Hello, I'm ready to help."},
        {"type": "message", "role": "assistant", "content": " Let me start by listing articles."},
        {"type": "user_message", "content": "Please continue"},
        {"type": "message", "role": "assistant", "content": "Sure, I'll continue working."},
    ]
    
    log_file = create_test_log_file(log_entries)
    
    try:
        agent = ReaderAgent(model="claude-haiku-4-5-20251001")
        runner = AgentRunner(
            agent_instance=agent,
            agent_id="test-002",
            log_file=log_file,
            start_paused=True
        )
        
        print(f"  Messages loaded: {len(agent.messages)}")
        for i, msg in enumerate(agent.messages):
            print(f"    {i+1}. {msg['role']}: {msg.get('content', '')[:50]}")
        
        assert len(agent.messages) == 3, f"Expected 3 messages, got {len(agent.messages)}"
        assert agent.messages[0]['role'] == 'assistant', "First message should be assistant"
        assert agent.messages[0]['content'] == "Hello, I'm ready to help. Let me start by listing articles.", "Content should be accumulated"
        assert agent.messages[1]['role'] == 'user', "Second message should be user"
        assert agent.messages[2]['role'] == 'assistant', "Third message should be assistant"
        
        print("✅ PASS: Simple messages loaded correctly")
    finally:
        log_file.unlink()


def test_tool_call_history():
    """Test loading tool calls and results."""
    print("\n🧪 Test 3: Tool call history")
    
    log_entries = [
        {"type": "message", "role": "assistant", "content": "I'll search for articles."},
        {"type": "tool_call", "tool": "find_articles", "args": {"search_string": "*"}},
        {"type": "tool_result", "tool": "find_articles", "result": ["article1.md", "article2.md"]},
        {"type": "message", "role": "assistant", "content": "Found 2 articles."},
    ]
    
    log_file = create_test_log_file(log_entries)
    
    try:
        agent = ReaderAgent(model="claude-haiku-4-5-20251001")
        runner = AgentRunner(
            agent_instance=agent,
            agent_id="test-003",
            log_file=log_file,
            start_paused=True
        )
        
        print(f"  Messages loaded: {len(agent.messages)}")
        for i, msg in enumerate(agent.messages):
            role = msg['role']
            has_tools = 'tool_calls' in msg
            is_tool_result = 'tool_call_id' in msg
            print(f"    {i+1}. {role}: {has_tools and 'with tool_calls' or ''}{is_tool_result and 'tool result' or ''}")
        
        assert len(agent.messages) >= 2, f"Expected at least 2 messages, got {len(agent.messages)}"
        
        # Find assistant message with tool calls
        assistant_with_tools = None
        for msg in agent.messages:
            if msg['role'] == 'assistant' and 'tool_calls' in msg:
                assistant_with_tools = msg
                break
        
        assert assistant_with_tools is not None, "Should have assistant message with tool_calls"
        assert len(assistant_with_tools['tool_calls']) == 1, "Should have 1 tool call"
        assert assistant_with_tools['tool_calls'][0]['function']['name'] == 'find_articles', "Tool should be find_articles"
        
        # Find tool result message
        tool_result = None
        for msg in agent.messages:
            if msg['role'] == 'tool':
                tool_result = msg
                break
        
        assert tool_result is not None, "Should have tool result message"
        assert tool_result['name'] == 'find_articles', "Tool result should be for find_articles"
        
        print("✅ PASS: Tool calls and results loaded correctly")
    finally:
        log_file.unlink()


def test_multiple_tool_calls():
    """Test loading multiple tool calls in sequence."""
    print("\n🧪 Test 4: Multiple tool calls")
    
    log_entries = [
        {"type": "message", "role": "assistant", "content": "I'll do several searches."},
        {"type": "tool_call", "tool": "find_articles", "args": {"search_string": "london"}},
        {"type": "tool_result", "tool": "find_articles", "result": ["london.md"]},
        {"type": "message", "role": "assistant", "content": "Now checking status."},
        {"type": "tool_call", "tool": "get_status", "args": {}},
        {"type": "tool_result", "tool": "get_status", "result": "Story at 50%"},
    ]
    
    log_file = create_test_log_file(log_entries)
    
    try:
        agent = ReaderAgent(model="claude-haiku-4-5-20251001")
        runner = AgentRunner(
            agent_instance=agent,
            agent_id="test-004",
            log_file=log_file,
            start_paused=True
        )
        
        print(f"  Messages loaded: {len(agent.messages)}")
        
        # Count tool calls
        tool_call_count = sum(1 for msg in agent.messages if 'tool_calls' in msg)
        tool_result_count = sum(1 for msg in agent.messages if msg['role'] == 'tool')
        
        print(f"  Tool calls: {tool_call_count}")
        print(f"  Tool results: {tool_result_count}")
        
        assert tool_call_count >= 2, f"Expected at least 2 tool calls, got {tool_call_count}"
        assert tool_result_count >= 2, f"Expected at least 2 tool results, got {tool_result_count}"
        
        print("✅ PASS: Multiple tool calls loaded correctly")
    finally:
        log_file.unlink()


def test_real_log_file():
    """Test with a real log file from tales_of_wonder session."""
    print("\n🧪 Test 5: Real log file")
    
    log_file = Path("/home/keenan/Dev/mechawiki/data/sessions/tales_of_wonder/logs/agent_reader-001.jsonl")
    
    if not log_file.exists():
        print("⏭️  SKIP: Real log file not found")
        return
    
    agent = ReaderAgent(model="claude-haiku-4-5-20251001", story_file="story.txt")
    runner = AgentRunner(
        agent_instance=agent,
        agent_id="reader-001",
        log_file=log_file,
        agent_config={"story_file": "story.txt"},
        start_paused=True
    )
    
    print(f"  Messages loaded: {len(agent.messages)}")
    
    assert len(agent.messages) > 0, "Should load messages from real log file"
    
    # Count message types
    assistant_msgs = sum(1 for msg in agent.messages if msg['role'] == 'assistant')
    user_msgs = sum(1 for msg in agent.messages if msg['role'] == 'user')
    tool_msgs = sum(1 for msg in agent.messages if msg['role'] == 'tool')
    
    print(f"  - Assistant messages: {assistant_msgs}")
    print(f"  - User messages: {user_msgs}")
    print(f"  - Tool messages: {tool_msgs}")
    
    print("✅ PASS: Real log file loaded successfully")


def test_agent_can_use_loaded_history():
    """Test that agent can actually use the loaded history."""
    print("\n🧪 Test 6: Agent can use loaded history")
    
    log_entries = [
        {"type": "message", "role": "assistant", "content": "I've read the first part of the story."},
        {"type": "tool_call", "tool": "advance", "args": {"num_words": 5000}},
        {"type": "tool_result", "tool": "advance", "result": "Advanced from 0 to 5000"},
        {"type": "message", "role": "assistant", "content": "Story is interesting so far."},
    ]
    
    log_file = create_test_log_file(log_entries)
    
    try:
        agent = ReaderAgent(model="claude-haiku-4-5-20251001")
        runner = AgentRunner(
            agent_instance=agent,
            agent_id="test-006",
            log_file=log_file,
            start_paused=True
        )
        
        # Check that messages are in the agent's message list
        assert len(agent.messages) > 0, "Agent should have messages"
        
        # Verify the agent can access its history
        first_msg = agent.messages[0]
        assert 'role' in first_msg, "Message should have role"
        assert 'content' in first_msg, "Message should have content"
        
        print(f"  ✓ Agent has {len(agent.messages)} messages in history")
        print(f"  ✓ Agent can access message structure")
        print("✅ PASS: Agent can use loaded history")
    finally:
        log_file.unlink()


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("🧪 Testing Agent History Loading")
    print("=" * 60)
    
    tests = [
        test_empty_history,
        test_simple_message_history,
        test_tool_call_history,
        test_multiple_tool_calls,
        test_real_log_file,
        test_agent_can_use_loaded_history,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ FAIL: {e}")
            failed += 1
        except Exception as e:
            print(f"💥 ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)

