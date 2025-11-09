"""
MechaWiki Flask Application.

Main Flask app that serves the API and manages agent lifecycle.
"""
import os
import logging
from flask import Flask
from flask_cors import CORS

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Initialize log manager
from .log_watcher import init_log_manager
from .config import session_config
log_manager = init_log_manager(session_config.logs_dir)

# Initialize agent manager
from .agent_manager import agent_manager

# Function to initialize agents (called from run_server, not at module level)
def init_and_start_agents():
    """Initialize and start agents. Called once from run_server()."""
    logger.info("🤖 Initializing test agents...")
    from .init_agents import init_test_agents, start_test_agents
    init_test_agents()
    start_test_agents(agent_manager)
    
    # Start watching existing agents
    for agent in session_config.list_agents():
        log_file = session_config.logs_dir / f"agent_{agent['id']}.jsonl"
        if log_file.exists():
            log_manager.start_watching_agent(agent['id'], str(log_file))

# Import routes (after app creation to avoid circular imports)
from . import agents, files, health

# Register blueprints
app.register_blueprint(agents.bp)
app.register_blueprint(files.bp)
app.register_blueprint(health.bp)

logger.info("🏰 MechaWiki server initialized")


def run_server(host='localhost', port=5000, debug=True):
    """Run the Flask development server."""
    # Initialize agents here (not at module level) to avoid double-init in debug mode
    # Only run when:
    # - Not in debug mode (run once), OR
    # - In debug mode AND in the reloader child process (WERKZEUG_RUN_MAIN='true')
    # This prevents running in BOTH the initial process AND the child process
    if not debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        init_and_start_agents()
    
    logger.info(f"🚀 Starting server on {host}:{port}")
    app.run(host=host, port=port, debug=debug, threaded=True, use_reloader=debug)


if __name__ == '__main__':
    run_server()

