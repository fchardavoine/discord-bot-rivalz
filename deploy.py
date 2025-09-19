#!/usr/bin/env python3
"""
Production deployment script for Discord bot with WSGI optimization.
Handles environment setup and production deployment preparation.
"""

import os
import sys
import subprocess
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_environment():
    """Check if all required environment variables are set"""
    required_vars = ['DISCORD_TOKEN']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing environment variables: {missing_vars}")
        return False
    
    logger.info("All required environment variables are set")
    return True

def check_dependencies():
    """Check if all required packages are installed"""
    required_packages = [
        'discord.py',
        'flask',
        'gunicorn',
        'requests',
        'aiohttp'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_').replace('.py', ''))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Missing packages: {missing_packages}")
        return False
    
    logger.info("All required packages are installed")
    return True

def start_production_server():
    """Start the production WSGI server with gunicorn"""
    logger.info("Starting production Discord bot with Gunicorn WSGI server...")
    
    port = os.environ.get('PORT', 5000)
    
    # Validate port to prevent command injection
    try:
        port = int(port)
        if not (1 <= port <= 65535):
            raise ValueError("Port must be between 1 and 65535")
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid PORT value: {port}. Using default port 5000. Error: {e}")
        port = 5000
    
    # Gunicorn command with optimized settings
    cmd = [
        'gunicorn',
        '--config', 'gunicorn.conf.py',
        '--bind', f'0.0.0.0:{port}',
        '--workers', '4',
        '--threads', '2',
        '--worker-class', 'sync',
        '--timeout', '120',
        '--keep-alive', '2',
        '--max-requests', '1000',
        '--max-requests-jitter', '50',
        '--preload',
        '--access-logfile', '-',
        '--error-logfile', '-',
        '--log-level', 'info',
        'wsgi:application'
    ]
    
    try:
        logger.info(f"Executing: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start production server: {e}")
        sys.exit(1)

def main():
    """Main deployment function"""
    logger.info("="*60)
    logger.info("DISCORD BOT PRODUCTION DEPLOYMENT")
    logger.info("="*60)
    logger.info(f"Deployment started at: {datetime.now()}")
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Start production server
    logger.info("Environment check passed - starting production server...")
    start_production_server()

if __name__ == "__main__":
    main()