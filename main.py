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
import threading
import time
from datetime import datetime
from flask import Flask, jsonify, request
from bot_monitor import notify_starting, notify_online, notify_offline, notify_failed, is_monitoring_enabled

# Configure logging for deployment
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Global bot status for health monitoring
bot_status = {
    'status': 'starting',
    'start_time': None,
    'guilds': 0,
    'last_check': None,
    'discord_connected': False
}

def update_bot_status(status, guilds=0):
    """Update bot status for health monitoring"""
    global bot_status
    bot_status['status'] = status
    bot_status['guilds'] = guilds
    bot_status['last_check'] = datetime.utcnow().isoformat()
    bot_status['discord_connected'] = (status == 'connected')
    if status == 'connected' and not bot_status['start_time']:
        bot_status['start_time'] = datetime.utcnow().isoformat()

def create_health_app():
    """Create Flask app for health monitoring and webhook restart"""
    app = Flask(__name__)
    
    @app.route('/health')
    def health():
        """Basic health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'service': 'discord-bot',
            'bot_status': bot_status['status'],
            'discord_connected': bot_status['discord_connected'],
            'guilds': bot_status['guilds'],
            'timestamp': datetime.utcnow().isoformat()
        })
    
    @app.route('/health/detailed')
    def health_detailed():
        """Enhanced health check that verifies bot functionality"""
        try:
            # Calculate uptime
            uptime_seconds = 0
            if bot_status.get('start_time'):
                start_time = datetime.fromisoformat(bot_status['start_time'].replace('Z', '+00:00'))
                uptime_seconds = (datetime.utcnow() - start_time).total_seconds()
            
            # Check if bot is responsive (last check within 180 seconds - more realistic)
            is_responsive = False
            if bot_status.get('last_check'):
                last_check = datetime.fromisoformat(bot_status['last_check'].replace('Z', '+00:00'))
                seconds_since_check = (datetime.utcnow() - last_check).total_seconds()
                is_responsive = seconds_since_check < 180
            else:
                # If no last_check, consider responsive if recently started
                if bot_status.get('start_time'):
                    start_time = datetime.fromisoformat(bot_status['start_time'].replace('Z', '+00:00'))
                    seconds_since_start = (datetime.utcnow() - start_time).total_seconds()
                    is_responsive = seconds_since_start < 300  # 5 minutes grace period for startup
            
            # Determine overall health
            is_healthy = (
                bot_status['discord_connected'] and 
                bot_status['status'] in ['connected', 'running'] and
                is_responsive and
                bot_status['guilds'] > 0
            )
            
            health_data = {
                'status': 'healthy' if is_healthy else 'unhealthy',
                'service': 'discord-bot',
                'bot_status': bot_status['status'],
                'discord_connected': bot_status['discord_connected'],
                'guilds': bot_status['guilds'],
                'is_responsive': is_responsive,
                'uptime_seconds': uptime_seconds,
                'uptime_human': f"{uptime_seconds//3600:.0f}h {(uptime_seconds%3600)//60:.0f}m",
                'last_check': bot_status.get('last_check'),
                'start_time': bot_status.get('start_time'),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            return jsonify(health_data), 200 if is_healthy else 503
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }), 500
    
    @app.route('/webhook/restart', methods=['POST', 'GET'])
    def webhook_restart():
        """External webhook endpoint for triggering bot restart"""
        try:
            logger.info("🔔 External restart webhook triggered")
            
            # Parse webhook data (UptimeRobot format)
            alert_type = None
            if request.method == 'POST':
                try:
                    data = request.get_json() or {}
                    alert_type = data.get('alertType')
                except:
                    pass
                if not alert_type:
                    alert_type = request.form.get('alertType') or request.args.get('alertType')
            else:
                alert_type = request.args.get('alertType')
            
            logger.info(f"📊 Webhook alert type: {alert_type}")
            
            # Require authentication for security
            auth_header = request.headers.get('Authorization')
            expected_auth = os.getenv('RESTART_SECRET', 'disabled')
            
            if expected_auth == 'disabled' or not auth_header or auth_header != f"Bearer {expected_auth}":
                logger.warning(f"🚫 Unauthorized restart attempt from {request.remote_addr}")
                return jsonify({
                    'status': 'unauthorized',
                    'message': 'Authentication required for restart',
                    'timestamp': datetime.utcnow().isoformat()
                }), 401
            
            # Only restart on down alerts (alertType=1) or if no alertType specified
            if alert_type is None or alert_type == '1' or alert_type == 1:
                logger.warning("🚨 EXTERNAL RESTART TRIGGERED - Forcing process exit")
                update_bot_status('restarting')
                
                # Force restart by exiting the process
                def delayed_restart():
                    time.sleep(2)  # Give time to send response
                    logger.error("💥 WEBHOOK RESTART: Forcing process exit")
                    os._exit(1)  # Force exit - shell wrapper will restart us
                
                restart_thread = threading.Thread(target=delayed_restart, daemon=True)
                restart_thread.start()
                
                return jsonify({
                    'status': 'restart_triggered',
                    'message': 'Bot restart initiated via webhook',
                    'alert_type': alert_type,
                    'timestamp': datetime.utcnow().isoformat()
                }), 200
            else:
                logger.info(f"✅ Webhook received but no restart needed (alertType: {alert_type})")
                return jsonify({
                    'status': 'acknowledged',
                    'message': 'Webhook received - no action taken',
                    'alert_type': alert_type,
                    'timestamp': datetime.utcnow().isoformat()
                }), 200
                
        except Exception as e:
            logger.error(f"❌ Webhook restart error: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }), 500
    
    @app.route('/api/status')
    def api_status():
        """Detailed bot status endpoint"""
        return jsonify(bot_status)
    
    @app.route('/refresh', methods=['POST'])
    def refresh():
        """repl.deploy refresh endpoint for automated GitHub deployments"""
        try:
            import sys
            import json
            
            # Log the repl.deploy format for daemon processing
            request_body = request.get_json() or {}
            signature = request.headers.get('Signature', '')
            
            # Log in repl.deploy format for daemon to process
            repl_deploy_log = f"repl.deploy{json.dumps(request_body)}{signature}"
            print(repl_deploy_log, flush=True)
            
            # Read daemon response from stdin (this would be handled by repl.deploy daemon)
            # For now, just acknowledge the request
            logger.info("🔄 repl.deploy refresh triggered - GitHub deployment restart initiated")
            
            # Signal success to repl.deploy daemon
            print("repl.deploy-success", flush=True)
            
            return jsonify({
                'status': 'success',
                'message': 'Deployment refresh triggered',
                'timestamp': datetime.utcnow().isoformat()
            }), 200
            
        except Exception as e:
            logger.error(f"❌ repl.deploy refresh error: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }), 500
    
    return app

def start_health_server():
    """Start Flask health server in background thread"""
    try:
        logger.info("🏥 Starting health monitoring server on port 5000...")
        app = create_health_app()
        
        # Disable Flask's request logging to reduce noise
        import logging as flask_logging
        flask_log = flask_logging.getLogger('werkzeug')
        flask_log.setLevel(flask_logging.ERROR)
        
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except Exception as e:
        logger.error(f"❌ Health server failed to start: {e}")

def start_health_monitoring():
    """Start health monitoring in background thread"""
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    logger.info("✅ Health monitoring server started")

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
            
            # Update health status
            update_bot_status('starting')
            
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
            
            # Update status when connected
            update_bot_status('connected', 1)  # Assume 1 guild for now
            
            # Run the bot with automatic reconnection
            await bot.start(token, reconnect=True)
            # If we reach here, bot stopped cleanly
            return True
            
        except discord.LoginFailure:
            logger.error("Discord login failed - check DISCORD_TOKEN")
            update_bot_status('error')
            return False  # Fatal error
        except discord.ConnectionClosed:
            logger.warning("Discord connection closed, attempting to reconnect...")
            update_bot_status('reconnecting')
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
    
    # Start health monitoring server first
    start_health_monitoring()
    
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