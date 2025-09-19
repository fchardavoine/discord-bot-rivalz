#!/usr/bin/env python3
"""
Aggressive bot health check and visibility fix
This script ensures the bot is visible and responding
"""

import discord
import asyncio
import logging
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def force_bot_online():
    """Force bot to appear online with aggressive presence updates"""
    
    # Create bot with maximum intents
    intents = discord.Intents.all()  # Enable ALL intents for maximum visibility
    
    client = discord.Client(intents=intents)
    
    @client.event
    async def on_ready():
        logger.info(f"🚀 HEALTH CHECK - Bot logged in as {client.user}")
        
        # Force status to online with multiple attempts
        for i in range(5):
            try:
                await client.change_presence(
                    status=discord.Status.online,
                    activity=discord.Game(name=f"🔥 LIVE & RESPONDING #{i+1}")
                )
                logger.info(f"✅ Status update #{i+1} successful")
                await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"Status update #{i+1} failed: {e}")
        
        # Test basic functionality
        for guild in client.guilds:
            logger.info(f"🏠 Guild: {guild.name} - Members: {guild.member_count}")
            
            # Find a channel to test response
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    try:
                        embed = discord.Embed(
                            title="🚀 BOT HEALTH CHECK",
                            description="Bot is ONLINE and responding to commands!",
                            color=0x00ff00,
                            timestamp=datetime.utcnow()
                        )
                        embed.add_field(name="Status", value="✅ Fully Operational", inline=True)
                        embed.add_field(name="Guilds", value=len(client.guilds), inline=True)
                        embed.add_field(name="Test Command", value="Try `!ping`", inline=True)
                        
                        await channel.send(embed=embed)
                        logger.info(f"✅ Health check message sent to #{channel.name}")
                        break
                    except Exception as e:
                        logger.error(f"Failed to send health check: {e}")
        
        # Wait 10 seconds then disconnect
        await asyncio.sleep(10)
        await client.close()
        logger.info("🔄 Health check complete - returning to main bot")
    
    # Get token and run health check
    token = os.getenv('DISCORD_TOKEN')
    if token:
        try:
            await client.start(token)
        except Exception as e:
            logger.error(f"Health check failed: {e}")
    else:
        logger.error("No Discord token found")

if __name__ == "__main__":
    asyncio.run(force_bot_online())