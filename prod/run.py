#!/usr/bin/env python3
"""Entry point for the Flask application."""

import sys
import os

# Add the parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

# Use production config for the standalone prod version
app = create_app('production')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5443, debug=False)
