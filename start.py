#!/usr/bin/env python3
"""
Simple, direct entry point for Replit deployment.
Ensures Flask runs as the main process on port 5000.
"""

import os
import sys
import logging
from flask import Flask, jsonify
from threading import Thread
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Simple status tracking
status = {'discord_connected': False, 'start_time': time.time()}

@app.route('/')
def home():
    uptime = int(time.time() - status['start_time'])
    return f'''
    <html>
    <head><title>Discord Bot - Ready</title></head>
    <body style="font-family: Arial; text-align: center; padding: 50px;">
        <h1>Discord Bot Status</h1>
        <p><strong>Status:</strong> Healthy</p>
        <p><strong>Uptime:</strong> {uptime} seconds</p>
        <p><strong>Discord:</strong> {'Connected' if status['discord_connected'] else 'Connecting'}</p>
        <p><strong>Port:</strong> 5000</p>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'discord-bot',
        'uptime': int(time.time() - status['start_time']),
        'discord_connected': status['discord_connected']
    })

@app.route('/ping')
def ping():
    return jsonify({'message': 'pong', 'timestamp': time.time()})

def start_discord_bot():
    """Start Discord bot in background"""
    try:
        logger.info("Starting Discord bot...")
        import main
        # Update our status when bot connects
        status['discord_connected'] = True
        main.start_discord_bot_only()
    except Exception as e:
        logger.error(f"Discord bot failed: {e}")
        status['discord_connected'] = False

if __name__ == '__main__':
    logger.info("Starting Discord bot deployment on port 5000...")
    
    # Start Discord bot in background thread
    bot_thread = Thread(target=start_discord_bot, daemon=True)
    bot_thread.start()
    
    # Get port from environment
    port = int(os.environ.get('PORT', 5000))
    
    # Run Flask as main process
    logger.info(f"Flask server starting on 0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)