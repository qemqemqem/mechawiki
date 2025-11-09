"""
MechaWiki Flask Application.

Main Flask app that serves the API and manages agent lifecycle.
"""
import os
import logging
from flask import Flask
from flask_cors import CORS

# Set up logging - will be enhanced with file handlers after config loads
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
from .config import agent_config, WIKICONTENT_PATH
log_manager = init_log_manager(agent_config.logs_dir)

# Set up file-based debug logging for server
def setup_server_debug_logging():
    """Add file handler to root logger for server-wide debug logging."""
    server_debug_file = agent_config.debug_logs_dir / "server.log"
    file_handler = logging.FileHandler(server_debug_file, mode='a')
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    logging.getLogger().addHandler(file_handler)
    logger.info(f"🔍 Server debug logging enabled: {server_debug_file}")

setup_server_debug_logging()

# Initialize cost tracker
from .cost_tracker import init_cost_tracker
cost_tracker = init_cost_tracker(agent_config.logs_dir.parent)  # agents/ directory

# Initialize agent manager
from .agent_manager import agent_manager

# Function to initialize agents (called from run_server, not at module level)
def init_and_start_agents():
    """Initialize and start agents. Called once from run_server()."""
    from .init_agents import start_agents
    
    logger.info("🤖 Loading agents...")
    start_agents(agent_manager)
    
    # Start watching existing agents
    for agent in agent_config.list_agents():
        log_file = agent_config.logs_dir / f"agent_{agent['id']}.jsonl"
        if log_file.exists():
            log_manager.start_watching_agent(agent['id'], str(log_file), agent.get('config'))

# Import routes (after app creation to avoid circular imports)
from . import agents, files, health

# Register blueprints
app.register_blueprint(agents.bp)
app.register_blueprint(files.bp)
app.register_blueprint(health.bp)

logger.info("🏰 MechaWiki server initialized")


def run_server(host='localhost', port=5000, debug=True):
    """Run the Flask development server."""
    # Initialize agents once at startup
    # In debug mode, we disable the reloader to prevent agents from restarting
    # on every code change (frontend has its own Vite reloader)
    try:
        init_and_start_agents()
    except Exception as e:
        logger.error("=" * 80)
        logger.error("❌ CRITICAL ERROR DURING AGENT INITIALIZATION")
        logger.error("=" * 80)
        logger.error(f"Error: {type(e).__name__}: {e}")
        logger.error("=" * 80)
        logger.error("Server startup failed. Fix the error and restart.")
        logger.error("=" * 80)
        raise  # Re-raise to crash the process
    
    logger.info(f"🚀 Starting server on {host}:{port}")
    # Disable reloader to prevent agent restarts on Python file changes
    # Frontend has Vite for hot reloading, backend can be manually restarted
    app.run(host=host, port=port, debug=debug, threaded=True, use_reloader=False)


if __name__ == '__main__':
    run_server()

