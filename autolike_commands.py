import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import logging

logger = logging.getLogger(__name__)

def setup_autolike_commands(bot):
    """Set up auto-like commands"""
    
    @bot.tree.command(name="autolike", description="Configure auto-like for messages and images in specific channels")
    @app_commands.describe(
        action="Action: setup, add, remove, list, toggle, emoji, mode",
        channel="Channel to configure auto-like for",
        value="Value for the action (emoji for emoji action, all/images for mode)"
    )
    async def autolike_slash(interaction: discord.Interaction, action: str, channel: Optional[discord.TextChannel] = None, value: Optional[str] = None):
        """Configure auto-like functionality"""
        
        # Check if user has manage_guild permission  
        if not hasattr(interaction.user, 'guild_permissions') or not interaction.user.guild_permissions.manage_guild:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You need the `Manage Server` permission to configure auto-like settings.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        guild_id = interaction.guild.id
        
        # Initialize auto-like settings if not exists
        if not hasattr(bot, 'autolike_settings'):
            bot.autolike_settings = {}
        
        if guild_id not in bot.autolike_settings:
            bot.autolike_settings[guild_id] = {
                'enabled': False,
                'channels': [],
                'emoji': '👍',
                'mode': 'all_messages'  # Changed default to all_messages as requested
            }
        
        guild_settings = bot.autolike_settings[guild_id]
        
        if action.lower() == "setup":
            embed = discord.Embed(
                title="🔧 Auto-Like Setup",
                description="Auto-like will automatically add reactions to messages in specified channels.",
                color=0x00ff7f
            )
            embed.add_field(
                name="Available Commands",
                value="• `/autolike add #channel` - Add a channel\n• `/autolike remove #channel` - Remove a channel\n• `/autolike toggle` - Enable/disable auto-like\n• `/autolike emoji 🎉` - Change reaction emoji\n• `/autolike mode all` - Like all messages\n• `/autolike mode images` - Like only images\n• `/autolike list` - View current settings",
                inline=False
            )
            embed.add_field(
                name="Current Status",
                value=f"**Enabled:** {'✅ Yes' if guild_settings['enabled'] else '❌ No'}\n**Channels:** {len(guild_settings['channels'])}\n**Emoji:** {guild_settings['emoji']}\n**Mode:** {'All messages' if guild_settings.get('mode', 'all_messages') == 'all_messages' else 'Images only'}",
                inline=False
            )
            await interaction.response.send_message(embed=embed)
            
        elif action.lower() == "add":
            if not channel:
                await interaction.response.send_message("❌ Please specify a channel to add.", ephemeral=True)
                return
            
            if channel.id not in guild_settings['channels']:
                guild_settings['channels'].append(channel.id)
                bot.save_autolike_settings()
                
                embed = discord.Embed(
                    title="✅ Channel Added",
                    description=f"Auto-like enabled for {channel.mention}",
                    color=0x00ff00
                )
                embed.add_field(name="Total Channels", value=str(len(guild_settings['channels'])), inline=True)
                embed.add_field(name="Status", value="✅ Enabled" if guild_settings['enabled'] else "❌ Disabled", inline=True)
            else:
                embed = discord.Embed(
                    title="⚠️ Already Added",
                    description=f"{channel.mention} is already in the auto-like list.",
                    color=0xffa500
                )
            
            await interaction.response.send_message(embed=embed)
            
        elif action.lower() == "remove":
            if not channel:
                await interaction.response.send_message("❌ Please specify a channel to remove.", ephemeral=True)
                return
            
            if channel.id in guild_settings['channels']:
                guild_settings['channels'].remove(channel.id)
                bot.save_autolike_settings()
                
                embed = discord.Embed(
                    title="✅ Channel Removed",
                    description=f"Auto-like disabled for {channel.mention}",
                    color=0x00ff00
                )
                embed.add_field(name="Remaining Channels", value=str(len(guild_settings['channels'])), inline=True)
            else:
                embed = discord.Embed(
                    title="⚠️ Not Found",
                    description=f"{channel.mention} is not in the auto-like list.",
                    color=0xffa500
                )
            
            await interaction.response.send_message(embed=embed)
            
        elif action.lower() == "toggle":
            guild_settings['enabled'] = not guild_settings['enabled']
            bot.save_autolike_settings()
            
            status = "✅ Enabled" if guild_settings['enabled'] else "❌ Disabled"
            embed = discord.Embed(
                title="🔄 Auto-Like Toggled",
                description=f"Auto-like is now **{status}**",
                color=0x00ff00 if guild_settings['enabled'] else 0xff6b6b
            )
            embed.add_field(name="Configured Channels", value=str(len(guild_settings['channels'])), inline=True)
            embed.add_field(name="Reaction Emoji", value=guild_settings['emoji'], inline=True)
            embed.add_field(name="Mode", value="All messages" if guild_settings.get('mode', 'all_messages') == 'all_messages' else "Images only", inline=True)
            
            await interaction.response.send_message(embed=embed)
            
        elif action.lower() == "emoji":
            if not value:
                await interaction.response.send_message("❌ Please specify an emoji to use.", ephemeral=True)
                return
            
            # Validate emoji (basic check)
            if len(value) > 10:  # Custom emojis or invalid input
                await interaction.response.send_message("❌ Please use a standard emoji (not custom Discord emojis).", ephemeral=True)
                return
            
            guild_settings['emoji'] = value
            bot.save_autolike_settings()
            
            embed = discord.Embed(
                title="✅ Emoji Updated",
                description=f"Auto-like will now use {value} for reactions",
                color=0x00ff00
            )
            await interaction.response.send_message(embed=embed)
            
        elif action.lower() == "mode":
            if not value:
                await interaction.response.send_message("❌ Please specify mode: `all` (all messages) or `images` (images only)", ephemeral=True)
                return
            
            mode_value = value.lower()
            if mode_value in ['all', 'messages', 'all_messages']:
                guild_settings['mode'] = 'all_messages'
                bot.save_autolike_settings()
                
                embed = discord.Embed(
                    title="✅ Mode Updated",
                    description="Auto-like will now react to **all messages** in configured channels",
                    color=0x00ff00
                )
            elif mode_value in ['images', 'images_only']:
                guild_settings['mode'] = 'images_only'
                bot.save_autolike_settings()
                
                embed = discord.Embed(
                    title="✅ Mode Updated", 
                    description="Auto-like will now react to **images only** in configured channels",
                    color=0x00ff00
                )
            else:
                await interaction.response.send_message("❌ Invalid mode. Use `all` for all messages or `images` for images only", ephemeral=True)
                return
            
            await interaction.response.send_message(embed=embed)
            
        elif action.lower() == "list":
            embed = discord.Embed(
                title="📋 Auto-Like Configuration",
                color=0x0099ff
            )
            
            embed.add_field(
                name="Status",
                value="✅ Enabled" if guild_settings['enabled'] else "❌ Disabled",
                inline=True
            )
            embed.add_field(
                name="Reaction Emoji",
                value=guild_settings['emoji'],
                inline=True
            )
            embed.add_field(
                name="Mode",
                value="All messages" if guild_settings.get('mode', 'all_messages') == 'all_messages' else "Images only",
                inline=True
            )
            embed.add_field(
                name="Total Channels",
                value=str(len(guild_settings['channels'])),
                inline=False
            )
            
            if guild_settings['channels']:
                channel_list = []
                for channel_id in guild_settings['channels']:
                    channel_obj = interaction.guild.get_channel(channel_id)
                    if channel_obj:
                        channel_list.append(f"• {channel_obj.mention}")
                    else:
                        channel_list.append(f"• Deleted Channel ({channel_id})")
                
                embed.add_field(
                    name="Configured Channels",
                    value="\n".join(channel_list),
                    inline=False
                )
            else:
                embed.add_field(
                    name="Configured Channels",
                    value="None configured",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed)
            
        else:
            embed = discord.Embed(
                title="❌ Invalid Action",
                description="Valid actions: `setup`, `add`, `remove`, `list`, `toggle`, `emoji`, `mode`",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @bot.command(name='autolike', help='Configure auto-like for messages in channels')
    async def autolike_command(ctx, action=None, channel: Optional[discord.TextChannel] = None, *, value=None):
        """Text command version of autolike configuration"""
        
        # Check permissions
        if not ctx.author.guild_permissions.manage_guild:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You need the `Manage Server` permission to configure auto-like settings.",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return
        
        if not action:
            embed = discord.Embed(
                title="🔧 Auto-Like Commands",
                description="Configure automatic reactions for messages in specific channels.",
                color=0x0099ff
            )
            embed.add_field(
                name="Available Commands",
                value="• `!autolike setup` - View setup guide\n• `!autolike add #channel` - Add channel\n• `!autolike remove #channel` - Remove channel\n• `!autolike toggle` - Enable/disable\n• `!autolike emoji 🎉` - Change emoji\n• `!autolike mode all` - Like all messages\n• `!autolike mode images` - Like images only\n• `!autolike list` - View settings",
                inline=False
            )
            await ctx.send(embed=embed)
            return
        
        # Initialize settings
        guild_id = ctx.guild.id
        if not hasattr(bot, 'autolike_settings'):
            bot.autolike_settings = {}
        
        if guild_id not in bot.autolike_settings:
            bot.autolike_settings[guild_id] = {
                'enabled': False,
                'channels': [],
                'emoji': '👍',
                'mode': 'all_messages'  # Default to all messages as requested
            }
        
        guild_settings = bot.autolike_settings[guild_id]
        
        # Handle different actions - reuse slash command logic
        if action.lower() == "setup":
            embed = discord.Embed(
                title="🔧 Auto-Like Setup",
                description="Auto-like will automatically add reactions to messages in specified channels.",
                color=0x00ff7f
            )
            embed.add_field(
                name="Text Commands",
                value="• `!autolike add #channel` - Add a channel\n• `!autolike remove #channel` - Remove a channel\n• `!autolike toggle` - Enable/disable auto-like\n• `!autolike emoji 🎉` - Change reaction emoji\n• `!autolike mode all` - Like all messages\n• `!autolike mode images` - Like images only\n• `!autolike list` - View current settings",
                inline=False
            )
            embed.add_field(
                name="Current Status",
                value=f"**Enabled:** {'✅ Yes' if guild_settings['enabled'] else '❌ No'}\n**Channels:** {len(guild_settings['channels'])}\n**Emoji:** {guild_settings['emoji']}\n**Mode:** {'All messages' if guild_settings.get('mode', 'all_messages') == 'all_messages' else 'Images only'}",
                inline=False
            )
            await ctx.send(embed=embed)
            
        elif action.lower() == "mode":
            if not value:
                await ctx.send("❌ Please specify mode: `all` (all messages) or `images` (images only)")
                return
            
            mode_value = value.lower()
            if mode_value in ['all', 'messages', 'all_messages']:
                guild_settings['mode'] = 'all_messages'
                bot.save_autolike_settings()
                
                embed = discord.Embed(
                    title="✅ Mode Updated",
                    description="Auto-like will now react to **all messages** in configured channels",
                    color=0x00ff00
                )
            elif mode_value in ['images', 'images_only']:
                guild_settings['mode'] = 'images_only'
                bot.save_autolike_settings()
                
                embed = discord.Embed(
                    title="✅ Mode Updated", 
                    description="Auto-like will now react to **images only** in configured channels",
                    color=0x00ff00
                )
            else:
                await ctx.send("❌ Invalid mode. Use `all` for all messages or `images` for images only")
                return
            
            await ctx.send(embed=embed)
        
        # For other actions, create a mock interaction to reuse slash command logic
        else:
            class MockInteraction:
                def __init__(self, ctx):
                    self.guild = ctx.guild
                    self.user = ctx.author
                    self.response = MockResponse(ctx)
            
            class MockResponse:
                def __init__(self, ctx):
                    self.ctx = ctx
                
                async def send_message(self, embed=None, ephemeral=False):
                    await self.ctx.send(embed=embed)
            
            # Create a mock interaction for other actions
            class MockInteraction:
                def __init__(self, ctx):
                    self.guild = ctx.guild
                    self.user = ctx.author
                    self.response = MockResponse(ctx)
            
            class MockResponse:
                def __init__(self, ctx):
                    self.ctx = ctx
                
                async def send_message(self, embed=None, ephemeral=False):
                    await self.ctx.send(embed=embed)
            
            # Reuse slash command logic
            mock_interaction = MockInteraction(ctx)
            await autolike_slash(mock_interaction, action, channel, value)
    
    logger.info("✅ Auto-like commands loaded successfully!")