#!/usr/bin/env python3
"""
Test if Discord bot responds to basic commands
"""

import requests
import time
import subprocess

def check_bot_health():
    """Check bot health comprehensively"""
    try:
        response = requests.get('http://localhost:5000/api/status', timeout=5)
        data = response.json()
        
        print("="*50)
        print("BOT HEALTH CHECK")
        print("="*50)
        print(f"Status: {data.get('status')}")
        print(f"Discord Connected: {data.get('discord_connected')}")
        print(f"Guilds: {data.get('guilds')}")
        print(f"Commands: {data.get('commands')}")
        print(f"Uptime: {data.get('uptime')} seconds")
        print("="*50)
        
        is_healthy = data.get('discord_connected') and data.get('status') == 'healthy'
        
        if is_healthy:
            print("✅ Bot is healthy and connected!")
            print("\nTo test in Discord:")
            print("1. Type !ping in your server")
            print("2. Bot should respond with latency info")
            print("3. If no response, check Discord permissions")
        else:
            print("⚠️ Bot needs attention")
            
        return is_healthy
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def quick_restart():
    """Quick bot restart"""
    print("Performing quick restart...")
    subprocess.run(['pkill', '-f', 'production.py'], capture_output=True)
    time.sleep(2)
    subprocess.Popen(['python', 'production.py'])
    print("Restart initiated")

if __name__ == "__main__":
    if not check_bot_health():
        print("\nAttempting restart...")
        quick_restart()
        time.sleep(10)
        check_bot_health()