"""
Example agent using BaseAgent with math tools.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import litellm
from agent.base_agent import BaseAgent

# Global variable for math operations
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

def get_x():
    """Get the current value of x
    
    Returns
    -------
    str
        Current value of x
    """
    global x
    return f"Current value of x: {x}"

def reset_x():
    """Reset x to 10
    
    Returns
    -------
    str
        Confirmation message
    """
    global x
    x = 10
    return f"Reset x to 10"

class MathAgent(BaseAgent):
    """
    Math agent that can perform operations on a global variable x.
    
    Demonstrates how to extend BaseAgent with custom tools and behavior.
    """
    
    def __init__(self, **kwargs):
        # Create tools using litellm helper
        tools = [
            {"type": "function", "function": litellm.utils.function_to_dict(add)},
            {"type": "function", "function": litellm.utils.function_to_dict(mult)},
            {"type": "function", "function": litellm.utils.function_to_dict(get_x)},
            {"type": "function", "function": litellm.utils.function_to_dict(reset_x)}
        ]
        
        available_functions = {
            "add": add,
            "mult": mult, 
            "get_x": get_x,
            "reset_x": reset_x
        }
        
        system_prompt = """You are a helpful math assistant. You have access to a global variable 'x' that starts at 10.

Available tools:
- add(a): Add a value to x
- mult(a): Multiply x by a value  
- get_x(): Get the current value of x
- reset_x(): Reset x back to 10

When performing mathematical operations, always:
1. Explain what you're doing step by step
2. Show the intermediate values
3. Give a clear final result

Be precise and helpful in your explanations."""
        
        super().__init__(
            tools=tools,
            available_functions=available_functions,
            system_prompt=system_prompt,
            **kwargs
        )
    
    def _execute_tool(self, tool_call: dict) -> str:
        """
        Custom tool execution that updates agent memory with x value.
        """
        # Execute the tool normally
        result = super()._execute_tool(tool_call)
        
        # Update memory with current x value
        global x
        self.set_memory("current_x", x)
        
        return result
    
    def get_current_x(self) -> int:
        """Get current x value from memory or global variable."""
        return self.get_memory("current_x", x)

def main():
    """Demo the MathAgent"""
    global x
    print(f"Initial x: {x}")
    
    # Create the math agent
    agent = MathAgent(stream=True)
    
    # Run a conversation
    result = agent.run_conversation(
        "Add 3 to x, then multiply by 4", 
        max_turns=10
    )
    
    print(f"\nFinal x: {x}")
    print(f"Agent memory x: {agent.get_current_x()}")

if __name__ == "__main__":
    main()