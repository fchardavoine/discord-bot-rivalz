#!/usr/bin/env python3
"""
Simple uptime monitoring to verify bot stays connected
"""

import requests
import time
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_bot_status():
    """Check if bot is actually running and connected"""
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
        logger.error(f"Status check failed: {e}")
        return False, None

def restart_bot_if_needed():
    """Restart bot if it's not working properly"""
    logger.info("Restarting bot for better stability...")
    
    try:
        # Kill existing processes
        subprocess.run(['pkill', '-f', 'production.py'], capture_output=True)
        time.sleep(3)
        
        # Start fresh
        subprocess.Popen(['python', 'production.py'])
        logger.info("Bot restarted")
        return True
    except Exception as e:
        logger.error(f"Restart failed: {e}")
        return False

def monitor_uptime():
    """Monitor bot uptime and report results"""
    print("="*60)
    print("DISCORD BOT UPTIME MONITORING")
    print("="*60)
    
    checks = 0
    successes = 0
    
    for i in range(10):  # Check 10 times over 5 minutes
        is_healthy, data = check_bot_status()
        checks += 1
        
        if is_healthy:
            successes += 1
            print(f"✓ Check {checks}: Bot online - Guilds: {data.get('guilds', 0)}")
        else:
            print(f"✗ Check {checks}: Bot offline or unhealthy")
            if checks == 3:  # Restart after 3 failed checks
                restart_bot_if_needed()
                time.sleep(60)  # Wait for restart
        
        time.sleep(30)  # Wait 30 seconds between checks
    
    uptime_rate = (successes / checks * 100) if checks > 0 else 0
    
    print("="*60)
    print(f"UPTIME RESULTS: {successes}/{checks} successful ({uptime_rate:.1f}%)")
    
    if uptime_rate >= 70:
        print("✅ Bot uptime is acceptable")
        print("Your bot should be visible in Discord now")
    else:
        print("❌ Bot uptime is poor - needs manual intervention")
        print("Try checking your Discord token and server settings")
    
    print("="*60)

if __name__ == "__main__":
    monitor_uptime()