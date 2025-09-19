# Twitch Streaming Notifications - Discord Bot Integration
# Real-time notifications when streamers go live using Twitch EventSub

import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import asyncio
import json
import time
import hashlib
import hmac
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import os
from sqlalchemy import text

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TwitchNotifications:
    def __init__(self, bot):
        self.bot = bot
        # Load credentials from environment variables
        self.client_id = os.getenv('TWITCH_CLIENT_ID')
        self.client_secret = os.getenv('TWITCH_CLIENT_SECRET') 
        self.webhook_secret = os.getenv('TWITCH_WEBHOOK_SECRET')
        self.access_token = None
        self.webhook_url = None
        self.subscriptions = {}
        
        # Log credential status (without exposing secrets)
        logger.info(f"Twitch API setup - Client ID: {'✅' if self.client_id else '❌'}, Client Secret: {'✅' if self.client_secret else '❌'}")
        # Don't initialize database immediately - wait for bot to be ready
        
    def init_database(self):
        """Initialize database tables for Twitch notifications"""
        try:
            # Import database and context from main database module
            from db_app import db, app
            
            with app.app_context():
                # Create Twitch tables using raw SQL via SQLAlchemy
                with db.engine.connect() as connection:
                    connection.execute(text('''
                        CREATE TABLE IF NOT EXISTS twitch_streamers (
                            id SERIAL PRIMARY KEY,
                            guild_id BIGINT NOT NULL,
                            channel_id BIGINT NOT NULL,
                            streamer_name TEXT NOT NULL,
                            streamer_id TEXT,
                            is_live BOOLEAN DEFAULT FALSE,
                            last_notification TIMESTAMP,
                            custom_message TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(guild_id, channel_id, streamer_name)
                        )
                    '''))
                    
                    # Notification settings table
                    connection.execute(text('''
                        CREATE TABLE IF NOT EXISTS twitch_settings (
                            guild_id BIGINT PRIMARY KEY,
                            webhook_channel_id BIGINT,
                            role_mention TEXT,
                            notification_color INTEGER DEFAULT 6570404,
                            include_game BOOLEAN DEFAULT TRUE,
                            include_preview BOOLEAN DEFAULT TRUE,
                            cooldown_minutes INTEGER DEFAULT 5
                        )
                    '''))
                    
                    # Add paused columns if they don't exist (schema safety)
                    connection.execute(text('''
                        ALTER TABLE twitch_settings 
                        ADD COLUMN IF NOT EXISTS paused BOOLEAN DEFAULT FALSE
                    '''))
                    
                    connection.execute(text('''
                        ALTER TABLE twitch_streamers 
                        ADD COLUMN IF NOT EXISTS paused BOOLEAN DEFAULT FALSE
                    '''))
                    
                    connection.commit()
                
                db.session.commit()
                logger.info("✅ Twitch notifications database tables created")
            
        except Exception as e:
            logger.error(f"❌ Failed to create Twitch database tables: {e}")
    
    async def get_access_token(self):
        """Get OAuth access token from Twitch"""
        if not self.client_id or not self.client_secret:
            return None
            
        url = "https://id.twitch.tv/oauth2/token"
        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.access_token = data['access_token']
                        return self.access_token
                    else:
                        logger.error(f"Failed to get Twitch access token: {resp.status}")
                        return None
        except Exception as e:
            logger.error(f"Error getting Twitch access token: {e}")
            return None
    
    async def get_user_id(self, username: str):
        """Get Twitch user ID from username"""
        if not self.access_token:
            await self.get_access_token()
            
        if not self.access_token:
            return None
            
        url = f"https://api.twitch.tv/helix/users?login={username}"
        headers = {
            'Client-ID': self.client_id,
            'Authorization': f'Bearer {self.access_token}'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data['data']:
                            return data['data'][0]['id']
                    return None
        except Exception as e:
            logger.error(f"Error getting Twitch user ID: {e}")
            return None
    
    async def get_stream_info(self, user_id: str):
        """Get current stream information"""
        if not self.access_token:
            await self.get_access_token()
            
        url = f"https://api.twitch.tv/helix/streams?user_id={user_id}"
        headers = {
            'Client-ID': self.client_id,
            'Authorization': f'Bearer {self.access_token}'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data['data'][0] if data['data'] else None
                    return None
        except Exception as e:
            logger.error(f"Error getting stream info: {e}")
            return None
    
    async def send_notification(self, streamer_data: dict, stream_info: dict, guild_id: int, channel_id: int, custom_message: Optional[str] = None):
        """Send Discord notification for live stream"""
        try:
            logger.info(f"🔍 DEBUG: Attempting to send notification for {streamer_data.get('display_name', 'Unknown')} to channel {channel_id}")
            channel = self.bot.get_channel(channel_id)
            if not channel:
                logger.error(f"❌ DEBUG: Channel {channel_id} not found in bot cache")
                return
            
            logger.info(f"✅ DEBUG: Found channel {channel.name} ({channel_id}) in guild {channel.guild.name}")
            
            # Get guild settings with explicit column selection
            from db_app import db, app
            with app.app_context():
                with db.engine.connect() as connection:
                    result = connection.execute(text('''
                        SELECT role_mention, notification_color, include_game, include_preview 
                        FROM twitch_settings WHERE guild_id = :guild_id
                    '''), {'guild_id': guild_id})
                    settings = result.fetchone()
            
            # Parse settings with correct column mapping
            role_mention = settings[0] if settings else None
            notification_color = settings[1] if settings else None
            include_game = settings[2] if settings and settings[2] is not None else True
            include_preview = settings[3] if settings and settings[3] is not None else True
            
            # Ensure color is always an integer - use Twitch purple unless custom color is set
            color_value = 0x9146FF  # Default Twitch purple
            if notification_color is not None:
                try:
                    val = int(notification_color) if not isinstance(notification_color, int) else notification_color
                    # Don't use legacy default (6570404), stick with Twitch purple
                    if val != 6570404:
                        color_value = val
                except (ValueError, TypeError):
                    color_value = 0x9146FF
            
            embed = discord.Embed(
                title=f"{streamer_data['display_name']} is now live on Twitch!",
                description=stream_info.get('title', 'No title'),
                url=f"https://twitch.tv/{streamer_data['login']}",
                color=color_value,
                timestamp=datetime.utcnow()
            )
            
            # Add stream details with inline layout matching reference image
            if include_game:
                embed.add_field(name="Game", value=stream_info.get('game_name', 'Unknown'), inline=True)
            
            embed.add_field(name="Viewers", value=str(stream_info.get('viewer_count', 0)), inline=True)
            
            # Set crisp large preview image with cache-buster
            logger.info(f"🖼️ DEBUG: Starting preview image handling - include_preview: {include_preview}")
            if include_preview and stream_info.get('thumbnail_url'):
                import time
                thumbnail_url = stream_info['thumbnail_url'].replace('{width}', '1280').replace('{height}', '720')
                final_url = f"{thumbnail_url}?t={int(time.time())}"
                logger.info(f"🖼️ Setting preview image: {final_url}")
                embed.set_image(url=final_url)
                logger.info(f"✅ Preview image set successfully")
            else:
                logger.info(f"🖼️ Preview image NOT set - include_preview: {include_preview}, thumbnail_url: {stream_info.get('thumbnail_url', 'None')}")
            
            # Set author with streamer icon - matching screenshot format
            embed.set_author(name=streamer_data['display_name'], icon_url=streamer_data.get('profile_image_url'))
            embed.set_footer(text="🎬 Twitch Stream Alert | Today at {}".format(datetime.now().strftime("%I:%M %p")), icon_url="https://static.twitchcdn.net/assets/favicon-32-d6025c14e900565d6177.png")
            
            # Prepare message content
            content = custom_message or f"**{streamer_data['display_name']}** just went live!"
            
            # Add role mention if configured
            if role_mention:
                content = f"{role_mention} {content}"
            
            # Create "Watch Stream" button
            class StreamView(discord.ui.View):
                def __init__(self, stream_url: str):
                    super().__init__(timeout=None)  # Persistent button
                    
                    # Create button that links to the stream
                    button = discord.ui.Button(
                        label="📺 Watch Live",
                        style=discord.ButtonStyle.link,
                        url=stream_url
                    )
                    self.add_item(button)
            
            # Send notification with button
            stream_url = f"https://twitch.tv/{streamer_data['login']}"
            view = StreamView(stream_url)
            
            await channel.send(content=content, embed=embed, view=view)
            
            # Update database
            with app.app_context():
                with db.engine.connect() as connection:
                    connection.execute(text('''
                        UPDATE twitch_streamers 
                        SET is_live = TRUE, last_notification = CURRENT_TIMESTAMP
                        WHERE guild_id = :guild_id AND streamer_name = :streamer_name
                    '''), {
                        'guild_id': guild_id,
                        'streamer_name': streamer_data['login']
                    })
                    connection.commit()
            
            logger.info(f"✅ Sent notification for {streamer_data['display_name']} in guild {guild_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to send notification: {e}")

    async def check_all_streams(self):
        """Check all monitored streamers for live status"""
        import time
        start_time = time.time()  # Initialize at the beginning 
        try:
            from db_app import db, app
            with app.app_context():
                with db.engine.connect() as connection:
                    # Get all streamers from database including pause status
                    result = connection.execute(text('''
                        SELECT guild_id, channel_id, streamer_name, streamer_id, is_live, custom_message, last_notification, paused
                        FROM twitch_streamers
                    '''))
                    streamers = result.fetchall()
            
            if not streamers:
                return
            
            logger.info(f"🔍 Checking {len(streamers)} streamers for live status...")
            
            # Check each streamer
            for guild_id, channel_id, streamer_name, streamer_id, is_live, custom_message, last_notification, streamer_paused in streamers:
                try:
                    # Get current stream status
                    stream_info = await self.get_stream_info(streamer_id)
                    
                    # Get user info for display name and profile
                    user_info = await self.get_user_info(streamer_id)
                    
                    if stream_info and not is_live:
                        # Check if notifications are paused for this individual streamer
                        if streamer_paused:
                            logger.info(f"⏸️ STREAMER PAUSED: {streamer_name} went live but this streamer is paused")
                        else:
                            # Streamer just went live - send notification
                            logger.info(f"🔴 DETECTED: {streamer_name} just went live!")
                            if user_info:
                                await self.send_notification(user_info, stream_info, guild_id, channel_id, custom_message)
                                logger.info(f"✅ NOTIFICATION SENT: {streamer_name} in {(time.time() - start_time):.1f}s")
                    
                    elif not stream_info and is_live:
                        # Streamer went offline - update database
                        with app.app_context():
                            with db.engine.connect() as connection:
                                connection.execute(text('''
                                    UPDATE twitch_streamers 
                                    SET is_live = FALSE
                                    WHERE guild_id = :guild_id AND streamer_name = :streamer_name
                                '''), {
                                    'guild_id': guild_id,
                                    'streamer_name': streamer_name
                                })
                                connection.commit()
                        logger.info(f"⚫ {streamer_name} went offline")
                        
                except Exception as e:
                    logger.error(f"Error checking stream for {streamer_name}: {e}")
            
            total_time = time.time() - start_time
            logger.info(f"⏱️ Stream check completed in {total_time:.1f}s")
                    
        except Exception as e:
            logger.error(f"Error in check_all_streams: {e}")
            logger.info(f"⏱️ Stream check failed after {(time.time() - start_time):.1f}s")

    async def get_user_info(self, user_id: str):
        """Get user information by ID"""
        if not self.access_token:
            await self.get_access_token()
            
        url = f"https://api.twitch.tv/helix/users?id={user_id}"
        headers = {
            'Client-ID': self.client_id,
            'Authorization': f'Bearer {self.access_token}'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data['data'][0] if data['data'] else None
                    return None
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return None


    async def start_monitoring(self):
        """Start the background monitoring loop"""
        logger.info("🔄 Starting Twitch stream monitoring...")
        while True:
            try:
                await self.check_all_streams()
                await asyncio.sleep(15)  # Check every 15 seconds - near minimum safe limit
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Continue even if there's an error

def setup_twitch_notifications(bot):
    """Setup Twitch notification commands"""
    twitch = TwitchNotifications(bot)
    
    # Initialize database and start monitoring after bot is ready
    async def _twitch_on_ready():
        if not hasattr(bot, '_twitch_db_initialized'):
            twitch.init_database()
            bot._twitch_db_initialized = True
            
            # Start monitoring in background
            bot.loop.create_task(twitch.start_monitoring())
            
    
    bot.add_listener(_twitch_on_ready, 'on_ready')
    
    # Group for Twitch commands
    twitch_group = app_commands.Group(name="twitch", description="Twitch streaming notifications")
    
    @twitch_group.command(name="add", description="Add a Twitch streamer to watch")
    @app_commands.describe(
        streamer="Twitch username to watch",
        channel="Discord channel for notifications (optional, defaults to current)",
        message="Custom notification message (optional)"
    )
    async def add_streamer(interaction: discord.Interaction, streamer: str, channel: Optional[discord.TextChannel] = None, message: Optional[str] = None):
        """Add a Twitch streamer to watch for live notifications"""
        
        # Check if user has manage guild permissions (must be a Member in a guild)
        if not interaction.guild or not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("❌ You need `Manage Server` permission to manage Twitch notifications!", ephemeral=True)
        
        await interaction.response.defer()
        
        try:
            target_channel = channel or interaction.channel
            guild_id = interaction.guild.id if interaction.guild else 0
            
            # Check if streamer exists on Twitch
            streamer_id = await twitch.get_user_id(streamer.lower())
            if not streamer_id:
                return await interaction.followup.send(f"❌ Twitch user `{streamer}` not found!", ephemeral=True)
            
            # Add to database
            from db_app import db, app
            with app.app_context():
                try:
                    with db.engine.connect() as connection:
                        connection.execute(text('''
                            INSERT INTO twitch_streamers (guild_id, channel_id, streamer_name, streamer_id, custom_message)
                            VALUES (:guild_id, :channel_id, :streamer_name, :streamer_id, :custom_message)
                        '''), {
                            'guild_id': guild_id,
                            'channel_id': target_channel.id if target_channel and hasattr(target_channel, 'id') else 0,
                            'streamer_name': streamer.lower(),
                            'streamer_id': streamer_id,
                            'custom_message': message
                        })
                        connection.commit()
                    
                    embed = discord.Embed(
                        title="✅ Streamer Added",
                        description=f"Now watching **{streamer}** for live notifications",
                        color=0x00ff00
                    )
                    # Format channel display
                    if target_channel and isinstance(target_channel, discord.TextChannel):
                        channel_display = target_channel.mention
                    elif target_channel:
                        channel_display = str(target_channel)
                    else:
                        channel_display = "Unknown"
                    embed.add_field(name="Channel", value=channel_display, inline=True)
                    embed.add_field(name="Streamer", value=f"[{streamer}](https://twitch.tv/{streamer})", inline=True)
                    if message:
                        embed.add_field(name="Custom Message", value=message, inline=False)
                    
                    await interaction.followup.send(embed=embed)
                    
                except Exception as integrity_error:
                    if "duplicate key" in str(integrity_error).lower() or "unique constraint" in str(integrity_error).lower():
                        # Format channel display for error message
                        if target_channel and isinstance(target_channel, discord.TextChannel):
                            channel_mention = target_channel.mention
                        elif target_channel:
                            channel_mention = str(target_channel)
                        else:
                            channel_mention = "Unknown"
                        await interaction.followup.send(f"❌ `{streamer}` is already being watched in {channel_mention}!", ephemeral=True)
                    else:
                        raise integrity_error
                
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to add streamer: {e}", ephemeral=True)
    
    @twitch_group.command(name="remove", description="Remove a Twitch streamer from watch list")
    @app_commands.describe(streamer="Twitch username to stop watching (optional - leave blank for menu)")
    async def remove_streamer(interaction: discord.Interaction, streamer: Optional[str] = None):
        """Remove a Twitch streamer from watch list"""
        
        # Check if user has manage guild permissions (must be a Member in a guild)
        if not interaction.guild or not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("❌ You need `Manage Server` permission to manage Twitch notifications!", ephemeral=True)
        
        # If no streamer specified, show interactive menu
        if not streamer:
            return await show_streamer_select_menu(interaction, "remove")
        
        try:
            from db_app import db, app
            with app.app_context():
                with db.engine.connect() as connection:
                    result = connection.execute(text('''
                        DELETE FROM twitch_streamers 
                        WHERE guild_id = :guild_id AND streamer_name = :streamer_name
                    '''), {
                        'guild_id': interaction.guild.id if interaction.guild else 0,
                        'streamer_name': streamer.lower()
                    })
                    
                    if result.rowcount > 0:
                        connection.commit()
                        embed = discord.Embed(
                            title="✅ Streamer Removed",
                            description=f"No longer watching **{streamer}** for live notifications",
                            color=0xff0000
                        )
                        await interaction.response.send_message(embed=embed)
                    else:
                        await interaction.response.send_message(f"❌ `{streamer}` is not in the watch list!", ephemeral=True)
                
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to remove streamer: {e}", ephemeral=True)
    
    @twitch_group.command(name="edit", description="Edit settings for an existing Twitch streamer")
    async def edit_streamer(interaction: discord.Interaction):
        """Edit settings for an existing Twitch streamer"""
        
        # Check if user has manage guild permissions (must be a Member in a guild)
        if not interaction.guild or not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("❌ You need `Manage Server` permission to manage Twitch notifications!", ephemeral=True)
        
        # Always show the interactive picker
        return await show_streamer_list_for_edit(interaction)
    
    @twitch_group.command(name="list", description="List all watched Twitch streamers")
    async def list_streamers(interaction: discord.Interaction):
        """List all watched Twitch streamers for this server"""
        
        try:
            from db_app import db, app
            with app.app_context():
                with db.engine.connect() as connection:
                    result = connection.execute(text('''
                        SELECT streamer_name, channel_id, is_live, custom_message, paused
                        FROM twitch_streamers 
                        WHERE guild_id = :guild_id
                        ORDER BY streamer_name
                    '''), {
                        'guild_id': interaction.guild.id if interaction.guild else 0
                    })
                    
                    streamers = result.fetchall()
            
            if not streamers:
                return await interaction.response.send_message("📺 No Twitch streamers are being watched in this server.", ephemeral=True)
            
            # Create embed with standard title and description
            embed = discord.Embed(
                title="📺 Watched Twitch Streamers",
                description=f"Monitoring {len(streamers)} streamers for live notifications",
                color=0x9146FF
            )
            
            live_streamers = []
            offline_streamers = []
            paused_streamers = []
            
            for streamer_name, channel_id, is_live, custom_message, paused in streamers:
                channel = bot.get_channel(channel_id)
                
                # Determine status with pause indicators (only individual streamer pause)
                if paused:
                    status = "⏸️ PAUSED"
                    base_info = f"{status} [{streamer_name}](https://twitch.tv/{streamer_name})"
                elif is_live:
                    status = "🔴 LIVE"
                    base_info = f"{status} [{streamer_name}](https://twitch.tv/{streamer_name})"
                else:
                    status = "⚫ Offline"
                    base_info = f"{status} [{streamer_name}](https://twitch.tv/{streamer_name})"
                
                streamer_info = base_info
                if channel:
                    streamer_info += f" → {channel.mention}"
                
                # Categorize streamers (only individual pause matters)
                if paused:
                    paused_streamers.append(streamer_info)
                elif is_live:
                    live_streamers.append(streamer_info)
                else:
                    offline_streamers.append(streamer_info)
            
            # Helper function to split long lists into multiple fields
            def add_streamer_fields(embed, streamers_list, field_name, emoji):
                if not streamers_list:
                    return
                
                # Discord embed field value limit is 1024 characters
                MAX_FIELD_LENGTH = 1024
                current_field = []
                current_length = 0
                field_count = 0
                
                for streamer in streamers_list:
                    # Add 1 for newline character
                    streamer_length = len(streamer) + 1
                    
                    # If adding this streamer would exceed the limit, create a new field
                    if current_length + streamer_length > MAX_FIELD_LENGTH and current_field:
                        field_count += 1
                        name = field_name if field_count == 1 else f"{field_name} (continued)"
                        embed.add_field(name=name, value='\n'.join(current_field), inline=False)
                        current_field = [streamer]
                        current_length = streamer_length
                    else:
                        current_field.append(streamer)
                        current_length += streamer_length
                
                # Add any remaining streamers
                if current_field:
                    field_count += 1
                    name = field_name if field_count == 1 else f"{field_name} (continued)"
                    embed.add_field(name=name, value='\n'.join(current_field), inline=False)
            
            # Add fields with proper length handling
            add_streamer_fields(embed, live_streamers, "🔴 Currently Live", "🔴")
            add_streamer_fields(embed, paused_streamers, "⏸️ Paused Notifications", "⏸️")
            add_streamer_fields(embed, offline_streamers, "⚫ Offline", "⚫")
            
            # Set footer
            footer_text = "Use /twitch add to watch more streamers"
            embed.set_footer(text=footer_text)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to list streamers: {e}", ephemeral=True)
    
    @twitch_group.command(name="settings", description="Configure Twitch notification settings")
    @app_commands.describe(
        role="Role to mention in notifications (optional)",
        color="Embed color as hex code without # (optional)",
        include_game="Include game name in notifications",
        include_preview="Include stream preview image",
        reset="Reset all settings to defaults (overrides other options)"
    )
    async def configure_settings(interaction: discord.Interaction, role: Optional[discord.Role] = None, color: Optional[str] = None, include_game: Optional[bool] = None, include_preview: Optional[bool] = None, reset: Optional[bool] = None):
        """Configure Twitch notification settings for this server"""
        
        # Check if user has manage guild permissions (must be a Member in a guild)
        if not interaction.guild or not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("❌ You need `Manage Server` permission to configure Twitch settings!", ephemeral=True)
        
        try:
            guild_id = interaction.guild.id if interaction.guild else 0
            from db_app import db, app
            
            with app.app_context():
                with db.engine.connect() as connection:
                    # Check if reset was requested
                    if reset:
                        # Reset to default values (overrides all other options)
                        role_mention = None
                        embed_color = 0x9146FF  # Default Twitch purple
                        game_setting = True
                        preview_setting = True
                    else:
                        # Get current settings
                        result = connection.execute(text('SELECT * FROM twitch_settings WHERE guild_id = :guild_id'), {'guild_id': guild_id})
                        current = result.fetchone()
                        
                        # Prepare update values - fix column indices 
                        role_mention = role.mention if role else (current[2] if current else None)
                        embed_color = int(color, 16) if color else (current[3] if current else 0x9146FF)
                        game_setting = include_game if include_game is not None else (current[4] if current else True)
                        preview_setting = include_preview if include_preview is not None else (current[5] if current else True)
                    
                    # Update or insert settings using PostgreSQL UPSERT
                    connection.execute(text('''
                        INSERT INTO twitch_settings (guild_id, role_mention, notification_color, include_game, include_preview)
                        VALUES (:guild_id, :role_mention, :notification_color, :include_game, :include_preview)
                        ON CONFLICT (guild_id) DO UPDATE SET
                            role_mention = EXCLUDED.role_mention,
                            notification_color = EXCLUDED.notification_color,
                            include_game = EXCLUDED.include_game,
                            include_preview = EXCLUDED.include_preview
                    '''), {
                        'guild_id': guild_id,
                        'role_mention': role_mention,
                        'notification_color': embed_color,
                        'include_game': game_setting,
                        'include_preview': preview_setting
                    })
                    
                    connection.commit()
            
            # Update title if settings were reset
            title = "✅ Twitch Settings Reset to Defaults" if reset else "✅ Twitch Settings Updated"
            
            embed = discord.Embed(
                title=title,
                color=embed_color
            )
            embed.add_field(name="Role Mention", value=role_mention or "None", inline=True)
            embed.add_field(name="Embed Color", value=f"#{embed_color:06x}", inline=True)
            embed.add_field(name="Include Game", value="✅" if game_setting else "❌", inline=True)
            embed.add_field(name="Include Preview", value="✅" if preview_setting else "❌", inline=True)
            
            await interaction.response.send_message(embed=embed)
            
        except ValueError:
            await interaction.response.send_message("❌ Invalid color code! Use hex format without # (e.g., FF0000)", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to update settings: {e}", ephemeral=True)
    
    @twitch_group.command(name="pause", description="Pause Twitch notifications for specific streamers")
    async def pause_notifications(interaction: discord.Interaction):
        """Pause Twitch notifications for specific streamers"""
        return await handle_pause_action(interaction, "multiple")
    
    @twitch_group.command(name="resume", description="Resume Twitch notifications for specific streamers")
    async def resume_notifications(interaction: discord.Interaction):
        """Resume Twitch notifications for specific streamers"""
        return await handle_resume_action(interaction, "multiple")
    
    @twitch_group.command(name="test", description="Test notification system with fake notification")
    async def test_notification(interaction: discord.Interaction):
        """Test the notification system with a fake notification"""
        
        # Check if user has manage guild permissions
        if not interaction.guild or not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("❌ You need `Manage Server` permission to test notifications!", ephemeral=True)
        
        await interaction.response.defer()
        
        try:
            from db_app import db, app
            
            # Get first streamer from database for testing
            with app.app_context():
                with db.engine.connect() as connection:
                    result = connection.execute(text('''
                        SELECT channel_id, streamer_name FROM twitch_streamers 
                        WHERE guild_id = :guild_id LIMIT 1
                    '''), {'guild_id': interaction.guild.id})
                    streamer_row = result.fetchone()
            
            if not streamer_row:
                return await interaction.followup.send("❌ No streamers found to test with. Add a streamer first with `/twitch add`!", ephemeral=True)
            
            channel_id, streamer_name = streamer_row
            
            # Create fake streamer and stream data for testing
            fake_streamer_data = {
                'display_name': 'TestStreamer',
                'login': streamer_name,
                'profile_image_url': 'https://static-cdn.jtvnw.net/user-default-pictures/de130ab0-def7-11e9-b668-784f43822e80-profile_image-300x300.png'
            }
            
            fake_stream_data = {
                'title': '🧪 TEST NOTIFICATION - This is a test stream',
                'game_name': 'Software Testing',
                'viewer_count': 1337,
                'thumbnail_url': 'https://static-cdn.jtvnw.net/ttv-boxart/509658-{width}x{height}.jpg',
                'tag_ids': ['test', 'debug']
            }
            
            # Create test button view
            class TestStreamView(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=None)
                    
                    button = discord.ui.Button(
                        label="📺 Watch Live",
                        style=discord.ButtonStyle.link,
                        url=f"https://twitch.tv/{streamer_name}"
                    )
                    self.add_item(button)
            
            # Get guild settings to match live notification format
            guild_id = interaction.guild.id if interaction.guild else 0
            from db_app import db, app
            with app.app_context():
                with db.engine.connect() as connection:
                    result = connection.execute(text('''
                        SELECT role_mention, notification_color, include_game, include_preview 
                        FROM twitch_settings WHERE guild_id = :guild_id
                    '''), {'guild_id': guild_id})
                    settings = result.fetchone()
            
            # Parse settings with correct column mapping (same as live notification)
            role_mention = settings[0] if settings else None
            notification_color = settings[1] if settings else None
            include_game = settings[2] if settings and settings[2] is not None else True
            include_preview = settings[3] if settings and settings[3] is not None else True
            
            # Ensure color matches live notification logic
            color_value = 0x9146FF  # Default Twitch purple
            if notification_color is not None:
                try:
                    val = int(notification_color) if not isinstance(notification_color, int) else notification_color
                    # Don't use legacy default (6570404), stick with Twitch purple
                    if val != 6570404:
                        color_value = val
                except (ValueError, TypeError):
                    color_value = 0x9146FF
            
            # Create test embed exactly matching live notification format
            embed = discord.Embed(
                title="TestStreamer is now live on Twitch!",
                description="🧪 TEST NOTIFICATION - This is a test stream",
                url=f"https://twitch.tv/{streamer_name}",
                color=color_value,
                timestamp=datetime.utcnow()
            )
            
            # Add stream details with inline layout matching live notification
            if include_game:
                embed.add_field(name="Game", value="Software Testing", inline=True)
            
            embed.add_field(name="Viewers", value="1337", inline=True)
            
            # Add large preview image only if settings allow it
            if include_preview:
                embed.set_image(url="https://static-cdn.jtvnw.net/ttv-boxart/509658-800x450.jpg")
            
            embed.set_author(name="TestStreamer", icon_url='https://static-cdn.jtvnw.net/user-default-pictures/de130ab0-def7-11e9-b668-784f43822e80-profile_image-300x300.png')
            embed.set_footer(text="🎬 Twitch Stream Alert | Today at {}".format(datetime.now().strftime("%I:%M %p")), icon_url="https://static.twitchcdn.net/assets/favicon-32-d6025c14e900565d6177.png")
            
            # Prepare message content matching live notification format
            content = "**TestStreamer** just went live!"
            
            # Add role mention if configured (same as live notification)
            if role_mention:
                content = f"{role_mention} {content}"
            
            # Add test indicator
            content = f"🧪 **TEST NOTIFICATION** - {content}"
            
            # Send test notification with button
            view = TestStreamView()
            channel = bot.get_channel(channel_id)
            await channel.send(
                content=content,
                embed=embed,
                view=view
            )
            
            channel_mention = channel.mention if channel else f"<#{channel_id}>"
            
            await interaction.followup.send(f"✅ Test notification sent to {channel_mention}!\nIf you don't see it, check the channel permissions or logs.")
            
        except Exception as e:
            await interaction.followup.send(f"❌ Test failed: {e}", ephemeral=True)






    @twitch_group.command(name="check", description="Manually check if a streamer is live")
    @app_commands.describe(streamer="Twitch username to check")
    async def check_streamer(interaction: discord.Interaction, streamer: str):
        """Manually check if a Twitch streamer is currently live"""
        
        await interaction.response.defer()
        
        try:
            # Get streamer ID
            streamer_id = await twitch.get_user_id(streamer.lower())
            if not streamer_id:
                return await interaction.followup.send(f"❌ Twitch user `{streamer}` not found!")
            
            # Get stream info
            stream_info = await twitch.get_stream_info(streamer_id)
            
            if stream_info:
                embed = discord.Embed(
                    title=f"🔴 {streamer} is LIVE!",
                    description=stream_info.get('title', 'No title'),
                    url=f"https://twitch.tv/{streamer}",
                    color=0x00ff00
                )
                embed.add_field(name="Game", value=stream_info.get('game_name', 'Unknown'), inline=True)
                embed.add_field(name="Viewers", value=str(stream_info.get('viewer_count', 0)), inline=True)
                embed.add_field(name="Started", value=f"<t:{int(datetime.fromisoformat(stream_info['started_at'].replace('Z', '+00:00')).timestamp())}:R>", inline=True)
                
                if stream_info.get('thumbnail_url'):
                    thumbnail_url = stream_info['thumbnail_url'].replace('{width}', '320').replace('{height}', '180')
                    embed.set_thumbnail(url=thumbnail_url)
                    
            else:
                embed = discord.Embed(
                    title=f"⚫ {streamer} is offline",
                    description="This streamer is not currently live",
                    color=0x808080
                )
            
            embed.set_footer(text="Manual stream check")
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to check streamer: {e}")
    
    # Add autocomplete for streamer parameter (must be defined before commands)
    async def streamer_autocomplete_consolidated(interaction: discord.Interaction, current: str):
        """Provide autocomplete suggestions for streamer names"""
        try:
            if not interaction.guild:
                return []
                
            from db_app import db, app
            with app.app_context():
                with db.engine.connect() as connection:
                    result = connection.execute(text('''
                        SELECT DISTINCT streamer_name 
                        FROM twitch_streamers 
                        WHERE guild_id = :guild_id AND streamer_name LIKE :pattern
                        LIMIT 25
                    '''), {
                        'guild_id': interaction.guild.id,
                        'pattern': f'%{current.lower()}%'
                    })
                    
                    streamers = [row[0] for row in result.fetchall()]
                    return [
                        app_commands.Choice(name=streamer.title(), value=streamer)
                        for streamer in streamers
                    ]
        except Exception:
            return []

    async def streamers_multiple_autocomplete(interaction: discord.Interaction, current: str):
        """Enhanced autocomplete for multiple streamers with status indicators for standalone commands"""
        try:
            if not interaction.guild:
                return []
                
            from db_app import db, app
            with app.app_context():
                with db.engine.connect() as connection:
                    # Parse existing streamers from current input
                    current_text = current.lower()
                    if ',' in current_text:
                        # User is typing multiple streamers
                        parts = [s.strip() for s in current_text.split(',')]
                        last_part = parts[-1] if parts else ""
                        prefix_parts = parts[:-1] if len(parts) > 1 else []
                        prefix = ", ".join(prefix_parts)
                        if prefix:
                            prefix += ", "
                    else:
                        # User is typing first/only streamer
                        last_part = current_text.strip()
                        prefix = ""
                    
                    # Get already selected streamers to exclude them
                    existing_streamers = []
                    if ',' in current_text:
                        existing_streamers = [s.strip() for s in current_text.split(',')[:-1] if s.strip()]
                    
                    # Get streamers that match the last part being typed
                    result = connection.execute(text('''
                        SELECT streamer_name, streamer_id, is_live, paused 
                        FROM twitch_streamers 
                        WHERE guild_id = :guild_id 
                        AND streamer_name LIKE :pattern
                        ORDER BY 
                            CASE 
                                WHEN paused THEN 2
                                WHEN is_live THEN 0  
                                ELSE 1
                            END,
                            streamer_name
                        LIMIT 20
                    '''), {
                        'guild_id': interaction.guild.id,
                        'pattern': f'%{last_part}%'
                    })
                    
                    choices = []
                    for row in result.fetchall():
                        streamer_name, streamer_id, is_live, paused = row
                        
                        # Skip if streamer is already in the list
                        if streamer_name in existing_streamers:
                            continue
                        
                        # Determine status indicator
                        if paused:
                            status_icon = "⏸️ PAUSED"
                        elif is_live:
                            status_icon = "🔴 LIVE"
                        else:
                            status_icon = "⚫ OFFLINE"
                        
                        # Format display name and value
                        display_name = f"[{streamer_name.title()}] {status_icon}"
                        value = f"{prefix}{streamer_name}"
                        
                        choices.append(
                            app_commands.Choice(name=display_name, value=value)
                        )
                    
                    return choices[:25]  # Discord limit
                    
        except Exception as e:
            # Fallback to basic autocomplete if enhanced fails
            try:
                from db_app import db, app
                with app.app_context():
                    with db.engine.connect() as connection:
                        # Simple fallback for basic streamer names
                        current_simple = current.lower().split(',')[-1].strip()
                        result = connection.execute(text('''
                            SELECT DISTINCT streamer_name 
                            FROM twitch_streamers 
                            WHERE guild_id = :guild_id AND streamer_name LIKE :pattern
                            LIMIT 20
                        '''), {
                            'guild_id': interaction.guild.id if interaction.guild else 0,
                            'pattern': f'%{current_simple}%'
                        })
                        
                        prefix = ""
                        if ',' in current:
                            parts = current.split(',')[:-1]
                            prefix = ", ".join(parts) + ", " if parts else ""
                        
                        streamers = [row[0] for row in result.fetchall()]
                        return [
                            app_commands.Choice(name=f"[{streamer.title()}]", value=f"{prefix}{streamer}")
                            for streamer in streamers[:20]
                        ]
            except:
                return []


    # Handler functions for each action
    async def handle_list_action(interaction: discord.Interaction):
        """Handle list action"""
        try:
            from db_app import db, app
            with app.app_context():
                with db.engine.connect() as connection:
                    # Get streamers with pause status
                    result = connection.execute(text('''
                        SELECT streamer_name, channel_id, is_live, custom_message, paused
                        FROM twitch_streamers 
                        WHERE guild_id = :guild_id
                        ORDER BY streamer_name
                    '''), {
                        'guild_id': interaction.guild.id if interaction.guild else 0
                    })
                    
                    streamers = result.fetchall()
                    
                    # Check server-wide pause status
                    server_result = connection.execute(text('''
                        SELECT paused FROM twitch_settings WHERE guild_id = :guild_id
                    '''), {
                        'guild_id': interaction.guild.id if interaction.guild else 0
                    })
                    server_settings = server_result.fetchone()
                    server_paused = server_settings[0] if server_settings else False
            
            if not streamers:
                return await interaction.response.send_message("📺 No Twitch streamers are being watched in this server.", ephemeral=True)
            
            # Determine embed title and color based on server pause status
            if server_paused:
                embed_title = "⏸️ Watched Twitch Streamers (Server Paused)"
                embed_color = 0xFFA500  # Warning orange
                description = f"Server notifications are paused. Monitoring {len(streamers)} streamers."
            else:
                embed_title = "📺 Watched Twitch Streamers"
                embed_color = 0x9146FF  # Twitch purple
                description = f"Monitoring {len(streamers)} streamers for live notifications"
            
            embed = discord.Embed(
                title=embed_title,
                description=description,
                color=embed_color
            )
            
            live_streamers = []
            offline_streamers = []
            paused_streamers = []
            
            for streamer_name, channel_id, is_live, custom_message, paused in streamers:
                channel = bot.get_channel(channel_id)
                
                # Build streamer info with channel mention
                streamer_info = f"[{streamer_name}](https://twitch.tv/{streamer_name})"
                if channel:
                    streamer_info += f" → {channel.mention}"
                
                # Categorize streamers based on status
                if paused:
                    paused_streamers.append(f"⏸️ {streamer_info}")
                elif is_live:
                    live_streamers.append(f"🔴 LIVE {streamer_info}")
                else:
                    offline_streamers.append(f"⚫ {streamer_info}")
            
            # Helper function to split long lists into multiple fields
            def add_streamer_fields(embed, streamers_list, field_name, emoji):
                if not streamers_list:
                    return
                
                # Discord embed field value limit is 1024 characters
                MAX_FIELD_LENGTH = 1024
                current_field = []
                current_length = 0
                field_count = 0
                
                for streamer in streamers_list:
                    # Add 1 for newline character
                    streamer_length = len(streamer) + 1
                    
                    # If adding this streamer would exceed the limit, create a new field
                    if current_length + streamer_length > MAX_FIELD_LENGTH and current_field:
                        field_count += 1
                        name = field_name if field_count == 1 else f"{field_name} (continued)"
                        embed.add_field(name=name, value='\n'.join(current_field), inline=False)
                        current_field = [streamer]
                        current_length = streamer_length
                    else:
                        current_field.append(streamer)
                        current_length += streamer_length
                
                # Add any remaining streamers
                if current_field:
                    field_count += 1
                    name = field_name if field_count == 1 else f"{field_name} (continued)"
                    embed.add_field(name=name, value='\n'.join(current_field), inline=False)
            
            # Add fields with proper length handling
            add_streamer_fields(embed, live_streamers, "🔴 Currently Live", "🔴")
            add_streamer_fields(embed, offline_streamers, "⚫ Offline", "⚫")
            add_streamer_fields(embed, paused_streamers, "⏸️ Paused", "⏸️")
            
            # Update footer to indicate pause status if applicable
            footer_text = "Use /twitch add to watch more streamers"
            if server_paused:
                footer_text = "⏸️ Server notifications paused • " + footer_text
            elif paused_streamers:
                footer_text = f"⏸️ {len(paused_streamers)} paused • " + footer_text
            
            embed.set_footer(text=footer_text)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to list streamers: {e}", ephemeral=True)

    async def handle_add_action(interaction: discord.Interaction, streamer: Optional[str], channel: Optional[discord.TextChannel], message: Optional[str]):
        """Handle add action"""
        if not streamer:
            return await interaction.response.send_message("❌ You must specify a streamer name to add!", ephemeral=True)
            
        # Check if user has manage guild permissions
        if not interaction.guild or not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("❌ You need `Manage Server` permission to add Twitch streamers!", ephemeral=True)

        # Use current channel if none specified
        target_channel = channel or interaction.channel
        if not isinstance(target_channel, discord.TextChannel):
            return await interaction.response.send_message("❌ Please specify a valid text channel for notifications!", ephemeral=True)

        streamer = streamer.lower()
        
        try:
            # Validate streamer exists on Twitch
            streamer_id = await twitch.get_user_id(streamer)
            if not streamer_id:
                return await interaction.response.send_message(f"❌ Twitch user `{streamer}` not found! Please check the username.", ephemeral=True)
            
            from db_app import db, app
            with app.app_context():
                with db.engine.connect() as connection:
                    # Check if streamer is already being watched
                    result = connection.execute(text('''
                        SELECT streamer_name FROM twitch_streamers 
                        WHERE guild_id = :guild_id AND streamer_name = :streamer_name
                    '''), {
                        'guild_id': interaction.guild.id,
                        'streamer_name': streamer
                    })
                    
                    if result.fetchone():
                        return await interaction.response.send_message(f"❌ `{streamer}` is already being watched in this server!", ephemeral=True)
                    
                    # Add streamer to database
                    connection.execute(text('''
                        INSERT INTO twitch_streamers (guild_id, channel_id, streamer_name, streamer_id, custom_message)
                        VALUES (:guild_id, :channel_id, :streamer_name, :streamer_id, :custom_message)
                    '''), {
                        'guild_id': interaction.guild.id,
                        'channel_id': target_channel.id,
                        'streamer_name': streamer,
                        'streamer_id': streamer_id,
                        'custom_message': message
                    })
                    connection.commit()

            embed = discord.Embed(
                title="✅ Streamer Added Successfully!",
                description=f"Now watching **{streamer}** for live notifications.",
                color=0x00FF00
            )
            embed.add_field(name="📺 Streamer", value=f"[{streamer}](https://twitch.tv/{streamer})", inline=True)
            embed.add_field(name="📢 Channel", value=target_channel.mention, inline=True)
            if message:
                embed.add_field(name="💬 Custom Message", value=message, inline=False)
            
            embed.set_footer(text="Live notifications will be sent when this streamer goes online!")
            await interaction.response.send_message(embed=embed)
                
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to add streamer: {e}", ephemeral=True)

    async def handle_remove_action(interaction: discord.Interaction, streamer: Optional[str]):
        """Handle remove action"""
        if not streamer:
            return await interaction.response.send_message("❌ You must specify a streamer name to remove!", ephemeral=True)
            
        # Check if user has manage guild permissions
        if not interaction.guild or not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("❌ You need `Manage Server` permission to remove Twitch streamers!", ephemeral=True)

        streamer = streamer.lower()
        
        try:
            from db_app import db, app
            with app.app_context():
                with db.engine.connect() as connection:
                    # Check if streamer exists
                    result = connection.execute(text('''
                        SELECT streamer_name FROM twitch_streamers 
                        WHERE guild_id = :guild_id AND streamer_name = :streamer_name
                    '''), {
                        'guild_id': interaction.guild.id,
                        'streamer_name': streamer
                    })
                    
                    if not result.fetchone():
                        return await interaction.response.send_message(f"❌ `{streamer}` is not in the watch list!", ephemeral=True)
                    
                    # Remove streamer from database
                    connection.execute(text('''
                        DELETE FROM twitch_streamers 
                        WHERE guild_id = :guild_id AND streamer_name = :streamer_name
                    '''), {
                        'guild_id': interaction.guild.id,
                        'streamer_name': streamer
                    })
                    connection.commit()

            embed = discord.Embed(
                title="✅ Streamer Removed Successfully!",
                description=f"No longer watching **{streamer}** for live notifications.",
                color=0xFF6B6B
            )
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to remove streamer: {e}", ephemeral=True)

    async def handle_edit_action(interaction: discord.Interaction, streamer: Optional[str], channel: Optional[discord.TextChannel], message: Optional[str]):
        """Handle edit action"""
        if not streamer:
            return await interaction.response.send_message("❌ You must specify a streamer name to edit!", ephemeral=True)
            
        # Check if user has manage guild permissions
        if not interaction.guild or not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("❌ You need `Manage Server` permission to edit Twitch streamers!", ephemeral=True)

        if not channel and not message:
            return await interaction.response.send_message("❌ You must specify at least one thing to edit (channel or message)!", ephemeral=True)
            
        streamer = streamer.lower()
        
        try:
            from db_app import db, app
            with app.app_context():
                with db.engine.connect() as connection:
                    # Check if streamer exists
                    result = connection.execute(text('''
                        SELECT channel_id, custom_message FROM twitch_streamers 
                        WHERE guild_id = :guild_id AND streamer_name = :streamer_name
                    '''), {
                        'guild_id': interaction.guild.id,
                        'streamer_name': streamer
                    })
                    
                    current = result.fetchone()
                    if not current:
                        return await interaction.response.send_message(f"❌ `{streamer}` is not in the watch list!", ephemeral=True)
                    
                    # Prepare update values
                    new_channel_id = channel.id if channel else current[0]
                    new_message = message if message is not None else current[1]
                    
                    # Update streamer
                    connection.execute(text('''
                        UPDATE twitch_streamers 
                        SET channel_id = :channel_id, custom_message = :custom_message
                        WHERE guild_id = :guild_id AND streamer_name = :streamer_name
                    '''), {
                        'guild_id': interaction.guild.id,
                        'streamer_name': streamer,
                        'channel_id': new_channel_id,
                        'custom_message': new_message
                    })
                    connection.commit()

            embed = discord.Embed(
                title="✅ Streamer Updated Successfully!",
                description=f"Updated settings for **{streamer}**.",
                color=0x4ECDC4
            )
            embed.add_field(name="📺 Streamer", value=f"[{streamer}](https://twitch.tv/{streamer})", inline=True)
            if channel:
                embed.add_field(name="📢 New Channel", value=channel.mention, inline=True)
            if message is not None:
                embed.add_field(name="💬 New Message", value=message if message else "*Removed custom message*", inline=False)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to edit streamer: {e}", ephemeral=True)

    class StreamerEditPickerView(discord.ui.View):
        """Interactive picker for editing specific streamers"""
        def __init__(self, guild_id: int, options: list):
            super().__init__(timeout=300)  # 5 minute timeout
            self.guild_id = guild_id
            
            # Create the select menu with the options
            self.streamer_select = discord.ui.Select(
                placeholder="🎯 Select a streamer to edit...",
                min_values=1,
                max_values=1,
                options=options
            )
            self.streamer_select.callback = self.on_streamer_select
            self.add_item(self.streamer_select)
            
        async def on_streamer_select(self, interaction: discord.Interaction):
            """Handle streamer selection and show edit options"""
            try:
                if not interaction.data or 'values' not in interaction.data:
                    return await interaction.response.send_message("❌ No streamer selected!", ephemeral=True)
                selected_streamer = interaction.data['values'][0]
                
                # Get current streamer data
                from db_app import db, app
                with app.app_context():
                    with db.engine.connect() as connection:
                        result = connection.execute(text('''
                            SELECT channel_id, custom_message, is_live, paused
                            FROM twitch_streamers 
                            WHERE guild_id = :guild_id AND streamer_name = :streamer_name
                        '''), {
                            'guild_id': self.guild_id,
                            'streamer_name': selected_streamer
                        })
                        streamer_data = result.fetchone()
                        
                        if not streamer_data:
                            return await interaction.response.send_message("❌ Streamer not found!", ephemeral=True)
                        
                        channel_id, custom_message, is_live, paused = streamer_data
                        
                # Get current channel info
                channel = None
                if interaction.guild:
                    channel = interaction.guild.get_channel(channel_id)
                channel_name = channel.mention if channel else "*(deleted channel)*"
                
                # Determine status
                if paused:
                    status = "⏸️ PAUSED"
                elif is_live:
                    status = "🔴 LIVE"
                else:
                    status = "⚫ OFFLINE"
                
                # Create edit interface
                edit_embed = discord.Embed(
                    title=f"✏️ Editing: {selected_streamer.title()}",
                    description=f"**Status:** {status}\n**Current Channel:** {channel_name}\n**Custom Message:** {custom_message or '*None set*'}",
                    color=0x4ECDC4,
                    url=f"https://twitch.tv/{selected_streamer}"
                )
                
                edit_embed.add_field(
                    name="🎛️ Quick Edit Options",
                    value="• **Change Channel** - Select a new notification channel\n• **Edit Message** - Update or remove custom message\n• **Advanced** - Use command for both channel + message",
                    inline=False
                )
                
                edit_embed.add_field(
                    name="💻 Advanced Command",
                    value=f"`/twitch edit streamer:{selected_streamer} channel:#channel message:text`",
                    inline=False
                )
                
                # Create edit view with buttons
                edit_view = StreamerEditOptionsView(self.guild_id, selected_streamer, channel_id, custom_message)
                
                # Update the message with edit interface
                await interaction.response.edit_message(embed=edit_embed, view=edit_view)
                
            except Exception as e:
                await interaction.response.send_message(f"❌ Failed to load streamer data: {e}", ephemeral=True)

    class StreamerEditOptionsView(discord.ui.View):
        """Interactive buttons for editing streamer settings"""
        def __init__(self, guild_id: int, streamer_name: str, current_channel_id: int, current_message: str):
            super().__init__(timeout=300)
            self.guild_id = guild_id
            self.streamer_name = streamer_name
            self.current_channel_id = current_channel_id
            self.current_message = current_message
            
        @discord.ui.button(label="Change Channel", style=discord.ButtonStyle.primary, emoji="📺")
        async def change_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
            """Show channel selector"""
            if not interaction.guild:
                return await interaction.response.send_message("❌ This command can only be used in a server!", ephemeral=True)
            # Get available text channels
            channels = [ch for ch in interaction.guild.channels if isinstance(ch, discord.TextChannel)]
            
            if len(channels) > 25:
                channels = channels[:25]  # Discord limit
                
            channel_options = [
                discord.SelectOption(
                    label=f"#{channel.name}",
                    value=str(channel.id),
                    description=f"Category: {channel.category.name if channel.category else 'No category'}",
                    emoji="📺"
                ) for channel in channels
            ]
            
            channel_select = discord.ui.Select(
                placeholder="📺 Select a new notification channel...",
                options=channel_options,
                min_values=1,
                max_values=1
            )
            
            async def channel_callback(interaction: discord.Interaction):
                if not interaction.data or 'values' not in interaction.data or not interaction.guild:
                    return await interaction.response.send_message("❌ Invalid selection!", ephemeral=True)
                new_channel_id = int(interaction.data['values'][0])
                new_channel = interaction.guild.get_channel(new_channel_id)
                
                if not new_channel:
                    return await interaction.response.send_message("❌ Channel not found!", ephemeral=True)
                
                # Update database
                from db_app import db, app
                with app.app_context():
                    with db.engine.connect() as connection:
                        connection.execute(text('''
                            UPDATE twitch_streamers 
                            SET channel_id = :channel_id
                            WHERE guild_id = :guild_id AND streamer_name = :streamer_name
                        '''), {
                            'channel_id': new_channel_id,
                            'guild_id': self.guild_id,
                            'streamer_name': self.streamer_name
                        })
                        connection.commit()
                
                success_embed = discord.Embed(
                    title="✅ Channel Updated",
                    description=f"**{self.streamer_name}** notifications will now be sent to {new_channel.mention}",
                    color=0x00ff00
                )
                await interaction.response.edit_message(embed=success_embed, view=None)
            
            channel_select.callback = channel_callback
            channel_view = discord.ui.View()
            channel_view.add_item(channel_select)
            
            await interaction.response.edit_message(
                embed=discord.Embed(title="📺 Select New Channel", description="Choose where notifications should be sent:", color=0x4ECDC4),
                view=channel_view
            )
            
        @discord.ui.button(label="Edit Message", style=discord.ButtonStyle.secondary, emoji="💬")
        async def edit_message(self, interaction: discord.Interaction, button: discord.ui.Button):
            """Show message edit modal"""
            modal = MessageEditModal(self.guild_id, self.streamer_name, self.current_message)
            await interaction.response.send_modal(modal)

    class MessageEditModal(discord.ui.Modal, title="Edit Custom Message"):
        """Modal for editing custom notification messages"""
        def __init__(self, guild_id: int, streamer_name: str, current_message: str):
            super().__init__()
            self.guild_id = guild_id
            self.streamer_name = streamer_name
            
            self.message_input = discord.ui.TextInput(
                label="Custom Notification Message",
                placeholder="Enter custom message or leave empty to remove...",
                default=current_message or "",
                required=False,
                max_length=500,
                style=discord.TextStyle.paragraph
            )
            self.add_item(self.message_input)
            
        async def on_submit(self, interaction: discord.Interaction):
            new_message = self.message_input.value.strip() if self.message_input.value else None
            
            # Update database
            from db_app import db, app
            with app.app_context():
                with db.engine.connect() as connection:
                    connection.execute(text('''
                        UPDATE twitch_streamers 
                        SET custom_message = :message
                        WHERE guild_id = :guild_id AND streamer_name = :streamer_name
                    '''), {
                        'message': new_message,
                        'guild_id': self.guild_id,
                        'streamer_name': self.streamer_name
                    })
                    connection.commit()
            
            # Create success response
            if new_message:
                description = f"**{self.streamer_name}** custom message updated to:\n\n> {new_message}"
            else:
                description = f"**{self.streamer_name}** custom message removed. Will use default notifications."
                
            success_embed = discord.Embed(
                title="✅ Message Updated",
                description=description,
                color=0x00ff00
            )
            await interaction.response.edit_message(embed=success_embed, view=None)

    class StreamerSelectView(discord.ui.View):
        """Interactive select menu for choosing multiple streamers"""
        def __init__(self, guild_id: int, action: str, options: list):
            super().__init__(timeout=300)  # 5 minute timeout
            self.guild_id = guild_id
            self.action = action  # "pause" or "resume"
            
            # Create the select menu with the options
            action_text = {
                "pause": "pause",
                "resume": "resume", 
                "remove": "remove"
            }.get(action, "manage")
            
            # Set appropriate selection limits based on action
            if action == "edit":
                max_select = 1  # Edit can only handle one streamer at a time
            else:
                max_select = min(len(options), 25)  # Others can select multiple
            
            self.select_menu = discord.ui.Select(
                placeholder=f"🎯 Select streamers to {action_text}...",
                min_values=1,
                max_values=max_select,
                options=options
            )
            self.select_menu.callback = self.streamer_select
            self.add_item(self.select_menu)
            
        async def streamer_select(self, interaction: discord.Interaction):
            """Handle streamer selection from dropdown"""
            try:
                # Get the selected streamers from the interaction data
                if not interaction.data or 'values' not in interaction.data:
                    return await interaction.response.send_message("❌ No streamers were selected!", ephemeral=True)
                selected_streamers = interaction.data['values']
                
                # Handle different actions
                if self.action == "remove":
                    return await self.handle_remove_action(interaction, selected_streamers)
                elif self.action == "edit":
                    return await self.handle_edit_action(interaction, selected_streamers)
                
                # Handle pause/resume actions
                is_pause = self.action == "pause"
                action_word = "Paused" if is_pause else "Resumed"
                action_icon = "⏸️" if is_pause else "▶️"
                color = 0xFFAA00 if is_pause else 0x00FF00
                
                from db_app import db, app
                with app.app_context():
                    with db.engine.connect() as connection:
                        # Get existing streamers and their pause status safely
                        existing_streamers = {}
                        to_update = []
                        already_correct = []
                        not_found = []
                        
                        for streamer_name in selected_streamers:
                            result = connection.execute(text('''
                                SELECT streamer_name, paused FROM twitch_streamers 
                                WHERE guild_id = :guild_id AND streamer_name = :streamer_name
                            '''), {
                                'guild_id': self.guild_id,
                                'streamer_name': streamer_name
                            })
                            streamer_data = result.fetchone()
                            
                            if not streamer_data:
                                not_found.append(streamer_name)
                            elif streamer_data[1] == is_pause:
                                already_correct.append(streamer_name)
                            else:
                                to_update.append(streamer_name)
                        
                        # Update streamers that need changes safely
                        for streamer_name in to_update:
                            connection.execute(text('''
                                UPDATE twitch_streamers 
                                SET paused = :paused
                                WHERE guild_id = :guild_id AND streamer_name = :streamer_name
                            '''), {
                                'guild_id': self.guild_id,
                                'paused': is_pause,
                                'streamer_name': streamer_name
                            })
                        
                        # Always commit to ensure database changes are saved
                        connection.commit()
                        
                        # Create detailed feedback embed
                        embed = discord.Embed(
                            title=f"{action_icon} Multiple Streamers {action_word}",
                            color=color
                        )
                        
                        if to_update:
                            embed.add_field(
                                name=f"✅ {action_word} ({len(to_update)})",
                                value=", ".join([f"`{name}`" for name in to_update]),
                                inline=False
                            )
                        
                        if already_correct:
                            status_word = "paused" if is_pause else "resumed"
                            embed.add_field(
                                name=f"ℹ️ Already {status_word} ({len(already_correct)})",
                                value=", ".join([f"`{name}`" for name in already_correct]),
                                inline=False
                            )
                        
                        if not_found:
                            embed.add_field(
                                name=f"❌ Not found ({len(not_found)})",
                                value=", ".join([f"`{name}`" for name in not_found]),
                                inline=False
                            )
                        
                        if not to_update and not already_correct and not not_found:
                            embed.description = f"No streamers were {action_word.lower()}."
                        else:
                            total_processed = len(to_update) + len(already_correct)
                            embed.description = f"Processed {total_processed}/{len(selected_streamers)} streamers."
                        
                        # Clear the view to prevent further interactions
                        self.clear_items()
                        await interaction.response.edit_message(embed=embed, view=self)
                        
            except Exception as e:
                await interaction.response.send_message(f"❌ Failed to process streamers: {e}", ephemeral=True)
        
        async def handle_remove_action(self, interaction: discord.Interaction, selected_streamers: list):
            """Handle removing selected streamers"""
            try:
                from db_app import db, app
                with app.app_context():
                    with db.engine.connect() as connection:
                        # Remove all selected streamers safely using parameterized queries
                        removed_count = 0
                        for streamer_name in selected_streamers:
                            result = connection.execute(text('''
                                DELETE FROM twitch_streamers 
                                WHERE guild_id = :guild_id AND streamer_name = :streamer_name
                            '''), {
                                'guild_id': self.guild_id,
                                'streamer_name': streamer_name
                            })
                            removed_count += result.rowcount
                        
                        connection.commit()
                        
                        # Create feedback embed
                        embed = discord.Embed(
                            title="🗑️ Streamers Removed",
                            description=f"Successfully removed {removed_count}/{len(selected_streamers)} streamers from the watch list.",
                            color=0xFF6B6B
                        )
                        
                        if removed_count > 0:
                            embed.add_field(
                                name=f"✅ Removed ({removed_count})",
                                value=", ".join([f"`{name}`" for name in selected_streamers[:removed_count]]),
                                inline=False
                            )
                        
                        if removed_count < len(selected_streamers):
                            not_found = len(selected_streamers) - removed_count
                            embed.add_field(
                                name=f"❌ Not found ({not_found})",
                                value="Some streamers were not in the watch list",
                                inline=False
                            )
                        
                        # Clear the view to prevent further interactions
                        self.clear_items()
                        await interaction.response.edit_message(embed=embed, view=self)
                        
            except Exception as e:
                await interaction.response.send_message(f"❌ Failed to remove streamers: {e}", ephemeral=True)
        
        async def handle_edit_action(self, interaction: discord.Interaction, selected_streamers: list):
            """Handle editing selected streamers"""
            try:
                # For edit, we can only handle one streamer at a time due to UI limitations
                if len(selected_streamers) > 1:
                    return await interaction.response.send_message("❌ Please select only **one** streamer to edit at a time!", ephemeral=True)
                
                streamer_name = selected_streamers[0]
                
                # Create feedback with instructions
                embed = discord.Embed(
                    title="✏️ Edit Streamer Settings",
                    description=f"To edit **{streamer_name}**, use the command:\n\n`/twitch edit streamer:{streamer_name} channel:#channel message:text`\n\nYou can specify either channel, message, or both.",
                    color=0x4ECDC4
                )
                embed.add_field(
                    name="📺 Selected Streamer",
                    value=f"[{streamer_name}](https://twitch.tv/{streamer_name})",
                    inline=True
                )
                embed.add_field(
                    name="💡 Tip",
                    value="Leave message empty to remove custom message",
                    inline=False
                )
                
                # Clear the view to prevent further interactions
                self.clear_items()
                await interaction.response.edit_message(embed=embed, view=self)
                
            except Exception as e:
                await interaction.response.send_message(f"❌ Failed to edit streamer: {e}", ephemeral=True)

    async def show_streamer_list_for_edit(interaction: discord.Interaction):
        """Show an interactive picker for editing streamers"""
        try:
            if not interaction.guild:
                return await interaction.response.send_message("❌ This command can only be used in a server!", ephemeral=True)
                
            from db_app import db, app
            with app.app_context():
                with db.engine.connect() as connection:
                    # Get all streamers for this guild with their status and settings
                    result = connection.execute(text('''
                        SELECT streamer_name, is_live, paused, channel_id, custom_message
                        FROM twitch_streamers 
                        WHERE guild_id = :guild_id
                        ORDER BY 
                            CASE 
                                WHEN paused THEN 2
                                WHEN is_live THEN 0  
                                ELSE 1
                            END,
                            streamer_name
                        LIMIT 25
                    '''), {'guild_id': interaction.guild.id})
                    
                    streamers = result.fetchall()
                    
                    if not streamers:
                        return await interaction.response.send_message("❌ No streamers found! Add some streamers first with `/twitch add`.", ephemeral=True)
                    
                    # Create select options for the interactive picker
                    options = []
                    for streamer_name, is_live, paused, channel_id, custom_message in streamers:
                        if paused:
                            status_icon = "⏸️"
                            status_text = "PAUSED"
                        elif is_live:
                            status_icon = "🔴"
                            status_text = "LIVE"
                        else:
                            status_icon = "⚫"
                            status_text = "OFFLINE"
                        
                        # Get current channel name for description
                        channel = interaction.guild.get_channel(channel_id)
                        channel_name = channel.name if channel else "deleted-channel"
                        
                        label = f"[{streamer_name.title()}] {status_icon} {status_text}"
                        description = f"→ #{channel_name}"
                        if custom_message:
                            description += f" | Custom: {custom_message[:30]}{'...' if len(custom_message) > 30 else ''}"
                        
                        options.append(discord.SelectOption(
                            label=label,
                            value=streamer_name,
                            description=description,
                            emoji=status_icon
                        ))
                    
                    # Create the interactive edit view
                    view = StreamerEditPickerView(interaction.guild.id, options)
                    
                    # Create embed
                    embed = discord.Embed(
                        title="✏️ Interactive Streamer Editor",
                        description=f"**{len(streamers)} streamers** available for editing.\nSelect a streamer below to edit their settings:",
                        color=0x4ECDC4
                    )
                    
                    embed.add_field(
                        name="🎯 How It Works",
                        value="• Select a streamer from the dropdown\n• Choose what you want to edit\n• Make your changes instantly",
                        inline=False
                    )
                    
                    embed.set_footer(text="💡 Select a streamer to get started!")
                    
                    await interaction.response.send_message(embed=embed, view=view)
                    
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to show streamer picker: {e}", ephemeral=True)

    async def show_streamer_select_menu(interaction: discord.Interaction, action: str):
        """Show interactive select menu for multiple streamer selection"""
        try:
            if not interaction.guild:
                return await interaction.response.send_message("❌ This command can only be used in a server!", ephemeral=True)
                
            from db_app import db, app
            with app.app_context():
                with db.engine.connect() as connection:
                    # Get all streamers for this guild with their status
                    result = connection.execute(text('''
                        SELECT streamer_name, is_live, paused 
                        FROM twitch_streamers 
                        WHERE guild_id = :guild_id
                        ORDER BY 
                            CASE 
                                WHEN paused THEN 2
                                WHEN is_live THEN 0  
                                ELSE 1
                            END,
                            streamer_name
                        LIMIT 25
                    '''), {'guild_id': interaction.guild.id})
                    
                    streamers = result.fetchall()
                    
                    if not streamers:
                        return await interaction.response.send_message("❌ No streamers found! Add some streamers first with `/twitch add`.", ephemeral=True)
                    
                    # Create streamer options with status indicators
                    options = []
                    for streamer_name, is_live, paused in streamers:
                        if paused:
                            status_icon = "⏸️"
                            status_text = "PAUSED"
                        elif is_live:
                            status_icon = "🔴"
                            status_text = "LIVE"
                        else:
                            status_icon = "⚫"
                            status_text = "OFFLINE"
                        
                        label = f"[{streamer_name.title()}] {status_icon} {status_text}"
                        options.append(discord.SelectOption(
                            label=label,
                            value=streamer_name,
                            description=f"Twitch.tv/{streamer_name}"
                        ))
                    
                    # Create the view with the options
                    view = StreamerSelectView(interaction.guild.id, action, options)
                    
                    # Create embed based on action
                    if action == "remove":
                        action_word = "remove"
                        action_icon = "🗑️"
                        color = 0xFF6B6B
                        instruction_text = "• Select **1-25** streamers to remove\n• This action cannot be undone\n• Streamers will be removed instantly"
                    elif action == "edit":
                        action_word = "edit"
                        action_icon = "✏️"
                        color = 0x4ECDC4
                        instruction_text = "• Select **exactly one** streamer to edit\n• You'll get instructions for the edit command\n• Can edit channel, message, or both"
                    elif action == "pause":
                        action_word = "pause"
                        action_icon = "⏸️"
                        color = 0xFFAA00
                        instruction_text = f"• Select **1-{len(streamers)}** streamers from the menu\n• Click outside to confirm your selection\n• Status will be updated instantly"
                    else:  # resume
                        action_word = "resume"
                        action_icon = "▶️"
                        color = 0x00FF00
                        instruction_text = f"• Select **1-{len(streamers)}** streamers from the menu\n• Click outside to confirm your selection\n• Status will be updated instantly"
                    
                    embed = discord.Embed(
                        title=f"{action_icon} Select Streamers to {action_word.title()}",
                        description=f"Choose multiple streamers to {action_word} from the dropdown below.\n\n🔴 = Live • ⚫ = Offline • ⏸️ = Paused",
                        color=color
                    )
                    embed.add_field(
                        name="📋 Instructions",
                        value=instruction_text,
                        inline=False
                    )
                    
                    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
                    
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to show streamer menu: {e}", ephemeral=True)

    async def handle_pause_action(interaction: discord.Interaction, target: Optional[str], streamers: Optional[str] = None):
        """Handle pause action for specific streamers"""
        # Check if user has manage guild permissions
        if not interaction.guild or not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("❌ You need `Manage Server` permission to manage Twitch notifications!", ephemeral=True)
            
        # Show interactive select menu for choosing streamers
        return await show_streamer_select_menu(interaction, "pause")

    async def handle_resume_action(interaction: discord.Interaction, target: Optional[str], streamers: Optional[str] = None):
        """Handle resume action for specific streamers"""
        # Check if user has manage guild permissions
        if not interaction.guild or not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("❌ You need `Manage Server` permission to manage Twitch notifications!", ephemeral=True)
            
        # Show interactive select menu for choosing streamers
        return await show_streamer_select_menu(interaction, "resume")

    async def handle_check_action(interaction: discord.Interaction, streamer: Optional[str]):
        """Handle check action"""
        if not streamer:
            return await interaction.response.send_message("❌ You must specify a streamer name to check!", ephemeral=True)
            
        await interaction.response.defer()
        
        try:
            # Get streamer ID
            streamer_id = await twitch.get_user_id(streamer.lower())
            if not streamer_id:
                return await interaction.followup.send(f"❌ Twitch user `{streamer}` not found!")
            
            # Get stream info
            stream_info = await twitch.get_stream_info(streamer_id)
            
            if stream_info:
                embed = discord.Embed(
                    title=f"🔴 {streamer} is LIVE!",
                    description=stream_info.get('title', 'No title'),
                    url=f"https://twitch.tv/{streamer}",
                    color=0x00ff00
                )
                embed.add_field(name="Game", value=stream_info.get('game_name', 'Unknown'), inline=True)
                embed.add_field(name="Viewers", value=str(stream_info.get('viewer_count', 0)), inline=True)
                embed.add_field(name="Started", value=f"<t:{int(datetime.fromisoformat(stream_info['started_at'].replace('Z', '+00:00')).timestamp())}:R>", inline=True)
                
                if stream_info.get('thumbnail_url'):
                    thumbnail_url = stream_info['thumbnail_url'].replace('{width}', '320').replace('{height}', '180')
                    embed.set_thumbnail(url=thumbnail_url)
                    
            else:
                embed = discord.Embed(
                    title=f"⚫ {streamer} is offline",
                    description="This streamer is not currently live",
                    color=0x808080
                )
            
            embed.set_footer(text="Manual stream check")
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to check streamer: {e}")

    async def handle_settings_action(interaction: discord.Interaction, role: Optional[discord.Role], color: Optional[str], include_game: Optional[bool], include_preview: Optional[bool]):
        """Handle settings action"""
        # Check if user has manage guild permissions
        if not interaction.guild or not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("❌ You need `Manage Server` permission to configure Twitch settings!", ephemeral=True)

        if not role and not color and include_game is None and include_preview is None:
            return await interaction.response.send_message("❌ You must specify at least one setting to change!", ephemeral=True)
        
        try:
            guild_id = interaction.guild.id if interaction.guild else 0
            from db_app import db, app
            
            with app.app_context():
                with db.engine.connect() as connection:
                    # Get current settings
                    result = connection.execute(text('SELECT * FROM twitch_settings WHERE guild_id = :guild_id'), {'guild_id': guild_id})
                    current = result.fetchone()
                    
                    # Prepare update values - fix column indices 
                    role_mention = role.mention if role else (current[2] if current else None)
                    embed_color = int(color, 16) if color else (current[3] if current else 0x9146FF)
                    game_setting = include_game if include_game is not None else (current[4] if current else True)
                    preview_setting = include_preview if include_preview is not None else (current[5] if current else True)
                    
                    # Update or insert settings using PostgreSQL UPSERT
                    connection.execute(text('''
                        INSERT INTO twitch_settings (guild_id, role_mention, notification_color, include_game, include_preview)
                        VALUES (:guild_id, :role_mention, :notification_color, :include_game, :include_preview)
                        ON CONFLICT (guild_id) DO UPDATE SET
                            role_mention = EXCLUDED.role_mention,
                            notification_color = EXCLUDED.notification_color,
                            include_game = EXCLUDED.include_game,
                            include_preview = EXCLUDED.include_preview
                    '''), {
                        'guild_id': guild_id,
                        'role_mention': role_mention,
                        'notification_color': embed_color,
                        'include_game': game_setting,
                        'include_preview': preview_setting
                    })
                    connection.commit()
            
            embed = discord.Embed(
                title="⚙️ Settings Updated Successfully!",
                description="Your Twitch notification settings have been updated.",
                color=embed_color
            )
            
            if role:
                embed.add_field(name="📌 Role Mention", value=role.mention, inline=True)
            if color:
                embed.add_field(name="🎨 Embed Color", value=f"#{color}", inline=True)
            if include_game is not None:
                embed.add_field(name="🎮 Include Game", value="✅ Yes" if include_game else "❌ No", inline=True)
            if include_preview is not None:
                embed.add_field(name="🖼️ Include Preview", value="✅ Yes" if include_preview else "❌ No", inline=True)
                
            await interaction.response.send_message(embed=embed)
            
        except ValueError:
            await interaction.response.send_message("❌ Invalid color format! Use hex format without # (e.g., FF5733)", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to update settings: {e}", ephemeral=True)

    async def handle_test_action(interaction: discord.Interaction):
        """Handle test action"""
        # Check if user has manage guild permissions
        if not interaction.guild or not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("❌ You need `Manage Server` permission to test notifications!", ephemeral=True)

        await interaction.response.send_message("🧪 Sending test notification...", ephemeral=True)
        
        # Get guild settings to test role mention functionality
        try:
            guild_id = interaction.guild.id if interaction.guild else 0
            from db_app import db, app
            with app.app_context():
                with db.engine.connect() as connection:
                    result = connection.execute(text('''
                        SELECT role_mention, notification_color, include_game, include_preview 
                        FROM twitch_settings WHERE guild_id = :guild_id
                    '''), {'guild_id': guild_id})
                    settings = result.fetchone()
            
            # Parse settings with correct column mapping
            role_mention = settings[0] if settings else None
            notification_color = settings[1] if settings else None
            include_game = settings[2] if settings and settings[2] is not None else True
            include_preview = settings[3] if settings and settings[3] is not None else True
            
            # Ensure color is always an integer - use Twitch purple unless custom color is set
            color_value = 0x9146FF  # Default Twitch purple
            if notification_color is not None:
                try:
                    val = int(notification_color) if not isinstance(notification_color, int) else notification_color
                    # Don't use legacy default (6570404), stick with Twitch purple
                    if val != 6570404:
                        color_value = val
                except (ValueError, TypeError):
                    color_value = 0x9146FF
            
            # Create a test notification with actual settings - matching live format
            embed = discord.Embed(
                title="TEST STREAMER is now live on Twitch!",
                description="This is a test notification to verify your setup is working correctly.",
                url="https://twitch.tv/test",
                color=color_value,
                timestamp=datetime.utcnow()
            )
            
            # Apply game setting with inline layout - matching live format
            if include_game:
                embed.add_field(name="Game", value="Testing Stream Notifications", inline=True)
                
            embed.add_field(name="Viewers", value="999", inline=True)
            
            # Apply preview setting with reliable test image - with debug logging
            if include_preview:
                # Use a reliable test image that always returns 200
                test_image_url = "https://picsum.photos/1280/720?random=1"
                logger.info(f"🖼️ TEST: Setting preview image: {test_image_url}")
                embed.set_image(url=test_image_url)
            else:
                logger.info(f"🖼️ TEST: Preview image NOT set - include_preview: {include_preview}")
            
            # Set author with streamer icon - matching live format
            embed.set_author(name="TEST STREAMER", icon_url="https://static-cdn.jtvnw.net/jtv_user_pictures/test-profile_image-70x70.png")
            embed.set_footer(text="🎬 Twitch Stream Alert | Today at {}".format(datetime.now().strftime("%I:%M %p")), icon_url="https://static.twitchcdn.net/assets/favicon-32-d6025c14e900565d6177.png")
            
            # Prepare message content with role mention test
            content = "**TEST STREAMER** just went live!"
            
            # Add role mention if configured (this tests the actual functionality)
            if role_mention:
                content = f"{role_mention} {content}"
                
            # Create "Watch Stream" button
            class StreamView(discord.ui.View):
                def __init__(self, stream_url: str):
                    super().__init__(timeout=None)
                    button = discord.ui.Button(
                        label="📺 Watch Live",
                        style=discord.ButtonStyle.link,
                        url=stream_url
                    )
                    self.add_item(button)
            
            stream_url = "https://twitch.tv/test"
            view = StreamView(stream_url)
            
            # Check if the channel supports sending messages
            if isinstance(interaction.channel, (discord.TextChannel, discord.VoiceChannel, discord.Thread, discord.DMChannel)):
                await interaction.channel.send(content=content, embed=embed, view=view)
            else:
                await interaction.followup.send("❌ Cannot send test notification to this channel type. Please use this command in a text channel.", ephemeral=True)
                
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to send test notification: {e}", ephemeral=True)

    # Register the twitch group with the bot's command tree
    bot.tree.add_command(twitch_group)
    
    print("✅ Twitch streaming notifications loaded successfully!")