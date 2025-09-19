# Extended Discord Commands - Every Possible Discord API Feature
# This file contains comprehensive Discord functionality covering all API capabilities

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
import json
import time
import datetime
from datetime import timedelta
import aiohttp
import base64
import io
import re
from typing import Optional, Literal, List
import logging

def setup_extended_commands(bot):
    """Setup all extended Discord commands - every possible API feature"""
    
    # ============= ADVANCED MODERATION COMMANDS =============
    
    @bot.tree.command(name="bulkban", description="Ban multiple users by ID")
    @app_commands.describe(user_ids="User IDs separated by spaces", reason="Reason for bans")
    @app_commands.default_permissions(ban_members=True)
    async def bulkban(interaction: discord.Interaction, user_ids: str, reason: str = "Bulk ban"):
        """Bulk ban users by ID"""
        if not interaction.user.guild_permissions.ban_members:
            return await interaction.response.send_message("❌ You need Ban Members permission!", ephemeral=True)
        
        ids = user_ids.split()
        banned_count = 0
        failed_count = 0
        
        await interaction.response.defer()
        
        for user_id in ids:
            try:
                user_id = int(user_id)
                await interaction.guild.ban(discord.Object(id=user_id), reason=reason)
                banned_count += 1
            except:
                failed_count += 1
        
        embed = discord.Embed(
            title="🔨 Bulk Ban Complete",
            description=f"**Banned:** {banned_count} users\n**Failed:** {failed_count} users",
            color=0xff0000
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        await interaction.followup.send(embed=embed)
    
    @bot.tree.command(name="softban", description="Ban and immediately unban to delete messages")
    @app_commands.describe(member="User to softban", reason="Reason for softban")
    @app_commands.default_permissions(ban_members=True)
    async def softban(interaction: discord.Interaction, member: discord.Member, reason: str = "Softban"):
        """Softban a user (ban + unban to delete messages)"""
        if not interaction.user.guild_permissions.ban_members:
            return await interaction.response.send_message("❌ You need Ban Members permission!", ephemeral=True)
        
        try:
            await member.ban(reason=f"Softban: {reason}", delete_message_days=7)
            await interaction.guild.unban(member, reason="Softban unban")
            
            embed = discord.Embed(
                title="🔨 User Softbanned",
                description=f"**User:** {member.mention}\n**Reason:** {reason}",
                color=0xff9900
            )
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to softban: {e}", ephemeral=True)
    
    # ============= ADVANCED CHANNEL MANAGEMENT =============
    
    @bot.tree.command(name="clone", description="Clone a channel")
    @app_commands.describe(channel="Channel to clone", name="Name for cloned channel")
    @app_commands.default_permissions(manage_channels=True)
    async def clone_channel(interaction: discord.Interaction, channel: discord.TextChannel, name: str = None):
        """Clone a channel with all settings"""
        if not interaction.user.guild_permissions.manage_channels:
            return await interaction.response.send_message("❌ You need Manage Channels permission!", ephemeral=True)
        
        new_name = name or f"{channel.name}-clone"
        
        try:
            new_channel = await channel.clone(name=new_name)
            embed = discord.Embed(
                title="📋 Channel Cloned",
                description=f"**Original:** {channel.mention}\n**Clone:** {new_channel.mention}",
                color=0x00ff00
            )
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to clone channel: {e}", ephemeral=True)
    
    @bot.tree.command(name="setnsfw", description="Set channel NSFW status")
    @app_commands.describe(channel="Channel to modify", nsfw="NSFW status")
    @app_commands.default_permissions(manage_channels=True)
    async def set_nsfw(interaction: discord.Interaction, channel: discord.TextChannel = None, nsfw: bool = True):
        """Set channel NSFW status"""
        if not interaction.user.guild_permissions.manage_channels:
            return await interaction.response.send_message("❌ You need Manage Channels permission!", ephemeral=True)
        
        channel = channel or interaction.channel
        
        try:
            await channel.edit(nsfw=nsfw)
            status = "enabled" if nsfw else "disabled"
            embed = discord.Embed(
                title="🔞 NSFW Status Changed",
                description=f"NSFW has been **{status}** for {channel.mention}",
                color=0xff0000 if nsfw else 0x00ff00
            )
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to change NSFW status: {e}", ephemeral=True)
    
    # ============= ADVANCED ROLE MANAGEMENT =============
    
    @bot.tree.command(name="roleall", description="Give a role to all members")
    @app_commands.describe(role="Role to give", include_bots="Include bots")
    @app_commands.default_permissions(manage_roles=True)
    async def role_all(interaction: discord.Interaction, role: discord.Role, include_bots: bool = False):
        """Give a role to all members in the server"""
        if not interaction.user.guild_permissions.manage_roles:
            return await interaction.response.send_message("❌ You need Manage Roles permission!", ephemeral=True)
        
        await interaction.response.defer()
        
        members = [m for m in interaction.guild.members if include_bots or not m.bot]
        success_count = 0
        
        for member in members:
            try:
                if role not in member.roles:
                    await member.add_roles(role)
                    success_count += 1
            except:
                continue
        
        embed = discord.Embed(
            title="🎭 Mass Role Assignment",
            description=f"Added {role.mention} to **{success_count}** members",
            color=role.color
        )
        await interaction.followup.send(embed=embed)
    
    @bot.tree.command(name="rolecreate", description="Create a new role")
    @app_commands.describe(
        name="Role name", 
        color="Hex color (e.g., #ff0000)",
        hoist="Show separately",
        mentionable="Allow mentioning"
    )
    @app_commands.default_permissions(manage_roles=True)
    async def create_role(interaction: discord.Interaction, name: str, color: str = None, hoist: bool = False, mentionable: bool = False):
        """Create a new role with custom settings"""
        if not interaction.user.guild_permissions.manage_roles:
            return await interaction.response.send_message("❌ You need Manage Roles permission!", ephemeral=True)
        
        role_color = discord.Color.default()
        if color:
            try:
                role_color = discord.Color(int(color.replace("#", ""), 16))
            except:
                pass
        
        try:
            role = await interaction.guild.create_role(
                name=name,
                color=role_color,
                hoist=hoist,
                mentionable=mentionable
            )
            
            embed = discord.Embed(
                title="🎭 Role Created",
                description=f"Created role: {role.mention}",
                color=role.color
            )
            embed.add_field(name="Hoisted", value="Yes" if hoist else "No", inline=True)
            embed.add_field(name="Mentionable", value="Yes" if mentionable else "No", inline=True)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to create role: {e}", ephemeral=True)
    
    # ============= REACTION ROLES =============
    
    @bot.tree.command(name="reactrole", description="Create a reaction role message")
    @app_commands.describe(
        title="Embed title",
        description="Embed description", 
        emoji="Emoji for reaction",
        role="Role to assign"
    )
    @app_commands.default_permissions(manage_roles=True)
    async def react_role(interaction: discord.Interaction, title: str, description: str, emoji: str, role: discord.Role):
        """Create a reaction role system"""
        if not interaction.user.guild_permissions.manage_roles:
            return await interaction.response.send_message("❌ You need Manage Roles permission!", ephemeral=True)
        
        embed = discord.Embed(
            title=title,
            description=f"{description}\n\nReact with {emoji} to get {role.mention}",
            color=role.color
        )
        embed.set_footer(text="React below to get the role!")
        
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        await message.add_reaction(emoji)
        
        # Store reaction role data (in a real bot, use a database)
        # For now, we'll handle it in the event listener
    
    # ============= SERVER ANALYTICS =============
    
    @bot.tree.command(name="analytics", description="Show detailed server analytics")
    async def server_analytics(interaction: discord.Interaction):
        """Show comprehensive server statistics"""
        guild = interaction.guild
        
        # Count channel types
        text_channels = len([c for c in guild.channels if isinstance(c, discord.TextChannel)])
        voice_channels = len([c for c in guild.channels if isinstance(c, discord.VoiceChannel)])
        categories = len([c for c in guild.channels if isinstance(c, discord.CategoryChannel)])
        
        # Count member types
        humans = len([m for m in guild.members if not m.bot])
        bots = len([m for m in guild.members if m.bot])
        online = len([m for m in guild.members if m.status != discord.Status.offline])
        
        # Role stats
        role_count = len(guild.roles)
        
        embed = discord.Embed(
            title="📊 Server Analytics",
            description=f"Detailed statistics for **{guild.name}**",
            color=0x3498db,
            timestamp=datetime.datetime.utcnow()
        )
        
        embed.add_field(
            name="👥 Members",
            value=f"**Total:** {guild.member_count}\n**Humans:** {humans}\n**Bots:** {bots}\n**Online:** {online}",
            inline=True
        )
        
        embed.add_field(
            name="📝 Channels",
            value=f"**Text:** {text_channels}\n**Voice:** {voice_channels}\n**Categories:** {categories}\n**Total:** {len(guild.channels)}",
            inline=True
        )
        
        embed.add_field(
            name="🎭 Other",
            value=f"**Roles:** {role_count}\n**Emojis:** {len(guild.emojis)}\n**Boosts:** {guild.premium_subscription_count}",
            inline=True
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        await interaction.response.send_message(embed=embed)
    
    # ============= VOICE CHANNEL MANAGEMENT =============
    
    @bot.tree.command(name="voicemove", description="Move user between voice channels")
    @app_commands.describe(member="Member to move", channel="Voice channel to move to")
    @app_commands.default_permissions(move_members=True)
    async def voice_move(interaction: discord.Interaction, member: discord.Member, channel: discord.VoiceChannel):
        """Move a member to a different voice channel"""
        if not interaction.user.guild_permissions.move_members:
            return await interaction.response.send_message("❌ You need Move Members permission!", ephemeral=True)
        
        if not member.voice:
            return await interaction.response.send_message("❌ User is not in a voice channel!", ephemeral=True)
        
        try:
            await member.move_to(channel)
            embed = discord.Embed(
                title="🔊 Member Moved",
                description=f"Moved {member.mention} to {channel.mention}",
                color=0x00ff00
            )
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to move member: {e}", ephemeral=True)
    
    @bot.tree.command(name="voicekick", description="Disconnect user from voice channel")
    @app_commands.describe(member="Member to disconnect")
    @app_commands.default_permissions(move_members=True)
    async def voice_kick(interaction: discord.Interaction, member: discord.Member):
        """Disconnect a member from voice channel"""
        if not interaction.user.guild_permissions.move_members:
            return await interaction.response.send_message("❌ You need Move Members permission!", ephemeral=True)
        
        if not member.voice:
            return await interaction.response.send_message("❌ User is not in a voice channel!", ephemeral=True)
        
        try:
            await member.move_to(None)
            embed = discord.Embed(
                title="🔊 Member Disconnected",
                description=f"Disconnected {member.mention} from voice",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to disconnect member: {e}", ephemeral=True)
    
    # ============= MESSAGE MANAGEMENT =============
    
    @bot.tree.command(name="pin", description="Pin a message")
    @app_commands.describe(message_id="ID of message to pin")
    @app_commands.default_permissions(manage_messages=True)
    async def pin_message(interaction: discord.Interaction, message_id: str):
        """Pin a message by ID"""
        if not interaction.user.guild_permissions.manage_messages:
            return await interaction.response.send_message("❌ You need Manage Messages permission!", ephemeral=True)
        
        try:
            message = await interaction.channel.fetch_message(int(message_id))
            await message.pin()
            await interaction.response.send_message(f"📌 Pinned message!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to pin message: {e}", ephemeral=True)
    
    @bot.tree.command(name="unpin", description="Unpin a message")
    @app_commands.describe(message_id="ID of message to unpin")
    @app_commands.default_permissions(manage_messages=True)
    async def unpin_message(interaction: discord.Interaction, message_id: str):
        """Unpin a message by ID"""
        if not interaction.user.guild_permissions.manage_messages:
            return await interaction.response.send_message("❌ You need Manage Messages permission!", ephemeral=True)
        
        try:
            message = await interaction.channel.fetch_message(int(message_id))
            await message.unpin()
            await interaction.response.send_message(f"📌 Unpinned message!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to unpin message: {e}", ephemeral=True)
    
    # ============= WEBHOOK MANAGEMENT =============
    
    @bot.tree.command(name="webhook", description="Create a webhook")
    @app_commands.describe(name="Webhook name", avatar_url="Avatar URL for webhook")
    @app_commands.default_permissions(manage_webhooks=True)
    async def create_webhook(interaction: discord.Interaction, name: str, avatar_url: str = None):
        """Create a webhook in the current channel"""
        if not interaction.user.guild_permissions.manage_webhooks:
            return await interaction.response.send_message("❌ You need Manage Webhooks permission!", ephemeral=True)
        
        try:
            avatar = None
            if avatar_url:
                async with aiohttp.ClientSession() as session:
                    async with session.get(avatar_url) as resp:
                        avatar = await resp.read()
            
            webhook = await interaction.channel.create_webhook(name=name, avatar=avatar)
            
            embed = discord.Embed(
                title="🔗 Webhook Created",
                description=f"**Name:** {webhook.name}\n**URL:** ||{webhook.url}||",
                color=0x00ff00
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to create webhook: {e}", ephemeral=True)
    
    # ============= INVITE MANAGEMENT =============
    
    @bot.tree.command(name="invitelist", description="List all server invites")
    @app_commands.default_permissions(manage_guild=True)
    async def invite_list(interaction: discord.Interaction):
        """List all active invites for the server"""
        if not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("❌ You need Manage Server permission!", ephemeral=True)
        
        try:
            invites = await interaction.guild.invites()
            
            if not invites:
                return await interaction.response.send_message("❌ No active invites found!", ephemeral=True)
            
            embed = discord.Embed(
                title="📨 Server Invites",
                description=f"Found {len(invites)} active invites",
                color=0x3498db
            )
            
            for invite in invites[:10]:  # Limit to 10 to avoid embed limits
                channel_name = invite.channel.name if invite.channel else "Unknown"
                inviter = invite.inviter.display_name if invite.inviter else "Unknown"
                uses = invite.uses or 0
                max_uses = invite.max_uses or "∞"
                
                embed.add_field(
                    name=f"Code: {invite.code}",
                    value=f"**Channel:** #{channel_name}\n**Inviter:** {inviter}\n**Uses:** {uses}/{max_uses}",
                    inline=True
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to fetch invites: {e}", ephemeral=True)
    
    # ============= EMOJI MANAGEMENT =============
    
    @bot.tree.command(name="steal", description="Steal an emoji from another server")
    @app_commands.describe(emoji="Emoji to steal", name="Name for the emoji")
    @app_commands.default_permissions(manage_emojis=True)
    async def steal_emoji(interaction: discord.Interaction, emoji: str, name: str = None):
        """Steal an emoji and add it to this server"""
        if not interaction.user.guild_permissions.manage_emojis:
            return await interaction.response.send_message("❌ You need Manage Emojis permission!", ephemeral=True)
        
        # Extract emoji ID from custom emoji
        custom_emoji = re.search(r'<a?:(\w+):(\d+)>', emoji)
        
        if not custom_emoji:
            return await interaction.response.send_message("❌ Please provide a custom emoji!", ephemeral=True)
        
        emoji_name = name or custom_emoji.group(1)
        emoji_id = custom_emoji.group(2)
        emoji_animated = emoji.startswith('<a:')
        
        emoji_url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{'gif' if emoji_animated else 'png'}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(emoji_url) as resp:
                    emoji_bytes = await resp.read()
            
            new_emoji = await interaction.guild.create_custom_emoji(
                name=emoji_name,
                image=emoji_bytes
            )
            
            embed = discord.Embed(
                title="🔗 Emoji Stolen!",
                description=f"Added {new_emoji} as `:{emoji_name}:`",
                color=0x00ff00
            )
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to steal emoji: {e}", ephemeral=True)
    
    # ============= THREAD MANAGEMENT =============
    
    @bot.tree.command(name="thread", description="Create a thread")
    @app_commands.describe(name="Thread name", message_id="Message to create thread from")
    async def create_thread(interaction: discord.Interaction, name: str, message_id: str = None):
        """Create a thread in the current channel"""
        try:
            if message_id:
                message = await interaction.channel.fetch_message(int(message_id))
                thread = await message.create_thread(name=name)
            else:
                thread = await interaction.channel.create_thread(name=name)
            
            embed = discord.Embed(
                title="🧵 Thread Created",
                description=f"Created thread: {thread.mention}",
                color=0x00ff00
            )
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to create thread: {e}", ephemeral=True)
    
    # ============= STAGE CHANNEL MANAGEMENT =============
    
    @bot.tree.command(name="stage", description="Start a stage instance")
    @app_commands.describe(
        channel="Stage channel",
        topic="Stage topic",
        privacy_level="Privacy level"
    )
    @app_commands.default_permissions(manage_channels=True)
    async def start_stage(interaction: discord.Interaction, channel: discord.StageChannel, topic: str, privacy_level: Literal["guild_only", "public"] = "guild_only"):
        """Start a stage instance"""
        if not interaction.user.guild_permissions.manage_channels:
            return await interaction.response.send_message("❌ You need Manage Channels permission!", ephemeral=True)
        
        try:
            privacy = discord.StagePrivacyLevel.guild_only if privacy_level == "guild_only" else discord.StagePrivacyLevel.public
            
            stage_instance = await channel.create_instance(
                topic=topic,
                privacy_level=privacy
            )
            
            embed = discord.Embed(
                title="🎙️ Stage Started",
                description=f"**Topic:** {topic}\n**Channel:** {channel.mention}",
                color=0x9b59b6
            )
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to start stage: {e}", ephemeral=True)
    
    # ============= GUILD SCHEDULED EVENTS =============
    
    @bot.tree.command(name="event", description="Create a scheduled event")
    @app_commands.describe(
        name="Event name",
        description="Event description",
        start_time="Start time (YYYY-MM-DD HH:MM)",
        location="Event location"
    )
    @app_commands.default_permissions(manage_events=True)
    async def create_event(interaction: discord.Interaction, name: str, description: str, start_time: str, location: str = None):
        """Create a scheduled guild event"""
        if not interaction.user.guild_permissions.manage_events:
            return await interaction.response.send_message("❌ You need Manage Events permission!", ephemeral=True)
        
        try:
            # Parse start time
            start_dt = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M")
            start_dt = start_dt.replace(tzinfo=datetime.timezone.utc)
            
            event = await interaction.guild.create_scheduled_event(
                name=name,
                description=description,
                start_time=start_dt,
                entity_type=discord.EntityType.external if location else discord.EntityType.voice,
                location=location
            )
            
            embed = discord.Embed(
                title="📅 Event Created",
                description=f"**{name}**\n{description}",
                color=0xe74c3c
            )
            embed.add_field(name="Start Time", value=f"<t:{int(start_dt.timestamp())}:F>", inline=False)
            if location:
                embed.add_field(name="Location", value=location, inline=False)
            
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to create event: {e}", ephemeral=True)
    
    print("✅ All extended Discord commands loaded successfully!")
