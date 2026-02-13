"""
Lambda entrypoint for opsdb Flask application.
Uses Mangum to convert Lambda events to ASGI and back.
"""
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app
from mangum import Mangum

# Create the Flask app
app = create_app('production')

# Create the Mangum handler
handler = Mangum(app, lifespan='off')

def lambda_handler(event, context):
    """
    AWS Lambda handler function.
    """
    return handler(event, context)
