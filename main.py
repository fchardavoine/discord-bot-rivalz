#!/usr/bin/env python3
"""
Pure background worker entry point for Discord bot.
Optimized for Replit background worker deployment.
"""

import os
import sys
import logging
import asyncio
import discord
from bot_monitor import notify_starting, notify_online, notify_offline, notify_failed, is_monitoring_enabled

# Configure logging for deployment
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def start_discord_bot():
    """Start Discord bot with automatic reconnection - returns True for clean stop, False for failure"""
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            logger.info(f"🤖 Initializing Discord bot (attempt {retry_count + 1}/{max_retries})...")
            
            # Notify monitoring system of startup attempt
            if retry_count == 0:
                await notify_starting(0)
            
            # Import bot components
            from bot import DiscordBot
            
            # Initialize bot with clean state
            bot = DiscordBot()
            
            # Get Discord token
            token = os.getenv('DISCORD_TOKEN')
            if not token:
                logger.error("DISCORD_TOKEN not found in environment variables")
                return False  # Fatal error
            
            # Start bot with reconnection enabled
            logger.info("🚀 Starting Discord bot as background worker...")
            
            # Run the bot with automatic reconnection
            await bot.start(token, reconnect=True)
            # If we reach here, bot stopped cleanly
            return True
            
        except discord.LoginFailure:
            logger.error("Discord login failed - check DISCORD_TOKEN")
            return False  # Fatal error
        except discord.ConnectionClosed:
            logger.warning("Discord connection closed, attempting to reconnect...")
            await notify_offline("Discord connection closed", retry_count + 1)
            retry_count += 1
            await asyncio.sleep(5)  # Wait before retry
        except Exception as e:
            logger.exception(f"Discord bot error (attempt {retry_count + 1}): {e}")
            retry_count += 1
            if retry_count < max_retries:
                wait_time = min(10 * retry_count, 60)  # Exponential backoff, max 60s
                logger.info(f"Retrying in {wait_time} seconds... ({retry_count}/{max_retries})")
                await asyncio.sleep(wait_time)
            else:
                logger.error("Max retries reached, bot startup failed")
                return False  # Give up after max retries

def main():
    """Main entry point with automatic restart on crash"""
    logger.info("="*60)
    logger.info("🤖 DISCORD BOT - AUTO-RESTART MODE")
    logger.info("="*60)
    
    restart_count = 0
    max_restarts = 100  # Allow many restarts
    clean_exit = False
    
    while restart_count < max_restarts:
        try:
            logger.info(f"🚀 Starting bot (restart #{restart_count})")
            
            # Notify of restart attempt if not first start  
            if restart_count > 0:
                asyncio.run(notify_starting(restart_count))
            
            # Run Discord bot and check result
            result = asyncio.run(start_discord_bot())
            
            if result:
                # Clean shutdown - exit normally
                logger.info("✅ Bot stopped cleanly")
                clean_exit = True
                break
            else:
                # Bot failed to start - treat as crash
                raise RuntimeError("Bot failed to initialize")
            
        except KeyboardInterrupt:
            logger.info("🛑 Bot shutdown requested by user")
            clean_exit = True
            break
        except SystemExit as e:
            if e.code == 0:
                logger.info("✅ Bot exited cleanly")
                clean_exit = True
                break
            else:
                # Treat non-zero exit as crash - log and restart
                logger.error(f"💥 Bot exited with non-zero code: {e.code}")
                restart_count += 1
        except BaseException as e:
            restart_count += 1
            logger.exception(f"💥 Bot crashed: {e}")
            asyncio.run(notify_offline(f"Bot crashed: {str(e)[:100]}", restart_count))
        
        # Handle restart logic (only reached on crashes)
        if restart_count >= max_restarts:
            logger.error("❌ Max restarts reached, stopping auto-restart")
            break
            
        wait_time = min(10 + (restart_count * 2), 60)  # Progressive delay, max 60s
        logger.info(f"🔄 Auto-restarting in {wait_time}s... (restart #{restart_count}/{max_restarts})")
        
        import time
        time.sleep(wait_time)
    
    # Exit with appropriate code
    if clean_exit:
        logger.info("🏁 Bot shutdown complete")
        sys.exit(0)
    else:
        logger.error("❌ Bot failed after maximum restart attempts")
        # Notify of final failure
        try:
            asyncio.run(notify_failed(restart_count))
        except:
            pass  # Don't let notification failures prevent exit
        sys.exit(1)

if __name__ == '__main__':
    main()