#!/usr/bin/env python3
"""
Run the MechaWiki server.
"""
from src.server.app import run_server

if __name__ == '__main__':
    run_server(host='localhost', port=5000, debug=True)

