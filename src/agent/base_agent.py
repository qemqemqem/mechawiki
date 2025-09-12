"""
Base Agent class for litellm tool use based agents
"""
import json
import litellm
from typing import Dict, List, Callable, Any, Optional


class BaseAgent:
    """
    Modular agent that uses litellm for tool use with streaming support.
    
    Different agents can inherit from this and customize:
    - Available tools
    - System prompt
    - Memory/context manipulation
    - Tool execution logic
    """
    
    def __init__(
        self, 
        model: str = "claude-3-5-haiku-20241022",
        system_prompt: str = "You are a helpful AI assistant.",
        tools: Optional[List[Dict]] = None,
        available_functions: Optional[Dict[str, Callable]] = None,
        memory: Optional[Dict[str, Any]] = None,
        stream: bool = True
    ):
        """
        Initialize the base agent.
        
        Args:
            model: LLM model to use (any litellm supported model)
            system_prompt: System prompt for the agent
            tools: List of tool definitions in OpenAI format
            available_functions: Dict mapping tool names to callable functions
            memory: Dict to store agent memory/context 
            stream: Whether to stream responses
        """
        self.model = model
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.available_functions = available_functions or {}
        self.memory = memory or {}
        self.stream = stream
        self.messages = []
        
    def add_tool(self, tool_def: Dict, function: Callable):
        """Add a single tool to the agent."""
        self.tools.append(tool_def)
        self.available_functions[tool_def["function"]["name"]] = function
    
    def set_system_prompt(self, prompt: str):
        """Update the system prompt."""
        self.system_prompt = prompt
    
    def get_memory(self, key: str, default=None):
        """Get value from agent memory."""
        return self.memory.get(key, default)
    
    def set_memory(self, key: str, value: Any):
        """Set value in agent memory."""
        self.memory[key] = value
    
    def update_memory(self, updates: Dict[str, Any]):
        """Update multiple memory values."""
        self.memory.update(updates)
    
    def reset_conversation(self):
        """Clear the conversation history."""
        self.messages = []
    
    def add_user_message(self, content: str):
        """Add a user message to the conversation."""
        self.messages.append({"role": "user", "content": content})
    
    def _execute_tool(self, tool_call: Dict) -> str:
        """
        Execute a single tool call. Override in subclasses for custom logic.
        
        Args:
            tool_call: Tool call dict with id, function name, and arguments
            
        Returns:
            Result string to add to conversation
        """
        function_name = tool_call["function"]["name"]
        function_args = json.loads(tool_call["function"]["arguments"])
        
        if function_name not in self.available_functions:
            return f"Error: Tool {function_name} not available"
        
        try:
            function_to_call = self.available_functions[function_name]
            result = function_to_call(**function_args)
            return str(result)
        except Exception as e:
            return f"Error executing {function_name}: {str(e)}"
    
    def _handle_streaming_response(self, response) -> tuple[str, List[Dict]]:
        """
        Handle streaming response from litellm.
        
        Returns:
            Tuple of (collected_content, tool_calls)
        """
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
        return collected_content, tool_calls
    
    def _handle_non_streaming_response(self, response) -> tuple[str, List[Dict]]:
        """
        Handle non-streaming response from litellm.
        
        Returns:
            Tuple of (content, tool_calls)
        """
        message = response.choices[0].message
        content = message.content if message.content else ""
        tool_calls = message.tool_calls if hasattr(message, 'tool_calls') and message.tool_calls else []
        
        if content:
            print(content)
            
        # Convert tool_calls to our expected format if needed
        if tool_calls and hasattr(tool_calls[0], 'id'):
            # Convert from OpenAI format to dict format
            formatted_tool_calls = []
            for tc in tool_calls:
                formatted_tool_calls.append({
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                })
            tool_calls = formatted_tool_calls
        
        return content, tool_calls
    
    def run_conversation(self, initial_message: str, max_turns: int = 10) -> str:
        """
        Run a complete conversation with the agent.
        
        Args:
            initial_message: First user message
            max_turns: Maximum number of conversation turns
            
        Returns:
            Final response from the agent
        """
        # Add initial user message
        self.add_user_message(initial_message)
        
        for turn in range(max_turns):
            print(f"\n--- LLM Response (Turn {turn + 1}) ---")
            
            # Make LLM call
            response = litellm.completion(
                model=self.model,
                messages=self.messages,
                tools=self.tools if self.tools else None,
                tool_choice="auto" if self.tools else None,
                stream=self.stream
            )
            
            # Handle response based on streaming mode
            if self.stream:
                collected_content, tool_calls = self._handle_streaming_response(response)
            else:
                collected_content, tool_calls = self._handle_non_streaming_response(response)
            
            # Check for tool calls
            if tool_calls and any(tc.get("id") for tc in tool_calls):
                valid_tool_calls = [tc for tc in tool_calls if tc.get("id")]
                print(f"\n--- Executing {len(valid_tool_calls)} tool calls ---")
                
                # Add assistant message
                assistant_message = {
                    "role": "assistant",
                    "content": collected_content if collected_content else None,
                    "tool_calls": valid_tool_calls
                }
                self.messages.append(assistant_message)
                
                # Execute each tool call
                for tool_call in valid_tool_calls:
                    function_name = tool_call["function"]["name"]
                    function_args = json.loads(tool_call["function"]["arguments"])
                    
                    print(f"Calling {function_name} with args: {function_args}")
                    
                    # Execute tool (can be overridden by subclasses)
                    result = self._execute_tool(tool_call)
                    print(f"Result: {result}")
                    
                    # Add function result to conversation
                    self.messages.append({
                        "tool_call_id": tool_call["id"],
                        "role": "tool", 
                        "name": function_name,
                        "content": result
                    })
            else:
                # No tool calls, conversation complete
                # Add final assistant message
                if collected_content:
                    self.messages.append({
                        "role": "assistant", 
                        "content": collected_content
                    })
                return collected_content
        
        return "Max turns reached"
    
    def single_turn(self, message: str) -> str:
        """
        Single turn interaction - doesn't maintain conversation history.
        
        Args:
            message: User message
            
        Returns:
            Agent response
        """
        temp_messages = [{"role": "user", "content": message}]
        
        response = litellm.completion(
            model=self.model,
            messages=temp_messages,
            tools=self.tools if self.tools else None,
            tool_choice="auto" if self.tools else None,
            stream=False  # Single turn is always non-streaming
        )
        
        message_obj = response.choices[0].message
        return message_obj.content if message_obj.content else "No response"