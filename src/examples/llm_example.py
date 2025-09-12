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
        collected_content = ""
        tool_calls = []
        
        for chunk in response:
            # Handle content
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
                collected_content += content
            
            # Handle tool calls
            if hasattr(chunk.choices[0].delta, 'tool_calls') and chunk.choices[0].delta.tool_calls:
                for delta_tool_call in chunk.choices[0].delta.tool_calls:
                    # Extend tool_calls list if needed
                    while len(tool_calls) <= delta_tool_call.index:
                        tool_calls.append({
                            "id": None,
                            "type": "function", 
                            "function": {"name": "", "arguments": ""}
                        })
                    
                    # Update the tool call at this index
                    if delta_tool_call.id:
                        tool_calls[delta_tool_call.index]["id"] = delta_tool_call.id
                    if delta_tool_call.function.name:
                        tool_calls[delta_tool_call.index]["function"]["name"] = delta_tool_call.function.name
                    if delta_tool_call.function.arguments:
                        tool_calls[delta_tool_call.index]["function"]["arguments"] += delta_tool_call.function.arguments
            
            # Check if streaming is complete
            if chunk.choices[0].finish_reason:
                break
        
        print()  # New line after streaming
        
        # Check for tool calls
        if tool_calls and any(tc["id"] for tc in tool_calls):
            valid_tool_calls = [tc for tc in tool_calls if tc["id"]]
            print(f"\n--- Executing {len(valid_tool_calls)} tool calls ---")
            
            # Create assistant message
            assistant_message = {
                "role": "assistant",
                "content": collected_content if collected_content else None,
                "tool_calls": valid_tool_calls
            }
            messages.append(assistant_message)
            
            # Execute each tool call
            for tool_call in valid_tool_calls:
                function_name = tool_call["function"]["name"]
                function_args = json.loads(tool_call["function"]["arguments"])
                
                print(f"Calling {function_name} with args: {function_args}")
                
                function_to_call = available_functions[function_name]
                function_result = function_to_call(**function_args)
                
                print(f"Result: {function_result}")
                
                # Add function result to conversation
                messages.append({
                    "tool_call_id": tool_call["id"],
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