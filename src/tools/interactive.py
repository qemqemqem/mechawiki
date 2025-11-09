"""
Interactive tools for InteractiveAgent.

These tools allow agents to pause and wait for user input.
"""
from typing import Dict, Any


# Special sentinel values for agent control flow
class WaitingForInput:
    """Sentinel to indicate agent should wait for user input."""
    pass


class Finished:
    """Sentinel to indicate agent has completed its task."""
    pass


def wait_for_user() -> WaitingForInput:
    """
    Pass control back to the user for input.
    
    This tool pauses the agent's turn and transfers control back to the user.
    The agent will wait for the user to provide their next message before
    continuing execution. 
    
    IMPORTANT: This tool does NOT emit any text to the user. Any text you want
    the user to see should be included in your assistant message BEFORE calling
    this tool. This tool simply signals that you are ready to receive user input.
    
    Returns
    -------
    WaitingForInput
        Sentinel object that AgentRunner will recognize
    
    Examples
    --------
    Present narrative text first, then call this tool to get user input:
    
    >>> # Agent emits text first, then calls wait_for_user()
    >>> # "You stand at a crossroads. The left path leads to mountains,
    >>> #  the right path leads to a dark forest. What do you do?"
    >>> wait_for_user()
    """
    return WaitingForInput()


def get_session_state() -> Dict[str, Any]:
    """
    Get current session state information.
    
    Returns
    -------
    dict
        Session state (story progress, active quests, etc.)
    
    Note
    ----
    Currently returns minimal state. Can be expanded later to track
    story progress, character state, active quests, etc.
    """
    # TODO: Implement proper session state tracking
    return {
        "success": True,
        "session": "active",
        "message": "Session state tracking not yet implemented"
    }


def done() -> Finished:
    """
    Signal that the agent has completed its task.
    
    This tool marks the agent's work as finished and transitions the agent
    to the "finished" state. The agent will stop running after calling this tool.
    
    IMPORTANT: This tool does NOT emit any text to the user. Any final message
    or summary you want the user to see should be included in your assistant
    message BEFORE calling this tool. This tool simply signals completion.
    
    Returns
    -------
    Finished
        Sentinel object that AgentRunner will recognize
    
    Examples
    --------
    Present your final message first, then call this tool to finish:
    
    >>> # Agent emits final summary first, then calls done()
    >>> # "The story is complete! I've written 5 chapters covering the hero's
    >>> #  journey from the village to defeating the dragon. Hope you enjoy!"
    >>> done()
    """
    return Finished()

