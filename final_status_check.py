#!/usr/bin/env python3
"""
Final status check to verify Discord bot uptime
"""

import requests
import time
import subprocess

def comprehensive_status_check():
    """Check bot status comprehensively"""
    print("="*60)
    print("DISCORD BOT UPTIME STATUS CHECK")
    print("="*60)
    
    try:
        response = requests.get('http://localhost:5000/api/status', timeout=5)
        data = response.json()
        
        print(f"✅ Bot Status: {data.get('status')}")
        print(f"✅ Discord Connected: {data.get('discord_connected')}")
        print(f"✅ Commands: {data.get('commands')}")
        print(f"✅ Guilds: {data.get('guilds')}")
        print(f"✅ Uptime: {data.get('uptime')} seconds")
        
        if data.get('discord_connected') and data.get('status') == 'healthy':
            print("\n🎉 SUCCESS: Bot is connected and healthy!")
            print("Bot should now stay online in Discord")
            
            # Check if bot responds to ping in Discord
            print("\nTo test bot in Discord:")
            print("1. Type !ping in your Discord server")
            print("2. Use /ping slash command")
            print("3. Check if bot appears online in member list")
            
            return True
        else:
            print("\n⚠️ Bot may still be connecting...")
            return False
            
    except Exception as e:
        print(f"❌ Status check failed: {e}")
        return False

def monitor_uptime(duration=300):  # 5 minutes
    """Monitor bot uptime for a specific duration"""
    print(f"\nMonitoring bot uptime for {duration} seconds...")
    start_time = time.time()
    checks = 0
    successes = 0
    
    while time.time() - start_time < duration:
        try:
            response = requests.get('http://localhost:5000/api/status', timeout=3)
            data = response.json()
            
            if data.get('discord_connected') and data.get('status') == 'healthy':
                successes += 1
                print(f"✓ Check {checks + 1}: Bot online")
            else:
                print(f"✗ Check {checks + 1}: Bot offline")
            
            checks += 1
            time.sleep(30)  # Check every 30 seconds
            
        except Exception as e:
            print(f"✗ Check {checks + 1}: Error - {e}")
            checks += 1
            time.sleep(30)
    
    uptime_percentage = (successes / checks * 100) if checks > 0 else 0
    print(f"\nUptime Results: {successes}/{checks} checks successful ({uptime_percentage:.1f}%)")
    
    if uptime_percentage >= 80:
        print("🎉 Bot uptime is stable!")
    else:
        print("⚠️ Bot uptime needs improvement")

if __name__ == "__main__":
    # Initial status check
    if comprehensive_status_check():
        # Monitor for 5 minutes if initial check passes
        monitor_uptime(300)
    else:
        print("Bot not ready for uptime monitoring")