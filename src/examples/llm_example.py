import os
import litellm
import json

# Global variable
x = 10

def add(a: int):
    """Add a value to x
    
    Parameters
    ----------
    a : int
        Value to add to x
    """
    global x
    x += a
    return f"Added {a} to x. New value: {x}"

def mult(a: int):
    """Multiply x by a value
    
    Parameters
    ----------
    a : int
        Value to multiply x by
    """
    global x
    x *= a
    return f"Multiplied x by {a}. New value: {x}"

# Set up API key (you'll need to set this)
# os.environ['ANTHROPIC_API_KEY'] = "your-key-here"

def main():
    print(f"Initial x: {x}")
    
    # Register functions using litellm helper
    tools = [
        {"type": "function", "function": litellm.utils.function_to_dict(add)},
        {"type": "function", "function": litellm.utils.function_to_dict(mult)}
    ]
    
    messages = [
        {"role": "user", "content": "Add 3 to x, then multiply by 4"}
    ]
    
    available_functions = {"add": add, "mult": mult}
    
    while True:
        print("\n--- LLM Response ---")
        
        # Stream the response
        response = litellm.completion(
            model="claude-3-5-haiku-20241022",
            messages=messages,
            tools=tools,
            tool_choice="auto",
            stream=True
        )
        
        # Collect streamed response
        full_response = None
        for chunk in response:
            if chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="", flush=True)
            
            # Store the complete response when streaming ends
            if chunk.choices[0].finish_reason:
                full_response = chunk.choices[0]
                break
        
        print()  # New line after streaming
        
        # Check for tool calls
        if full_response and full_response.message.tool_calls:
            print(f"\n--- Executing {len(full_response.message.tool_calls)} tool calls ---")
            
            # Add assistant message to conversation
            messages.append(full_response.message)
            
            # Execute each tool call
            for tool_call in full_response.message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                print(f"Calling {function_name} with args: {function_args}")
                
                function_to_call = available_functions[function_name]
                function_result = function_to_call(**function_args)
                
                print(f"Result: {function_result}")
                
                # Add function result to conversation
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool", 
                    "name": function_name,
                    "content": function_result
                })
        else:
            # No tool calls, conversation complete
            break
    
    print(f"\nFinal x: {x}")

if __name__ == "__main__":
    main()