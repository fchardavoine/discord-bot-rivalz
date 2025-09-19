#!/usr/bin/env python3
"""
Simple bot restart utility to ensure persistent Discord connection
"""

import os
import signal
import subprocess
import time
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_bot_health():
    """Check if bot is healthy and connected"""
    try:
        response = requests.get('http://localhost:5000/api/status', timeout=5)
        data = response.json()
        return data.get('discord_connected', False) and data.get('status') == 'healthy'
    except:
        return False

def restart_bot():
    """Kill and restart the Discord bot"""
    logger.info("Restarting Discord bot for persistent connection...")
    
    # Kill existing processes
    subprocess.run(['pkill', '-f', 'production.py'], capture_output=True)
    time.sleep(3)
    
    # Start fresh bot process
    subprocess.Popen(['python', 'production.py'])
    logger.info("Fresh bot instance started")

def ensure_uptime():
    """Keep checking and restart if needed"""
    check_count = 0
    restart_count = 0
    max_restarts = 5
    
    logger.info("Starting Discord bot uptime monitor...")
    
    while restart_count < max_restarts:
        if check_bot_health():
            check_count += 1
            if check_count % 10 == 0:  # Log every 10 checks
                logger.info("Bot is healthy and connected")
        else:
            logger.warning("Bot is not connected to Discord")
            restart_bot()
            restart_count += 1
            time.sleep(60)  # Wait for restart
            continue
        
        time.sleep(30)  # Check every 30 seconds
    
    logger.error("Max restarts reached - manual intervention needed")

if __name__ == "__main__":
    ensure_uptime()