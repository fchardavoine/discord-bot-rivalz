#!/usr/bin/env python3
"""
Production deployment entry point for Discord bot.
This ensures the bot runs in true production mode with proper process management.
"""

import os
import sys
import asyncio
import threading
import logging
import signal
from datetime import datetime

# Configure production logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot_production.log')
    ]
)
logger = logging.getLogger(__name__)

# Global variables for process management
bot_instance = None
flask_thread = None
should_run = True

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global should_run
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    should_run = False
    
    if bot_instance:
        asyncio.create_task(bot_instance.close())
    
    sys.exit(0)

def run_flask_app():
    """Run Flask app in production mode with gunicorn-like behavior"""
    try:
        from main import app
        logger.info("Starting Flask application in production mode...")
        
        # Run with production settings
        app.run(
            host='0.0.0.0',
            port=int(os.environ.get('PORT', 5000)),
            debug=False,
            use_reloader=False,
            threaded=True
        )
    except Exception as e:
        logger.error(f"Flask app error: {e}")

async def run_discord_bot():
    """Run Discord bot with production-grade error handling"""
    global bot_instance
    
    retry_count = 0
    max_retries = 10
    
    while should_run and retry_count < max_retries:
        try:
            from bot import DiscordBot
            bot_instance = DiscordBot()
            
            discord_token = os.getenv('DISCORD_TOKEN')
            if not discord_token:
                logger.error("DISCORD_TOKEN not found in environment variables")
                break
            
            logger.info(f"Starting Discord bot (attempt {retry_count + 1}/{max_retries})")
            await bot_instance.start(discord_token)
            
        except Exception as e:
            retry_count += 1
            logger.error(f"Bot startup failed (attempt {retry_count}): {e}")
            
            if retry_count < max_retries:
                wait_time = min(60 * retry_count, 300)  # Max 5 minute wait
                logger.info(f"Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
            else:
                logger.critical("Max retries reached, bot startup failed permanently")
                break
        
        if not should_run:
            break
            
        # If we get here, bot disconnected, wait before retry
        logger.warning("Bot disconnected, attempting restart in 30 seconds...")
        await asyncio.sleep(30)

def main():
    """Main production entry point"""
    global flask_thread
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    logger.info("="*60)
    logger.info("🚀 DISCORD BOT - PRODUCTION MODE STARTUP")
    logger.info(f"⚡ Starting at: {datetime.utcnow()}")
    logger.info(f"🔧 Python version: {sys.version}")
    logger.info(f"📍 Working directory: {os.getcwd()}")
    logger.info("="*60)
    
    try:
        # Start Flask app in separate thread
        flask_thread = threading.Thread(target=run_flask_app, daemon=True)
        flask_thread.start()
        logger.info("✅ Flask app thread started")
        
        # Run Discord bot in main thread with async loop
        asyncio.run(run_discord_bot())
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.critical(f"Critical error in main: {e}")
    finally:
        logger.info("Production bot shutdown complete")

if __name__ == "__main__":
    main()