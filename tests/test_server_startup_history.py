#!/usr/bin/env python3
"""
Test that agents actually load history when the server starts.
This simulates the actual server startup flow.
"""
import sys
import os
from pathlib import Path

# Set session to tales_of_wonder for testing
os.environ['SESSION_NAME'] = 'tales_of_wonder'

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from server.config import session_config
from server.agent_manager import agent_manager
from server.init_agents import start_test_agents


def test_server_startup_history():
    """Test that agents load history when server starts."""
    
    print(f"\n🧪 Testing server startup with session: {session_config.session_name}")
    print(f"📁 Session directory: {session_config.session_dir}")
    print(f"📁 Logs directory: {session_config.logs_dir}")
    
    # Check for existing log files
    log_files = list(session_config.logs_dir.glob("*.jsonl"))
    print(f"\n📊 Found {len(log_files)} log files:")
    for log_file in log_files:
        size = log_file.stat().st_size
        print(f"  - {log_file.name} ({size} bytes)")
    
    if not log_files:
        print("\n⚠️  No log files found. Cannot test history loading.")
        print("   Run agents first to create logs, then restart and test.")
        return False
    
    # Start agents (this is what happens when server starts)
    print(f"\n🚀 Starting agents (simulating server startup)...")
    agents = start_test_agents(agent_manager)
    
    print(f"\n📊 Started {len(agents)} agents")
    
    # Check each agent's history
    success = True
    agents_with_real_history = 0
    
    for agent_data in session_config.list_agents():
        agent_id = agent_data["id"]
        runner = agent_manager.get_agent(agent_id)
        
        if not runner:
            print(f"❌ Agent {agent_id} not found in agent_manager")
            success = False
            continue
        
        # Get the actual agent instance
        agent_instance = runner.agent
        message_count = len(agent_instance.messages)
        
        # Check log file to see if there's actually conversation history
        log_file = session_config.logs_dir / f"agent_{agent_id}.jsonl"
        has_real_history = False
        if log_file.exists():
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        entry = eval(line) if line.strip().startswith('{') else None
                        if entry and entry.get('type') in ['message', 'tool_call', 'tool_result', 'user_message']:
                            has_real_history = True
                            break
                    except:
                        pass
        
        print(f"\n🤖 Agent: {agent_id}")
        print(f"   Log file has real history: {'Yes' if has_real_history else 'No (only status messages)'}")
        print(f"   Messages loaded in agent: {message_count}")
        
        if has_real_history:
            agents_with_real_history += 1
            if message_count > 0:
                print(f"   ✅ History loaded successfully!")
                # Show first few messages
                for i, msg in enumerate(agent_instance.messages[:3]):
                    role = msg.get('role', 'unknown')
                    content = str(msg.get('content', ''))[:50]
                    has_tools = 'tool_calls' in msg
                    print(f"      {i+1}. [{role}] {content}{'...' if len(str(msg.get('content', ''))) > 50 else ''} {has_tools and '(+tools)' or ''}")
            else:
                print(f"   ❌ FAILED: Log has history but agent loaded 0 messages!")
                success = False
        else:
            print(f"   ℹ️  No conversation history to load (expected 0 messages)")
    
    if agents_with_real_history == 0:
        print(f"\n⚠️  Warning: No agents have real conversation history in their logs")
        print(f"   Cannot verify history loading works. Run agents first, then restart.")
    
    # Clean up
    print(f"\n🧹 Stopping agents...")
    agent_manager.stop_all()
    
    return success


if __name__ == '__main__':
    try:
        success = test_server_startup_history()
        if success:
            print("\n" + "="*60)
            print("✅ SUCCESS: Agents load history on server startup!")
            print("="*60)
        else:
            print("\n" + "="*60)
            print("❌ FAILED: Agents did NOT load history on server startup!")
            print("="*60)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

