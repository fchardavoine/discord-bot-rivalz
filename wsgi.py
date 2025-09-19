#!/usr/bin/env python3
"""
Production WSGI entry point for Discord bot with gunicorn optimization.
Optimized for Replit production deployment with proper process management.
"""

import os
import logging
import threading
import asyncio
from main import app

# Configure production logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global Discord bot instance
discord_bot_instance = None
bot_thread = None

def start_discord_bot():
    """Start Discord bot in background thread"""
    global discord_bot_instance, bot_thread
    
    def run_bot():
        try:
            import asyncio
            from bot import DiscordBot
            
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            discord_bot_instance = DiscordBot()
            loop.run_until_complete(discord_bot_instance.start(os.getenv('DISCORD_TOKEN')))
        except Exception as e:
            logger.error(f"Discord bot error: {e}")
    
    if bot_thread is None or not bot_thread.is_alive():
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        logger.info("Discord bot started in background thread")

# Start Discord bot when WSGI app loads
start_discord_bot()

# WSGI application object for gunicorn
application = app

# Health check endpoint for production monitoring
@app.route('/health')
def health_check():
    """Production health check endpoint"""
    return {
        'status': 'healthy',
        'discord_bot': 'running' if bot_thread and bot_thread.is_alive() else 'stopped',
        'timestamp': app.config.get('START_TIME', 'unknown')
    }

if __name__ == "__main__":
    # Development fallback
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)