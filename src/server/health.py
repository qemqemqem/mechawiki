"""
Health and status endpoints.
"""
from flask import Blueprint, jsonify
from .config import WIKICONTENT_PATH

bp = Blueprint('health', __name__, url_prefix='/api')


@bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "service": "mechawiki-server"
    })


@bp.route('/status', methods=['GET'])
def status():
    """Overall system status."""
    return jsonify({
        "status": "running",
        "wikicontent_path": str(WIKICONTENT_PATH),
        "wikicontent_exists": WIKICONTENT_PATH.exists()
    })

