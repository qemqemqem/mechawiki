"""
File management endpoints.

Serves wiki content and provides file change feed.
"""
import logging
import queue
import json
from pathlib import Path
from flask import Blueprint, jsonify, request, Response
from .config import WIKICONTENT_PATH
from .log_watcher import log_manager

logger = logging.getLogger(__name__)

bp = Blueprint('files', __name__, url_prefix='/api/files')


@bp.route('', methods=['GET'])
def list_files():
    """List all files in wikicontent."""
    if not WIKICONTENT_PATH.exists():
        return jsonify({"error": "Wikicontent path not found"}), 404
    
    files = []
    
    # Walk through wikicontent directory
    for file_path in WIKICONTENT_PATH.rglob('*'):
        if file_path.is_file():
            rel_path = file_path.relative_to(WIKICONTENT_PATH)
            files.append({
                "path": str(rel_path),
                "name": file_path.name,
                "size": file_path.stat().st_size,
                "modified": file_path.stat().st_mtime
            })
    
    return jsonify({"files": files})


@bp.route('/feed', methods=['GET'])
def file_feed():
    """SSE stream of file changes from agent logs."""
    def generate():
        """Generate SSE events for file changes."""
        # Subscribe to file feed
        feed_queue = log_manager.subscribe_to_file_feed()
        
        # Send initial keepalive
        yield f": connected\n\n"
        
        # Stream file events as they arrive
        try:
            while True:
                try:
                    file_event = feed_queue.get(timeout=30)  # 30 second timeout
                    yield f"data: {json.dumps(file_event)}\n\n"
                except queue.Empty:
                    # Send keepalive
                    yield f": keepalive\n\n"
        except GeneratorExit:
            logger.info("Client disconnected from file feed")
    
    return Response(generate(), mimetype='text/event-stream')


@bp.route('/<path:file_path>', methods=['GET'])
def get_file(file_path):
    """Get file content."""
    full_path = WIKICONTENT_PATH / file_path
    
    if not full_path.exists():
        return jsonify({"error": "File not found"}), 404
    
    if not full_path.is_file():
        return jsonify({"error": "Path is not a file"}), 400
    
    try:
        content = full_path.read_text(encoding='utf-8')
        return jsonify({
            "path": file_path,
            "content": content,
            "size": full_path.stat().st_size
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route('/<path:file_path>', methods=['POST'])
def save_file(file_path):
    """Save file content (for user edits in UI)."""
    data = request.json
    content = data.get('content', '')
    
    full_path = WIKICONTENT_PATH / file_path
    
    try:
        # Ensure parent directory exists
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content
        full_path.write_text(content, encoding='utf-8')
        
        logger.info(f"💾 Saved file: {file_path}")
        return jsonify({"status": "saved", "path": file_path})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

