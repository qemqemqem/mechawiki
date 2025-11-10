"""
Base Agent class for litellm tool use based agents.

Agents are generators that yield events instead of printing.
"""
import json
import litellm
import logging
from typing import Dict, List, Callable, Any, Optional, Generator

logger = logging.getLogger(__name__)


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
        stream: bool = True,
        agent_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the base agent.
        
        Args:
            model: LLM model to use (any litellm supported model)
            system_prompt: System prompt for the agent
            tools: List of tool definitions in OpenAI format
            memory: Dict to store agent memory/context 
            stream: Whether to stream responses
            agent_config: Optional agent configuration dict (for subclass use)
        """
        self.model = model
        self.tools = tools or []
        self.memory = memory or {}
        self.stream = stream
        self.messages = []
        
        # Log path for git commits (set by AgentRunner)
        self.log_path = None
        
        # Cost tracking
        self.total_cost = 0.0
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.turn_count = 0
        
        # Add the built-in end() tool
        self._add_end_tool()
        
        # Add the built-in report_issue() tool
        self._add_report_issue_tool()
        
        # Enhance system prompt with auto-generated tool descriptions
        self.system_prompt = self._enhance_system_prompt(system_prompt)
        
        logger.debug(f"🤖 BaseAgent initialized: model={model}, stream={stream}, tools={len(self.tools)}")
        
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
    
    def get_cost_stats(self) -> Dict[str, Any]:
        """Get cost and usage statistics for this agent.
        
        Returns:
            Dict with total_cost, total_prompt_tokens, total_completion_tokens, 
            total_tokens, turn_count, and average_cost_per_turn
        """
        total_tokens = self.total_prompt_tokens + self.total_completion_tokens
        avg_cost = self.total_cost / self.turn_count if self.turn_count > 0 else 0.0
        
        return {
            "total_cost": round(self.total_cost, 6),
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": total_tokens,
            "turn_count": self.turn_count,
            "average_cost_per_turn": round(avg_cost, 6)
        }
    
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
        end_tool = {"type": "function", "function": litellm.utils.function_to_dict(end), "_function": end}
        self.tools.append(end_tool)
    
    def _add_report_issue_tool(self):
        """Add the built-in report_issue() tool for reporting bugs or impossible tasks."""
        def report_issue(issue_str: str):
            """Report a bug or issue encountered during operation.
            
            Call this tool when you believe you have encountered a bug in the system,
            or when the system prompt has instructed you to do something that is 
            impossible or cannot be completed with the available tools.
            
            Parameters
            ----------
            issue_str : str
                Description of the issue, bug, or impossible task encountered
            """
            return "Issue logged successfully. The developer will review this report. Please carry on as best as possible despite this issue."
        
        # Create tool definition using litellm helper
        report_issue_tool = {"type": "function", "function": litellm.utils.function_to_dict(report_issue), "_function": report_issue}
        self.tools.append(report_issue_tool)
    
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
    
    def _create_helpful_json_error(self, function_name: str, raw_args: str, json_error: json.JSONDecodeError) -> str:
        """
        Create a helpful, succinct error message for JSON parsing failures in tool calls.
        
        Args:
            function_name: Name of the tool that was called
            raw_args: The raw argument string that failed to parse
            json_error: The JSONDecodeError that was raised
            
        Returns:
            A clear, actionable error message
        """
        # Check if JSON is incomplete (missing closing brace/bracket)
        stripped = raw_args.strip()
        is_incomplete = False
        
        if stripped and not stripped.endswith('}') and not stripped.endswith(']'):
            is_incomplete = True
        elif stripped.count('{') > stripped.count('}'):
            is_incomplete = True
        elif stripped.count('[') > stripped.count(']'):
            is_incomplete = True
        
        # Try to find the tool schema to identify required parameters
        tool_schema = None
        for tool in self.tools:
            if tool.get("type") == "function" and tool.get("function", {}).get("name") == function_name:
                tool_schema = tool.get("function", {})
                break
        
        # Build error message
        if is_incomplete:
            msg = f"ERROR: Incomplete JSON arguments for tool '{function_name}'.\n"
            msg += f"The arguments appear to be cut off or missing closing braces.\n"
            
            # Show what was received (truncated)
            preview = raw_args[:150] + "..." if len(raw_args) > 150 else raw_args
            msg += f"Received: {preview}\n"
            
            # If we have the schema, show required parameters
            if tool_schema:
                params = tool_schema.get("parameters", {})
                required = params.get("required", [])
                if required:
                    msg += f"Required parameters: {', '.join(required)}\n"
            
            msg += "Please retry the tool call with complete JSON arguments."
        else:
            # Other JSON error (malformed syntax, etc.)
            msg = f"ERROR: Malformed JSON arguments for tool '{function_name}'.\n"
            msg += f"JSON parse error: {str(json_error)}\n"
            
            # Show what was received (truncated)
            preview = raw_args[:150] + "..." if len(raw_args) > 150 else raw_args
            msg += f"Received: {preview}\n"
            msg += "Please retry the tool call with valid JSON syntax."
        
        return msg
    
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
            logger.error(f"❌ Tool not found: {function_name}")
            return {
                "error": f"Tool {function_name} not available",
                "success": False
            }
        
        try:
            logger.debug(f"🔧 Executing tool: {function_name}({function_args})")
            result = function_to_call(**function_args)
            
            # Check if result is EndConversation signal
            if isinstance(result, EndConversation):
                logger.info(f"🏁 Tool {function_name} returned EndConversation signal")
                return result  # Return the signal directly
            
            logger.debug(f"✅ Tool {function_name} completed successfully")
            return result  # Return the result directly
            
        except Exception as e:
            # Tool error - return as error result (not exception)
            # This allows the agent to see and respond to errors
            logger.error(f"❌ Tool {function_name} raised exception: {e}")
            return {
                "error": str(e),
                "success": False,
                "tool": function_name
            }
    
    def _handle_streaming_response(self, response) -> Generator[Dict, None, tuple[str, str, List[Dict], Dict]]:
        """
        Handle streaming response from litellm - yields events.
        
        Yields:
            Events: text_token, thinking_token, thinking_start, thinking_end
            
        Returns:
            Tuple of (collected_content, collected_thinking, tool_calls, usage_info)
        """
        collected_content = ""
        collected_thinking = ""
        tool_calls = []
        thinking_active = False
        usage_info = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        
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
            
            # Capture usage info from chunks (usually in final chunk)
            if hasattr(chunk, 'usage') and chunk.usage:
                usage_info["prompt_tokens"] = getattr(chunk.usage, 'prompt_tokens', 0)
                usage_info["completion_tokens"] = getattr(chunk.usage, 'completion_tokens', 0)
                usage_info["total_tokens"] = getattr(chunk.usage, 'total_tokens', 0)
            
            # Check if streaming is complete
            if chunk.choices[0].finish_reason:
                break
        
        # End thinking if still active
        if thinking_active:
            yield {'type': 'thinking_end'}
        
        return collected_content, collected_thinking, tool_calls, usage_info
    
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
    
    def _validate_and_repair_conversation_history(self) -> None:
        """
        Validate and repair conversation history to ensure Anthropic API requirements.
        
        Anthropic requires that every assistant message with tool_calls (tool_use) 
        must be immediately followed by tool messages (tool_result) with matching IDs.
        
        This method modifies self.messages in-place to:
        1. Collect all tool_results and map them to their tool_calls
        2. Reconstruct history with tool_results in correct positions
        3. Add dummy tool_results for any orphaned tool_calls
        4. Validate tool_result content format
        """
        if not self.messages:
            return
        
        repairs_made = 0
        results_rearranged = 0
        orphaned_results_removed = 0
        
        # FIRST PASS: Collect all tool_results and validate their content
        tool_results_by_id = {}  # Map tool_call_id -> tool_result message
        for msg in self.messages:
            if msg.get("role") == "tool":
                msg_copy = msg.copy()
                content = msg_copy.get("content", "")
                
                # Check if content is a string
                if not isinstance(content, str):
                    logger.warning(f"⚠️ Tool result content is not a string: {type(content)}. Converting to string.")
                    msg_copy["content"] = str(content)
                    repairs_made += 1
                
                # Check if content is valid (not empty, not too large)
                content = msg_copy.get("content", "")
                if not content or len(content) < 2:
                    logger.warning(f"⚠️ Tool result has empty or invalid content. Adding error message.")
                    msg_copy["content"] = json.dumps({"error": "Tool result content was empty or invalid"})
                    repairs_made += 1
                
                # Truncate if too large (> 100KB)
                max_content_size = 100000
                if len(content) > max_content_size:
                    logger.warning(f"⚠️ Tool result content too large ({len(content)} chars). Truncating to {max_content_size} chars.")
                    msg_copy["content"] = content[:max_content_size] + "\n... [truncated]"
                    repairs_made += 1
                
                # Verify it's valid JSON (Anthropic expects JSON in tool results)
                content = msg_copy.get("content", "")
                try:
                    json.loads(content)
                except json.JSONDecodeError:
                    logger.warning(f"⚠️ Tool result content is not valid JSON. Wrapping in JSON object.")
                    msg_copy["content"] = json.dumps({"result": content})
                    repairs_made += 1
                
                # Store the validated tool_result
                tool_call_id = msg_copy.get("tool_call_id")
                if tool_call_id:
                    tool_results_by_id[tool_call_id] = msg_copy
        
        # SECOND PASS: Build a map of which tool_call_ids exist
        valid_tool_call_ids = set()
        for msg in self.messages:
            if msg.get("role") == "assistant" and msg.get("tool_calls"):
                for tc in msg.get("tool_calls", []):
                    if tc.get("id"):
                        valid_tool_call_ids.add(tc.get("id"))
        
        # THIRD PASS: Reconstruct history with tool_results in correct positions
        repaired_history = []
        i = 0
        
        while i < len(self.messages):
            msg = self.messages[i]
            
            # Skip tool messages - they'll be reinserted in correct positions
            if msg.get("role") == "tool":
                i += 1
                continue
            
            # Check if this is an assistant message with tool_calls
            if msg.get("role") == "assistant" and msg.get("tool_calls"):
                # Add the assistant message
                repaired_history.append(msg)
                
                tool_calls = msg.get("tool_calls", [])
                tool_call_ids = [tc.get("id") for tc in tool_calls if tc.get("id")]
                
                # Add tool_results immediately after, in the correct order
                for tool_call_id in tool_call_ids:
                    if tool_call_id in tool_results_by_id:
                        # Found the tool_result - add it in correct position
                        repaired_history.append(tool_results_by_id[tool_call_id])
                        # Mark this result as used
                        del tool_results_by_id[tool_call_id]
                    else:
                        # Missing tool_result - add dummy
                        tool_name = "unknown"
                        for tc in tool_calls:
                            if tc.get("id") == tool_call_id:
                                tool_name = tc.get("function", {}).get("name", "unknown")
                                break
                        
                        logger.warning(
                            f"⚠️ Found orphaned tool_call without tool_result: {tool_call_id} ({tool_name}). "
                            "Adding dummy tool_result to satisfy API requirements."
                        )
                        repairs_made += 1
                        
                        repaired_history.append({
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "name": tool_name,
                            "content": json.dumps({
                                "error": "Tool result was lost during history loading. This is a repair operation.",
                                "repaired": True,
                                "tool_name": tool_name
                            })
                        })
            else:
                # Regular message (user, assistant without tool_calls, etc.)
                repaired_history.append(msg)
            
            i += 1
        
        # Count how many tool_results we rearranged
        # (Original position count minus results still in tool_results_by_id)
        original_tool_result_count = sum(1 for msg in self.messages if msg.get("role") == "tool")
        results_rearranged = original_tool_result_count - len(tool_results_by_id)
        
        # Any tool_results left in tool_results_by_id are truly orphaned (no matching tool_call)
        for tool_call_id, orphaned_result in tool_results_by_id.items():
            if tool_call_id not in valid_tool_call_ids:
                logger.warning(
                    f"⚠️ Found orphaned tool_result with tool_call_id={tool_call_id}. "
                    "No matching tool_call found anywhere. Removing."
                )
                orphaned_results_removed += 1
        
        # Log if we made any repairs
        total_changes = repairs_made + orphaned_results_removed
        if total_changes > 0 or results_rearranged > 0:
            logger.warning(
                f"🔧 Repaired conversation history: "
                f"rearranged {results_rearranged} tool_result(s), "
                f"added {repairs_made} dummy tool_result(s), "
                f"removed {orphaned_results_removed} orphaned tool_result(s) "
                f"({len(self.messages)} -> {len(repaired_history)} messages)"
            )
        else:
            logger.debug(f"✅ Conversation history validated: {len(self.messages)} messages, no repairs needed")
        
        # Update conversation history in-place
        self.messages = repaired_history
    
    def _handle_non_streaming_response(self, response) -> tuple[str, str, List[Dict], Dict]:
        """
        Handle non-streaming response from litellm.
        
        Returns:
            Tuple of (content, thinking, tool_calls, usage_info)
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
        
        # Extract usage info
        usage_info = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        if hasattr(response, 'usage') and response.usage:
            usage_info["prompt_tokens"] = getattr(response.usage, 'prompt_tokens', 0)
            usage_info["completion_tokens"] = getattr(response.usage, 'completion_tokens', 0)
            usage_info["total_tokens"] = getattr(response.usage, 'total_tokens', 0)
        
        return content, "", tool_calls, usage_info
    
    def run_forever(self, initial_message: Optional[str] = None, max_turns: int = 3) -> Generator[Dict, None, None]:
        """
        Run a conversation with the agent - yields events.
        
        This is a generator that yields events for streaming tokens, tool calls,
        and tool results. AgentRunner consumes these events and logs them.
        
        Args:
            initial_message: First user message (optional - None to continue without adding)
            max_turns: Maximum turns (None = run forever, int = limit turns)
            
        Yields:
            Events: text_token, thinking_token, tool_call, tool_result, status
            
        Raises:
            ContextLengthExceeded: If conversation exceeds 300,000 characters
        """
        # Add initial message if provided
        if initial_message is not None:
            self.add_user_message(initial_message)
        
        turn = 0
        while True:
            turn += 1
            
            # Check turn limit
            if max_turns is not None and turn > max_turns:
                return  # Generator exits
            
            # Check context length BEFORE making LLM call
            context_length = self._get_context_length()
            logger.debug(f"📏 Context length: {context_length} chars ({len(self.messages)} messages)")
            if context_length > 300000:
                logger.error(f"❌ Context length exceeded: {context_length} chars (limit: 300,000)")
                raise ContextLengthExceeded(
                    f"Context length is {context_length} characters (limit: 300,000)"
                )
            
            # Validate and repair conversation history (defensive programming)
            self._validate_and_repair_conversation_history()
            
            # Make LLM call (Haiku 4.5 has built-in thinking)
            response = litellm.completion(
                model=self.model,
                messages=self.messages,
                tools=self.tools if self.tools else None,
                tool_choice="auto" if self.tools else None,
                stream=self.stream,
                stream_options={'include_usage': True} if self.stream else None,
                temperature=1.0
            )
            
            # Store response for cost calculation later
            original_response = response
            
            # Handle response - yields events from streaming
            if self.stream:
                # _handle_streaming_response is now a generator
                stream_gen = self._handle_streaming_response(response)
                collected_content = ""
                collected_thinking = ""
                tool_calls = []
                usage_info = {}
                
                try:
                    while True:
                        event = next(stream_gen)
                        yield event  # Forward events to caller
                except StopIteration as e:
                    # Generator returned final values
                    collected_content, collected_thinking, tool_calls, usage_info = e.value
            else:
                collected_content, collected_thinking, tool_calls, usage_info = self._handle_non_streaming_response(response)
            
            # Track cost and token usage
            turn_prompt_tokens = usage_info.get("prompt_tokens", 0)
            turn_completion_tokens = usage_info.get("completion_tokens", 0)
            
            # Calculate cost using litellm utility (handles model-specific pricing)
            try:
                if self.stream:
                    # For streaming, use prompt/completion strings method
                    # (streaming response generator is consumed, can't reuse it)
                    prompt_text = " ".join([msg.get("content", "") for msg in self.messages if msg.get("role") == "user"])
                    turn_cost = litellm.completion_cost(
                        model=self.model,
                        prompt=prompt_text,
                        completion=collected_content
                    )
                else:
                    # For non-streaming, use the actual response object
                    turn_cost = litellm.completion_cost(completion_response=original_response)
            except Exception as e:
                logger.warning(f"Could not calculate cost: {e}")
                turn_cost = 0.0
            
            # Update cumulative tracking
            self.total_cost += turn_cost
            self.total_prompt_tokens += turn_prompt_tokens
            self.total_completion_tokens += turn_completion_tokens
            self.turn_count += 1
            
            # Log cost information
            logger.info(
                f"💰 Turn {self.turn_count} | Cost: ${turn_cost:.6f} | "
                f"Tokens: {turn_prompt_tokens}p + {turn_completion_tokens}c = {turn_prompt_tokens + turn_completion_tokens}t | "
                f"Total: ${self.total_cost:.6f}"
            )
            
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
                    
                    # Parse tool call arguments with error handling
                    try:
                        function_args = json.loads(tool_call["function"]["arguments"])
                    except json.JSONDecodeError as e:
                        # Malformed JSON from LLM - provide a helpful error message
                        logger.warning(f"⚠️ Malformed JSON in tool call {function_name}: {e}")
                        error_msg = self._create_helpful_json_error(
                            function_name, 
                            tool_call["function"]["arguments"],
                            e
                        )
                        
                        # Yield tool_call event with error
                        yield {
                            'type': 'tool_call',
                            'tool': function_name,
                            'args': None,
                            'error': error_msg
                        }
                        
                        # Create error result to send back to LLM
                        raw_result = {
                            'error': error_msg,
                            'success': False
                        }
                        
                        # Add tool result to messages
                        tool_result_message = {
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "content": json.dumps(raw_result)
                        }
                        self.messages.append(tool_result_message)
                        
                        # Yield tool_result event
                        yield {
                            'type': 'tool_result',
                            'tool': function_name,
                            'result': raw_result
                        }
                        
                        # Skip to next tool call
                        continue
                    
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
                            'reason': 'Agent called end()',
                            'source': 'base_agent.run_forever.end_conversation'
                        }
                        return  # Exit generator
                    
                    # Check if tool returned WaitingForInput signal
                    if isinstance(raw_result, dict) and raw_result.get('_waiting_for_input'):
                        # Yield status event for waiting
                        yield {
                            'type': 'status',
                            'status': 'waiting_for_input',
                            'message': raw_result.get('prompt', 'Waiting for user input'),
                            'source': 'base_agent.run_forever.waiting_for_input'
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
                    
                    # Check if tool returned Finished signal
                    if isinstance(raw_result, dict) and raw_result.get('_finished'):
                        # Yield status event for finished
                        yield {
                            'type': 'status',
                            'status': 'finished',
                            'message': raw_result.get('message', 'Task completed'),
                            'source': 'base_agent.run_forever.finished'
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
                        # Break this turn - agent is finished
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
    