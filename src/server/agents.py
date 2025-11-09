"""
Agent management endpoints.

Handles creating, listing, and controlling agents.
"""
import logging
import queue
from datetime import datetime
from pathlib import Path
from flask import Blueprint, jsonify, request, Response
from .config import session_config
from .log_watcher import log_manager
from .agent_manager import agent_manager
import json

logger = logging.getLogger(__name__)

bp = Blueprint('agents', __name__, url_prefix='/api/agents')


@bp.route('', methods=['GET'])
def list_agents():
    """List all agents with their current status."""
    agents = session_config.list_agents()
    
    # Enrich with status from logs
    enriched = []
    for agent in agents:
        agent_data = agent.copy()
        
        # Get status and last action from log
        status_info = log_manager.get_agent_status(agent['id'])
        agent_data.update(status_info)
        
        enriched.append(agent_data)
    
    return jsonify({"agents": enriched})


@bp.route('/create', methods=['POST'])
def create_agent():
    """Create a new agent."""
    data = request.json
    
    # Validate required fields
    required = ['name', 'type']
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Generate ID
    agent_id = f"{data['type'].lower()}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Create agent config
    agent_data = {
        "id": agent_id,
        "name": data['name'],
        "type": data['type'],
        "status": "stopped",  # Will be updated when agent starts
        "config": data.get('config', {})
    }
    
    try:
        agent_config = session_config.add_agent(agent_data)
        
        # Create empty log file
        log_file = session_config.logs_dir / f"agent_{agent_id}.jsonl"
        log_file.write_text('')
        
        # Start watching this agent's log
        log_manager.start_watching_agent(agent_id, str(log_file))
        
        # Start the agent instance (unpaused by default)
        wikicontent_path = Path.home() / "Dev" / "wikicontent"
        agent_manager.start_agent(
            agent_id=agent_id,
            agent_type=data['type'],
            log_file=log_file,
            wikicontent_path=wikicontent_path,
            agent_config=agent_config.get('config', {})
        )
        
        logger.info(f"✅ Created and started agent (running): {agent_id}")
        return jsonify(agent_config), 201
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@bp.route('/<agent_id>', methods=['GET'])
def get_agent(agent_id):
    """Get specific agent details."""
    agent = session_config.get_agent(agent_id)
    
    if not agent:
        return jsonify({"error": "Agent not found"}), 404
    
    # Enrich with status from logs
    status_info = log_manager.get_agent_status(agent_id)
    agent.update(status_info)
    
    return jsonify(agent)


@bp.route('/<agent_id>/pause', methods=['POST'])
def pause_agent(agent_id):
    """Pause an agent."""
    agent = session_config.get_agent(agent_id)
    
    if not agent:
        return jsonify({"error": "Agent not found"}), 404
    
    # Pause the agent instance (it will write to its own log)
    agent_manager.pause_agent(agent_id)
    
    logger.info(f"⏸️ Paused agent: {agent_id}")
    return jsonify({"status": "paused"})


@bp.route('/<agent_id>/resume', methods=['POST'])
def resume_agent(agent_id):
    """Resume a paused agent."""
    agent = session_config.get_agent(agent_id)
    
    if not agent:
        return jsonify({"error": "Agent not found"}), 404
    
    # Resume the agent instance (it will write to its own log)
    agent_manager.resume_agent(agent_id)
    
    logger.info(f"▶️ Resumed agent: {agent_id}")
    return jsonify({"status": "running"})


@bp.route('/<agent_id>/archive', methods=['POST'])
def archive_agent(agent_id):
    """Archive an agent."""
    agent = session_config.get_agent(agent_id)
    
    if not agent:
        return jsonify({"error": "Agent not found"}), 404
    
    # Write archive status to log
    log_file = session_config.logs_dir / f"agent_{agent_id}.jsonl"
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "type": "status",
        "status": "archived",
        "message": "Archived by user"
    }
    
    with open(log_file, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
    
    # Stop watching this agent
    log_manager.stop_watching_agent(agent_id)
    
    # Stop the agent instance
    agent_manager.stop_agent(agent_id)
    
    logger.info(f"📦 Archived agent: {agent_id}")
    return jsonify({"status": "archived"})


@bp.route('/pause-all', methods=['POST'])
def pause_all_agents():
    """Pause all running agents."""
    # Pause all agents in agent manager (they will write to their own logs)
    agent_manager.pause_all()
    
    paused_count = len(session_config.list_agents())
    logger.info(f"⏸️ Paused all agents ({paused_count})")
    return jsonify({"status": "paused", "count": paused_count})


@bp.route('/resume-all', methods=['POST'])
def resume_all_agents():
    """Resume all paused agents."""
    # Resume all agents in agent manager (they will write to their own logs)
    agent_manager.resume_all()
    
    resumed_count = len(session_config.list_agents())
    logger.info(f"▶️ Resumed all agents ({resumed_count})")
    return jsonify({"status": "running", "count": resumed_count})


@bp.route('/<agent_id>/message', methods=['POST'])
def send_message(agent_id):
    """Send a message to an agent."""
    agent = session_config.get_agent(agent_id)
    
    if not agent:
        return jsonify({"error": "Agent not found"}), 404
    
    data = request.json
    message = data.get('message', '')
    
    if not message:
        return jsonify({"error": "Message cannot be empty"}), 400
    
    # Write user message to log
    log_file = session_config.logs_dir / f"agent_{agent_id}.jsonl"
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "type": "user_message",
        "content": message
    }
    
    with open(log_file, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
    
    logger.info(f"💬 Sent message to agent {agent_id}: {message[:50]}...")
    return jsonify({"status": "sent"})


@bp.route('/<agent_id>/logs', methods=['GET'])
def get_logs(agent_id):
    """Stream agent logs via SSE."""
    agent = session_config.get_agent(agent_id)
    
    if not agent:
        return jsonify({"error": "Agent not found"}), 404
    
    def generate():
        """Generate SSE events from agent logs."""
        # Subscribe to log updates
        log_queue = log_manager.subscribe_to_agent(agent_id)
        
        # Send existing logs first
        log_file = session_config.logs_dir / f"agent_{agent_id}.jsonl"
        if log_file.exists():
            with open(log_file, 'r') as f:
                for line in f:
                    if line.strip():
                        yield f"data: {line}\n\n"
        
        # Stream new logs as they arrive
        try:
            while True:
                log_entry = log_queue.get(timeout=30)  # 30 second timeout
                yield f"data: {json.dumps(log_entry)}\n\n"
        except queue.Empty:
            # Send keepalive
            yield f": keepalive\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

