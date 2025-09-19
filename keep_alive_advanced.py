#!/usr/bin/env python3
"""
Advanced keep-alive system for Discord bot with enhanced monitoring
"""

from flask import Flask, jsonify
import threading
import time
import requests
import logging
import os

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global bot monitoring status
bot_monitor = {
    'last_check': None,
    'consecutive_failures': 0,
    'total_restarts': 0,
    'bot_healthy': False,
    'monitoring_active': True
}

@app.route('/')
def home():
    """Health check endpoint"""
    return jsonify({
        'service': 'discord-bot-monitor',
        'status': 'active',
        'bot_healthy': bot_monitor['bot_healthy'],
        'monitoring': bot_monitor['monitoring_active'],
        'restarts': bot_monitor['total_restarts'],
        'last_check': str(bot_monitor['last_check'])
    })

@app.route('/restart-bot')
def restart_bot_endpoint():
    """Manual bot restart endpoint"""
    restart_discord_bot()
    return jsonify({'message': 'Bot restart initiated'})

def check_discord_bot():
    """Check if Discord bot is running and healthy"""
    try:
        response = requests.get('http://localhost:5000/api/status', timeout=3)
        data = response.json()
        
        is_healthy = (
            data.get('status') == 'healthy' and 
            data.get('discord_connected') == True and
            data.get('guilds', 0) > 0
        )
        
        return is_healthy, data
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return False, None

def restart_discord_bot():
    """Restart the Discord bot process"""
    import subprocess
    
    logger.warning("Restarting Discord bot...")
    bot_monitor['total_restarts'] += 1
    
    try:
        # Kill existing bot process
        subprocess.run(['pkill', '-f', 'production.py'], capture_output=True)
        time.sleep(5)
        
        # Start new bot process
        subprocess.Popen(['python', 'production.py'], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL)
        
        logger.info("Bot restart initiated")
        return True
    except Exception as e:
        logger.error(f"Failed to restart bot: {e}")
        return False

def monitor_bot():
    """Background monitoring thread"""
    max_failures = 3
    check_interval = 45  # seconds
    
    while bot_monitor['monitoring_active']:
        bot_monitor['last_check'] = time.strftime('%Y-%m-%d %H:%M:%S')
        
        is_healthy, status_data = check_discord_bot()
        bot_monitor['bot_healthy'] = is_healthy
        
        if is_healthy:
            bot_monitor['consecutive_failures'] = 0
            if status_data:
                logger.info(f"Bot healthy - Guilds: {status_data.get('guilds', 0)}, Commands: {status_data.get('commands', 0)}")
        else:
            bot_monitor['consecutive_failures'] += 1
            logger.warning(f"Bot unhealthy ({bot_monitor['consecutive_failures']}/{max_failures})")
            
            if bot_monitor['consecutive_failures'] >= max_failures:
                if bot_monitor['total_restarts'] < 10:  # Limit total restarts
                    restart_discord_bot()
                    bot_monitor['consecutive_failures'] = 0
                    time.sleep(60)  # Wait for restart
                else:
                    logger.error("Too many restarts - stopping monitoring")
                    bot_monitor['monitoring_active'] = False
        
        time.sleep(check_interval)

def run_monitor():
    """Start the monitoring system"""
    # Start bot monitoring in background
    monitor_thread = threading.Thread(target=monitor_bot, daemon=True)
    monitor_thread.start()
    logger.info("Discord bot monitoring started")
    
    # Run Flask app
    app.run(host='0.0.0.0', port=3001, debug=False)

if __name__ == '__main__':
    run_monitor()