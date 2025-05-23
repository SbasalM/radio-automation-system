#!/usr/bin/env python
"""
Radio Workflow Automation System - Main Entry Point
This file starts the web application server
"""

from app import create_app
import os

# Create the Flask application
app = create_app()

if __name__ == '__main__':
    # Ensure required directories exist
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('processed', exist_ok=True)
    os.makedirs('instance', exist_ok=True)
    
    # Run the application
    # Debug=True means it will show errors and auto-reload when you make changes
    app.run(debug=True, host='0.0.0.0', port=5000)