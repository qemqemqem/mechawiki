"""
Test litellm cost tracking to verify it works with our setup.
"""
import litellm
import pytest


def test_litellm_cost_calculation_with_mock_response():
    """Test that litellm.completion_cost() works with a mock response object."""
    # Create a mock response like we do in BaseAgent
    class MockUsage:
        def __init__(self, prompt_tokens, completion_tokens):
            self.prompt_tokens = prompt_tokens
            self.completion_tokens = completion_tokens
            self.total_tokens = prompt_tokens + completion_tokens
    
    class MockResponse:
        def __init__(self, model, usage):
            self.model = model
            self.usage = usage
    
    mock_response = MockResponse(
        "claude-haiku-4-5-20251001",
        MockUsage(100, 50)
    )
    
    cost = litellm.completion_cost(completion_response=mock_response)
    
    print(f"\n💰 Cost for 100 prompt + 50 completion tokens: ${cost:.6f}")
    
    assert cost > 0, "Cost should be greater than 0"
    assert isinstance(cost, float), "Cost should be a float"
    
    # Haiku is cheap but not free - should be less than 1 cent for 150 tokens
    assert cost < 0.01, "Cost for 150 tokens should be less than $0.01"


def test_litellm_streaming_response_has_usage():
    """Test that streaming responses include usage info."""
    # Make a real streaming call (this will cost a tiny amount)
    response = litellm.completion(
        model="claude-haiku-4-5-20251001",
        messages=[{"role": "user", "content": "Say 'test' once."}],
        stream=True,
        temperature=1.0
    )
    
    usage_found = False
    usage_info = {}
    
    # Iterate through streaming chunks
    for chunk in response:
        print(f"🔍 Chunk: {chunk}")
        
        # Check if this chunk has usage info
        if hasattr(chunk, 'usage') and chunk.usage:
            usage_found = True
            usage_info = {
                "prompt_tokens": getattr(chunk.usage, 'prompt_tokens', 0),
                "completion_tokens": getattr(chunk.usage, 'completion_tokens', 0),
                "total_tokens": getattr(chunk.usage, 'total_tokens', 0)
            }
            print(f"💰 Usage info found: {usage_info}")
    
    assert usage_found, "Usage info should be present in streaming response"
    assert usage_info.get("prompt_tokens", 0) > 0, "Should have prompt tokens"
    assert usage_info.get("completion_tokens", 0) > 0, "Should have completion tokens"
    
    # Note: For streaming, we'd need to reconstruct a response object
    # But since we iterated through all chunks, we lost the original response
    # In practice, we construct a mock response with the usage info
    class MockUsage:
        def __init__(self, prompt_tokens, completion_tokens):
            self.prompt_tokens = prompt_tokens
            self.completion_tokens = completion_tokens
            self.total_tokens = prompt_tokens + completion_tokens
    
    class MockResponse:
        def __init__(self, model, usage):
            self.model = model
            self.usage = usage
    
    mock_response = MockResponse(
        "claude-haiku-4-5-20251001",
        MockUsage(usage_info["prompt_tokens"], usage_info["completion_tokens"])
    )
    cost = litellm.completion_cost(completion_response=mock_response)
    
    print(f"💰 Calculated cost: ${cost:.6f}")
    assert cost > 0, "Cost should be greater than 0"


def test_litellm_non_streaming_response_has_usage():
    """Test that non-streaming responses include usage info."""
    # Make a real non-streaming call (this will cost a tiny amount)
    response = litellm.completion(
        model="claude-haiku-4-5-20251001",
        messages=[{"role": "user", "content": "Say 'test' once."}],
        stream=False,
        temperature=1.0
    )
    
    print(f"🔍 Response: {response}")
    
    # Check for usage info
    assert hasattr(response, 'usage'), "Response should have usage attribute"
    assert response.usage is not None, "Usage should not be None"
    
    prompt_tokens = getattr(response.usage, 'prompt_tokens', 0)
    completion_tokens = getattr(response.usage, 'completion_tokens', 0)
    
    print(f"💰 Tokens: {prompt_tokens}p + {completion_tokens}c")
    
    assert prompt_tokens > 0, "Should have prompt tokens"
    assert completion_tokens > 0, "Should have completion tokens"
    
    # Calculate cost using the response object (correct way)
    cost = litellm.completion_cost(completion_response=response)
    
    print(f"💰 Calculated cost: ${cost:.6f}")
    assert cost > 0, "Cost should be greater than 0"


if __name__ == "__main__":
    print("Running litellm cost tracking tests...")
    print("=" * 60)
    
    # Skip mock test for now - test with real responses
    #print("\n1. Testing cost calculation with mock response...")
    #test_litellm_cost_calculation_with_mock_response()
    
    print("\n1. Testing non-streaming response usage info...")
    test_litellm_non_streaming_response_has_usage()
    
    print("\n2. Testing streaming response usage info...")
    test_litellm_streaming_response_has_usage()
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")

