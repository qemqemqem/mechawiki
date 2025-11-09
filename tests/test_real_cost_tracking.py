"""
Test that mimics EXACTLY how BaseAgent calls litellm and tracks costs.
This will verify that our cost tracking setup actually works.
"""
import litellm


def test_exact_baseagent_pattern():
    """Test the exact pattern used in BaseAgent for streaming + cost tracking."""
    
    print("\n" + "="*60)
    print("Testing EXACT BaseAgent pattern for cost tracking")
    print("="*60)
    
    # Mimic BaseAgent's call exactly
    model = "claude-haiku-4-5-20251001"
    messages = [{"role": "user", "content": "Say 'hello' once."}]
    stream = True
    
    print(f"\n1. Making litellm.completion() call...")
    print(f"   Model: {model}")
    print(f"   Stream: {stream}")
    print(f"   Stream options: {{'include_usage': True}}")
    
    response = litellm.completion(
        model=model,
        messages=messages,
        tools=None,
        tool_choice=None,
        stream=stream,
        stream_options={'include_usage': True} if stream else None,
        temperature=1.0
    )
    
    print(f"\n2. Iterating through streaming response...")
    
    usage_info = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    collected_content = ""
    chunk_count = 0
    
    for chunk in response:
        chunk_count += 1
        
        # Collect content
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            collected_content += content
            print(f"   Chunk {chunk_count}: '{content}'")
        
        # Check for usage (should be in final chunk)
        if hasattr(chunk, 'usage') and chunk.usage:
            usage_info["prompt_tokens"] = getattr(chunk.usage, 'prompt_tokens', 0)
            usage_info["completion_tokens"] = getattr(chunk.usage, 'completion_tokens', 0)
            usage_info["total_tokens"] = getattr(chunk.usage, 'total_tokens', 0)
            print(f"\n   ✅ Found usage info in chunk {chunk_count}!")
            print(f"      Prompt tokens: {usage_info['prompt_tokens']}")
            print(f"      Completion tokens: {usage_info['completion_tokens']}")
            print(f"      Total tokens: {usage_info['total_tokens']}")
    
    print(f"\n3. Collected content: '{collected_content}'")
    
    # Verify we got usage info
    assert usage_info["prompt_tokens"] > 0, "Should have prompt tokens"
    assert usage_info["completion_tokens"] > 0, "Should have completion tokens"
    print(f"\n   ✅ Usage info successfully extracted!")
    
    # Calculate cost EXACTLY like BaseAgent does (no mocking!)
    print(f"\n4. Calculating cost with litellm.completion_cost()...")
    print(f"   Using prompt/completion strings method (BaseAgent's streaming approach)")
    
    # Extract prompt from messages (like BaseAgent does)
    prompt_text = " ".join([m["content"] for m in messages if m.get("role") == "user"])
    
    print(f"   Prompt: '{prompt_text}'")
    print(f"   Completion: '{collected_content}'")
    
    try:
        cost = litellm.completion_cost(
            model=model,
            prompt=prompt_text,
            completion=collected_content
        )
        
        print(f"\n   ✅ Cost calculated: ${cost:.6f}")
        
        assert cost > 0, "Cost should be greater than 0"
        print(f"   ✅ Cost is non-zero!")
        
        return cost
        
    except Exception as e:
        print(f"   ❌ Error calculating cost: {e}")
        raise


def test_non_streaming_pattern():
    """Test non-streaming pattern for comparison."""
    
    print("\n" + "="*60)
    print("Testing non-streaming pattern (for comparison)")
    print("="*60)
    
    model = "claude-haiku-4-5-20251001"
    messages = [{"role": "user", "content": "Say 'hello' once."}]
    
    print(f"\n1. Making non-streaming litellm.completion() call...")
    
    response = litellm.completion(
        model=model,
        messages=messages,
        stream=False,
        temperature=1.0
    )
    
    print(f"   ✅ Response received")
    print(f"   Content: '{response.choices[0].message.content}'")
    print(f"   Usage: {response.usage.prompt_tokens}p + {response.usage.completion_tokens}c")
    
    # Calculate cost directly from response
    print(f"\n2. Calculating cost...")
    cost = litellm.completion_cost(completion_response=response)
    print(f"   ✅ Cost: ${cost:.6f}")
    
    assert cost > 0, "Cost should be greater than 0"
    
    return cost


if __name__ == "__main__":
    print("\n" + "🔬 Testing Real LiteLLM Cost Tracking" + "\n")
    
    # Test streaming (what BaseAgent uses)
    streaming_cost = test_exact_baseagent_pattern()
    
    # Test non-streaming (for comparison)
    non_streaming_cost = test_non_streaming_pattern()
    
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print(f"Streaming cost:     ${streaming_cost:.6f}")
    print(f"Non-streaming cost: ${non_streaming_cost:.6f}")
    print(f"\n✅ Both patterns work! Cost tracking should work in BaseAgent.")
    print("="*60)

