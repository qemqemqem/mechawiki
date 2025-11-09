"""
Interactive tools for InteractiveAgent.

These tools allow agents to pause and wait for user input.
"""
from typing import Dict, Any


# Special sentinel value to signal waiting for input
class WaitingForInput:
    """Sentinel to indicate agent should wait for user input."""
    def __init__(self, prompt: str = "Waiting for user input..."):
        self.prompt = prompt


def wait_for_user(prompt: str = "What would you like to do?") -> WaitingForInput:
    """
    Pause and wait for user input.
    
    This tool causes the agent to yield a waiting_for_input status event,
    which breaks the current turn and waits for a user_message to be added
    to the log before continuing.
    
    Parameters
    ----------
    prompt : str
        Message to display while waiting (optional, for context)
    
    Returns
    -------
    WaitingForInput
        Sentinel object that AgentRunner will recognize
    
    Examples
    --------
    Use this when you want the user to make a choice or provide input:
    
    >>> wait_for_user("Do you want to continue the story?")
    >>> wait_for_user("What should the hero do next?")
    """
    return WaitingForInput(prompt=prompt)


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

