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
        action="Action to perform (setup, add, remove, list, toggle, emoji, mode)",
        channel="Channel to configure auto-like for",
        emoji="Emoji to use for auto-like reactions OR mode value (all/images)"
    )
    async def autolike_slash(interaction: discord.Interaction, action: str, channel: discord.TextChannel = None, emoji: str = None):
        """Configure auto-like functionality for images"""
        
        # Check if user has manage_guild permission
        if not interaction.user.guild_permissions.manage_guild:
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
                'mode': 'images_only'  # 'images_only' or 'all_messages'
            }
        
        guild_settings = bot.autolike_settings[guild_id]
        
        if action.lower() == "setup":
            embed = discord.Embed(
                title="🔧 Auto-Like Setup",
                description="Auto-like will automatically add reactions to images posted in specified channels.",
                color=0x00ff7f
            )
            embed.add_field(
                name="How to Configure",
                value="• `/autolike add #channel` - Add a channel\n• `/autolike remove #channel` - Remove a channel\n• `/autolike toggle` - Enable/disable auto-like\n• `/autolike emoji 🎉` - Change reaction emoji\n• `/autolike mode all` - Like all messages\n• `/autolike mode images` - Like only images\n• `/autolike list` - View current settings",
                inline=False
            )
            embed.add_field(
                name="Current Status",
                value=f"**Enabled:** {'✅ Yes' if guild_settings['enabled'] else '❌ No'}\n**Channels:** {len(guild_settings['channels'])}\n**Emoji:** {guild_settings['emoji']}",
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
            
            await interaction.response.send_message(embed=embed)
            
        elif action.lower() == "emoji":
            if not emoji:
                await interaction.response.send_message("❌ Please specify an emoji to use.", ephemeral=True)
                return
            
            # Validate emoji (basic check)
            if len(emoji) > 10:  # Custom emojis or invalid input
                await interaction.response.send_message("❌ Please use a standard emoji (not custom Discord emojis).", ephemeral=True)
                return
            
            guild_settings['emoji'] = emoji
            bot.save_autolike_settings()
            
            embed = discord.Embed(
                title="✅ Emoji Updated",
                description=f"Auto-like will now use {emoji} for reactions",
                color=0x00ff00
            )
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
                name="Total Channels",
                value=str(len(guild_settings['channels'])),
                inline=True
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
                description="Valid actions: `setup`, `add`, `remove`, `list`, `toggle`, `emoji`",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @bot.command(name='autolike', help='Configure auto-like for images in channels')
    async def autolike_command(ctx, action=None, channel: discord.TextChannel = None, *, emoji=None):
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
                description="Configure automatic reactions for images in specific channels.",
                color=0x0099ff
            )
            embed.add_field(
                name="Available Commands",
                value="• `!autolike setup` - View setup guide\n• `!autolike add #channel` - Add channel\n• `!autolike remove #channel` - Remove channel\n• `!autolike toggle` - Enable/disable\n• `!autolike emoji 🎉` - Change emoji\n• `!autolike list` - View settings",
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
                'mode': 'images_only'  # 'images_only' or 'all_messages'
            }
        
        guild_settings = bot.autolike_settings[guild_id]
        
        # Handle different actions
        if action.lower() == "setup":
            embed = discord.Embed(
                title="🔧 Auto-Like Setup",
                description="Auto-like will automatically add reactions to images posted in specified channels.",
                color=0x00ff7f
            )
            embed.add_field(
                name="Text Commands",
                value="• `!autolike add #channel` - Add a channel\n• `!autolike remove #channel` - Remove a channel\n• `!autolike toggle` - Enable/disable auto-like\n• `!autolike emoji 🎉` - Change reaction emoji\n• `!autolike list` - View current settings",
                inline=False
            )
            embed.add_field(
                name="Current Status",
                value=f"**Enabled:** {'✅ Yes' if guild_settings['enabled'] else '❌ No'}\n**Channels:** {len(guild_settings['channels'])}\n**Emoji:** {guild_settings['emoji']}",
                inline=False
            )
            await ctx.send(embed=embed)
            
        elif action.lower() == "add":
            if not channel:
                await ctx.send("❌ Please specify a channel to add. Example: `!autolike add #screenshots`")
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
            
            await ctx.send(embed=embed)
            
        elif action.lower() == "remove":
            if not channel:
                await ctx.send("❌ Please specify a channel to remove. Example: `!autolike remove #screenshots`")
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
            
            await ctx.send(embed=embed)
            
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
            
            await ctx.send(embed=embed)
            
        elif action.lower() == "emoji":
            if not emoji:
                await ctx.send("❌ Please specify an emoji to use. Example: `!autolike emoji 🎉`")
                return
            
            # Validate emoji (basic check)
            if len(emoji) > 10:  # Custom emojis or invalid input
                await ctx.send("❌ Please use a standard emoji (not custom Discord emojis).")
                return
            
            guild_settings['emoji'] = emoji
            bot.save_autolike_settings()
            
            embed = discord.Embed(
                title="✅ Emoji Updated",
                description=f"Auto-like will now use {emoji} for reactions",
                color=0x00ff00
            )
            await ctx.send(embed=embed)
            
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
                name="Total Channels",
                value=str(len(guild_settings['channels'])),
                inline=True
            )
            
            if guild_settings['channels']:
                channel_list = []
                for channel_id in guild_settings['channels']:
                    channel_obj = ctx.guild.get_channel(channel_id)
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
            
            await ctx.send(embed=embed)
            
        else:
            embed = discord.Embed(
                title="❌ Invalid Action",
                description="Valid actions: `setup`, `add`, `remove`, `list`, `toggle`, `emoji`",
                color=0xff0000
            )
            await ctx.send(embed=embed)
    
    logger.info("✅ Auto-like commands loaded successfully!")