#!/usr/bin/env python3
"""
Production-ready Flask application entry point for Discord bot deployment.
This serves as the main web application that Replit deployments expect.
"""

import os
import logging
from flask import Flask, jsonify, render_template_string
from threading import Thread
from datetime import datetime
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Create Flask app as the main application
app = Flask(__name__)

# Bot status tracking
bot_status = {
    'status': 'starting',
    'start_time': None,
    'guilds': 0,
    'last_check': None,
    'discord_connected': False
}

def update_bot_status(status, guilds=0):
    """Update bot status information"""
    global bot_status
    bot_status['status'] = status
    bot_status['guilds'] = guilds
    bot_status['last_check'] = datetime.utcnow().isoformat()
    bot_status['discord_connected'] = (status == 'connected')
    if status == 'connected' and not bot_status['start_time']:
        bot_status['start_time'] = datetime.utcnow().isoformat()
    logger.info(f"Bot status updated: {status} (guilds: {guilds})")

@app.route('/')
def home():
    """Main endpoint that serves bot status page"""
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Discord Bot - Deployment Ready</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                text-align: center; 
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                color: white;
            }
            .container {
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                padding: 40px;
                border-radius: 20px;
                display: inline-block;
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                border: 1px solid rgba(255,255,255,0.2);
                max-width: 600px;
                margin: 20px;
            }
            .status {
                font-size: 28px;
                font-weight: bold;
                margin: 20px 0;
            }
            .status.connected { color: #00ff88; }
            .status.connecting { color: #ffaa00; }
            .status.error { color: #ff6b6b; }
            .info { margin: 15px 0; font-size: 16px; opacity: 0.9; }
            .endpoints {
                background: rgba(0,0,0,0.2);
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
                text-align: left;
            }
            .endpoint { 
                margin: 8px 0; 
                font-family: 'Courier New', monospace;
                background: rgba(255,255,255,0.1);
                padding: 8px;
                border-radius: 5px;
            }
            h1 { margin: 0 0 20px 0; font-size: 2.5em; }
            h3 { margin: 20px 0 10px 0; color: #f0f0f0; }
        </style>
        <script>
            function updateStatus() {
                fetch('/api/status')
                    .then(response => response.json())
                    .then(data => {
                        const statusEl = document.getElementById('bot-status');
                        const lastCheckEl = document.getElementById('last-check');
                        const guildsEl = document.getElementById('guilds');
                        
                        statusEl.textContent = data.status;
                        statusEl.className = 'status ' + data.status;
                        lastCheckEl.textContent = new Date(data.last_check).toLocaleString();
                        guildsEl.textContent = data.guilds;
                    })
                    .catch(err => console.log('Status update failed:', err));
            }
            
            setInterval(updateStatus, 5000);
            updateStatus();
        </script>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Discord Bot</h1>
            <div id="bot-status" class="status {{ bot_status.status }}">{{ bot_status.status }}</div>
            <div class="info">Guilds Connected: <strong id="guilds">{{ bot_status.guilds }}</strong></div>
            <div class="info">Last Check: <span id="last-check">{{ bot_status.last_check or 'Never' }}</span></div>
            
            <div class="endpoints">
                <h3>API Endpoints</h3>
                <div class="endpoint">GET / - This status page</div>
                <div class="endpoint">GET /health - Health check for deployment</div>
                <div class="endpoint">GET /api/status - Detailed bot status JSON</div>
            </div>
            
            <div class="info">
                ✅ Production deployment ready<br>
                ✅ Health checks operational<br>
                ✅ Discord bot {{ 'connected' if bot_status.discord_connected else 'starting' }}
            </div>
        </div>
    </body>
    </html>
    ''', bot_status=bot_status)

@app.route('/health')
def health():
    """Health check endpoint for deployment"""
    return jsonify({
        'status': 'healthy',
        'service': 'discord-bot',
        'bot_status': bot_status['status'],
        'discord_connected': bot_status['discord_connected'],
        'guilds': bot_status['guilds'],
        'timestamp': datetime.utcnow().isoformat(),
        'uptime': bot_status.get('start_time', 'not started')
    })

@app.route('/api/status')
def api_status():
    """Detailed API status endpoint"""
    return jsonify(bot_status)

@app.route('/ping')
def ping():
    """Simple ping endpoint"""
    return jsonify({'message': 'pong', 'timestamp': datetime.utcnow().isoformat()})

async def start_discord_bot():
    """Start Discord bot in background thread"""
    try:
        logger.info("Starting Discord bot in background thread...")
        update_bot_status('initializing')
        
        # Import Discord bot modules  
        import main
        # Start the Discord bot using the correct function
        await main.start_discord_bot()
        
    except Exception as e:
        logger.error(f"Failed to start Discord bot: {e}")
        update_bot_status('error')

# Start Discord bot with supervision (auto-restart on failure)
import asyncio
import time
import threading

# Global stop event for graceful shutdown
stop_event = threading.Event()

def run_discord_bot_supervised():
    """Supervised Discord bot runner with automatic restart"""
    restart_count = 0
    max_restarts = 100
    
    while not stop_event.is_set() and restart_count < max_restarts:
        try:
            logger.info(f"🤖 Starting supervised Discord bot (attempt {restart_count + 1})")
            update_bot_status('starting')
            
            # Run the Discord bot
            result = asyncio.run(start_discord_bot())
            
            if result is True:
                # Clean shutdown requested
                logger.info("✅ Discord bot stopped cleanly")
                update_bot_status('stopped')
                break
            else:
                # Bot failed, prepare for restart
                restart_count += 1
                logger.error(f"💥 Discord bot failed (restart #{restart_count}/{max_restarts})")
                update_bot_status('restarting')
                
                if restart_count >= max_restarts:
                    logger.error("❌ Max restarts reached - stopping supervision")
                    update_bot_status('failed')
                    break
                
                # Progressive backoff delay
                wait_time = min(10 + (restart_count * 2), 60)
                logger.info(f"🔄 Restarting Discord bot in {wait_time}s...")
                time.sleep(wait_time)
                
        except Exception as e:
            restart_count += 1
            logger.exception(f"💥 Discord bot supervisor error: {e}")
            update_bot_status('error')
            
            if restart_count < max_restarts:
                wait_time = min(10 + (restart_count * 2), 60)
                logger.info(f"🔄 Supervisor restarting in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error("❌ Supervisor giving up after max failures")
                break
    
    # If we exhausted all retries, force process restart
    if restart_count >= max_restarts:
        logger.error("🚨 CRITICAL: Forcing process restart due to persistent failures")
        import os
        os._exit(1)  # Force VM to restart the entire process

# Start supervised bot in non-daemon thread (so Flask waits for it)
bot_thread = Thread(target=run_discord_bot_supervised, daemon=False)
bot_thread.start()

# Update status to show we're ready
update_bot_status('starting')

if __name__ == '__main__':
    logger.info("🚀 Starting production Discord bot deployment...")
    logger.info("Flask app serving on port 5000 with health checks")
    
    # Run Flask app on port 5000
    app.run(host='0.0.0.0', port=5000, debug=False)