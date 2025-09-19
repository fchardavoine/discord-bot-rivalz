#!/usr/bin/env python3
"""
Simple production WSGI server for Discord bot deployment.
"""

import os
import logging
from main import app

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# WSGI application object
application = app

if __name__ == "__main__":
    # Get port from environment
    port = int(os.environ.get('PORT', 5000))
    
    # Run with gunicorn in production
    import subprocess
    import sys
    
    cmd = [
        'gunicorn',
        '--bind', f'0.0.0.0:{port}',
        '--workers', '1',
        '--threads', '4', 
        '--timeout', '120',
        '--keep-alive', '2',
        '--max-requests', '1000',
        '--access-logfile', '-',
        '--error-logfile', '-',
        '--log-level', 'info',
        'production_wsgi:application'
    ]
    
    subprocess.run(cmd)