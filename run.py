#!/usr/bin/env python3
"""
Production entry point for Discord bot deployment.
This is the main entry point expected by Replit deployments.
"""

import os
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Main entry point for deployment"""
    logger.info("🚀 Starting Discord Bot deployment from run.py...")
    
    # Import and run the Flask application
    from app import app
    
    # Get port from environment or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    logger.info(f"Starting Flask server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    main()