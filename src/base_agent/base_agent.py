"""
Base Agent class for litellm tool use based agents.

Agents are generators that yield events instead of printing.
"""
import json
import litellm
from typing import Dict, List, Callable, Any, Optional, Generator


class ToolError(Exception):
    """Simple exception for tool execution errors."""
    pass

class EndConversation():
    """Simple object for ending the conversation."""
    pass

class ContextLengthExceeded(Exception):
    """Raised when conversation context exceeds 300,000 characters."""
    pass



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
        model: str = "claude-haiku-4-5-20251001",
        system_prompt: str = "You love good stories.",
        tools: Optional[List[Dict]] = None,
        memory: Optional[Dict[str, Any]] = None,
        stream: bool = True
    ):
        """
        Initialize the base agent.
        
        Args:
            model: LLM model to use (any litellm supported model)
            system_prompt: System prompt for the agent
            tools: List of tool definitions in OpenAI format
            memory: Dict to store agent memory/context 
            stream: Whether to stream responses
        """
        self.model = model
        self.tools = tools or []
        self.memory = memory or {}
        self.stream = stream
        self.messages = []
        
        # Add the built-in end() tool
        self._add_end_tool()
        
        # Enhance system prompt with auto-generated tool descriptions
        self.system_prompt = self._enhance_system_prompt(system_prompt)
        
    def add_tool(self, tool_def: Dict, function: Callable):
        """Add a single tool to the agent."""
        self.tools.append(tool_def)
    
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
    
    def _add_end_tool(self):
        """Add the built-in end() tool to terminate conversations."""
        def end(reason: str = "Task completed"):
            """End the conversation.
            
            Parameters
            ----------
            reason : str
                Reason for ending the conversation
            """
            return EndConversation()
        
        # Create tool definition using litellm helper
        end_tool = {"type": "function", "function": litellm.utils.function_to_dict(end)}
        self.tools.append(end_tool)
    
    def reset_conversation(self):
        """Clear the conversation history."""
        self.messages = []
    
    def add_user_message(self, content: str):
        """Add a user message to the conversation."""
        self.messages.append({"role": "user", "content": content})
    
    def _get_context_length(self) -> int:
        """Calculate total characters in conversation history."""
        total_chars = 0
        for msg in self.messages:
            # Count content
            if 'content' in msg:
                total_chars += len(str(msg['content']))
            # Count tool call arguments if present
            if 'tool_calls' in msg:
                for tc in msg['tool_calls']:
                    if 'function' in tc and 'arguments' in tc['function']:
                        total_chars += len(tc['function']['arguments'])
        return total_chars
    
    
    def advance_content(self, content: str, start_word: int):
        """Add new advance content and archive old content blocks to prevent context bloat.
        
        This system maintains a sliding window of story content by:
        1. Archiving older advance() content blocks beyond the configured limit
        2. Adding the new content block with metadata tags
        
        Args:
            content: The story content to add
            start_word: Starting word position of this content block
        """
        # Import config here to avoid circular imports
        try:
            import toml
            config = toml.load("config.toml")
            active_limit = config["story"]["active_content_blocks"]
        except Exception as e:
            print(f"Error loading config: {e}")
            active_limit = 2  # Fallback default
        
        # Find all existing advance content message indices
        advance_messages = []
        for i, msg in enumerate(self.messages):
            if msg.get("_advance_content", False):
                advance_messages.append(i)
        
        # Archive older advance messages (keep only last N-1 active to make room for new one)
        if len(advance_messages) >= active_limit:
            messages_to_archive = advance_messages[:-(active_limit-1)]
            
            for msg_idx in messages_to_archive:
                original_start = self.messages[msg_idx].get("_start_word", 0)
                self.messages[msg_idx]["content"] = f"""Content starting at word {original_start}:

[Content removed for length reasons. Use advance() to view current content]"""
        
        # Add new advance message with metadata
        new_msg = {
            "role": "user",
            "content": f"""Content starting at word {start_word}:

{content}""",
            "_advance_content": True,
            "_start_word": start_word
        }
        self.messages.append(new_msg)
    
    def _post_tool_execution_hook(self):
        """Hook for subclasses to override for post-tool-execution processing.
        
        Called after all tool calls in a turn have been executed and their
        results added to the conversation. Override in subclasses to add
        custom behavior like content processing, state updates, etc.
        """
        pass
    
    def _generate_tools_description(self) -> str:
        """Generate a description of available tools from their definitions."""
        import inspect
        
        if not self.tools:
            return "No tools available."
        
        descriptions = ["Available tools:"]
        descriptions.append("=" * 50)
        
        for i, tool in enumerate(self.tools):
            if tool.get("type") == "function":
                func_def = tool.get("function", {})
                name = func_def.get("name", "unknown")
                
                # Try to get full docstring from the actual function
                full_description = "No description available"
                if "_function" in tool:
                    actual_function = tool["_function"]
                    docstring = inspect.getdoc(actual_function)
                    if docstring:
                        full_description = docstring.strip()
                else:
                    # Fallback to the basic description from function_to_dict
                    full_description = func_def.get("description", "No description available")
                
                # Extract parameters for signature
                parameters = func_def.get("parameters", {}).get("properties", {})
                param_names = list(parameters.keys())
                param_str = ", ".join(param_names) if param_names else ""
                
                # Add separator between tools (except before first tool)
                if i > 0:
                    descriptions.append("")
                
                # Format with clear structure
                descriptions.append(f"🔧 {name}({param_str})")
                descriptions.append("-" * (len(name) + len(param_str) + 4))
                descriptions.append(full_description)
        
        return "\n".join(descriptions)
    
    def _enhance_system_prompt(self, base_prompt: str) -> str:
        """Enhance system prompt with auto-generated tool descriptions."""
        tools_desc = self._generate_tools_description()
        
        # # If the prompt already contains "Available tools:", replace that section
        # if "Available tools:" in base_prompt:
        #     # Split on the tools section and replace it
        #     parts = base_prompt.split("Available tools:")
        #     if len(parts) > 1:
        #         # Find the end of the tools section (next paragraph or end)
        #         after_tools = parts[1]
        #         next_section_start = after_tools.find("\n\n")
        #         if next_section_start != -1:
        #             # There's content after the tools section
        #             after_section = after_tools[next_section_start:]
        #             return f"{parts[0]}{tools_desc}{after_section}"
        #         else:
        #             # Tools section is at the end
        #             return f"{parts[0]}{tools_desc}"
            
        # If no tools section exists, append it
        return f"{base_prompt}\n\n{tools_desc}"
    
    def _execute_tool(self, tool_call: Dict) -> Any:
        """
        Execute a single tool call. Override in subclasses for custom logic.
        
        Tool errors are caught and returned as error results (not exceptions),
        so the agent can handle them gracefully.
        
        Args:
            tool_call: Tool call dict with id, function name, and arguments
            
        Returns:
            Result (can be any type, including EndConversation signal)
            or dict with 'error' and 'success' fields for tool errors
        """
        function_name = tool_call["function"]["name"]
        function_args = json.loads(tool_call["function"]["arguments"])
        
        # Find the tool definition and get the function
        function_to_call = None
        for tool in self.tools:
            if tool.get("function", {}).get("name") == function_name:
                function_to_call = tool.get("_function")
                break
        
        if function_to_call is None:
            # Tool not found - return error result
            return {
                "error": f"Tool {function_name} not available",
                "success": False
            }
        
        try:
            result = function_to_call(**function_args)
            
            # Check if result is EndConversation signal
            if isinstance(result, EndConversation):
                return result  # Return the signal directly
            
            return result  # Return the result directly
            
        except Exception as e:
            # Tool error - return as error result (not exception)
            # This allows the agent to see and respond to errors
            return {
                "error": str(e),
                "success": False,
                "tool": function_name
            }
    
    def _handle_streaming_response(self, response) -> Generator[Dict, None, tuple[str, str, List[Dict]]]:
        """
        Handle streaming response from litellm - yields events.
        
        Yields:
            Events: text_token, thinking_token, thinking_start, thinking_end
            
        Returns:
            Tuple of (collected_content, collected_thinking, tool_calls)
        """
        collected_content = ""
        collected_thinking = ""
        tool_calls = []
        thinking_active = False
        
        for chunk in response:
            # Try to extract thinking (Claude extended thinking)
            thinking_content = self._extract_thinking_from_chunk(chunk)
            if thinking_content:
                if not thinking_active:
                    yield {'type': 'thinking_start'}
                    thinking_active = True
                yield {'type': 'thinking_token', 'content': thinking_content}
                collected_thinking += thinking_content
                continue  # Don't process as regular content
            
            # Regular content
            if chunk.choices[0].delta.content:
                # If we were thinking and now have content, end thinking
                if thinking_active:
                    yield {'type': 'thinking_end'}
                    thinking_active = False
                
                content = chunk.choices[0].delta.content
                yield {'type': 'text_token', 'content': content}
                collected_content += content
            
            # Handle tool calls (fully formed from litellm)
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
        
        # End thinking if still active
        if thinking_active:
            yield {'type': 'thinking_end'}
        
        return collected_content, collected_thinking, tool_calls
    
    def _extract_thinking_from_chunk(self, chunk) -> Optional[str]:
        """
        Extract thinking/reasoning content from LLM response chunk.
        
        Supports Claude extended thinking via reasoning_content field.
        """
        delta = chunk.choices[0].delta
        
        # Check for Claude extended thinking
        if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
            return delta.reasoning_content
        
        # Future: Could parse <thinking> tags if needed
        
        return None
    
    def _handle_non_streaming_response(self, response) -> tuple[str, str, List[Dict]]:
        """
        Handle non-streaming response from litellm.
        
        Returns:
            Tuple of (content, thinking, tool_calls)
        """
        # For non-streaming, we don't have thinking extraction yet
        # Just return the content and empty thinking
        choice = response.choices[0]
        content = choice.message.content or ""
        tool_calls = []
        
        if hasattr(choice.message, 'tool_calls') and choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                tool_calls.append({
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                })
        
        return content, "", tool_calls
    
    def run_forever(self, initial_message: str, max_turns: int = 3) -> Generator[Dict, None, None]:
        """
        Run a conversation with the agent - yields events.
        
        This is a generator that yields events for streaming tokens, tool calls,
        and tool results. AgentRunner consumes these events and logs them.
        
        Args:
            initial_message: First user message
            max_turns: Maximum turns (None = run forever, int = limit turns)
            
        Yields:
            Events: text_token, thinking_token, tool_call, tool_result, status
            
        Raises:
            ContextLengthExceeded: If conversation exceeds 300,000 characters
        """
        # Add initial message
        self.add_user_message(initial_message)
        
        turn = 0
        while True:
            turn += 1
            
            # Check turn limit
            if max_turns is not None and turn > max_turns:
                return  # Generator exits
            
            # Check context length BEFORE making LLM call
            context_length = self._get_context_length()
            if context_length > 300000:
                raise ContextLengthExceeded(
                    f"Context length is {context_length} characters (limit: 300,000)"
                )
            
            # Make LLM call (Haiku 4.5 has built-in thinking)
            response = litellm.completion(
                model=self.model,
                messages=self.messages,
                tools=self.tools if self.tools else None,
                tool_choice="auto" if self.tools else None,
                stream=self.stream,
                temperature=1.0
            )
            
            # Handle response - yields events from streaming
            if self.stream:
                # _handle_streaming_response is now a generator
                stream_gen = self._handle_streaming_response(response)
                collected_content = ""
                collected_thinking = ""
                tool_calls = []
                
                try:
                    while True:
                        event = next(stream_gen)
                        yield event  # Forward events to caller
                except StopIteration as e:
                    # Generator returned final values
                    collected_content, collected_thinking, tool_calls = e.value
            else:
                collected_content, collected_thinking, tool_calls = self._handle_non_streaming_response(response)
            
            # Build assistant message for conversation history
            assistant_message = {
                "role": "assistant",
                "content": collected_content if collected_content else None
            }
            
            # Add thinking if present
            if collected_thinking:
                assistant_message["thinking"] = collected_thinking
            
            # Check for tool calls
            if tool_calls and any(tc.get("id") for tc in tool_calls):
                valid_tool_calls = [tc for tc in tool_calls if tc.get("id")]
                
                # Add tool_calls to assistant message
                assistant_message["tool_calls"] = valid_tool_calls
                self.messages.append(assistant_message)
                
                # Execute each tool call
                for tool_call in valid_tool_calls:
                    function_name = tool_call["function"]["name"]
                    function_args = json.loads(tool_call["function"]["arguments"])
                    
                    # Yield tool_call event
                    yield {
                        'type': 'tool_call',
                        'tool': function_name,
                        'args': function_args
                    }
                    
                    # Execute tool (errors become error results)
                    raw_result = self._execute_tool(tool_call)
                    
                    # Check if tool returned EndConversation signal
                    if isinstance(raw_result, EndConversation):
                        yield {
                            'type': 'status',
                            'status': 'ended',
                            'reason': 'Agent called end()'
                        }
                        return  # Exit generator
                    
                    # Check if tool returned WaitingForInput signal
                    if isinstance(raw_result, dict) and raw_result.get('_waiting_for_input'):
                        # Yield status event for waiting
                        yield {
                            'type': 'status',
                            'status': 'waiting_for_input',
                            'message': raw_result.get('prompt', 'Waiting for user input')
                        }
                        # Also yield the tool_result
                        yield {
                            'type': 'tool_result',
                            'tool': function_name,
                            'result': raw_result
                        }
                        # Add to conversation
                        result_content = json.dumps(raw_result)
                        self.messages.append({
                            "tool_call_id": tool_call["id"],
                            "role": "tool",
                            "name": function_name,
                            "content": result_content
                        })
                        # Break this turn - wait for user input
                        return
                    
                    # Yield tool_result event
                    yield {
                        'type': 'tool_result',
                        'tool': function_name,
                        'result': raw_result
                    }
                    
                    # Add function result to conversation
                    # Convert result to string for conversation (but event has full result)
                    if isinstance(raw_result, dict):
                        result_content = json.dumps(raw_result)
                    else:
                        result_content = str(raw_result)
                    
                    self.messages.append({
                        "tool_call_id": tool_call["id"],
                        "role": "tool", 
                        "name": function_name,
                        "content": result_content
                    })

                # If the last message isn't a user message, add a user message
                if self.messages[-1]["role"] != "user":
                    self.messages.append({
                        "role": "user",
                        "content": "Please continue."
                    })
                
                # Hook for subclasses to perform post-tool-execution processing
                self._post_tool_execution_hook()
            else:
                # No tool calls - add assistant message and continue
                if collected_content or collected_thinking:
                    self.messages.append(assistant_message)
    