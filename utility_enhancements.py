"""
Advanced Utility Features for Discord Bot
Includes: Server analytics, custom tags, reminder system, URL previews
"""

import discord
from discord import app_commands
from discord.ext import commands, tasks
import aiohttp
import asyncio
import json
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List
import re
from bs4 import BeautifulSoup
import os
import sqlite3
from db_app import app, with_db_context
from models import *

class ServerAnalytics:
    """Track and display server analytics"""
    
    def __init__(self, bot):
        self.bot = bot
        self.daily_stats = {}
        
    def record_message(self, guild_id: int, user_id: int, channel_id: int):
        """Record a message for analytics"""
        try:
            today = datetime.now(timezone.utc).date()
            
            with db.session.begin():
                # Update server stats
                stats = ServerStats.query.filter_by(
                    guild_id=guild_id, 
                    date=today
                ).first()
                
                if not stats:
                    stats = ServerStats(guild_id=guild_id, date=today)
                    db.session.add(stats)
                
                stats.messages_count += 1
                
                # Update user profile
                user = UserProfile.query.filter_by(
                    user_id=user_id, 
                    guild_id=guild_id
                ).first()
                
                if user:
                    user.messages_sent += 1
                    user.xp += 1
                    # Level up check
                    new_level = int((user.xp / 100) ** 0.5) + 1
                    if new_level > user.level:
                        user.level = new_level
                
        except Exception as e:
            print(f"Analytics error: {e}")
    
    def record_command(self, guild_id: int, user_id: int, command_name: str, channel_id: int):
        """Record command usage"""
        try:
            with db.session.begin():
                cmd_usage = CommandUsage(
                    guild_id=guild_id,
                    user_id=user_id,
                    command_name=command_name,
                    channel_id=channel_id
                )
                db.session.add(cmd_usage)
                
                # Update user profile
                user = UserProfile.query.filter_by(
                    user_id=user_id,
                    guild_id=guild_id
                ).first()
                
                if user:
                    user.commands_used += 1
                    user.xp += 2  # Commands give more XP
                
        except Exception as e:
            print(f"Command analytics error: {e}")

class URLPreviewSystem:
    """URL preview and metadata extraction"""
    
    @staticmethod
    def _is_safe_url(url: str) -> bool:
        """Check if URL is safe to fetch (prevent SSRF)"""
        try:
            from urllib.parse import urlparse
            import ipaddress
            import socket
            
            parsed = urlparse(url)
            
            # Only allow HTTP/HTTPS
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Must have a hostname
            if not parsed.hostname:
                return False
            
            # Resolve hostname to IP
            try:
                ip = socket.gethostbyname(parsed.hostname)
                ip_obj = ipaddress.ip_address(ip)
                
                # Block private/reserved IPs
                if ip_obj.is_private or ip_obj.is_reserved or ip_obj.is_loopback:
                    return False
                    
                # Block multicast and link-local
                if ip_obj.is_multicast or ip_obj.is_link_local:
                    return False
                    
            except (socket.gaierror, ValueError):
                return False
            
            # Block dangerous ports
            dangerous_ports = {22, 23, 25, 53, 135, 139, 445, 993, 995, 1433, 1521, 3306, 3389, 5432, 5984, 6379, 8086, 9200, 11211, 27017, 50070}
            if parsed.port and parsed.port in dangerous_ports:
                return False
                
            return True
        except Exception:
            return False

    @staticmethod
    async def get_url_preview(url: str) -> Optional[Dict]:
        """Extract metadata from URL (with SSRF protection)"""
        try:
            # Security validation
            if not URLPreviewSystem._is_safe_url(url):
                return None
            
            # Create URL hash for caching
            url_hash = hashlib.sha256(url.encode()).hexdigest()
            
            # Check cache first
            cached = UrlPreview.query.filter_by(url_hash=url_hash).first()
            if cached and cached.expires_at > datetime.now(timezone.utc):
                return {
                    'title': cached.title,
                    'description': cached.description,
                    'image': cached.image_url,
                    'site_name': cached.site_name
                }
            
            # Fetch new data with strict limits
            timeout = aiohttp.ClientTimeout(total=3, connect=1)
            connector = aiohttp.TCPConnector(limit=1, limit_per_host=1)
            async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
                try:
                    headers = {
                        'User-Agent': 'Discord-Bot-URL-Preview/1.0',
                        'Accept': 'text/html,application/xhtml+xml',
                    }
                    async with session.get(url, headers=headers) as response:
                        if response.status != 200:
                            return None
                        
                        # Check content type
                        content_type = response.headers.get('content-type', '').lower()
                        if not content_type.startswith('text/html'):
                            return None
                        
                        # Limit response size (1MB max)
                        content_length = response.headers.get('content-length')
                        if content_length and int(content_length) > 1024 * 1024:
                            return None
                            
                        html_bytes = await response.read()
                        if len(html_bytes) > 1024 * 1024:  # 1MB limit
                            return None
                            
                        html = html_bytes.decode('utf-8', errors='ignore')
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract metadata
                        title = None
                        description = None
                        image = None
                        site_name = None
                        
                        # Try Open Graph tags first
                        og_title = soup.find('meta', property='og:title')
                        if og_title:
                            title = og_title.get('content')
                        
                        og_desc = soup.find('meta', property='og:description')
                        if og_desc:
                            description = og_desc.get('content')
                        
                        og_image = soup.find('meta', property='og:image')
                        if og_image:
                            image = og_image.get('content')
                        
                        og_site = soup.find('meta', property='og:site_name')
                        if og_site:
                            site_name = og_site.get('content')
                        
                        # Fallback to standard tags
                        if not title:
                            title_tag = soup.find('title')
                            if title_tag:
                                title = title_tag.get_text().strip()
                        
                        if not description:
                            desc_tag = soup.find('meta', attrs={'name': 'description'})
                            if desc_tag:
                                description = desc_tag.get('content')
                        
                        # Cache the result
                        with db.session.begin():
                            if cached:
                                cached.title = title
                                cached.description = description
                                cached.image_url = image
                                cached.site_name = site_name
                                cached.expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
                            else:
                                preview = UrlPreview(
                                    url_hash=url_hash,
                                    original_url=url,
                                    title=title,
                                    description=description,
                                    image_url=image,
                                    site_name=site_name,
                                    expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
                                )
                                db.session.add(preview)
                            db.session.commit()
                        
                        return {
                            'title': title,
                            'description': description,
                            'image': image,
                            'site_name': site_name
                        }
                        
                except Exception as e:
                    print(f"URL preview error: {e}")
                    return None
                    
        except Exception as e:
            print(f"URL preview system error: {e}")
            return None

def setup_utility_enhancements(bot):
    """Setup all utility enhancement commands"""
    
    # Initialize analytics system
    analytics = ServerAnalytics(bot)
    url_preview = URLPreviewSystem()
    
    # Hook into message events for analytics
    @bot.event
    async def on_message(message):
        if not message.author.bot and message.guild:
            analytics.record_message(message.guild.id, message.author.id, message.channel.id)
            
            # Check for URLs in message for preview
            url_pattern = r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?'
            urls = re.findall(url_pattern, message.content)
            
            if urls and len(urls) == 1:  # Only preview single URLs to avoid spam
                url = urls[0]
                preview_data = await url_preview.get_url_preview(url)
                
                if preview_data and preview_data.get('title'):
                    embed = discord.Embed(
                        title=preview_data['title'][:256],
                        description=preview_data.get('description', '')[:500],
                        color=0x1f8b4c,
                        url=url
                    )
                    
                    if preview_data.get('image'):
                        embed.set_image(url=preview_data['image'])
                    
                    if preview_data.get('site_name'):
                        embed.set_footer(text=f"📄 {preview_data['site_name']}")
                    
                    try:
                        await message.channel.send(embed=embed)
                    except:
                        pass  # Ignore errors
    
    # ============= ANALYTICS COMMANDS =============
    
    @bot.tree.command(name="analytics", description="View server analytics and statistics")
    @app_commands.describe(timeframe="Time period to analyze")
    @app_commands.choices(timeframe=[
        app_commands.Choice(name="Today", value="today"),
        app_commands.Choice(name="This Week", value="week"),
        app_commands.Choice(name="This Month", value="month"),
        app_commands.Choice(name="All Time", value="all")
    ])
    async def analytics_command(interaction: discord.Interaction, timeframe: str = "week"):
        """Display server analytics"""
        if not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("❌ You need Manage Server permission!", ephemeral=True)
        
        guild_id = interaction.guild.id
        
        try:
            # Calculate date range
            now = datetime.now(timezone.utc)
            if timeframe == "today":
                start_date = now.date()
                end_date = start_date
            elif timeframe == "week":
                start_date = (now - timedelta(days=7)).date()
                end_date = now.date()
            elif timeframe == "month":
                start_date = (now - timedelta(days=30)).date()
                end_date = now.date()
            else:  # all time
                start_date = None
                end_date = None
            
            # Query statistics
            stats_query = ServerStats.query.filter_by(guild_id=guild_id)
            if start_date:
                stats_query = stats_query.filter(ServerStats.date >= start_date)
            if end_date:
                stats_query = stats_query.filter(ServerStats.date <= end_date)
            
            stats_list = stats_query.all()
            
            if not stats_list:
                return await interaction.response.send_message("📊 No analytics data available for this period.", ephemeral=True)
            
            # Calculate totals
            total_messages = sum(s.messages_count for s in stats_list)
            total_commands = sum(s.commands_used for s in stats_list)
            avg_daily_messages = total_messages / len(stats_list) if stats_list else 0
            
            # Get top commands
            cmd_query = CommandUsage.query.filter_by(guild_id=guild_id)
            if start_date:
                cmd_query = cmd_query.filter(CommandUsage.timestamp >= datetime.combine(start_date, datetime.min.time()))
            
            top_commands = db.session.query(
                CommandUsage.command_name,
                db.func.count(CommandUsage.id).label('count')
            ).filter_by(guild_id=guild_id).group_by(CommandUsage.command_name).order_by(db.func.count(CommandUsage.id).desc()).limit(5).all()
            
            # Create analytics embed
            embed = discord.Embed(
                title="📊 Server Analytics",
                description=f"Statistics for **{timeframe.replace('_', ' ').title()}**",
                color=0x3498db,
                timestamp=now
            )
            
            embed.add_field(
                name="📈 Message Statistics",
                value=f"**Total Messages:** {total_messages:,}\n**Average/Day:** {avg_daily_messages:.1f}\n**Days Tracked:** {len(stats_list)}",
                inline=True
            )
            
            embed.add_field(
                name="🤖 Bot Usage",
                value=f"**Commands Used:** {total_commands:,}\n**Avg Commands/Day:** {total_commands/len(stats_list) if stats_list else 0:.1f}",
                inline=True
            )
            
            embed.add_field(
                name="👥 Server Info",
                value=f"**Members:** {interaction.guild.member_count}\n**Channels:** {len(interaction.guild.channels)}\n**Roles:** {len(interaction.guild.roles)}",
                inline=True
            )
            
            if top_commands:
                cmd_list = "\n".join([f"**{cmd[0]}** - {cmd[1]:,} uses" for cmd in top_commands])
                embed.add_field(
                    name="🏆 Top Commands",
                    value=cmd_list,
                    inline=False
                )
            
            embed.set_footer(text=f"Analytics for {interaction.guild.name}", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to generate analytics: {e}", ephemeral=True)
    
    # ============= CUSTOM TAGS SYSTEM =============
    
    @bot.tree.command(name="tagcreate", description="Create a custom server tag")
    @app_commands.describe(name="Tag name", content="Tag content")
    async def tag_create(interaction: discord.Interaction, name: str, content: str):
        """Create a custom tag"""
        if not interaction.user.guild_permissions.manage_messages:
            return await interaction.response.send_message("❌ You need Manage Messages permission!", ephemeral=True)
        
        if len(name) > 50:
            return await interaction.response.send_message("❌ Tag name too long! Max 50 characters.", ephemeral=True)
        
        if len(content) > 2000:
            return await interaction.response.send_message("❌ Tag content too long! Max 2000 characters.", ephemeral=True)
        
        try:
            # Check if tag already exists
            existing = CustomTag.query.filter_by(
                guild_id=interaction.guild.id,
                name=name.lower()
            ).first()
            
            if existing:
                return await interaction.response.send_message(f"❌ Tag `{name}` already exists!", ephemeral=True)
            
            # Create new tag
            with db.session.begin():
                tag = CustomTag(
                    guild_id=interaction.guild.id,
                    name=name.lower(),
                    content=content,
                    created_by=interaction.user.id
                )
                db.session.add(tag)
                db.session.commit()
            
            embed = discord.Embed(
                title="✅ Tag Created",
                description=f"Created tag `{name}` successfully!\n\nUse `/tag {name}` to display it.",
                color=0x00ff00
            )
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to create tag: {e}", ephemeral=True)
    
    @bot.tree.command(name="tagshow", description="Display a custom server tag")
    @app_commands.describe(name="Tag name to display")
    async def tag_show(interaction: discord.Interaction, name: str):
        """Show a custom tag"""
        try:
            tag = CustomTag.query.filter_by(
                guild_id=interaction.guild.id,
                name=name.lower()
            ).first()
            
            if not tag:
                return await interaction.response.send_message(f"❌ Tag `{name}` not found!", ephemeral=True)
            
            # Update usage counter
            with db.session.begin():
                tag.uses += 1
                db.session.commit()
            
            # Display tag content
            if tag.embed_data:
                # Rich embed
                embed_data = json.loads(tag.embed_data)
                embed = discord.Embed.from_dict(embed_data)
            else:
                # Simple content
                embed = discord.Embed(
                    description=tag.content,
                    color=0x3498db
                )
            
            embed.set_footer(text=f"Tag: {tag.name} | Uses: {tag.uses}")
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to show tag: {e}", ephemeral=True)
    
    @bot.tree.command(name="taglist", description="List all server tags")
    async def tag_list(interaction: discord.Interaction):
        """List all custom tags"""
        try:
            tags = CustomTag.query.filter_by(guild_id=interaction.guild.id).order_by(CustomTag.uses.desc()).all()
            
            if not tags:
                return await interaction.response.send_message("📝 No custom tags found for this server.", ephemeral=True)
            
            embed = discord.Embed(
                title="📝 Server Tags",
                color=0x3498db
            )
            
            # Group tags in pages of 10
            tag_list = []
            for tag in tags[:25]:  # Limit to 25 tags
                creator = interaction.guild.get_member(tag.created_by)
                creator_name = creator.display_name if creator else "Unknown"
                tag_list.append(f"**{tag.name}** - {tag.uses} uses (by {creator_name})")
            
            embed.description = "\n".join(tag_list)
            embed.set_footer(text=f"Total: {len(tags)} tags | Use /tagshow <name> to display a tag")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to list tags: {e}", ephemeral=True)
    
    # ============= REMINDER SYSTEM =============
    
    @bot.tree.command(name="remind", description="Set a personal reminder")
    @app_commands.describe(
        duration="How long until reminder (e.g., '1h', '30m', '2d')",
        content="What to remind you about"
    )
    async def remind_me(interaction: discord.Interaction, duration: str, content: str):
        """Set a personal reminder"""
        try:
            # Parse duration
            time_units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400, 'w': 604800}
            duration = duration.lower().strip()
            
            # Extract number and unit
            import re
            match = re.match(r'^(\d+)([smhdw])$', duration)
            if not match:
                return await interaction.response.send_message(
                    "❌ Invalid duration format! Use: `1h`, `30m`, `2d`, etc.", 
                    ephemeral=True
                )
            
            amount, unit = match.groups()
            seconds = int(amount) * time_units[unit]
            
            if seconds < 60:  # Minimum 1 minute
                return await interaction.response.send_message("❌ Minimum reminder time is 1 minute!", ephemeral=True)
            
            if seconds > 2592000:  # Maximum 30 days
                return await interaction.response.send_message("❌ Maximum reminder time is 30 days!", ephemeral=True)
            
            # Create reminder
            remind_at = datetime.now(timezone.utc) + timedelta(seconds=seconds)
            
            with db.session.begin():
                reminder = Reminder(
                    user_id=interaction.user.id,
                    guild_id=interaction.guild.id,
                    channel_id=interaction.channel.id,
                    content=content,
                    remind_at=remind_at
                )
                db.session.add(reminder)
                db.session.commit()
            
            embed = discord.Embed(
                title="⏰ Reminder Set",
                description=f"I'll remind you about: **{content}**",
                color=0x3498db
            )
            embed.add_field(
                name="When",
                value=f"<t:{int(remind_at.timestamp())}:F> (<t:{int(remind_at.timestamp())}:R>)",
                inline=False
            )
            embed.set_footer(text="You'll be pinged when the time comes!")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to set reminder: {e}", ephemeral=True)
    
    @bot.tree.command(name="reminders", description="View your active reminders")
    async def my_reminders(interaction: discord.Interaction):
        """View active reminders"""
        try:
            reminders = Reminder.query.filter_by(
                user_id=interaction.user.id,
                guild_id=interaction.guild.id,
                is_completed=False
            ).order_by(Reminder.remind_at).all()
            
            if not reminders:
                return await interaction.response.send_message("⏰ You have no active reminders.", ephemeral=True)
            
            embed = discord.Embed(
                title="⏰ Your Active Reminders",
                color=0x3498db
            )
            
            for i, reminder in enumerate(reminders[:10], 1):  # Limit to 10
                embed.add_field(
                    name=f"{i}. {reminder.content[:50]}{'...' if len(reminder.content) > 50 else ''}",
                    value=f"<t:{int(reminder.remind_at.timestamp())}:R>",
                    inline=False
                )
            
            if len(reminders) > 10:
                embed.set_footer(text=f"Showing first 10 of {len(reminders)} reminders")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to get reminders: {e}", ephemeral=True)
    
    # Background task to check reminders
    @tasks.loop(minutes=1)
    async def check_reminders():
        """Check for due reminders"""
        try:
            with app.app_context():
                now = datetime.now(timezone.utc)
                due_reminders = Reminder.query.filter(
                    Reminder.remind_at <= now,
                    Reminder.is_completed == False
                ).all()
                
                for reminder in due_reminders:
                    try:
                        guild = bot.get_guild(reminder.guild_id)
                        if not guild:
                            continue
                        
                        channel = guild.get_channel(reminder.channel_id)
                        user = guild.get_member(reminder.user_id)
                        
                        if channel and user:
                            embed = discord.Embed(
                                title="⏰ Reminder",
                                description=reminder.content,
                                color=0xff9500
                            )
                            embed.set_footer(text="This is your reminder!")
                            
                            await channel.send(f"{user.mention}", embed=embed)
                        
                        # Mark as completed
                        with db.session.begin():
                            reminder.is_completed = True
                            
                    except Exception as e:
                        print(f"Error sending reminder: {e}")
                    
        except Exception as e:
            print(f"Error checking reminders: {e}")
    
    # Start the reminder task
    if not check_reminders.is_running():
        check_reminders.start()
    
    print("✅ All utility enhancement commands loaded successfully!")