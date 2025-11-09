"""
Agent management endpoints.

Handles creating, listing, and controlling agents.
"""
import logging
import queue
from datetime import datetime
from pathlib import Path
from flask import Blueprint, jsonify, request, Response
from .config import agent_config, WIKICONTENT_PATH
from .log_watcher import log_manager
from .agent_manager import agent_manager
import json

logger = logging.getLogger(__name__)

bp = Blueprint('agents', __name__, url_prefix='/api/agents')


@bp.route('', methods=['GET'])
def list_agents():
    """List all agents with their current status."""
    agents = agent_config.list_agents()
    
    # Enrich with status from logs
    enriched = []
    for agent in agents:
        agent_data = agent.copy()
        
        # Get status and last action from log
        status_info = log_manager.get_agent_status(agent['id'])
        agent_data.update(status_info)
        
        # Flatten story_file to top level for frontend convenience
        if 'config' in agent_data and 'story_file' in agent_data['config']:
            agent_data['story_file'] = agent_data['config']['story_file']
        
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
    
    # Use provided ID or generate one
    if 'id' in data and data['id']:
        agent_id = data['id']
    else:
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
        agent_data_saved = agent_config.add_agent(agent_data)
        
        # Create empty log file
        log_file = agent_config.logs_dir / f"agent_{agent_id}.jsonl"
        log_file.write_text('')
        
        # Start watching this agent's log
        log_manager.start_watching_agent(agent_id, str(log_file), agent_data_saved.get('config', {}))
        
        # Start the agent instance (unpaused by default)
        agent_manager.start_agent(
            agent_id=agent_id,
            agent_type=data['type'],
            log_file=log_file,
            wikicontent_path=WIKICONTENT_PATH,
            agent_config=agent_data_saved.get('config', {})
        )
        
        logger.info(f"✅ Created and started agent (running): {agent_id}")
        return jsonify(agent_data_saved), 201
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@bp.route('/<agent_id>', methods=['GET'])
def get_agent(agent_id):
    """Get specific agent details."""
    agent = agent_config.get_agent(agent_id)
    
    if not agent:
        return jsonify({"error": "Agent not found"}), 404
    
    # Enrich with status from logs
    status_info = log_manager.get_agent_status(agent_id)
    agent.update(status_info)
    
    # Flatten story_file to top level for frontend convenience
    if 'config' in agent and 'story_file' in agent['config']:
        agent['story_file'] = agent['config']['story_file']
    
    return jsonify(agent)


@bp.route('/<agent_id>/pause', methods=['POST'])
def pause_agent(agent_id):
    """Pause an agent."""
    agent = agent_config.get_agent(agent_id)
    
    if not agent:
        return jsonify({"error": "Agent not found"}), 404
    
    # Pause the agent instance (it will write to its own log)
    agent_manager.pause_agent(agent_id)
    
    logger.info(f"⏸️ Paused agent: {agent_id}")
    return jsonify({"status": "paused"})


@bp.route('/<agent_id>/resume', methods=['POST'])
def resume_agent(agent_id):
    """Resume a paused agent."""
    agent = agent_config.get_agent(agent_id)
    
    if not agent:
        return jsonify({"error": "Agent not found"}), 404
    
    # Resume the agent instance (it will write to its own log)
    agent_manager.resume_agent(agent_id)
    
    logger.info(f"▶️ Resumed agent: {agent_id}")
    return jsonify({"status": "running"})


@bp.route('/<agent_id>/archive', methods=['POST'])
def archive_agent(agent_id):
    """Archive an agent."""
    agent = agent_config.get_agent(agent_id)
    
    if not agent:
        return jsonify({"error": "Agent not found"}), 404
    
    # Write archive status to log
    log_file = agent_config.logs_dir / f"agent_{agent_id}.jsonl"
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
    # Get all agents and filter by status
    agents = agent_config.list_agents()
    paused_count = 0
    
    for agent in agents:
        agent_id = agent['id']
        status_info = log_manager.get_agent_status(agent_id)
        current_status = status_info.get('status', 'unknown')
        
        # Only pause agents that are currently running
        if current_status == 'running':
            agent_manager.pause_agent(agent_id)
            paused_count += 1
    
    logger.info(f"⏸️ Paused {paused_count} running agents")
    return jsonify({"status": "paused", "count": paused_count})


@bp.route('/resume-all', methods=['POST'])
def resume_all_agents():
    """Resume all paused agents."""
    # Get all agents and filter by status
    agents = agent_config.list_agents()
    resumed_count = 0
    
    for agent in agents:
        agent_id = agent['id']
        status_info = log_manager.get_agent_status(agent_id)
        current_status = status_info.get('status', 'unknown')
        
        # Only resume agents that are currently paused
        if current_status == 'paused':
            agent_manager.resume_agent(agent_id)
            resumed_count += 1
    
    logger.info(f"▶️ Resumed {resumed_count} paused agents")
    return jsonify({"status": "running", "count": resumed_count})


@bp.route('/<agent_id>/message', methods=['POST'])
def send_message(agent_id):
    """Send a message to an agent."""
    agent = agent_config.get_agent(agent_id)
    
    if not agent:
        return jsonify({"error": "Agent not found"}), 404
    
    data = request.json
    message = data.get('message', '')
    
    if not message:
        return jsonify({"error": "Message cannot be empty"}), 400
    
    # Check agent's current status and resume if not running
    status_info = log_manager.get_agent_status(agent_id)
    current_status = status_info.get('status', 'unknown')
    
    if current_status != 'running':
        agent_manager.resume_agent(agent_id)
        logger.info(f"▶️ Auto-resumed agent {agent_id} (was {current_status})")
    
    # Write user message to log
    log_file = agent_config.logs_dir / f"agent_{agent_id}.jsonl"
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "type": "user_message",
        "content": message
    }
    
    with open(log_file, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
    
    logger.info(f"💬 Sent message to agent {agent_id}: {message[:50]}...")
    return jsonify({"status": "sent"})


@bp.route('/<agent_id>/reload', methods=['POST'])
def reload_agent(agent_id):
    """Reload agent status from logs."""
    agent = agent_config.get_agent(agent_id)
    
    if not agent:
        return jsonify({"error": "Agent not found"}), 404
    
    # Force re-read of log file
    log_file = agent_config.logs_dir / f"agent_{agent_id}.jsonl"
    log_manager.start_watching_agent(agent_id, str(log_file), agent.get('config'))
    
    logger.info(f"🔄 Reloaded agent: {agent_id}")
    return jsonify({"status": "reloaded"})


@bp.route('/session/cost', methods=['GET'])
def get_session_cost():
    """Get session-wide cost statistics."""
    from .cost_tracker import get_cost_tracker
    tracker = get_cost_tracker()
    
    if not tracker:
        return jsonify({"error": "Cost tracker not initialized"}), 500
    
    return jsonify(tracker.get_stats())


@bp.route('/<agent_id>/logs', methods=['GET'])
def get_logs(agent_id):
    """Stream agent logs via SSE."""
    agent = agent_config.get_agent(agent_id)
    
    if not agent:
        return jsonify({"error": "Agent not found"}), 404
    
    def generate():
        """Generate SSE events from agent logs."""
        # Subscribe to log updates
        log_queue = log_manager.subscribe_to_agent(agent_id)
        
        # Send existing logs first
        log_file = agent_config.logs_dir / f"agent_{agent_id}.jsonl"
        if log_file.exists():
            with open(log_file, 'r') as f:
                for line in f:
                    if line.strip():
                        yield f"data: {line}\n\n"
        
        # Stream new logs as they arrive
        while True:
            try:
                log_entry = log_queue.get(timeout=30)  # 30 second timeout
                yield f"data: {json.dumps(log_entry)}\n\n"
            except queue.Empty:
                # Send keepalive and continue
                yield f": keepalive\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

