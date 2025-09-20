# Advanced Discord Features - Cutting-edge Discord API capabilities
# Every possible Discord feature implementation

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

def setup_advanced_features(bot):
    """Setup advanced Discord API features"""
    
    # ============= CONTEXT MENUS (User & Message Commands) =============
    
    @bot.tree.context_menu(name="User Info")
    async def user_info_context(interaction: discord.Interaction, member: discord.Member):
        """Context menu command for user info"""
        embed = discord.Embed(
            title="👤 User Information",
            color=member.color or 0x000000
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Username", value=str(member), inline=True)
        embed.add_field(name="Display Name", value=member.display_name, inline=True)
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Joined", value=f"<t:{int(member.joined_at.timestamp())}:F>", inline=True)
        embed.add_field(name="Created", value=f"<t:{int(member.created_at.timestamp())}:F>", inline=True)
        embed.add_field(name="Roles", value=f"{len(member.roles)-1} roles", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @bot.tree.context_menu(name="Translate Message")
    async def translate_context(interaction: discord.Interaction, message: discord.Message):
        """Context menu command to translate a message"""
        embed = discord.Embed(
            title="🌐 Message Translation",
            description=f"**Original:** {message.content[:500]}\n**Translation:** Translation requires API setup",
            color=0x4285f4
        )
        embed.set_footer(text=f"Message by {message.author.display_name}")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # ============= AUTOCOMPLETE FEATURES =============
    
    async def tag_autocomplete(interaction: discord.Interaction, current: str):
        """Autocomplete for tag commands"""
        tags = ["welcome", "rules", "faq", "help", "support", "info", "discord", "bot", "commands", "server"]
        return [
            app_commands.Choice(name=tag, value=tag)
            for tag in tags if current.lower() in tag.lower()
        ][:25]
    
    @bot.tree.command(name="tag", description="Show a server tag")
    @app_commands.describe(name="Tag name")
    @app_commands.autocomplete(name=tag_autocomplete)
    async def show_tag(interaction: discord.Interaction, name: str):
        """Show a predefined server tag"""
        tags = {
            "welcome": "Welcome to our Discord server! Please read the rules and have fun!",
            "rules": "1. Be respectful\n2. No spam\n3. Follow Discord ToS\n4. Have fun!",
            "faq": "Frequently Asked Questions:\nQ: How do I get help?\nA: Use the /help command!",
            "help": "Need help? Contact a moderator or use our support commands!",
            "support": "For technical support, please create a ticket in #support",
            "info": "This is a community Discord server focused on gaming and friendship.",
            "discord": "Discord is a voice, video and text communication service.",
            "bot": "I'm a multi-purpose Discord bot with many features!",
            "commands": "Use /help to see all available commands!",
            "server": f"Welcome to {interaction.guild.name}! We're glad you're here."
        }
        
        content = tags.get(name.lower(), "Tag not found!")
        
        embed = discord.Embed(
            title=f"📋 Tag: {name}",
            description=content,
            color=0x3498db
        )
        
        await interaction.response.send_message(embed=embed)
    
    # ============= MODAL FORMS =============
    
    class FeedbackModal(discord.ui.Modal, title='Server Feedback'):
        def __init__(self):
            super().__init__()
        
        feedback_type = discord.ui.TextInput(
            label='Feedback Type',
            placeholder='Bug Report, Suggestion, Compliment, etc.',
            max_length=50
        )
        
        feedback_content = discord.ui.TextInput(
            label='Your Feedback',
            style=discord.TextStyle.paragraph,
            placeholder='Please provide detailed feedback...',
            max_length=1000
        )
        
        async def on_submit(self, interaction: discord.Interaction):
            embed = discord.Embed(
                title="📝 Feedback Received",
                description="Thank you for your feedback!",
                color=0x00ff00
            )
            embed.add_field(name="Type", value=self.feedback_type.value, inline=True)
            embed.add_field(name="Feedback", value=self.feedback_content.value[:500], inline=False)
            embed.set_footer(text=f"From: {interaction.user}")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @bot.tree.command(name="feedback", description="Provide server feedback")
    async def feedback_command(interaction: discord.Interaction):
        """Open a feedback form modal"""
        modal = FeedbackModal()
        await interaction.response.send_modal(modal)
    
    # ============= BUTTON INTERACTIONS =============
    
    class RoleButtonView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)
        
        @discord.ui.button(label='Gamer', style=discord.ButtonStyle.primary, emoji='🎮')
        async def gamer_role(self, interaction: discord.Interaction, button: discord.ui.Button):
            role = discord.utils.get(interaction.guild.roles, name="Gamer")
            if role:
                if role in interaction.user.roles:
                    await interaction.user.remove_roles(role)
                    await interaction.response.send_message(f"Removed {role.mention} role!", ephemeral=True)
                else:
                    await interaction.user.add_roles(role)
                    await interaction.response.send_message(f"Added {role.mention} role!", ephemeral=True)
            else:
                await interaction.response.send_message("Role not found!", ephemeral=True)
        
        @discord.ui.button(label='Artist', style=discord.ButtonStyle.secondary, emoji='🎨')
        async def artist_role(self, interaction: discord.Interaction, button: discord.ui.Button):
            role = discord.utils.get(interaction.guild.roles, name="Artist")
            if role:
                if role in interaction.user.roles:
                    await interaction.user.remove_roles(role)
                    await interaction.response.send_message(f"Removed {role.mention} role!", ephemeral=True)
                else:
                    await interaction.user.add_roles(role)
                    await interaction.response.send_message(f"Added {role.mention} role!", ephemeral=True)
            else:
                await interaction.response.send_message("Role not found!", ephemeral=True)
    
    @bot.tree.command(name="rolemenu", description="Create a role selection menu")
    @app_commands.default_permissions(manage_roles=True)
    async def role_menu(interaction: discord.Interaction):
        """Create an interactive role selection menu"""
        embed = discord.Embed(
            title="🎭 Role Selection",
            description="Click the buttons below to add or remove roles!",
            color=0x9b59b6
        )
        
        view = RoleButtonView()
        await interaction.response.send_message(embed=embed, view=view)
    
    # ============= SELECT MENUS =============
    
    class ColorRoleSelect(discord.ui.Select):
        def __init__(self):
            options = [
                discord.SelectOption(label='Red', value='red', emoji='🔴'),
                discord.SelectOption(label='Blue', value='blue', emoji='🔵'),
                discord.SelectOption(label='Green', value='green', emoji='🟢'),
                discord.SelectOption(label='Yellow', value='yellow', emoji='🟡'),
                discord.SelectOption(label='Purple', value='purple', emoji='🟣'),
            ]
            super().__init__(placeholder='Choose a color role...', options=options, max_values=1)
        
        async def callback(self, interaction: discord.Interaction):
            color_map = {
                'red': 0xff0000,
                'blue': 0x0000ff,
                'green': 0x00ff00,
                'yellow': 0xffff00,
                'purple': 0x800080
            }
            
            selected_color = self.values[0]
            role_name = f"{selected_color.title()} Team"
            
            role = discord.utils.get(interaction.guild.roles, name=role_name)
            if not role:
                # Create role if it doesn't exist
                try:
                    role = await interaction.guild.create_role(
                        name=role_name,
                        color=discord.Color(color_map[selected_color])
                    )
                except:
                    pass
            
            if role:
                # Remove other color roles first
                color_roles = [discord.utils.get(interaction.guild.roles, name=f"{c.title()} Team") 
                              for c in color_map.keys()]
                color_roles = [r for r in color_roles if r and r in interaction.user.roles]
                
                if color_roles:
                    await interaction.user.remove_roles(*color_roles)
                
                await interaction.user.add_roles(role)
                await interaction.response.send_message(f"You now have the {role.mention} role!", ephemeral=True)
            else:
                await interaction.response.send_message("Failed to assign role!", ephemeral=True)
    
    class ColorRoleView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)
            self.add_item(ColorRoleSelect())
    
    @bot.tree.command(name="colorroles", description="Create color role selection menu")
    @app_commands.default_permissions(manage_roles=True)
    async def color_roles(interaction: discord.Interaction):
        """Create a color role selection dropdown"""
        embed = discord.Embed(
            title="🌈 Color Roles",
            description="Select a color from the dropdown below!",
            color=0x000000
        )
        
        view = ColorRoleView()
        await interaction.response.send_message(embed=embed, view=view)
    
    # ============= PERSISTENT VIEWS =============
    
    class PersistentRoleView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)
        
        @discord.ui.button(label='Notifications', style=discord.ButtonStyle.secondary, emoji='🔔', custom_id='notifications_role')
        async def notifications_role(self, interaction: discord.Interaction, button: discord.ui.Button):
            role = discord.utils.get(interaction.guild.roles, name="Notifications")
            if role:
                if role in interaction.user.roles:
                    await interaction.user.remove_roles(role)
                    await interaction.response.send_message("You will no longer receive notifications!", ephemeral=True)
                else:
                    await interaction.user.add_roles(role)
                    await interaction.response.send_message("You will now receive notifications!", ephemeral=True)
            else:
                await interaction.response.send_message("Notifications role not found!", ephemeral=True)
    
    # ============= SLASH COMMAND GROUPS =============
    
    moderation_group = app_commands.Group(name="moderation", description="Advanced moderation commands")
    
    @moderation_group.command(name="automod", description="Configure automoderation")
    @app_commands.describe(
        action="Automod action",
        setting="Setting to configure"
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="Enable", value="enable"),
            app_commands.Choice(name="Disable", value="disable"),
            app_commands.Choice(name="Configure", value="configure")
        ],
        setting=[
            app_commands.Choice(name="Spam Detection", value="spam"),
            app_commands.Choice(name="Link Filtering", value="links"),
            app_commands.Choice(name="Word Filter", value="words"),
            app_commands.Choice(name="Caps Lock", value="caps")
        ]
    )
    async def automod_config(interaction: discord.Interaction, action: str, setting: str):
        """Configure automoderation settings"""
        if not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("❌ You need Manage Server permission!", ephemeral=True)
        
        embed = discord.Embed(
            title="🤖 Automoderation Configuration",
            description=f"**Action:** {action.title()}\n**Setting:** {setting.title()}",
            color=0x3498db
        )
        embed.add_field(name="Status", value="Configuration saved!", inline=False)
        embed.set_footer(text="Note: This is a demo - real automod would require database storage")
        
        await interaction.response.send_message(embed=embed)
    
    @moderation_group.command(name="logs", description="Configure logging settings")
    @app_commands.describe(
        log_type="Type of logs to configure",
        channel="Channel for logs"
    )
    @app_commands.choices(log_type=[
        app_commands.Choice(name="Message Logs", value="messages"),
        app_commands.Choice(name="Member Logs", value="members"),
        app_commands.Choice(name="Moderation Logs", value="moderation"),
        app_commands.Choice(name="Voice Logs", value="voice")
    ])
    async def configure_logs(interaction: discord.Interaction, log_type: str, channel: discord.TextChannel):
        """Configure server logging"""
        if not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("❌ You need Manage Server permission!", ephemeral=True)
        
        embed = discord.Embed(
            title="📝 Logging Configuration",
            description=f"**Log Type:** {log_type.title()}\n**Channel:** {channel.mention}",
            color=0x2ecc71
        )
        embed.set_footer(text="Logging configuration saved!")
        
        await interaction.response.send_message(embed=embed)
    
    bot.tree.add_command(moderation_group)
    
    # ============= TRANSFORMERS =============
    
    class MemberTransformer(app_commands.Transformer):
        async def transform(self, interaction: discord.Interaction, value: str) -> discord.Member:
            # Try to get member by ID, mention, or name
            try:
                # Try ID first
                member_id = int(value.strip('<@!>'))
                return interaction.guild.get_member(member_id)
            except ValueError:
                # Try by name
                member = discord.utils.get(interaction.guild.members, display_name=value)
                if not member:
                    member = discord.utils.get(interaction.guild.members, name=value)
                return member
    
    # ============= COMMAND ERROR HANDLING =============
    
    async def safe_respond(interaction: discord.Interaction, *args, **kwargs):
        """Safe interaction responder that avoids double acknowledgment"""
        try:
            if interaction.response.is_done():
                return await interaction.followup.send(*args, **kwargs)
            else:
                return await interaction.response.send_message(*args, **kwargs)
        except Exception as e:
            print(f"Error in safe_respond: {e}")
            # If all else fails, try followup
            try:
                return await interaction.followup.send(*args, **kwargs)
            except:
                pass  # Give up gracefully

    # DISABLED - was causing interaction conflicts
    # @bot.tree.error
    async def on_app_command_error_DISABLED(interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Global error handler for slash commands"""
        try:
            if isinstance(error, app_commands.CommandOnCooldown):
                embed = discord.Embed(
                    title="⏰ Command on Cooldown",
                    description=f"Please wait {error.retry_after:.2f} seconds before using this command again.",
                    color=0xff9900
                )
                await safe_respond(interaction, embed=embed, ephemeral=True)
            elif isinstance(error, app_commands.MissingPermissions):
                embed = discord.Embed(
                    title="❌ Missing Permissions",
                    description="You don't have permission to use this command.",
                    color=0xff0000
                )
                await safe_respond(interaction, embed=embed, ephemeral=True)
            else:
                # Only respond to real errors, not CommandInvokeError which is already handled
                if not isinstance(error, app_commands.CommandInvokeError):
                    embed = discord.Embed(
                        title="❌ Command Error", 
                        description="An error occurred while executing this command.",
                        color=0xff0000
                    )
                    await safe_respond(interaction, embed=embed, ephemeral=True)
        except Exception as e:
            print(f"Error in global error handler: {e}")
    
    # ============= COOLDOWNS AND CHECKS =============
    
    @bot.tree.command(name="premium", description="Premium-only command with cooldown")
    @app_commands.checks.cooldown(1, 60.0, key=lambda i: i.user.id)
    async def premium_command(interaction: discord.Interaction):
        """Example premium command with cooldown"""
        # Check if user has premium role
        premium_role = discord.utils.get(interaction.guild.roles, name="Premium")
        
        if premium_role and premium_role in interaction.user.roles:
            embed = discord.Embed(
                title="⭐ Premium Feature",
                description="Welcome to the premium features!",
                color=0xffd700
            )
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                title="❌ Premium Required",
                description="This feature requires premium membership.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    print("✅ All advanced Discord features loaded successfully!")