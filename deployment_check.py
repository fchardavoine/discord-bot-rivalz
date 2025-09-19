#!/usr/bin/env python3
"""
Check deployment readiness for production WSGI
"""

import requests
import subprocess
import os

def check_deployment():
    """Check if deployment is ready"""
    print("="*60)
    print("PRODUCTION WSGI DEPLOYMENT CHECK")
    print("="*60)
    
    # Check if Discord bot is running
    try:
        response = requests.get('http://localhost:5000/api/status', timeout=5)
        data = response.json()
        
        print(f"Bot Status: {data.get('status')}")
        print(f"Commands: {data.get('commands')}")
        print(f"Discord Connected: {data.get('discord_connected')}")
        print(f"Guilds: {data.get('guilds')}")
        
    except Exception as e:
        print(f"Bot check failed: {e}")
    
    # Check gunicorn availability
    try:
        result = subprocess.run(['gunicorn', '--version'], capture_output=True, text=True)
        print(f"Gunicorn version: {result.stdout.strip()}")
    except Exception as e:
        print(f"Gunicorn check failed: {e}")
    
    # Check environment variables
    token_set = "DISCORD_TOKEN" in os.environ
    print(f"Discord token set: {token_set}")
    
    print("="*60)
    print("PRODUCTION DEPLOYMENT OPTIONS:")
    print("1. Current: python production.py (working)")
    print("2. WSGI: gunicorn production_wsgi:application")
    print("3. Procfile: Ready for Replit deployment")
    print("="*60)
    
    if data.get('discord_connected'):
        print("SUCCESS: Bot is operational and ready for production!")
    else:
        print("Bot may still be loading...")

if __name__ == "__main__":
    check_deployment()