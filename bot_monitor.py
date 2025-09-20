#!/usr/bin/env python3
"""
Discord Bot Status Monitor
Sends webhook notifications when bot goes offline/online/restarts
"""

import os
import aiohttp
import asyncio
import logging
import discord
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class BotStatusMonitor:
    def __init__(self):
        self.webhook_url = os.getenv('MONITOR_WEBHOOK_URL')
        self.bot_name = "Rivalz#3030"
        self.last_status = None
        
    def is_enabled(self):
        """Check if monitoring is enabled (webhook URL provided)"""
        return bool(self.webhook_url)
    
    async def send_status_alert(self, status: str, message: str, color: int = 0x3498db, restart_count: int = None):
        """Send status alert to Discord webhook"""
        if not self.is_enabled():
            logger.debug("Monitor webhook not configured, skipping notification")
            return
            
        try:
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            
            # Create embed
            embed = {
                "title": f"🤖 {self.bot_name} Status Alert",
                "description": message,
                "color": color,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "fields": [
                    {
                        "name": "Status",
                        "value": status,
                        "inline": True
                    },
                    {
                        "name": "Time",
                        "value": timestamp,
                        "inline": True
                    }
                ]
            }
            
            # Add restart count if provided
            if restart_count is not None:
                embed["fields"].append({
                    "name": "Restart #",
                    "value": str(restart_count),
                    "inline": True
                })
            
            # Send webhook
            async with aiohttp.ClientSession() as session:
                webhook_data = {
                    "embeds": [embed],
                    "username": "Bot Monitor",
                    "avatar_url": "https://cdn.discordapp.com/embed/avatars/0.png"
                }
                
                async with session.post(self.webhook_url, json=webhook_data) as response:
                    if response.status == 204:
                        logger.info(f"✅ Status alert sent: {status}")
                    else:
                        logger.warning(f"⚠️ Webhook failed with status {response.status}")
                        
        except Exception as e:
            logger.error(f"❌ Failed to send status alert: {e}")
    
    async def notify_bot_starting(self, restart_count: int = 0):
        """Notify that bot is starting"""
        if restart_count == 0:
            await self.send_status_alert(
                "🚀 STARTING",
                f"**{self.bot_name}** is starting up...",
                color=0x3498db,
                restart_count=restart_count
            )
        else:
            await self.send_status_alert(
                "🔄 RESTARTING",
                f"**{self.bot_name}** is restarting after an outage...",
                color=0xf39c12,
                restart_count=restart_count
            )
    
    async def notify_bot_online(self, restart_count: int = 0):
        """Notify that bot is fully online"""
        await self.send_status_alert(
            "✅ ONLINE",
            f"**{self.bot_name}** is now **ONLINE** and responding to commands!",
            color=0x00ff00,
            restart_count=restart_count
        )
        self.last_status = "online"
    
    async def notify_bot_offline(self, reason: str = "Unknown", restart_count: int = None):
        """Notify that bot went offline"""
        if self.last_status == "online":  # Only notify if we were previously online
            await self.send_status_alert(
                "❌ OFFLINE",
                f"**{self.bot_name}** has gone **OFFLINE**!\n**Reason:** {reason}\n**Auto-restart:** Attempting...",
                color=0xe74c3c,
                restart_count=restart_count
            )
        self.last_status = "offline"
    
    async def notify_bot_failed(self, restart_count: int):
        """Notify that bot failed to start after max retries"""
        await self.send_status_alert(
            "💥 FAILED",
            f"**{self.bot_name}** has **FAILED** to start after {restart_count} attempts!\n**Action needed:** Manual intervention required.",
            color=0x992d22,
            restart_count=restart_count
        )

# Global monitor instance
monitor = BotStatusMonitor()

# Convenience functions for use in other modules
async def notify_starting(restart_count: int = 0):
    await monitor.notify_bot_starting(restart_count)

async def notify_online(restart_count: int = 0):
    await monitor.notify_bot_online(restart_count)

async def notify_offline(reason: str = "Connection lost", restart_count: int = None):
    await monitor.notify_bot_offline(reason, restart_count)

async def notify_failed(restart_count: int):
    await monitor.notify_bot_failed(restart_count)

def is_monitoring_enabled():
    return monitor.is_enabled()

# Setup instructions message
SETUP_MESSAGE = """
🔔 **Bot Status Monitor Setup**

To enable automatic notifications when your bot goes offline:

1. **Create a webhook in your Discord server:**
   - Go to Server Settings → Integrations → Webhooks
   - Click "New Webhook"
   - Choose a channel for notifications
   - Copy the webhook URL

2. **Add the webhook URL to your environment:**
   - Add `MONITOR_WEBHOOK_URL` to your Replit Secrets
   - Paste your webhook URL as the value

3. **Restart your bot** and you'll get automatic notifications for:
   ✅ Bot coming online
   ❌ Bot going offline  
   🔄 Bot restarting
   💥 Bot failing to start

**No more manual checking needed!**
"""

if __name__ == "__main__":
    print(SETUP_MESSAGE)