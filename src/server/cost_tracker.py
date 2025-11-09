"""
Session-wide cost tracking with milestone logging.

Tracks cumulative costs across all agents in a session and logs
milestones to costs.log when crossing dollar thresholds.
"""
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional


class CostTracker:
    """
    Tracks session-wide LLM costs with milestone logging.
    
    Logs to costs.log whenever cumulative cost crosses a dollar threshold.
    Thread-safe for use with multiple agents.
    """
    
    def __init__(self, session_dir: Path):
        """
        Initialize cost tracker.
        
        Args:
            session_dir: Path to session directory (where costs.log will be created)
        """
        self.session_dir = Path(session_dir)
        self.cost_log = self.session_dir / "costs.log"
        
        # Thread-safe cost tracking
        self._lock = threading.Lock()
        self._total_cost = 0.0
        self._last_logged_dollar = 0  # Track which dollar milestone we last logged
        
        # Per-agent tracking for stats
        self._agent_costs = {}  # agent_id -> cost
        
        # Initialize log file if it doesn't exist
        if not self.cost_log.exists():
            self.cost_log.write_text("")
    
    def add_cost(self, agent_id: str, cost: float):
        """
        Add cost from an agent and check for dollar milestones.
        
        Args:
            agent_id: Agent that incurred the cost
            cost: Cost in USD to add
        """
        with self._lock:
            # Update totals
            self._total_cost += cost
            self._agent_costs[agent_id] = self._agent_costs.get(agent_id, 0.0) + cost
            
            # Check if we crossed a dollar milestone
            current_dollar = int(self._total_cost)
            if current_dollar > self._last_logged_dollar:
                # We crossed one or more dollar milestones
                self._log_milestone(current_dollar)
                self._last_logged_dollar = current_dollar
    
    def get_total_cost(self) -> float:
        """Get total session cost."""
        with self._lock:
            return self._total_cost
    
    def get_agent_cost(self, agent_id: str) -> float:
        """Get cost for specific agent."""
        with self._lock:
            return self._agent_costs.get(agent_id, 0.0)
    
    def get_stats(self) -> dict:
        """Get cost statistics."""
        with self._lock:
            return {
                "total_cost": round(self._total_cost, 6),
                "total_cost_dollars": f"${self._total_cost:.2f}",
                "agent_costs": {
                    agent_id: round(cost, 6) 
                    for agent_id, cost in self._agent_costs.items()
                }
            }
    
    def _log_milestone(self, dollar_amount: int):
        """Log a dollar milestone to costs.log."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if dollar_amount == 1:
            message = f"[{timestamp}] First dollar spent! Total: ${dollar_amount}.00\n"
        else:
            message = f"[{timestamp}] Another ${dollar_amount - self._last_logged_dollar} spent. Total spend this session: ${dollar_amount}.00\n"
        
        with open(self.cost_log, 'a') as f:
            f.write(message)


# Global cost tracker instance (initialized by server)
_cost_tracker: Optional[CostTracker] = None


def init_cost_tracker(session_dir: Path) -> CostTracker:
    """Initialize the global cost tracker."""
    global _cost_tracker
    _cost_tracker = CostTracker(session_dir)
    return _cost_tracker


def get_cost_tracker() -> Optional[CostTracker]:
    """Get the global cost tracker instance."""
    return _cost_tracker

