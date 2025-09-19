#!/usr/bin/env python3
"""
Simple test to see if bot responds to ping
"""

import requests
import time

def simple_test():
    """Quick test to see if bot is working"""
    print("Testing Discord bot...")
    
    try:
        response = requests.get('http://localhost:5000/api/status', timeout=5)
        data = response.json()
        
        print(f"Bot connected: {data.get('discord_connected')}")
        print(f"Status: {data.get('status')}")
        print(f"Guilds: {data.get('guilds')}")
        print(f"Uptime: {data.get('uptime')} seconds")
        
        if data.get('discord_connected'):
            print("\n✅ Bot is connected to Discord!")
            print("Try typing !ping in your Discord server")
            return True
        else:
            print("\n❌ Bot is not connected")
            return False
            
    except Exception as e:
        print(f"❌ Error checking bot: {e}")
        return False

if __name__ == "__main__":
    simple_test()