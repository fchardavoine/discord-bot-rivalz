from flask import Flask, jsonify
from threading import Thread
import logging
import os
import asyncio
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

# Create Flask app for keeping the bot alive on Replit
app = Flask('')

# Bot status tracking
bot_status = {
    'status': 'starting',
    'start_time': None,
    'guilds': 0,
    'last_check': None
}


def update_bot_status(status, guilds=0):
    """Update bot status information"""
    global bot_status
    bot_status['status'] = status
    bot_status['guilds'] = guilds
    bot_status['last_check'] = datetime.utcnow().isoformat()
    if status == 'connected' and not bot_status['start_time']:
        bot_status['start_time'] = datetime.utcnow().isoformat()


@app.route('/')
def home():
    """Simple endpoint to keep the bot alive"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Discord Bot Status</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                text-align: center; 
                margin-top: 50px;
                background-color: #f0f0f0;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 10px;
                display: inline-block;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            .status {
                color: #00ff00;
                font-size: 24px;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Discord Bot</h1>
            <p class="status">✅ Bot is running!</p>
            <p>This endpoint keeps the bot alive on Replit.</p>
            <p>Your Discord bot is operational and ready to serve commands!</p>
        </div>
    </body>
    </html>
    '''


@app.route('/health')
def health():
    """Health check endpoint for deployment"""
    return jsonify({
        'status': 'healthy',
        'message': 'Discord bot is operational',
        'bot_status': bot_status['status'],
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/api/status')
def api_status():
    """Detailed API status endpoint"""
    return jsonify(bot_status)


def run_flask():
    """Run the Flask app"""
    try:
        logger.info("Starting Flask server on port 5000...")
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    except Exception as e:
        logger.error(f"Failed to start keep-alive server: {e}")


def keep_alive():
    """Start the keep-alive server in a separate thread"""
    try:
        t = Thread(target=run_flask)
        t.daemon = True
        t.start()
        logger.info("Keep-alive server started on port 5000")
    except Exception as e:
        logger.error(f"Failed to start keep-alive thread: {e}")


def run_as_main():
    """Run Flask as the main process for deployment"""
    try:
        logger.info("Starting Flask server as main process on port 5000...")
        # Start Discord bot in background thread
        from threading import Thread

        def start_discord_bot():
            try:
                import main
                main.start_discord_bot_only()
            except Exception as e:
                logger.error(f"Failed to start Discord bot: {e}")
                update_bot_status('error')

        # Start bot in background
        bot_thread = Thread(target=start_discord_bot)
        bot_thread.daemon = True
        bot_thread.start()

        # Run Flask as main process
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    except Exception as e:
        logger.error(f"Failed to start main server: {e}")
        raise
