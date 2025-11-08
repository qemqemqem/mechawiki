"""
MechaWiki Flask Application.

Main Flask app that serves the API and manages agent lifecycle.
"""
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
from .config import LOGS_DIR, agent_config
log_manager = init_log_manager(LOGS_DIR)

# Start watching existing agents
for agent in agent_config.list_agents():
    log_file = LOGS_DIR / f"agent_{agent['id']}.jsonl"
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
    logger.info(f"🚀 Starting server on {host}:{port}")
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == '__main__':
    run_server()

