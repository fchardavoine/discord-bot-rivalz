import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
import logging
import io
import aiohttp
from datetime import datetime, timedelta
from typing import Optional
from PIL import Image, ImageDraw, ImageFont
import os

# Import AI integration
try:
    from ai_integration import (
        initialize_ai_clients, 
        chat_with_gpt, 
        chat_with_gemini, 
        analyze_image_with_gpt, 
        analyze_image_with_gemini,
        get_ai_status
    )
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    logging.warning("AI integration not available")

logger = logging.getLogger(__name__)

def setup_commands(bot):
    """Set up all bot commands"""
    
    # Initialize AI clients if available
    if AI_AVAILABLE:
        initialize_ai_clients()

    
    @bot.command(name='hello', help='Greet the bot')
    async def hello(ctx):
        """Simple hello command"""
        greetings = [
            f"Hello {ctx.author.mention}! 👋",
            f"Hi there {ctx.author.mention}! 😊",
            f"Hey {ctx.author.mention}! How's it going? 🌟",
            f"Greetings {ctx.author.mention}! ✨"
        ]
        await ctx.send(random.choice(greetings))
    
    @bot.command(name='ping', help='Check bot latency')
    async def ping(ctx):
        """Simple ping command that works"""
        latency = round(bot.latency * 1000)
        await ctx.send(f"🏓 Pong! Latency: {latency}ms")
    
    @bot.command(name='info', help='Get bot information')
    async def info(ctx):
        """Display bot information"""
        embed = discord.Embed(
            title="Bot Information",
            color=0x0099ff,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Bot Name", value=bot.user.name, inline=True)
        embed.add_field(name="Bot ID", value=bot.user.id, inline=True)
        embed.add_field(name="Servers", value=len(bot.guilds), inline=True)
        embed.add_field(name="Users", value=len(bot.users), inline=True)
        embed.add_field(name="Python Version", value="3.x", inline=True)
        embed.add_field(name="Discord.py Version", value=discord.__version__, inline=True)
        embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        
        await ctx.send(embed=embed)
    
    @bot.command(name='roll', help='Roll a dice (1-6) or specify max number')
    async def roll(ctx, max_num: int = 6):
        """Roll a dice with specified maximum number"""
        if max_num < 1:
            await ctx.send("❌ Please provide a number greater than 0.")
            return
        
        if max_num > 1000:
            await ctx.send("❌ Maximum number too large! Please use a number less than 1000.")
            return
        
        result = random.randint(1, max_num)
        embed = discord.Embed(
            title="🎲 Dice Roll",
            description=f"You rolled: **{result}** (1-{max_num})",
            color=0x9932cc
        )
        await ctx.send(embed=embed)
    
    @bot.command(name='coinflip', aliases=['flip', 'coin'], help='Flip a coin')
    async def coinflip(ctx):
        """Flip a coin"""
        result = random.choice(['Heads', 'Tails'])
        emoji = "🟡" if result == "Heads" else "⚪"
        
        embed = discord.Embed(
            title="🪙 Coin Flip",
            description=f"{emoji} **{result}**!",
            color=0xffd700
        )
        await ctx.send(embed=embed)
    
    @bot.command(name='8ball', help='Ask the magic 8-ball a question')
    async def eight_ball(ctx, *, question: str = ""):
        """Magic 8-ball command"""
        if not question.strip():
            await ctx.send("❌ Please ask a question! Example: `!8ball Will it rain today?`")
            return
        
        responses = [
            "🟢 It is certain",
            "🟢 It is decidedly so",
            "🟢 Without a doubt",
            "🟢 Yes definitely",
            "🟢 You may rely on it",
            "🟢 As I see it, yes",
            "🟢 Most likely",
            "🟢 Outlook good",
            "🟢 Yes",
            "🟢 Signs point to yes",
            "🟡 Reply hazy, try again",
            "🟡 Ask again later",
            "🟡 Better not tell you now",
            "🟡 Cannot predict now",
            "🟡 Concentrate and ask again",
            "🔴 Don't count on it",
            "🔴 My reply is no",
            "🔴 My sources say no",
            "🔴 Outlook not so good",
            "🔴 Very doubtful"
        ]
        
        response = random.choice(responses)
        
        embed = discord.Embed(
            title="🎱 Magic 8-Ball",
            color=0x8b008b
        )
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Answer", value=response, inline=False)
        embed.set_footer(text=f"Asked by {ctx.author}")
        
        await ctx.send(embed=embed)
    

    
    @bot.command(name='clear', help='Clear messages (Admin only)')
    @commands.has_permissions(manage_messages=True)
    async def clear(ctx, amount: int = 5):
        """Clear messages from the channel"""
        if amount < 1 or amount > 100:
            await ctx.send("❌ Please specify a number between 1 and 100.")
            return
        
        deleted = await ctx.channel.purge(limit=amount + 1)  # +1 to include the command message
        
        embed = discord.Embed(
            title="🧹 Messages Cleared",
            description=f"Deleted {len(deleted) - 1} messages.",
            color=0x00ff00
        )
        
        # Send confirmation and delete it after 3 seconds
        msg = await ctx.send(embed=embed)
        await asyncio.sleep(3)
        await msg.delete()
    
    # ============= SLASH COMMANDS =============
    
    @bot.tree.command(name="hello", description="Get a friendly greeting from the bot")
    async def slash_hello(interaction: discord.Interaction):
        """Slash command version of hello"""
        greetings = [
            f"Hello {interaction.user.mention}! 👋",
            f"Hi there {interaction.user.mention}! 😊",
            f"Hey {interaction.user.mention}! How's it going? 🌟",
            f"Greetings {interaction.user.mention}! ✨"
        ]
        await interaction.response.send_message(random.choice(greetings))
    
    @bot.tree.command(name="ping", description="Check bot latency")
    async def slash_ping(interaction: discord.Interaction):
        """Simple slash ping command that works"""
        latency = round(bot.latency * 1000)
        await interaction.response.send_message(f"🏓 Pong! Latency: {latency}ms")
    
    @bot.tree.command(name="info", description="Get information about the bot")
    async def slash_info(interaction: discord.Interaction):
        """Slash command version of info"""
        embed = discord.Embed(
            title="Bot Information",
            color=0x0099ff,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Bot Name", value=bot.user.name, inline=True)
        embed.add_field(name="Bot ID", value=bot.user.id, inline=True)
        embed.add_field(name="Servers", value=len(bot.guilds), inline=True)
        embed.add_field(name="Users", value=len(bot.users), inline=True)
        embed.add_field(name="Python Version", value="3.x", inline=True)
        embed.add_field(name="Discord.py Version", value=discord.__version__, inline=True)
        embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)
        embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="roll", description="Roll a dice")
    @app_commands.describe(max_num="Maximum number on the dice (default: 6)")
    async def slash_roll(interaction: discord.Interaction, max_num: int = 6):
        """Slash command version of roll"""
        if max_num < 1:
            await interaction.response.send_message("❌ Please provide a number greater than 0.", ephemeral=True)
            return
        
        if max_num > 1000:
            await interaction.response.send_message("❌ Maximum number too large! Please use a number less than 1000.", ephemeral=True)
            return
        
        result = random.randint(1, max_num)
        embed = discord.Embed(
            title="🎲 Dice Roll",
            description=f"You rolled: **{result}** (1-{max_num})",
            color=0x9932cc
        )
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="coinflip", description="Flip a coin")
    async def slash_coinflip(interaction: discord.Interaction):
        """Slash command version of coinflip"""
        result = random.choice(['Heads', 'Tails'])
        emoji = "🟡" if result == "Heads" else "⚪"
        
        embed = discord.Embed(
            title="🪙 Coin Flip",
            description=f"{emoji} **{result}**!",
            color=0xffd700
        )
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="8ball", description="Ask the magic 8-ball a question")
    @app_commands.describe(question="The question you want to ask the 8-ball")
    async def slash_eight_ball(interaction: discord.Interaction, question: str):
        """Slash command version of 8ball"""
        if not question.strip():
            await interaction.response.send_message("❌ Please ask a question!", ephemeral=True)
            return
        
        responses = [
            "🟢 It is certain",
            "🟢 It is decidedly so",
            "🟢 Without a doubt",
            "🟢 Yes definitely",
            "🟢 You may rely on it",
            "🟢 As I see it, yes",
            "🟢 Most likely",
            "🟢 Outlook good",
            "🟢 Yes",
            "🟢 Signs point to yes",
            "🟡 Reply hazy, try again",
            "🟡 Ask again later",
            "🟡 Better not tell you now",
            "🟡 Cannot predict now",
            "🟡 Concentrate and ask again",
            "🔴 Don't count on it",
            "🔴 My reply is no",
            "🔴 My sources say no",
            "🔴 Outlook not so good",
            "🔴 Very doubtful"
        ]
        
        response = random.choice(responses)
        
        embed = discord.Embed(
            title="🎱 Magic 8-Ball",
            color=0x8b008b
        )
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Answer", value=response, inline=False)
        embed.set_footer(text=f"Asked by {interaction.user}")
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="serverinfo", description="Get information about the current server")
    async def slash_serverinfo(interaction: discord.Interaction):
        """Slash command version of serverinfo"""
        if not interaction.guild:
            await interaction.response.send_message("❌ This command can only be used in a server!", ephemeral=True)
            return
            
        guild = interaction.guild
        
        embed = discord.Embed(
            title=f"Server Information: {guild.name}",
            color=0x00ff00,
            timestamp=datetime.utcnow()
        )
        
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.add_field(name="Server ID", value=guild.id, inline=True)
        embed.add_field(name="Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        embed.add_field(name="Created", value=guild.created_at.strftime("%B %d, %Y"), inline=True)
        embed.add_field(name="Members", value=guild.member_count, inline=True)
        embed.add_field(name="Text Channels", value=len(guild.text_channels), inline=True)
        embed.add_field(name="Voice Channels", value=len(guild.voice_channels), inline=True)
        embed.add_field(name="Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="Emojis", value=len(guild.emojis), inline=True)
        embed.add_field(name="Boost Level", value=guild.premium_tier, inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="userinfo", description="Get information about a user")
    @app_commands.describe(member="The user to get information about (leave empty for yourself)")
    async def slash_userinfo(interaction: discord.Interaction, member: Optional[discord.Member] = None):
        """Slash command version of userinfo"""
        if member is None:
            member = interaction.user
        
        embed = discord.Embed(
            title=f"User Information: {member}",
            color=member.color if hasattr(member, 'color') else 0x0099ff,
            timestamp=datetime.utcnow()
        )
        
        embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
        embed.add_field(name="User ID", value=member.id, inline=True)
        embed.add_field(name="Username", value=member.name, inline=True)
        embed.add_field(name="Discriminator", value=f"#{member.discriminator}", inline=True)
        embed.add_field(name="Account Created", value=member.created_at.strftime("%B %d, %Y"), inline=True)
        
        if isinstance(member, discord.Member):
            embed.add_field(name="Joined Server", value=member.joined_at.strftime("%B %d, %Y") if member.joined_at else "Unknown", inline=True)
            embed.add_field(name="Roles", value=len(member.roles) - 1, inline=True)  # -1 to exclude @everyone
            embed.add_field(name="Top Role", value=member.top_role.mention, inline=True)
            embed.add_field(name="Status", value=str(member.status).title(), inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="clear", description="Clear messages from the channel (Admin only)")
    @app_commands.describe(amount="Number of messages to delete (1-100, default: 5)")
    async def slash_clear(interaction: discord.Interaction, amount: int = 5):
        """Slash command version of clear"""
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ You need the 'Manage Messages' permission to use this command.", ephemeral=True)
            return
        
        if amount < 1 or amount > 100:
            await interaction.response.send_message("❌ Please specify a number between 1 and 100.", ephemeral=True)
            return
        
        # Defer the response since purging might take time
        await interaction.response.defer(ephemeral=True)
        
        deleted = await interaction.channel.purge(limit=amount)
        
        embed = discord.Embed(
            title="🧹 Messages Cleared",
            description=f"Deleted {len(deleted)} messages.",
            color=0x00ff00
        )
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    # ============= ADVANCED COMMANDS =============
    
    def parse_color(color_input: str) -> int:
        """Parse color from string input"""
        color_map = {
            'red': 0xff0000, 'green': 0x00ff00, 'blue': 0x0000ff,
            'yellow': 0xffff00, 'purple': 0x800080, 'orange': 0xffa500,
            'pink': 0xffc0cb, 'cyan': 0x00ffff, 'magenta': 0xff00ff,
            'lime': 0x32cd32, 'gold': 0xffd700, 'silver': 0xc0c0c0,
            'black': 0x000000, 'white': 0xffffff, 'gray': 0x808080,
            'discord': 0x5865f2, 'blurple': 0x5865f2
        }
        
        color_lower = color_input.lower().strip()
        
        # Check if it's a named color
        if color_lower in color_map:
            return color_map[color_lower]
        
        # Check if it's a hex color
        if color_lower.startswith('#'):
            color_lower = color_lower[1:]
        
        try:
            return int(color_lower, 16)
        except ValueError:
            return 0x3498db  # Default blue if parsing fails
    
    # Unified messaging system with clean subcommands - each type shows only relevant parameters
    message_group = app_commands.Group(name="message", description="Send different types of messages")
    
    @message_group.command(name="text", description="💬 Send a regular text message")
    @app_commands.describe(
        content="Your message content",
        channel="Target channel (optional - defaults to current)"
    )
    async def message_text(
        interaction: discord.Interaction,
        content: str,
        channel: Optional[discord.TextChannel] = None
    ):
        """Send a regular text message"""
        await handle_message_command(interaction, "text", content=content, channel=channel)
    
    @message_group.command(name="announcement", description="📢 Send an announcement with embed styling")
    @app_commands.describe(
        content="Announcement content",
        channel="Target channel (optional - defaults to current)",
        title="Announcement title (optional)",
        color="Embed color (hex or name like 'blue', 'red')"
    )
    async def message_announcement(
        interaction: discord.Interaction,
        content: str,
        channel: Optional[discord.TextChannel] = None,
        title: Optional[str] = None,
        color: Optional[str] = None
    ):
        """Send an announcement with embed styling"""
        await handle_message_command(interaction, "announcement", content=content, channel=channel, title=title, color=color)
    
    @message_group.command(name="embed", description="✨ Send a custom embed with title and styling")
    @app_commands.describe(
        title="Embed title",
        content="Embed content/description", 
        channel="Target channel (optional - defaults to current)",
        color="Embed color (hex or name like 'blue', 'red')"
    )
    async def message_embed(
        interaction: discord.Interaction,
        title: str,
        content: str,
        channel: Optional[discord.TextChannel] = None,
        color: Optional[str] = None
    ):
        """Send a custom embed"""
        await handle_message_command(interaction, "embed", content=content, channel=channel, title=title, color=color)
    
    @message_group.command(name="file", description="📎 Send a file with an optional message")
    @app_commands.describe(
        attachment="File to send",
        content="Optional message to accompany the file",
        channel="Target channel (optional - defaults to current)"
    )
    async def message_file(
        interaction: discord.Interaction,
        attachment: discord.Attachment,
        content: Optional[str] = None,
        channel: Optional[discord.TextChannel] = None
    ):
        """Send a file with optional message"""
        await handle_message_command(interaction, "file", content=content, channel=channel, attachment=attachment)
    
    @message_group.command(name="file-only", description="🔗 Send just a file without any message")
    @app_commands.describe(
        attachment="File to send",
        channel="Target channel (optional - defaults to current)"
    )
    async def message_file_only(
        interaction: discord.Interaction,
        attachment: discord.Attachment,
        channel: Optional[discord.TextChannel] = None
    ):
        """Send just a file without message"""
        await handle_message_command(interaction, "file_only", channel=channel, attachment=attachment)
    
    # Register the command group
    bot.tree.add_command(message_group)
    
    async def handle_message_command(
        interaction: discord.Interaction,
        message_type: str,
        content: Optional[str] = None,
        channel: Optional[discord.TextChannel] = None,
        title: Optional[str] = None,
        color: Optional[str] = None,
        attachment: Optional[discord.Attachment] = None
    ):
        """Send any type of message with comprehensive Discord features"""
        
        print(f"[DEBUG] /message command started by {interaction.user}")
        
        try:
            # Handle interaction - defer if not already acknowledged, otherwise use followup
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
                print(f"[DEBUG] Deferred interaction")
            else:
                print(f"[DEBUG] Interaction already acknowledged - using followup")
            
            # Helper function to send messages safely
            async def safe_send(message, ephemeral=True):
                if interaction.response.is_done():
                    await interaction.followup.send(message, ephemeral=ephemeral)
                else:
                    await interaction.response.send_message(message, ephemeral=ephemeral)
            
            # Permission check - only require manage_messages for advanced features
            requires_manage_messages = message_type in ["announcement", "embed"]
            if requires_manage_messages and not interaction.user.guild_permissions.manage_messages:
                await safe_send("❌ You need the 'Manage Messages' permission for announcement and custom embed messages.")
                return
            
            # Determine target channel
            target_channel = channel or interaction.channel
            
            # Permission check for target channel
            if not target_channel.permissions_for(interaction.guild.me).send_messages:
                await safe_send(f"❌ I don't have permission to send messages in {target_channel.mention}.")
                return
            
            # Validate inputs
            if message_type == "text" and not content:
                await safe_send("❌ Content is required for text messages!")
                return
                
            if message_type == "announcement" and not content:
                await safe_send("❌ Content is required for announcements!")
                return
                
            if message_type == "embed" and (not title or not content):
                await safe_send("❌ Both title and content are required for custom embeds!")
                return
                
            if message_type in ["file", "file_only"] and not attachment:
                await safe_send("❌ You must attach a file for file messages!")
                return
            
            # Initialize success message
            success_msg = "✅ Message sent!"
            
            # Process the message based on type
            if message_type == "text":
                await target_channel.send(content)
                success_msg = f"✅ Message sent to {target_channel.mention}" if channel else "✅ Message sent!"
                
            elif message_type == "announcement":
                if not title:
                    title = "Announcement"
                    
                embed_color = 0xffaa00  # Default orange
                if color:
                    embed_color = parse_color(color)
                    
                embed = discord.Embed(
                    title=f"📢 {title}",
                    description=content,
                    color=embed_color,
                    timestamp=datetime.utcnow()
                )
                embed.set_footer(text=f"Announcement by {interaction.user}", 
                               icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
                
                await target_channel.send(embed=embed)
                success_msg = f"✅ Announcement sent to {target_channel.mention}" if channel else "✅ Announcement sent!"
                
            elif message_type == "embed":
                embed_color = 0x3498db  # Default blue
                if color:
                    embed_color = parse_color(color)
                    
                embed = discord.Embed(
                    title=title,
                    description=content,
                    color=embed_color,
                    timestamp=datetime.utcnow()
                )
                embed.set_footer(text=f"Created by {interaction.user}")
                
                await target_channel.send(embed=embed)
                success_msg = f"✅ Custom embed sent to {target_channel.mention}" if channel else "✅ Custom embed sent!"
                
            elif message_type in ["file", "file_only"]:
                file_data = await attachment.read()
                discord_file = discord.File(
                    fp=io.BytesIO(file_data),
                    filename=attachment.filename
                )
                
                message_content = content if message_type == "file" and content else None
                await target_channel.send(content=message_content, file=discord_file)
                
                success_msg = f"✅ File `{attachment.filename}` sent to {target_channel.mention}" if channel else f"✅ File `{attachment.filename}` sent!"
            
            print(f"[DEBUG] About to send response: {success_msg}")
            # Send success message using the safe method
            await safe_send(success_msg)
            print(f"[DEBUG] Success response sent")
                
        except Exception as e:
            print(f"[DEBUG] Command exception: {str(e)}")
            # Send error message using safe method
            try:
                async def safe_send_error(message, ephemeral=True):
                    if interaction.response.is_done():
                        await interaction.followup.send(message, ephemeral=ephemeral)
                    else:
                        await interaction.response.send_message(message, ephemeral=ephemeral)
                await safe_send_error(f"❌ Error: {str(e)}")
            except Exception as error_send_failed:
                print(f"[DEBUG] Could not send error response: {error_send_failed}")
    
    # Removed announce command - now part of unified /message system
    
    # Removed sendfile command - now part of unified /message system
    
    @bot.tree.command(name="quickpoll", description="Create a simple yes/no poll")
    @app_commands.describe(question="The yes/no question to ask")
    async def slash_quickpoll(interaction: discord.Interaction, question: str):
        """Create a simple yes/no poll"""
        embed = discord.Embed(
            title="📊 Quick Poll",
            description=f"**{question}**",
            color=0x3498db,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="How to vote:", value="✅ Yes\n❌ No", inline=False)
        embed.set_footer(text=f"Poll created by {interaction.user}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        
        await interaction.response.send_message(embed=embed)
        
        # Get the message to add reactions
        message = await interaction.original_response()
        await message.add_reaction("✅")
        await message.add_reaction("❌")
    
    # Traditional text command versions for the new features
    # Removed old text poll command - replaced with unified slash poll system
    @bot.command(name='quickpoll', help='Create a simple yes/no poll')
    async def quickpoll(ctx, *, question):
        """Create a simple yes/no poll"""
        embed = discord.Embed(
            title="📊 Quick Poll",
            description=f"**{question}**",
            color=0x3498db,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="How to vote:", value="✅ Yes\n❌ No", inline=False)
        embed.set_footer(text=f"Poll created by {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        
        message = await ctx.send(embed=embed)
        await message.add_reaction("✅")
        await message.add_reaction("❌")
    
    # Removed old send command - now part of unified /message system
    
    # Removed old announce command - now part of unified /message system
    
    # Removed old sendfile command - now part of unified /message system
    
    @bot.command(name='image', help='Send an image with optional message')
    async def send_image(ctx, *, message=""):
        """Send an image with optional message"""
        if not ctx.message.attachments:
            await ctx.send("❌ Please attach an image to send!")
            return
        
        try:
            attachment = ctx.message.attachments[0]
            
            # Check if it's an image
            if not attachment.content_type or not attachment.content_type.startswith('image/'):
                await ctx.send("❌ Please attach an image file (jpg, png, gif, etc.)")
                return
            
            file_data = await attachment.read()
            discord_file = discord.File(
                fp=io.BytesIO(file_data),
                filename=attachment.filename
            )
            
            embed = discord.Embed(
                title="📸 Image Share",
                description=message if message else f"Image shared by {ctx.author.mention}",
                color=0x3498db,
                timestamp=datetime.utcnow()
            )
            embed.set_image(url=f"attachment://{attachment.filename}")
            embed.set_footer(text=f"Shared by {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
            
            await ctx.send(embed=embed, file=discord_file)
            
        except Exception as e:
            await ctx.send(f"❌ Failed to process image: {str(e)}")
    
    # ============= MODERATION COMMANDS =============
    
    @bot.command(name='kick', help='Kick a member from the server (Admin only)')
    @commands.has_permissions(kick_members=True)
    async def kick_member(ctx, member: discord.Member, *, reason="No reason provided"):
        """Kick a member from the server"""
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("❌ You cannot kick someone with equal or higher permissions!")
            return
        
        try:
            await member.kick(reason=reason)
            embed = discord.Embed(
                title="👢 Member Kicked",
                description=f"**{member}** has been kicked from the server.",
                color=0xff6b6b,
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            embed.set_footer(text=f"User ID: {member.id}")
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Failed to kick member: {str(e)}")
    
    @bot.command(name='ban', help='Ban a member from the server (Admin only)')
    @commands.has_permissions(ban_members=True)
    async def ban_member(ctx, member: discord.Member, *, reason="No reason provided"):
        """Ban a member from the server"""
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("❌ You cannot ban someone with equal or higher permissions!")
            return
        
        try:
            await member.ban(reason=reason)
            embed = discord.Embed(
                title="🔨 Member Banned",
                description=f"**{member}** has been banned from the server.",
                color=0xff0000,
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            embed.set_footer(text=f"User ID: {member.id}")
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Failed to ban member: {str(e)}")
    
    @bot.command(name='unban', help='Unban a user from the server (Admin only)')
    @commands.has_permissions(ban_members=True)
    async def unban_user(ctx, user_id: int, *, reason="No reason provided"):
        """Unban a user from the server"""
        try:
            user = await bot.fetch_user(user_id)
            await ctx.guild.unban(user, reason=reason)
            embed = discord.Embed(
                title="✅ User Unbanned",
                description=f"**{user}** has been unbanned from the server.",
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            embed.set_footer(text=f"User ID: {user.id}")
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Failed to unban user: {str(e)}")
    
    @bot.command(name='mute', help='Mute a member (timeout) (Admin only)')
    @commands.has_permissions(moderate_members=True)
    async def mute_member(ctx, member: discord.Member, duration: int = 10, *, reason="No reason provided"):
        """Mute a member using timeout"""
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("❌ You cannot mute someone with equal or higher permissions!")
            return
        
        try:
            timeout_duration = discord.utils.utcnow() + timedelta(minutes=duration)
            await member.timeout(timeout_duration, reason=reason)
            
            embed = discord.Embed(
                title="🔇 Member Muted",
                description=f"**{member}** has been muted for {duration} minutes.",
                color=0xffa500,
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Duration", value=f"{duration} minutes", inline=True)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            embed.set_footer(text=f"User ID: {member.id}")
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Failed to mute member: {str(e)}")
    
    @bot.command(name='unmute', help='Unmute a member (Admin only)')
    @commands.has_permissions(moderate_members=True)
    async def unmute_member(ctx, member: discord.Member, *, reason="No reason provided"):
        """Unmute a member"""
        try:
            await member.timeout(None, reason=reason)
            embed = discord.Embed(
                title="🔊 Member Unmuted",
                description=f"**{member}** has been unmuted.",
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            embed.set_footer(text=f"User ID: {member.id}")
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Failed to unmute member: {str(e)}")
    
    # ============= SERVER MANAGEMENT COMMANDS =============
    
    @bot.command(name='server', help='Get detailed server information')
    async def server_info(ctx):
        """Display detailed server information"""
        guild = ctx.guild
        embed = discord.Embed(
            title=f"📊 {guild.name} Server Information",
            color=0x7289da,
            timestamp=datetime.utcnow()
        )
        
        # Basic info
        embed.add_field(name="Server ID", value=guild.id, inline=True)
        embed.add_field(name="Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        embed.add_field(name="Created", value=guild.created_at.strftime("%B %d, %Y"), inline=True)
        
        # Member stats
        embed.add_field(name="Total Members", value=guild.member_count, inline=True)
        embed.add_field(name="Humans", value=len([m for m in guild.members if not m.bot]), inline=True)
        embed.add_field(name="Bots", value=len([m for m in guild.members if m.bot]), inline=True)
        
        # Channel stats
        embed.add_field(name="Text Channels", value=len(guild.text_channels), inline=True)
        embed.add_field(name="Voice Channels", value=len(guild.voice_channels), inline=True)
        embed.add_field(name="Categories", value=len(guild.categories), inline=True)
        
        # Other info
        embed.add_field(name="Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="Emojis", value=len(guild.emojis), inline=True)
        embed.add_field(name="Boost Level", value=guild.premium_tier, inline=True)
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)
    
    @bot.command(name='user', help='Get detailed user information')
    async def user_info(ctx, member: discord.Member = None):
        """Display detailed user information"""
        if member is None:
            member = ctx.author
        
        embed = discord.Embed(
            title=f"👤 {member} User Information",
            color=member.color if member.color != discord.Color.default() else 0x7289da,
            timestamp=datetime.utcnow()
        )
        
        # Basic info
        embed.add_field(name="User ID", value=member.id, inline=True)
        embed.add_field(name="Nickname", value=member.nick or "None", inline=True)
        embed.add_field(name="Bot", value="Yes" if member.bot else "No", inline=True)
        
        # Dates
        embed.add_field(name="Account Created", value=member.created_at.strftime("%B %d, %Y"), inline=True)
        embed.add_field(name="Joined Server", value=member.joined_at.strftime("%B %d, %Y") if member.joined_at else "Unknown", inline=True)
        embed.add_field(name="Status", value=str(member.status).title(), inline=True)
        
        # Roles
        roles = [role.mention for role in member.roles[1:]]  # Exclude @everyone
        if roles:
            embed.add_field(name=f"Roles ({len(roles)})", value=" ".join(roles) if len(" ".join(roles)) < 1024 else f"{len(roles)} roles", inline=False)
        
        # Permissions
        if member.guild_permissions.administrator:
            embed.add_field(name="Key Permissions", value="Administrator", inline=True)
        else:
            perms = []
            if member.guild_permissions.manage_guild: perms.append("Manage Server")
            if member.guild_permissions.manage_channels: perms.append("Manage Channels")
            if member.guild_permissions.manage_messages: perms.append("Manage Messages")
            if member.guild_permissions.kick_members: perms.append("Kick Members")
            if member.guild_permissions.ban_members: perms.append("Ban Members")
            if perms:
                embed.add_field(name="Key Permissions", value=", ".join(perms), inline=True)
        
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)
    
    # ============= ENTERTAINMENT COMMANDS =============
    
    @bot.command(name='joke', help='Get a random joke')
    async def random_joke(ctx):
        """Send a random joke"""
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "Why did the scarecrow win an award? He was outstanding in his field!",
            "Why don't eggs tell jokes? They'd crack each other up!",
            "What do you call a fake noodle? An impasta!",
            "Why did the math book look so sad? Because it had too many problems!",
            "What do you call a bear with no teeth? A gummy bear!",
            "Why can't a bicycle stand up by itself? It's two tired!",
            "What do you call a fish wearing a bowtie? Sofishticated!",
            "Why did the coffee file a police report? It got mugged!",
            "What's the best thing about Switzerland? I don't know, but the flag is a big plus!"
        ]
        
        embed = discord.Embed(
            title="😂 Random Joke",
            description=random.choice(jokes),
            color=0xffff00,
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)
    
    @bot.command(name='quote', help='Get an inspirational quote')
    async def inspirational_quote(ctx):
        """Send an inspirational quote"""
        quotes = [
            "The only way to do great work is to love what you do. - Steve Jobs",
            "Innovation distinguishes between a leader and a follower. - Steve Jobs",
            "Life is what happens to you while you're busy making other plans. - John Lennon",
            "The future belongs to those who believe in the beauty of their dreams. - Eleanor Roosevelt",
            "It is during our darkest moments that we must focus to see the light. - Aristotle",
            "The way to get started is to quit talking and begin doing. - Walt Disney",
            "Don't let yesterday take up too much of today. - Will Rogers",
            "You learn more from failure than from success. Don't let it stop you. - Unknown",
            "If you are working on something that you really care about, you don't have to be pushed. - Steve Jobs",
            "Success is not final, failure is not fatal: it is the courage to continue that counts. - Winston Churchill"
        ]
        
        embed = discord.Embed(
            title="✨ Inspirational Quote",
            description=random.choice(quotes),
            color=0x9932cc,
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)
    
    @bot.command(name='weather', help='Get weather information (placeholder)')
    async def weather_info(ctx, *, location="your area"):
        """Weather command placeholder"""
        embed = discord.Embed(
            title="🌤️ Weather Information",
            description=f"Weather data for {location} would appear here.\n\nTo enable real weather data, you would need to:\n1. Get an API key from a weather service\n2. Add it to your bot's configuration\n3. Update the weather command",
            color=0x87ceeb,
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text="Weather feature requires API key setup")
        await ctx.send(embed=embed)
    
    @bot.command(name='reminder', help='Set a reminder (basic version)')
    async def set_reminder(ctx, time_minutes: int, *, message):
        """Set a basic reminder"""
        if time_minutes > 1440:  # 24 hours
            await ctx.send("❌ Maximum reminder time is 24 hours (1440 minutes)!")
            return
        
        if time_minutes < 1:
            await ctx.send("❌ Minimum reminder time is 1 minute!")
            return
        
        embed = discord.Embed(
            title="⏰ Reminder Set",
            description=f"I'll remind you about: **{message}**",
            color=0x00ff00,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Time", value=f"{time_minutes} minutes", inline=True)
        embed.add_field(name="Channel", value=ctx.channel.mention, inline=True)
        await ctx.send(embed=embed)
        
        # Simple reminder using asyncio.sleep
        await asyncio.sleep(time_minutes * 60)
        
        reminder_embed = discord.Embed(
            title="⏰ Reminder!",
            description=f"Hey {ctx.author.mention}! You asked me to remind you about:\n\n**{message}**",
            color=0xff6b6b,
            timestamp=datetime.utcnow()
        )
        reminder_embed.set_footer(text=f"Set {time_minutes} minutes ago")
        await ctx.send(embed=reminder_embed)
    
    # ============= REMOVED OLD ADVANCED POLL SYSTEM =============
    # Use /poll instead - provides EasyPoll.bot-style layout with letters (A, B, C)
    # and professional button-based voting instead of reactions

    # ============= COMPREHENSIVE MODERATION SYSTEM =============
    
    @bot.tree.command(name="kick", description="Kick a member from the server")
    @app_commands.describe(member="Member to kick", reason="Reason for kicking")
    async def kick_member(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        """Kick a member from the server"""
        if not interaction.user.guild_permissions.kick_members:
            await interaction.response.send_message("❌ You need the 'Kick Members' permission to use this command.", ephemeral=True)
            return
        
        if member.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            await interaction.response.send_message("❌ You cannot kick someone with equal or higher role.", ephemeral=True)
            return
        
        if not interaction.guild.me.guild_permissions.kick_members:
            await interaction.response.send_message("❌ I don't have permission to kick members.", ephemeral=True)
            return
        
        try:
            await member.send(f"You have been kicked from {interaction.guild.name}. Reason: {reason}")
        except:
            pass  # Member has DMs disabled
        
        await member.kick(reason=f"{reason} | Kicked by {interaction.user}")
        
        embed = discord.Embed(
            title="👢 Member Kicked",
            description=f"{member.mention} has been kicked from the server.",
            color=0xff6b6b,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
        embed.set_footer(text=f"User ID: {member.id}")
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="ban", description="Ban a member from the server")
    @app_commands.describe(member="Member to ban", reason="Reason for banning", delete_days="Days of messages to delete (0-7)")
    async def ban_member(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided", delete_days: int = 0):
        """Ban a member from the server"""
        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message("❌ You need the 'Ban Members' permission to use this command.", ephemeral=True)
            return
        
        if member.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            await interaction.response.send_message("❌ You cannot ban someone with equal or higher role.", ephemeral=True)
            return
        
        if not interaction.guild.me.guild_permissions.ban_members:
            await interaction.response.send_message("❌ I don't have permission to ban members.", ephemeral=True)
            return
        
        if delete_days < 0 or delete_days > 7:
            await interaction.response.send_message("❌ Delete days must be between 0 and 7.", ephemeral=True)
            return
        
        try:
            await member.send(f"You have been banned from {interaction.guild.name}. Reason: {reason}")
        except:
            pass  # Member has DMs disabled
        
        await member.ban(reason=f"{reason} | Banned by {interaction.user}", delete_message_days=delete_days)
        
        embed = discord.Embed(
            title="🔨 Member Banned",
            description=f"{member.mention} has been banned from the server.",
            color=0xff0000,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
        embed.add_field(name="Messages Deleted", value=f"{delete_days} days", inline=True)
        embed.set_footer(text=f"User ID: {member.id}")
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="unban", description="Unban a user from the server")
    @app_commands.describe(user_id="User ID to unban", reason="Reason for unbanning")
    async def unban_user(interaction: discord.Interaction, user_id: str, reason: str = "No reason provided"):
        """Unban a user from the server"""
        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message("❌ You need the 'Ban Members' permission to use this command.", ephemeral=True)
            return
        
        try:
            user = await bot.fetch_user(int(user_id))
            await interaction.guild.unban(user, reason=f"{reason} | Unbanned by {interaction.user}")
            
            embed = discord.Embed(
                title="✅ User Unbanned",
                description=f"{user.mention} has been unbanned from the server.",
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            embed.set_footer(text=f"User ID: {user.id}")
            
            await interaction.response.send_message(embed=embed)
            
        except ValueError:
            await interaction.response.send_message("❌ Invalid user ID.", ephemeral=True)
        except discord.NotFound:
            await interaction.response.send_message("❌ User not found or not banned.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error unbanning user: {str(e)}", ephemeral=True)
    
    @bot.tree.command(name="timeout", description="Timeout a member")
    @app_commands.describe(member="Member to timeout", duration="Duration in minutes", reason="Reason for timeout")
    async def timeout_member(interaction: discord.Interaction, member: discord.Member, duration: int, reason: str = "No reason provided"):
        """Timeout a member"""
        if not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message("❌ You need the 'Moderate Members' permission to use this command.", ephemeral=True)
            return
        
        if member.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            await interaction.response.send_message("❌ You cannot timeout someone with equal or higher role.", ephemeral=True)
            return
        
        if duration < 1 or duration > 40320:  # 28 days max
            await interaction.response.send_message("❌ Duration must be between 1 minute and 28 days (40320 minutes).", ephemeral=True)
            return
        
        timeout_until = datetime.utcnow() + timedelta(minutes=duration)
        
        try:
            await member.timeout(timeout_until, reason=f"{reason} | Timed out by {interaction.user}")
            
            embed = discord.Embed(
                title="⏰ Member Timed Out",
                description=f"{member.mention} has been timed out.",
                color=0xffa500,
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Duration", value=f"{duration} minutes", inline=True)
            embed.add_field(name="Until", value=f"<t:{int(timeout_until.timestamp())}:f>", inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            embed.set_footer(text=f"User ID: {member.id}")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error timing out member: {str(e)}", ephemeral=True)
    
    @bot.tree.command(name="untimeout", description="Remove timeout from a member")
    @app_commands.describe(member="Member to remove timeout from", reason="Reason for removing timeout")
    async def untimeout_member(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        """Remove timeout from a member"""
        if not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message("❌ You need the 'Moderate Members' permission to use this command.", ephemeral=True)
            return
        
        if not member.timed_out:
            await interaction.response.send_message("❌ This member is not timed out.", ephemeral=True)
            return
        
        try:
            await member.timeout(None, reason=f"{reason} | Timeout removed by {interaction.user}")
            
            embed = discord.Embed(
                title="✅ Timeout Removed",
                description=f"Timeout has been removed from {member.mention}.",
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            embed.set_footer(text=f"User ID: {member.id}")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error removing timeout: {str(e)}", ephemeral=True)
    
    @bot.tree.command(name="warn", description="Warn a member")
    @app_commands.describe(member="Member to warn", reason="Reason for warning")
    async def warn_member(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        """Warn a member (logged only)"""
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ You need the 'Manage Messages' permission to use this command.", ephemeral=True)
            return
        
        try:
            await member.send(f"You have been warned in {interaction.guild.name}. Reason: {reason}")
            dm_sent = "✅"
        except:
            dm_sent = "❌ (DMs disabled)"
        
        embed = discord.Embed(
            title="⚠️ Member Warned",
            description=f"{member.mention} has been warned.",
            color=0xffff00,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
        embed.add_field(name="DM Sent", value=dm_sent, inline=True)
        embed.set_footer(text=f"User ID: {member.id}")
        
        await interaction.response.send_message(embed=embed)
    
    # ============= ROLE MANAGEMENT =============
    
    @bot.tree.command(name="addrole", description="Add a role to a member")
    @app_commands.describe(member="Member to give role to", role="Role to add")
    async def add_role(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        """Add a role to a member"""
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("❌ You need the 'Manage Roles' permission to use this command.", ephemeral=True)
            return
        
        if role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            await interaction.response.send_message("❌ You cannot assign a role equal to or higher than your highest role.", ephemeral=True)
            return
        
        if role >= interaction.guild.me.top_role:
            await interaction.response.send_message("❌ I cannot assign a role equal to or higher than my highest role.", ephemeral=True)
            return
        
        if role in member.roles:
            await interaction.response.send_message(f"❌ {member.mention} already has the {role.mention} role.", ephemeral=True)
            return
        
        try:
            await member.add_roles(role, reason=f"Role added by {interaction.user}")
            
            embed = discord.Embed(
                title="✅ Role Added",
                description=f"Added {role.mention} to {member.mention}.",
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text=f"Action by {interaction.user}")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error adding role: {str(e)}", ephemeral=True)
    
    @bot.tree.command(name="removerole", description="Remove a role from a member")
    @app_commands.describe(member="Member to remove role from", role="Role to remove")
    async def remove_role(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        """Remove a role from a member"""
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("❌ You need the 'Manage Roles' permission to use this command.", ephemeral=True)
            return
        
        if role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            await interaction.response.send_message("❌ You cannot manage a role equal to or higher than your highest role.", ephemeral=True)
            return
        
        if role not in member.roles:
            await interaction.response.send_message(f"❌ {member.mention} doesn't have the {role.mention} role.", ephemeral=True)
            return
        
        try:
            await member.remove_roles(role, reason=f"Role removed by {interaction.user}")
            
            embed = discord.Embed(
                title="✅ Role Removed",
                description=f"Removed {role.mention} from {member.mention}.",
                color=0xff6b6b,
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text=f"Action by {interaction.user}")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error removing role: {str(e)}", ephemeral=True)
    
    # ============= CHANNEL MANAGEMENT =============
    
    @bot.tree.command(name="lock", description="Lock a channel")
    @app_commands.describe(channel="Channel to lock (optional)", reason="Reason for locking")
    async def lock_channel(interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None, reason: str = "No reason provided"):
        """Lock a channel"""
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ You need the 'Manage Channels' permission to use this command.", ephemeral=True)
            return
        
        target_channel = channel or interaction.channel
        
        try:
            await target_channel.set_permissions(interaction.guild.default_role, send_messages=False, reason=f"Channel locked by {interaction.user}: {reason}")
            
            embed = discord.Embed(
                title="🔒 Channel Locked",
                description=f"{target_channel.mention} has been locked.",
                color=0xff0000,
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error locking channel: {str(e)}", ephemeral=True)
    
    @bot.tree.command(name="unlock", description="Unlock a channel")
    @app_commands.describe(channel="Channel to unlock (optional)", reason="Reason for unlocking")
    async def unlock_channel(interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None, reason: str = "No reason provided"):
        """Unlock a channel"""
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ You need the 'Manage Channels' permission to use this command.", ephemeral=True)
            return
        
        target_channel = channel or interaction.channel
        
        try:
            await target_channel.set_permissions(interaction.guild.default_role, send_messages=None, reason=f"Channel unlocked by {interaction.user}: {reason}")
            
            embed = discord.Embed(
                title="🔓 Channel Unlocked",
                description=f"{target_channel.mention} has been unlocked.",
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error unlocking channel: {str(e)}", ephemeral=True)
    
    @bot.tree.command(name="slowmode", description="Set channel slowmode")
    @app_commands.describe(seconds="Slowmode delay in seconds (0 to disable)", channel="Channel to modify (optional)")
    async def set_slowmode(interaction: discord.Interaction, seconds: int, channel: Optional[discord.TextChannel] = None):
        """Set channel slowmode"""
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ You need the 'Manage Channels' permission to use this command.", ephemeral=True)
            return
        
        if seconds < 0 or seconds > 21600:  # 6 hours max
            await interaction.response.send_message("❌ Slowmode must be between 0 and 21600 seconds (6 hours).", ephemeral=True)
            return
        
        target_channel = channel or interaction.channel
        
        try:
            await target_channel.edit(slowmode_delay=seconds, reason=f"Slowmode set by {interaction.user}")
            
            if seconds == 0:
                description = f"Slowmode has been disabled in {target_channel.mention}."
                color = 0x00ff00
            else:
                description = f"Slowmode set to {seconds} seconds in {target_channel.mention}."
                color = 0xffa500
            
            embed = discord.Embed(
                title="⏱️ Slowmode Updated",
                description=description,
                color=color,
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error setting slowmode: {str(e)}", ephemeral=True)

    # ============= UTILITY COMMANDS =============
    
    @bot.command(name='avatar', help='Get a user\'s avatar')
    async def get_avatar(ctx, member: discord.Member = None):
        """Get a user's avatar"""
        if member is None:
            member = ctx.author
        
        embed = discord.Embed(
            title=f"🖼️ {member.display_name}'s Avatar",
            color=member.color if member.color != discord.Color.default() else 0x7289da,
            timestamp=datetime.utcnow()
        )
        
        if member.avatar:
            embed.set_image(url=member.avatar.url)
            embed.add_field(name="Avatar URL", value=f"[Click here]({member.avatar.url})", inline=False)
        else:
            embed.description = f"{member.display_name} doesn't have a custom avatar."
        
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)
    
    @bot.command(name='roleinfo', help='Get information about a role')
    async def role_info(ctx, *, role_name):
        """Get information about a role"""
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            await ctx.send(f"❌ Role '{role_name}' not found!")
            return
        
        embed = discord.Embed(
            title=f"🎭 Role Information: {role.name}",
            color=role.color if role.color != discord.Color.default() else 0x7289da,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Role ID", value=role.id, inline=True)
        embed.add_field(name="Created", value=role.created_at.strftime("%B %d, %Y"), inline=True)
        embed.add_field(name="Position", value=role.position, inline=True)
        embed.add_field(name="Members", value=len(role.members), inline=True)
        embed.add_field(name="Mentionable", value="Yes" if role.mentionable else "No", inline=True)
        embed.add_field(name="Hoisted", value="Yes" if role.hoist else "No", inline=True)
        
        # Key permissions
        perms = []
        if role.permissions.administrator: perms.append("Administrator")
        if role.permissions.manage_guild: perms.append("Manage Server")
        if role.permissions.manage_channels: perms.append("Manage Channels")
        if role.permissions.manage_messages: perms.append("Manage Messages")
        if role.permissions.kick_members: perms.append("Kick Members")
        if role.permissions.ban_members: perms.append("Ban Members")
        
        if perms:
            embed.add_field(name="Key Permissions", value=", ".join(perms), inline=False)
        
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)
    
    @bot.command(name='channelinfo', help='Get information about a channel')
    async def channel_info(ctx, channel: discord.TextChannel = None):
        """Get information about a channel"""
        if channel is None:
            channel = ctx.channel
        
        embed = discord.Embed(
            title=f"📺 Channel Information: #{channel.name}",
            color=0x7289da,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Channel ID", value=channel.id, inline=True)
        embed.add_field(name="Created", value=channel.created_at.strftime("%B %d, %Y"), inline=True)
        embed.add_field(name="Category", value=channel.category.name if channel.category else "None", inline=True)
        embed.add_field(name="Position", value=channel.position, inline=True)
        embed.add_field(name="NSFW", value="Yes" if channel.nsfw else "No", inline=True)
        embed.add_field(name="Slowmode", value=f"{channel.slowmode_delay}s" if channel.slowmode_delay else "Disabled", inline=True)
        
        if channel.topic:
            embed.add_field(name="Topic", value=channel.topic, inline=False)
        
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)
    
    # ============= ENTERTAINMENT & FUN COMMANDS =============
    
    # Trivia command removed to avoid duplicate registration with entertainment_commands.py
    
    @bot.tree.command(name="meme", description="Get a random programming meme")
    async def programming_meme(interaction: discord.Interaction):
        """Get a random programming meme text"""
        memes = [
            "It works on my machine! 🤷‍♂️",
            "99 little bugs in the code, 99 little bugs. Take one down, patch it around... 117 little bugs in the code.",
            "There are only 10 types of people: those who understand binary and those who don't.",
            "Programming is like writing a book... except if you miss a single comma on page 153, the whole thing makes no sense.",
            "Why do programmers prefer dark mode? Because light attracts bugs! 🐛",
            "A SQL query walks into a bar, walks up to two tables and asks: 'Can I join you?'",
            "How many programmers does it take to change a light bulb? None. That's a hardware problem.",
            "Debugging: Being the detective in a crime movie where you are also the murderer.",
            "Code never lies, comments sometimes do.",
            "The best thing about a boolean is even if you are wrong, you are only off by a bit."
        ]
        
        embed = discord.Embed(
            title="😂 Programming Meme",
            description=random.choice(memes),
            color=0xff69b4,
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text=f"Requested by {interaction.user}")
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="dadjoke", description="Get a random dad joke")
    async def dad_joke(interaction: discord.Interaction):
        """Get a random dad joke"""
        jokes = [
            "I'm afraid for the calendar. Its days are numbered.",
            "Why don't scientists trust atoms? Because they make up everything!",
            "Did you hear about the mathematician who's afraid of negative numbers? He'll stop at nothing to avoid them!",
            "What do you call a fake noodle? An impasta!",
            "I only know 25 letters of the alphabet. I don't know y.",
            "What did the ocean say to the beach? Nothing, it just waved.",
            "Why do fathers take an extra pair of socks when they go golfing? In case they get a hole in one!",
            "What's the best thing about Switzerland? I don't know, but the flag is a big plus.",
            "Did you hear about the claustrophobic astronaut? He just needed some space!",
            "Why don't eggs tell jokes? They'd crack each other up!"
        ]
        
        embed = discord.Embed(
            title="👨 Dad Joke",
            description=random.choice(jokes),
            color=0xffd700,
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text=f"Requested by {interaction.user}")
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="fortune", description="Get your fortune")
    async def fortune_teller(interaction: discord.Interaction):
        """Get a random fortune"""
        fortunes = [
            "🌟 Great success awaits you in the near future!",
            "💼 A new opportunity will present itself this week.",
            "❤️ Love is in the air for you today.",
            "🎯 Your hard work will soon pay off.",
            "🌈 After the storm comes the rainbow.",
            "🔮 Trust your instincts, they will guide you well.",
            "🎊 Celebration and joy are coming your way.",
            "📚 Knowledge gained today will serve you tomorrow.",
            "🌸 New friendships will blossom soon.",
            "⭐ You are destined for greatness!"
        ]
        
        embed = discord.Embed(
            title="🔮 Your Fortune",
            description=random.choice(fortunes),
            color=0x800080,
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text=f"Fortune for {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="rps", description="Play Rock Paper Scissors against the bot")
    @app_commands.describe(choice="Your choice: rock, paper, or scissors")
    async def rock_paper_scissors(interaction: discord.Interaction, choice: str):
        """Play Rock Paper Scissors"""
        choice = choice.lower()
        if choice not in ['rock', 'paper', 'scissors']:
            await interaction.response.send_message("❌ Please choose rock, paper, or scissors!", ephemeral=True)
            return
        
        bot_choice = random.choice(['rock', 'paper', 'scissors'])
        
        # Determine winner
        if choice == bot_choice:
            result = "It's a tie!"
            color = 0xffff00
            emoji = "🤝"
        elif (choice == 'rock' and bot_choice == 'scissors') or \
             (choice == 'paper' and bot_choice == 'rock') or \
             (choice == 'scissors' and bot_choice == 'paper'):
            result = "You win!"
            color = 0x00ff00
            emoji = "🎉"
        else:
            result = "I win!"
            color = 0xff0000
            emoji = "🤖"
        
        # Emoji mapping
        emojis = {'rock': '🪨', 'paper': '📄', 'scissors': '✂️'}
        
        embed = discord.Embed(
            title=f"{emoji} Rock Paper Scissors",
            color=color,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Your Choice", value=f"{emojis[choice]} {choice.title()}", inline=True)
        embed.add_field(name="My Choice", value=f"{emojis[bot_choice]} {bot_choice.title()}", inline=True)
        embed.add_field(name="Result", value=f"**{result}**", inline=False)
        embed.set_footer(text=f"Played by {interaction.user}")
        
        await interaction.response.send_message(embed=embed)
    
    # ============= SERVER UTILITY COMMANDS =============
    
    @bot.tree.command(name="membercount", description="Get server member count")
    async def member_count(interaction: discord.Interaction):
        """Get detailed member count information"""
        guild = interaction.guild
        
        total_members = guild.member_count
        humans = len([m for m in guild.members if not m.bot])
        bots = len([m for m in guild.members if m.bot])
        online = len([m for m in guild.members if m.status != discord.Status.offline])
        
        embed = discord.Embed(
            title=f"👥 {guild.name} Member Statistics",
            color=0x0099ff,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Total Members", value=f"{total_members:,}", inline=True)
        embed.add_field(name="Humans", value=f"{humans:,}", inline=True)
        embed.add_field(name="Bots", value=f"{bots:,}", inline=True)
        embed.add_field(name="Online Now", value=f"{online:,}", inline=True)
        embed.add_field(name="Roles", value=f"{len(guild.roles):,}", inline=True)
        embed.add_field(name="Channels", value=f"{len(guild.channels):,}", inline=True)
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        embed.set_footer(text=f"Server created on {guild.created_at.strftime('%B %d, %Y')}")
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="roles", description="List all server roles")
    async def list_roles(interaction: discord.Interaction):
        """List all roles in the server"""
        roles = sorted(interaction.guild.roles, key=lambda r: r.position, reverse=True)
        
        # Skip @everyone role and limit to 20 roles
        roles = [r for r in roles if r.name != "@everyone"][:20]
        
        embed = discord.Embed(
            title=f"🎭 Roles in {interaction.guild.name}",
            color=0x9932cc,
            timestamp=datetime.utcnow()
        )
        
        role_list = ""
        for role in roles:
            member_count = len(role.members)
            role_list += f"{role.mention} - {member_count} members\n"
        
        if role_list:
            embed.description = role_list
        else:
            embed.description = "No roles found."
        
        if len(interaction.guild.roles) > 21:  # 20 + @everyone
            embed.set_footer(text=f"Showing top 20 roles out of {len(interaction.guild.roles)-1} total")
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="emojis", description="List server emojis")
    async def list_emojis(interaction: discord.Interaction):
        """List all custom emojis in the server"""
        emojis = interaction.guild.emojis
        
        if not emojis:
            embed = discord.Embed(
                title="😔 No Custom Emojis",
                description="This server doesn't have any custom emojis.",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed)
            return
        
        # Limit to first 20 emojis
        emoji_list = emojis[:20]
        
        embed = discord.Embed(
            title=f"😀 Custom Emojis in {interaction.guild.name}",
            color=0xffd700,
            timestamp=datetime.utcnow()
        )
        
        emoji_text = ""
        for emoji in emoji_list:
            animated = "🎬" if emoji.animated else "🖼️"
            emoji_text += f"{emoji} `:{emoji.name}:` {animated}\n"
        
        embed.description = emoji_text
        
        if len(emojis) > 20:
            embed.set_footer(text=f"Showing 20 out of {len(emojis)} emojis")
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="whois", description="Get detailed information about a user")
    @app_commands.describe(member="Member to get information about")
    async def whois(interaction: discord.Interaction, member: Optional[discord.Member] = None):
        """Get detailed user information"""
        if member is None:
            member = interaction.user
        
        embed = discord.Embed(
            title=f"👤 User Information: {member.display_name}",
            color=member.color if member.color != discord.Color.default() else 0x0099ff,
            timestamp=datetime.utcnow()
        )
        
        # Basic info
        embed.add_field(name="Username", value=f"{member.name}#{member.discriminator}", inline=True)
        embed.add_field(name="User ID", value=member.id, inline=True)
        embed.add_field(name="Nickname", value=member.display_name if member.display_name != member.name else "None", inline=True)
        
        # Status and activity
        embed.add_field(name="Status", value=str(member.status).title(), inline=True)
        if member.activity:
            activity_type = "Playing" if member.activity.type == discord.ActivityType.playing else "Activity"
            embed.add_field(name=activity_type, value=member.activity.name, inline=True)
        
        # Dates
        embed.add_field(name="Account Created", value=f"<t:{int(member.created_at.timestamp())}:F>", inline=False)
        embed.add_field(name="Joined Server", value=f"<t:{int(member.joined_at.timestamp())}:F>", inline=False)
        
        # Roles (top 5)
        if len(member.roles) > 1:  # More than @everyone
            roles = [role.mention for role in member.roles[1:6]]  # Skip @everyone, show top 5
            roles_text = ", ".join(roles)
            if len(member.roles) > 6:
                roles_text += f" (+{len(member.roles)-6} more)"
            embed.add_field(name="Roles", value=roles_text, inline=False)
        
        # Permissions
        key_perms = []
        if member.guild_permissions.administrator: key_perms.append("Administrator")
        elif member.guild_permissions.manage_guild: key_perms.append("Manage Server")
        elif member.guild_permissions.manage_channels: key_perms.append("Manage Channels")
        elif member.guild_permissions.manage_messages: key_perms.append("Manage Messages")
        elif member.guild_permissions.kick_members: key_perms.append("Kick Members")
        elif member.guild_permissions.ban_members: key_perms.append("Ban Members")
        
        if key_perms:
            embed.add_field(name="Key Permissions", value=", ".join(key_perms), inline=False)
        
        # Avatar
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        
        embed.set_footer(text=f"Requested by {interaction.user}")
        
        await interaction.response.send_message(embed=embed)
    
    # ============= ADVANCED UTILITY COMMANDS =============
    
    @bot.tree.command(name="avatar", description="Get a user's avatar")
    @app_commands.describe(member="Member to get avatar of")
    async def get_avatar_slash(interaction: discord.Interaction, member: Optional[discord.Member] = None):
        """Get a user's avatar"""
        if member is None:
            member = interaction.user
        
        embed = discord.Embed(
            title=f"🖼️ {member.display_name}'s Avatar",
            color=member.color if member.color != discord.Color.default() else 0x7289da,
            timestamp=datetime.utcnow()
        )
        
        if member.avatar:
            embed.set_image(url=member.avatar.url)
            embed.add_field(name="Avatar URL", value=f"[Download Avatar]({member.avatar.url})", inline=False)
        else:
            embed.set_image(url=member.default_avatar.url)
            embed.description = f"{member.display_name} is using the default Discord avatar."
        
        embed.set_footer(text=f"Requested by {interaction.user}")
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="banner", description="Get a user's banner")
    @app_commands.describe(member="Member to get banner of")
    async def get_banner(interaction: discord.Interaction, member: Optional[discord.Member] = None):
        """Get a user's banner"""
        if member is None:
            member = interaction.user
        
        # Fetch user to get banner
        user = await bot.fetch_user(member.id)
        
        embed = discord.Embed(
            title=f"🎨 {member.display_name}'s Banner",
            color=member.color if member.color != discord.Color.default() else 0x7289da,
            timestamp=datetime.utcnow()
        )
        
        if user.banner:
            embed.set_image(url=user.banner.url)
            embed.add_field(name="Banner URL", value=f"[Download Banner]({user.banner.url})", inline=False)
        else:
            embed.description = f"{member.display_name} doesn't have a custom banner."
        
        embed.set_footer(text=f"Requested by {interaction.user}")
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="server", description="Get server information")
    async def server_info_slash(interaction: discord.Interaction):
        """Get detailed server information"""
        guild = interaction.guild
        
        embed = discord.Embed(
            title=f"🏰 Server Information: {guild.name}",
            color=0x0099ff,
            timestamp=datetime.utcnow()
        )
        
        # Basic info
        embed.add_field(name="Server ID", value=guild.id, inline=True)
        embed.add_field(name="Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        embed.add_field(name="Created", value=f"<t:{int(guild.created_at.timestamp())}:F>", inline=True)
        
        # Counts
        embed.add_field(name="Members", value=f"{guild.member_count:,}", inline=True)
        embed.add_field(name="Roles", value=f"{len(guild.roles):,}", inline=True)
        embed.add_field(name="Channels", value=f"{len(guild.channels):,}", inline=True)
        
        # Features
        features = []
        if guild.premium_tier > 0:
            features.append(f"Boost Level {guild.premium_tier}")
        if guild.premium_subscription_count:
            features.append(f"{guild.premium_subscription_count} Boosts")
        if guild.verification_level != discord.VerificationLevel.none:
            features.append(f"Verification: {guild.verification_level.name.title()}")
        
        if features:
            embed.add_field(name="Features", value=" • ".join(features), inline=False)
        
        if guild.description:
            embed.add_field(name="Description", value=guild.description, inline=False)
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        if guild.banner:
            embed.set_image(url=guild.banner.url)
        
        embed.set_footer(text=f"Requested by {interaction.user}")
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="invite", description="Create an invite link")
    @app_commands.describe(
        channel="Channel to create invite for",
        max_age="Invite duration in hours (0 = never expires)",
        max_uses="Maximum uses (0 = unlimited)"
    )
    async def create_invite(interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None, 
                           max_age: int = 0, max_uses: int = 0):
        """Create an invite link"""
        if not interaction.user.guild_permissions.create_instant_invite:
            await interaction.response.send_message("❌ You need the 'Create Instant Invite' permission to use this command.", ephemeral=True)
            return
        
        target_channel = channel or interaction.channel
        
        if not target_channel.permissions_for(interaction.guild.me).create_instant_invite:
            await interaction.response.send_message("❌ I don't have permission to create invites in that channel.", ephemeral=True)
            return
        
        try:
            # Convert hours to seconds (0 = never expires)
            max_age_seconds = max_age * 3600 if max_age > 0 else 0
            
            invite = await target_channel.create_invite(
                max_age=max_age_seconds,
                max_uses=max_uses,
                reason=f"Invite created by {interaction.user}"
            )
            
            embed = discord.Embed(
                title="🔗 Invite Created",
                description=f"**Invite URL:** {invite.url}",
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Channel", value=target_channel.mention, inline=True)
            embed.add_field(name="Expires", value=f"{max_age} hours" if max_age > 0 else "Never", inline=True)
            embed.add_field(name="Max Uses", value=max_uses if max_uses > 0 else "Unlimited", inline=True)
            embed.set_footer(text=f"Created by {interaction.user}")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error creating invite: {str(e)}", ephemeral=True)
    
    @bot.tree.command(name="nickname", description="Change a user's nickname")
    @app_commands.describe(member="Member to change nickname", nickname="New nickname (leave empty to reset)")
    async def change_nickname(interaction: discord.Interaction, member: discord.Member, nickname: str = None):
        """Change a user's nickname"""
        if not interaction.user.guild_permissions.manage_nicknames:
            await interaction.response.send_message("❌ You need the 'Manage Nicknames' permission to use this command.", ephemeral=True)
            return
        
        if member.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner and member != interaction.user:
            await interaction.response.send_message("❌ You cannot change the nickname of someone with equal or higher role.", ephemeral=True)
            return
        
        old_nickname = member.display_name
        
        try:
            await member.edit(nick=nickname, reason=f"Nickname changed by {interaction.user}")
            
            if nickname:
                description = f"Changed {member.mention}'s nickname to **{nickname}**"
            else:
                description = f"Reset {member.mention}'s nickname"
            
            embed = discord.Embed(
                title="✏️ Nickname Changed",
                description=description,
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Old Nickname", value=old_nickname, inline=True)
            embed.add_field(name="New Nickname", value=nickname or member.name, inline=True)
            embed.set_footer(text=f"Changed by {interaction.user}")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error changing nickname: {str(e)}", ephemeral=True)
    
    # Removed say command - now part of unified /message system
    
    # Removed embed command - now part of unified /message system
    
    @bot.tree.command(name="uptime", description="Check bot uptime")
    async def bot_uptime(interaction: discord.Interaction):
        """Check how long the bot has been running"""
        uptime_seconds = (datetime.utcnow() - bot.start_time).total_seconds()
        
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        seconds = int(uptime_seconds % 60)
        
        uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
        
        embed = discord.Embed(
            title="⏰ Bot Uptime",
            description=f"I've been online for: **{uptime_str}**",
            color=0x00ff00,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Started", value=f"<t:{int(bot.start_time.timestamp())}:F>", inline=False)
        embed.set_footer(text=f"Requested by {interaction.user}")
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="botinfo", description="Get information about the bot")
    async def bot_info_command(interaction: discord.Interaction):
        """Get detailed bot information"""
        embed = discord.Embed(
            title="🤖 Bot Information",
            color=0x0099ff,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Bot Name", value=bot.user.name, inline=True)
        embed.add_field(name="Bot ID", value=bot.user.id, inline=True)
        embed.add_field(name="Servers", value=len(bot.guilds), inline=True)
        embed.add_field(name="Users", value=len(bot.users), inline=True)
        embed.add_field(name="Commands", value=len([cmd for cmd in bot.tree.get_commands()]), inline=True)
        embed.add_field(name="Discord.py Version", value=discord.__version__, inline=True)
        
        # Bot permissions in current server
        perms = interaction.channel.permissions_for(interaction.guild.me)
        key_perms = []
        if perms.administrator: key_perms.append("Administrator")
        elif perms.manage_guild: key_perms.append("Manage Server")
        elif perms.manage_channels: key_perms.append("Manage Channels")
        elif perms.manage_messages: key_perms.append("Manage Messages")
        elif perms.kick_members: key_perms.append("Kick Members")
        elif perms.ban_members: key_perms.append("Ban Members")
        
        if key_perms:
            embed.add_field(name="Key Permissions", value=", ".join(key_perms[:3]), inline=False)
        
        embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)
        embed.set_footer(text=f"Requested by {interaction.user}")
        
        await interaction.response.send_message(embed=embed)
    
    # ============= MESSAGE EDITING COMMANDS =============
    
    @bot.command(name='editmsg', help='Edit a message sent by the bot')
    async def edit_message(ctx, message_id: int, *, new_content):
        """Edit a message sent by the bot"""
        try:
            # Try to fetch the message from the current channel
            message = await ctx.channel.fetch_message(message_id)
            
            # Check if the message was sent by the bot
            if message.author != bot.user:
                embed = discord.Embed(
                    title="❌ Error",
                    description="I can only edit messages that I sent!",
                    color=0xff0000
                )
                await ctx.send(embed=embed)
                return
            
            # Edit the message
            await message.edit(content=new_content)
            
            embed = discord.Embed(
                title="✅ Message Edited",
                description=f"Successfully edited [message]({message.jump_url})",
                color=0x00ff00
            )
            await ctx.send(embed=embed, delete_after=5)
            
        except discord.NotFound:
            embed = discord.Embed(
                title="❌ Message Not Found",
                description="Could not find a message with that ID in this channel.",
                color=0xff0000
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Permission Error",
                description="I don't have permission to edit that message.",
                color=0xff0000
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred: {str(e)}",
                color=0xff0000
            )
            await ctx.send(embed=embed)

    @bot.command(name='editembed', help='Edit an embed message sent by the bot')
    async def edit_embed(ctx, message_id: int, title: str = None, *, description: str = None):
        """Edit an embed message sent by the bot"""
        try:
            # Try to fetch the message from the current channel
            message = await ctx.channel.fetch_message(message_id)
            
            # Check if the message was sent by the bot
            if message.author != bot.user:
                embed = discord.Embed(
                    title="❌ Error",
                    description="I can only edit messages that I sent!",
                    color=0xff0000
                )
                await ctx.send(embed=embed)
                return
            
            # Check if the message has embeds
            if not message.embeds:
                embed = discord.Embed(
                    title="❌ Error",
                    description="That message doesn't have an embed to edit!",
                    color=0xff0000
                )
                await ctx.send(embed=embed)
                return
            
            # Get the existing embed and update it
            existing_embed = message.embeds[0]
            new_embed = discord.Embed(
                title=title or existing_embed.title,
                description=description or existing_embed.description,
                color=existing_embed.color
            )
            
            # Preserve existing fields
            for field in existing_embed.fields:
                new_embed.add_field(name=field.name, value=field.value, inline=field.inline)
            
            # Preserve other embed properties
            if existing_embed.thumbnail:
                new_embed.set_thumbnail(url=existing_embed.thumbnail.url)
            if existing_embed.image:
                new_embed.set_image(url=existing_embed.image.url)
            if existing_embed.footer:
                new_embed.set_footer(text=existing_embed.footer.text, icon_url=existing_embed.footer.icon_url)
            
            # Edit the message
            await message.edit(embed=new_embed)
            
            embed = discord.Embed(
                title="✅ Embed Edited",
                description=f"Successfully edited [embed message]({message.jump_url})",
                color=0x00ff00
            )
            await ctx.send(embed=embed, delete_after=5)
            
        except discord.NotFound:
            embed = discord.Embed(
                title="❌ Message Not Found",
                description="Could not find a message with that ID in this channel.",
                color=0xff0000
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Permission Error",
                description="I don't have permission to edit that message.",
                color=0xff0000
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred: {str(e)}",
                color=0xff0000
            )
            await ctx.send(embed=embed)

    @bot.command(name='delmsg', help='Delete a message sent by the bot')
    async def delete_message(ctx, message_id: int):
        """Delete a message sent by the bot"""
        try:
            # Try to fetch the message from the current channel
            message = await ctx.channel.fetch_message(message_id)
            
            # Check if the message was sent by the bot
            if message.author != bot.user:
                embed = discord.Embed(
                    title="❌ Error",
                    description="I can only delete messages that I sent!",
                    color=0xff0000
                )
                await ctx.send(embed=embed)
                return
            
            # Delete the message
            await message.delete()
            
            embed = discord.Embed(
                title="✅ Message Deleted",
                description="Successfully deleted the message.",
                color=0x00ff00
            )
            await ctx.send(embed=embed, delete_after=3)
            
        except discord.NotFound:
            embed = discord.Embed(
                title="❌ Message Not Found",
                description="Could not find a message with that ID in this channel.",
                color=0xff0000
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Permission Error",
                description="I don't have permission to delete that message.",
                color=0xff0000
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred: {str(e)}",
                color=0xff0000
            )
            await ctx.send(embed=embed)

    @bot.command(name='demo', help='Demonstrate self-editing capabilities')
    async def demo_edit(ctx):
        """Demonstrate the bot's ability to edit its own messages"""
        # Send initial message
        embed = discord.Embed(
            title="🤖 Self-Edit Demo",
            description="This message will be edited in 3 seconds...",
            color=0x3498db
        )
        message = await ctx.send(embed=embed)
        
        # Wait 3 seconds
        await asyncio.sleep(3)
        
        # Edit the message
        new_embed = discord.Embed(
            title="✅ Message Edited!",
            description="The bot successfully edited its own message!\n\nThis demonstrates that the bot can modify any message it sends.",
            color=0x00ff00
        )
        new_embed.add_field(
            name="Message ID", 
            value=f"`{message.id}`", 
            inline=False
        )
        new_embed.add_field(
            name="How to use this", 
            value=f"You can now use `!editmsg {message.id} Your new content` to edit this message manually!", 
            inline=False
        )
        
        await message.edit(embed=new_embed)

    @bot.command(name='everyone', help='Send a message with @everyone (Admin only)')
    @commands.has_permissions(administrator=True)
    async def everyone_message(ctx, *, message):
        """Send a message with @everyone mention"""
        try:
            # Check if bot has permission to mention everyone
            if not ctx.guild.me.guild_permissions.mention_everyone:
                embed = discord.Embed(
                    title="❌ Permission Error",
                    description="I don't have permission to mention @everyone in this server.",
                    color=0xff0000
                )
                await ctx.send(embed=embed)
                return
            
            # Send the message with @everyone
            await ctx.send(f"@everyone {message}")
            
            # Confirmation
            embed = discord.Embed(
                title="✅ Announcement Sent",
                description="Successfully sent message with @everyone mention.",
                color=0x00ff00
            )
            await ctx.send(embed=embed, delete_after=5)
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Permission Error",
                description="I don't have permission to mention @everyone.",
                color=0xff0000
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to send message: {str(e)}",
                color=0xff0000
            )
            await ctx.send(embed=embed)

    @bot.command(name='here', help='Send a message with @here (Admin only)')
    @commands.has_permissions(administrator=True)
    async def here_message(ctx, *, message):
        """Send a message with @here mention"""
        try:
            # Check if bot has permission to mention everyone
            if not ctx.guild.me.guild_permissions.mention_everyone:
                embed = discord.Embed(
                    title="❌ Permission Error",
                    description="I don't have permission to use @here in this server.",
                    color=0xff0000
                )
                await ctx.send(embed=embed)
                return
            
            # Send the message with @here
            await ctx.send(f"@here {message}")
            
            # Confirmation
            embed = discord.Embed(
                title="✅ Announcement Sent",
                description="Successfully sent message with @here mention.",
                color=0x00ff00
            )
            await ctx.send(embed=embed, delete_after=5)
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Permission Error",
                description="I don't have permission to use @here.",
                color=0xff0000
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to send message: {str(e)}",
                color=0xff0000
            )
            await ctx.send(embed=embed)

    @bot.command(name='sendfile_everyone', help='Send a file with @everyone mention (Admin only)')
    @commands.has_permissions(administrator=True)
    async def sendfile_everyone(ctx, *, message=""):
        """Send a file with @everyone mention"""
        try:
            # Check if there's an attachment
            if not ctx.message.attachments:
                embed = discord.Embed(
                    title="❌ No File Attached",
                    description="Please attach a file to send with the @everyone mention.\n\nUsage: `!sendfile_everyone Your message here` (with file attached)",
                    color=0xff0000
                )
                await ctx.send(embed=embed)
                return
            
            # Check if bot has permission to mention everyone
            if not ctx.guild.me.guild_permissions.mention_everyone:
                embed = discord.Embed(
                    title="❌ Permission Error",
                    description="I don't have permission to mention @everyone in this server.",
                    color=0xff0000
                )
                await ctx.send(embed=embed)
                return
            
            # Get the first attachment
            attachment = ctx.message.attachments[0]
            
            # Download the file
            file_data = await attachment.read()
            discord_file = discord.File(
                fp=io.BytesIO(file_data),
                filename=attachment.filename
            )
            
            # Prepare the message content
            content = f"@everyone"
            if message.strip():
                content += f" {message}"
            
            # Send the file with @everyone mention
            await ctx.send(content=content, file=discord_file)
            
            # Confirmation
            embed = discord.Embed(
                title="✅ File Sent with @everyone",
                description=f"Successfully sent `{attachment.filename}` with @everyone mention.",
                color=0x00ff00
            )
            await ctx.send(embed=embed, delete_after=5)
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Permission Error",
                description="I don't have permission to mention @everyone or send files.",
                color=0xff0000
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to send file: {str(e)}",
                color=0xff0000
            )
            await ctx.send(embed=embed)

    @bot.command(name='sendfile_here', help='Send a file with @here mention (Admin only)')
    @commands.has_permissions(administrator=True)
    async def sendfile_here(ctx, *, message=""):
        """Send a file with @here mention"""
        try:
            # Check if there's an attachment
            if not ctx.message.attachments:
                embed = discord.Embed(
                    title="❌ No File Attached",
                    description="Please attach a file to send with the @here mention.\n\nUsage: `!sendfile_here Your message here` (with file attached)",
                    color=0xff0000
                )
                await ctx.send(embed=embed)
                return
            
            # Check if bot has permission to mention everyone
            if not ctx.guild.me.guild_permissions.mention_everyone:
                embed = discord.Embed(
                    title="❌ Permission Error",
                    description="I don't have permission to use @here in this server.",
                    color=0xff0000
                )
                await ctx.send(embed=embed)
                return
            
            # Get the first attachment
            attachment = ctx.message.attachments[0]
            
            # Download the file
            file_data = await attachment.read()
            discord_file = discord.File(
                fp=io.BytesIO(file_data),
                filename=attachment.filename
            )
            
            # Prepare the message content
            content = f"@here"
            if message.strip():
                content += f" {message}"
            
            # Send the file with @here mention
            await ctx.send(content=content, file=discord_file)
            
            # Confirmation
            embed = discord.Embed(
                title="✅ File Sent with @here",
                description=f"Successfully sent `{attachment.filename}` with @here mention.",
                color=0x00ff00
            )
            await ctx.send(embed=embed, delete_after=5)
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Permission Error",
                description="I don't have permission to use @here or send files.",
                color=0xff0000
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to send file: {str(e)}",
                color=0xff0000
            )
            await ctx.send(embed=embed)
    
    # ============= ADVANCED DISCORD FEATURES =============
    
    @bot.tree.command(name="nuke", description="Delete and recreate a channel (Admin only)")
    @app_commands.describe(channel="Channel to nuke", reason="Reason for nuking")
    async def nuke_channel(interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None, reason: str = "Channel nuked"):
        """Delete and recreate a channel"""
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ You need the 'Manage Channels' permission to use this command.", ephemeral=True)
            return
        
        target_channel = channel or interaction.channel
        
        if not interaction.guild.me.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ I don't have permission to manage channels.", ephemeral=True)
            return
        
        # Store channel properties
        position = target_channel.position
        category = target_channel.category
        overwrites = target_channel.overwrites
        topic = target_channel.topic
        slowmode = target_channel.slowmode_delay
        nsfw = target_channel.nsfw
        
        try:
            # Create new channel with same properties
            new_channel = await target_channel.clone(reason=f"Channel nuked by {interaction.user}: {reason}")
            await new_channel.edit(position=position)
            
            # Delete old channel
            await target_channel.delete(reason=f"Channel nuked by {interaction.user}: {reason}")
            
            embed = discord.Embed(
                title="💥 Channel Nuked",
                description=f"Channel has been successfully nuked and recreated!",
                color=0xff6b6b,
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            embed.set_footer(text="All messages in this channel have been deleted")
            
            await new_channel.send(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error nuking channel: {str(e)}", ephemeral=True)
    
    @bot.tree.command(name="massban", description="Ban multiple users by ID (Admin only)")
    @app_commands.describe(user_ids="User IDs separated by commas", reason="Reason for mass ban")
    async def mass_ban(interaction: discord.Interaction, user_ids: str, reason: str = "Mass ban"):
        """Ban multiple users by their IDs"""
        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message("❌ You need the 'Ban Members' permission to use this command.", ephemeral=True)
            return
        
        # Parse user IDs
        ids = [id.strip() for id in user_ids.split(',')]
        if len(ids) > 10:
            await interaction.response.send_message("❌ Maximum 10 users can be banned at once.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        banned_count = 0
        failed_bans = []
        
        for user_id in ids:
            try:
                user = await bot.fetch_user(int(user_id.strip()))
                await interaction.guild.ban(user, reason=f"Mass ban by {interaction.user}: {reason}")
                banned_count += 1
            except ValueError:
                failed_bans.append(f"{user_id} (Invalid ID)")
            except discord.NotFound:
                failed_bans.append(f"{user_id} (User not found)")
            except Exception as e:
                failed_bans.append(f"{user_id} (Error: {str(e)})")
        
        embed = discord.Embed(
            title="🔨 Mass Ban Results",
            color=0xff0000,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Successfully Banned", value=f"{banned_count} users", inline=True)
        embed.add_field(name="Failed Bans", value=f"{len(failed_bans)} users", inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        
        if failed_bans:
            failed_text = "\n".join(failed_bans[:5])  # Show first 5 failures
            if len(failed_bans) > 5:
                failed_text += f"\n... and {len(failed_bans)-5} more"
            embed.add_field(name="Failed IDs", value=failed_text, inline=False)
        
        embed.set_footer(text=f"Mass ban executed by {interaction.user}")
        
        await interaction.followup.send(embed=embed)
    
    @bot.tree.command(name="purge", description="Advanced message deletion with filters")
    @app_commands.describe(
        amount="Number of messages to check (max 100)",
        user="Only delete messages from this user",
        contains="Only delete messages containing this text",
        embeds="Delete messages with embeds (true/false)",
        bots="Delete messages from bots (true/false)"
    )
    async def advanced_purge(interaction: discord.Interaction, amount: int, user: Optional[discord.Member] = None, 
                           contains: Optional[str] = None, embeds: Optional[bool] = None, bots: Optional[bool] = None):
        """Advanced message purging with filters"""
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ You need the 'Manage Messages' permission to use this command.", ephemeral=True)
            return
        
        if amount < 1 or amount > 100:
            await interaction.response.send_message("❌ Amount must be between 1 and 100.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        def check(message):
            # Skip the interaction message itself
            if message.id == interaction.id:
                return False
            
            # User filter
            if user and message.author != user:
                return False
            
            # Content filter
            if contains and contains.lower() not in message.content.lower():
                return False
            
            # Embeds filter
            if embeds is not None:
                if embeds and not message.embeds:
                    return False
                elif not embeds and message.embeds:
                    return False
            
            # Bots filter
            if bots is not None:
                if bots and not message.author.bot:
                    return False
                elif not bots and message.author.bot:
                    return False
            
            return True
        
        try:
            deleted = await interaction.channel.purge(limit=amount, check=check)
            
            embed = discord.Embed(
                title="🧹 Advanced Purge Complete",
                description=f"Deleted {len(deleted)} messages.",
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            
            filters_applied = []
            if user: filters_applied.append(f"User: {user.mention}")
            if contains: filters_applied.append(f"Contains: '{contains}'")
            if embeds is not None: filters_applied.append(f"Embeds: {embeds}")
            if bots is not None: filters_applied.append(f"Bots: {bots}")
            
            if filters_applied:
                embed.add_field(name="Filters Applied", value="\n".join(filters_applied), inline=False)
            
            embed.set_footer(text=f"Purge executed by {interaction.user}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error during purge: {str(e)}")
    
    @bot.tree.command(name="snipe", description="View the last deleted message")
    async def snipe_message(interaction: discord.Interaction):
        """View the last deleted message in the channel"""
        # This would require storing deleted messages in memory
        # For now, we'll show a placeholder
        embed = discord.Embed(
            title="👻 Message Snipe",
            description="No recently deleted messages found in this channel.",
            color=0x9932cc,
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text="Snipe feature tracks deleted messages")
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="steal", description="Add an emoji from another server")
    @app_commands.describe(emoji="Emoji to steal (use the emoji or its URL)", name="Name for the emoji (optional)")
    async def steal_emoji(interaction: discord.Interaction, emoji: str, name: Optional[str] = None):
        """Steal an emoji from another server"""
        if not interaction.user.guild_permissions.manage_emojis:
            await interaction.response.send_message("❌ You need the 'Manage Emojis' permission to use this command.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            # Try to extract emoji URL and name
            if emoji.startswith('<') and emoji.endswith('>'):
                # Custom emoji format <:name:id> or <a:name:id>
                parts = emoji.strip('<>').split(':')
                if len(parts) == 3:
                    animated = parts[0] == 'a'
                    emoji_name = name or parts[1]
                    emoji_id = parts[2]
                    emoji_url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{'gif' if animated else 'png'}"
                else:
                    await interaction.followup.send("❌ Invalid emoji format!")
                    return
            elif emoji.startswith('http'):
                # Direct URL
                emoji_url = emoji
                emoji_name = name or "stolen_emoji"
            else:
                await interaction.followup.send("❌ Please provide a custom emoji or direct image URL!")
                return
            
            # Download emoji
            async with aiohttp.ClientSession() as session:
                async with session.get(emoji_url) as resp:
                    if resp.status != 200:
                        await interaction.followup.send("❌ Could not download emoji!")
                        return
                    emoji_data = await resp.read()
            
            # Add emoji to server
            new_emoji = await interaction.guild.create_custom_emoji(
                name=emoji_name,
                image=emoji_data,
                reason=f"Emoji stolen by {interaction.user}"
            )
            
            embed = discord.Embed(
                title="😈 Emoji Stolen Successfully!",
                description=f"Added {new_emoji} as `:{emoji_name}:` to the server!",
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            embed.set_thumbnail(url=new_emoji.url)
            embed.set_footer(text=f"Stolen by {interaction.user}")
            
            await interaction.followup.send(embed=embed)
            
        except discord.HTTPException as e:
            if "Maximum number of emojis reached" in str(e):
                await interaction.followup.send("❌ Server has reached the maximum number of emojis!")
            else:
                await interaction.followup.send(f"❌ Failed to add emoji: {str(e)}")
        except Exception as e:
            await interaction.followup.send(f"❌ Error stealing emoji: {str(e)}")
    
    # ============= AUTO-MODERATION FEATURES =============
    # Note: Auto-moderation functionality available via /moderation automod group command
    
    # ============= REACTION ROLES =============
    
    @bot.tree.command(name="reactionrole", description="Set up reaction roles")
    @app_commands.describe(
        message_id="Message ID to add reactions to",
        emoji="Emoji to use",
        role="Role to assign"
    )
    async def reaction_role(interaction: discord.Interaction, message_id: str, emoji: str, role: discord.Role):
        """Set up reaction roles"""
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("❌ You need the 'Manage Roles' permission to use this command.", ephemeral=True)
            return
        
        try:
            message = await interaction.channel.fetch_message(int(message_id))
            await message.add_reaction(emoji)
            
            embed = discord.Embed(
                title="⚡ Reaction Role Created",
                description=f"Reacting with {emoji} on [this message](https://discord.com/channels/{interaction.guild.id}/{interaction.channel.id}/{message_id}) will assign {role.mention}",
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text=f"Set up by {interaction.user}")
            
            await interaction.response.send_message(embed=embed)
            
        except ValueError:
            await interaction.response.send_message("❌ Invalid message ID!", ephemeral=True)
        except discord.NotFound:
            await interaction.response.send_message("❌ Message not found!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error setting up reaction role: {str(e)}", ephemeral=True)
    
    # ============= GIVEAWAY SYSTEM =============
    
    @bot.tree.command(name="giveaway", description="Start a giveaway")
    @app_commands.describe(
        duration="Duration in minutes",
        winners="Number of winners",
        prize="Prize description"
    )
    async def start_giveaway(interaction: discord.Interaction, duration: int, winners: int, prize: str):
        """Start a giveaway"""
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ You need the 'Manage Messages' permission to use this command.", ephemeral=True)
            return
        
        if duration < 1 or duration > 1440:  # Max 24 hours
            await interaction.response.send_message("❌ Duration must be between 1 and 1440 minutes (24 hours).", ephemeral=True)
            return
        
        if winners < 1 or winners > 20:
            await interaction.response.send_message("❌ Number of winners must be between 1 and 20.", ephemeral=True)
            return
        
        end_time = datetime.utcnow() + timedelta(minutes=duration)
        
        embed = discord.Embed(
            title="🎉 GIVEAWAY! 🎉",
            description=f"**Prize:** {prize}\n**Winners:** {winners}\n**Ends:** <t:{int(end_time.timestamp())}:R>",
            color=0xffd700,
            timestamp=end_time
        )
        embed.add_field(name="How to Enter", value="React with 🎉 to enter!", inline=False)
        embed.set_footer(text=f"Hosted by {interaction.user} • Ends at")
        
        await interaction.response.send_message(embed=embed)
        
        message = await interaction.original_response()
        await message.add_reaction("🎉")
    
    # ============= MUSIC COMMANDS (Placeholder) =============
    
    @bot.tree.command(name="play", description="Play music (voice feature placeholder)")
    @app_commands.describe(query="Song to search for")
    async def play_music(interaction: discord.Interaction, query: str):
        """Play music (placeholder for voice functionality)"""
        embed = discord.Embed(
            title="🎵 Music Player",
            description="Music functionality requires voice support libraries.\nThis feature is coming soon!",
            color=0xff69b4,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Requested Song", value=query, inline=False)
        embed.add_field(name="Coming Soon", value="• YouTube music support\n• Spotify integration\n• Queue management\n• Volume controls", inline=False)
        embed.set_footer(text=f"Requested by {interaction.user}")
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="queue", description="View music queue (placeholder)")
    async def music_queue(interaction: discord.Interaction):
        """View music queue (placeholder)"""
        embed = discord.Embed(
            title="🎶 Music Queue",
            description="No songs in queue.\nMusic functionality coming soon!",
            color=0xff69b4,
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text="Queue is currently empty")
        
        await interaction.response.send_message(embed=embed)
    
    # ============= TIMER COMMANDS =============
    
    @bot.tree.command(name="timer", description="Start a countdown timer")
    @app_commands.describe(
        duration="Timer duration (e.g., '30s', '5m', '1h')",
        label="Optional label for the timer"
    )
    async def start_timer(interaction: discord.Interaction, duration: str, label: str = "Timer"):
        """Start a countdown timer"""
        time_map = {'s': 1, 'm': 60, 'h': 3600}
        
        try:
            if duration[-1].lower() in time_map:
                amount = int(duration[:-1])
                unit = duration[-1].lower()
                seconds = amount * time_map[unit]
                
                if seconds > 86400:  # 24 hours max
                    await interaction.response.send_message("❌ Maximum timer duration is 24 hours!", ephemeral=True)
                    return
                
                if seconds < 1:
                    await interaction.response.send_message("❌ Timer must be at least 1 second!", ephemeral=True)
                    return
                
                end_time = datetime.utcnow() + timedelta(seconds=seconds)
                
                embed = discord.Embed(
                    title="⏱️ Timer Started",
                    description=f"**{label}** timer is running for {amount}{unit}!",
                    color=0x00ff00,
                    timestamp=datetime.utcnow()
                )
                embed.add_field(name="Duration", value=f"{amount}{unit}", inline=True)
                embed.add_field(name="Ends At", value=f"<t:{int(end_time.timestamp())}:t>", inline=True)
                embed.add_field(name="Time Remaining", value=f"<t:{int(end_time.timestamp())}:R>", inline=False)
                embed.set_footer(text=f"Timer set by {interaction.user}")
                
                await interaction.response.send_message(embed=embed)
                
                # Run timer in background
                async def timer_complete():
                    await asyncio.sleep(seconds)
                    try:
                        timer_embed = discord.Embed(
                            title="⏰ TIMER COMPLETE!",
                            description=f"🔔 **{label}** timer ({amount}{unit}) has finished!",
                            color=0xff0000,
                            timestamp=datetime.utcnow()
                        )
                        timer_embed.set_footer(text=f"Timer was set by {interaction.user}")
                        
                        await interaction.followup.send(f"{interaction.user.mention}", embed=timer_embed)
                    except:
                        pass
                
                asyncio.create_task(timer_complete())
                
            else:
                await interaction.response.send_message("❌ Invalid time format! Use format like '30s', '5m', '1h'", ephemeral=True)
                
        except ValueError:
            await interaction.response.send_message("❌ Invalid time format! Use format like '30s', '5m', '1h'", ephemeral=True)
    
    # ============= AI CHAT COMMANDS =============
    
    @bot.tree.command(name="chatgpt", description="Chat with ChatGPT AI")
    @app_commands.describe(message="Your message to ChatGPT")
    async def chat_gpt(interaction: discord.Interaction, message: str):
        """Chat with ChatGPT"""
        if not AI_AVAILABLE:
            await interaction.response.send_message("❌ AI features are not available.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            response = await chat_with_gpt(message, interaction.user.display_name)
            
            embed = discord.Embed(
                title="🤖 ChatGPT Response",
                description=response[:4000],  # Discord embed limit
                color=0x10a37f,
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Your Question", value=message[:1000], inline=False)
            embed.set_footer(text=f"Asked by {interaction.user}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)}")
    
    @bot.tree.command(name="gemini", description="Chat with Google Gemini AI")
    @app_commands.describe(message="Your message to Gemini")
    async def chat_gemini(interaction: discord.Interaction, message: str):
        """Chat with Google Gemini"""
        if not AI_AVAILABLE:
            await interaction.response.send_message("❌ AI features are not available.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            response = await chat_with_gemini(message, interaction.user.display_name)
            
            embed = discord.Embed(
                title="✨ Gemini Response",
                description=response[:4000],  # Discord embed limit
                color=0x4285f4,
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Your Question", value=message[:1000], inline=False)
            embed.set_footer(text=f"Asked by {interaction.user}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)}")
    
    @bot.tree.command(name="analyze", description="Analyze an image with AI")
    @app_commands.describe(
        image="Image to analyze (attach an image)",
        ai_model="AI model to use",
        prompt="Custom analysis prompt (optional)"
    )
    async def analyze_image(interaction: discord.Interaction, image: discord.Attachment, 
                           ai_model: str = "gemini", prompt: str = "Describe this image in detail"):
        """Analyze an image with AI"""
        if not AI_AVAILABLE:
            await interaction.response.send_message("❌ AI features are not available.", ephemeral=True)
            return
        
        # Check if it's an image
        if not image.content_type or not image.content_type.startswith('image/'):
            await interaction.response.send_message("❌ Please attach a valid image file.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            if ai_model.lower() == "chatgpt":
                response = await analyze_image_with_gpt(image.url, prompt)
                title = "🤖 ChatGPT Image Analysis"
                color = 0x10a37f
            else:  # Default to Gemini
                response = await analyze_image_with_gemini(image.url, prompt)
                title = "✨ Gemini Image Analysis"
                color = 0x4285f4
            
            embed = discord.Embed(
                title=title,
                description=response[:4000],
                color=color,
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Analysis Prompt", value=prompt[:1000], inline=False)
            embed.set_image(url=image.url)
            embed.set_footer(text=f"Analyzed by {interaction.user}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error analyzing image: {str(e)}")
    
    @bot.tree.command(name="aistatus", description="Check AI integration status")
    async def ai_status(interaction: discord.Interaction):
        """Check AI integration status"""
        if not AI_AVAILABLE:
            await interaction.response.send_message("❌ AI integration module not loaded.", ephemeral=True)
            return
        
        status = get_ai_status()
        
        embed = discord.Embed(
            title="🤖 AI Integration Status",
            color=0x00ff00 if (status['openai'] or status['gemini']) else 0xff0000,
            timestamp=datetime.utcnow()
        )
        
        # OpenAI Status
        openai_status = "✅ Connected" if status['openai'] else ("🔑 Key Missing" if not status['openai_key'] else "❌ Connection Failed")
        embed.add_field(name="ChatGPT (OpenAI)", value=openai_status, inline=True)
        
        # Gemini Status
        gemini_status = "✅ Connected" if status['gemini'] else ("🔑 Key Missing" if not status['gemini_key'] else "❌ Connection Failed")
        embed.add_field(name="Gemini (Google)", value=gemini_status, inline=True)
        
        # Available Features
        features = []
        if status['openai']: features.extend(["✅ ChatGPT Chat", "✅ Image Analysis (GPT)"])
        if status['gemini']: features.extend(["✅ Gemini Chat", "✅ Image Analysis (Gemini)"])
        
        if not features:
            features.append("❌ No AI features available")
            embed.add_field(name="Setup Required", value="Ask an admin to provide OPENAI_API_KEY and/or GEMINI_API_KEY", inline=False)
        
        embed.add_field(name="Available Features", value="\n".join(features), inline=False)
        embed.set_footer(text=f"Requested by {interaction.user}")
        
        await interaction.response.send_message(embed=embed)
    
    # ============= WELCOME SYSTEM COMMANDS =============
    
    @bot.command(name='testwelcome', help='Test the welcome message system (Admin only)')
    @commands.has_permissions(manage_guild=True)
    async def test_welcome(ctx, member: discord.Member = None):
        """Test the welcome message by simulating a member join"""
        test_member = member or ctx.author
        
        # First, check what welcome channel will be used
        welcome_channel = await bot.find_welcome_channel(ctx.guild)
        
        if not welcome_channel:
            embed = discord.Embed(
                title="❌ Welcome Test Failed",
                description="No welcome channel found! The bot needs permission to send messages in at least one channel.",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return
        
        # Show which channel will be used
        status_embed = discord.Embed(
            title="🔍 Welcome Channel Detection",
            description=f"Found welcome channel: {welcome_channel.mention}\nTesting welcome message...",
            color=0xffff00
        )
        status_msg = await ctx.send(embed=status_embed)
        
        # Show the exact welcome message design as it will appear
        # Load welcome settings
        import json
        try:
            with open('welcome_settings.json', 'r') as f:
                settings = json.load(f)
            guild_settings = settings.get(str(ctx.guild.id), {})
        except:
            guild_settings = {}
        
        # Get the same message that would be sent to new members
        if guild_settings.get('message'):
            interactive_message = guild_settings['message']
            # Process channel mentions
            for channel in ctx.guild.text_channels:
                if 'rulebook' in channel.name.lower() or 'rule' in channel.name.lower():
                    interactive_message = interactive_message.replace('#📖-rulebook', f'<#{channel.id}>')
                    interactive_message = interactive_message.replace('#rulebook', f'<#{channel.id}>')
                elif 'waiting' in channel.name.lower() or 'wait' in channel.name.lower():
                    interactive_message = interactive_message.replace('#⏳-waiting-area', f'<#{channel.id}>')
                    interactive_message = interactive_message.replace('#waiting-area', f'<#{channel.id}>')
                    interactive_message = interactive_message.replace('#waiting', f'<#{channel.id}>')
            
            welcome_description = f"Hey {test_member.display_name}!\n\n{interactive_message}"
        else:
            welcome_description = f"🎉 **Hey there {test_member.mention}!**\n\n✨ **Welcome to {ctx.guild.name}!** ✨\n\nWe're absolutely thrilled to have you join our amazing community! Get ready for awesome conversations, fun events, and great friendships!\n\n🚀 **Your adventure starts here!**"
        
        # Create embed exactly like your dopalaki image
        test_embed = discord.Embed(
            color=0x57F287  # Green border like Discord
        )
        
        # Set the large member avatar as the main image (centered like your image)
        test_embed.set_image(url=test_member.avatar.url if test_member.avatar else test_member.default_avatar.url)
        
        # Create the black background effect with member name using code block
        member_name_section = f"```\n{test_member.display_name}\n```"
        
        # Add the welcome text exactly like your image
        welcome_text = f"**Welcome to RIVALZ MLB THE SHOW!**"
        
        # Combine everything in description to match your image layout
        test_embed.description = f"{welcome_description}\n\n{member_name_section}\n{welcome_text}"
        
        # Update with the test message
        await status_msg.edit(content="📝 **Clean Welcome Design:**", embed=test_embed)
    
    @bot.command(name='welcomeinfo', help='Get information about the welcome system')
    async def welcome_info(ctx):
        """Display information about the welcome system"""
        embed = discord.Embed(
            title="🌟 Welcome System Information",
            description="Your Discord bot has an advanced welcome system that creates beautiful welcome pages when new members join!",
            color=0x7289da,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="🎉 Features",
            value="• **Beautiful welcome embeds** with member info\n• **Personal DM welcome** messages\n• **Server statistics** and member count\n• **Quick start guide** for new members\n• **Bot command help** included\n• **Server boost status** display",
            inline=False
        )
        
        embed.add_field(
            name="📺 Channel Detection",
            value="Automatically finds the best channel:\n• `#welcome` (priority)\n• `#general`\n• `#lobby`\n• `#entrance`\n• `#main`\n• First available channel",
            inline=True
        )
        
        embed.add_field(
            name="🔧 Admin Commands",
            value="• `!testwelcome [@user]` - Test welcome system\n• `!welcomeinfo` - This information\n• Bot automatically detects joins!",
            inline=True
        )
        
        embed.add_field(
            name="💡 Welcome Message Includes",
            value="✨ **Public Channel:**\n• Member avatar and mention\n• Member count milestone\n• Server statistics\n• Quick start guide\n• Bot commands help\n\n📩 **Private DM:**\n• Personal welcome message\n• Server rules reminder\n• Getting started tips",
            inline=False
        )
        
        embed.set_footer(text="Welcome system is always active and ready!")
        await ctx.send(embed=embed)
    
    @bot.command(name='setwelcome', help='Customize welcome message design (Admin only)')
    @commands.has_permissions(manage_guild=True)
    async def set_welcome_design(ctx, design_type: str = None, *, settings=None):
        """Customize the welcome page design"""
        if not design_type:
            # Show available customization options
            embed = discord.Embed(
                title="🎨 Welcome Page Customization",
                description="Customize how your welcome pages look and feel!",
                color=0x9932cc,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="🎨 Design Commands",
                value="`!setwelcome color [hex]` - Set embed color\n`!setwelcome title [text]` - Custom title\n`!setwelcome message [text]` - Custom message\n`!setwelcome image [url]` - Welcome image\n`!setwelcome channel #channel` - Set welcome channel",
                inline=False
            )
            
            embed.add_field(
                name="🎭 Style Presets",
                value="`!setwelcome style minimal` - Clean minimal design\n`!setwelcome style party` - Fun party theme\n`!setwelcome style elegant` - Professional look\n`!setwelcome style gaming` - Gaming community style",
                inline=False
            )
            
            embed.add_field(
                name="⚙️ Other Options",
                value="`!setwelcome reset` - Reset to default\n`!setwelcome preview` - Preview current design\n`!testwelcome` - Test with real message",
                inline=False
            )
            
            await ctx.send(embed=embed)
            return
        
        # Handle different customization options
        if design_type.lower() == 'color' and settings:
            # Set custom color
            try:
                # Remove # if present and convert to int
                color_hex = settings.replace('#', '')
                color_int = int(color_hex, 16)
                
                # Store in bot's custom settings (you could use a database here)
                if not hasattr(bot, 'welcome_settings'):
                    bot.welcome_settings = {}
                if ctx.guild.id not in bot.welcome_settings:
                    bot.welcome_settings[ctx.guild.id] = {}
                
                bot.welcome_settings[ctx.guild.id]['color'] = color_int
                
                embed = discord.Embed(
                    title="✅ Welcome Color Updated",
                    description=f"Welcome pages will now use color `#{color_hex.upper()}`",
                    color=color_int,
                    timestamp=datetime.utcnow()
                )
                await ctx.send(embed=embed)
                
            except ValueError:
                await ctx.send("❌ Invalid color format! Use hex format like `#FF5733` or `FF5733`")
        
        elif design_type.lower() == 'title' and settings:
            # Set custom title
            if not hasattr(bot, 'welcome_settings'):
                bot.welcome_settings = {}
            if ctx.guild.id not in bot.welcome_settings:
                bot.welcome_settings[ctx.guild.id] = {}
            
            bot.welcome_settings[ctx.guild.id]['title'] = settings
            
            embed = discord.Embed(
                title="✅ Welcome Title Updated",
                description=f"New welcome title: **{settings}**",
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            await ctx.send(embed=embed)
        
        elif design_type.lower() == 'message' and settings:
            # Set custom welcome message
            if not hasattr(bot, 'welcome_settings'):
                bot.welcome_settings = {}
            if ctx.guild.id not in bot.welcome_settings:
                bot.welcome_settings[ctx.guild.id] = {}
            
            bot.welcome_settings[ctx.guild.id]['message'] = settings
            
            embed = discord.Embed(
                title="✅ Welcome Message Updated",
                description=f"New welcome message:\n{settings}",
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            await ctx.send(embed=embed)
        
        elif design_type.lower() == 'image' and settings:
            # Set custom welcome image
            if not hasattr(bot, 'welcome_settings'):
                bot.welcome_settings = {}
            if ctx.guild.id not in bot.welcome_settings:
                bot.welcome_settings[ctx.guild.id] = {}
            
            bot.welcome_settings[ctx.guild.id]['image_url'] = settings
            
            embed = discord.Embed(
                title="✅ Welcome Image Updated",
                description="New welcome image has been set!",
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            embed.set_image(url=settings)
            await ctx.send(embed=embed)
        
        elif design_type.lower() == 'channel':
            # Set custom welcome channel
            if ctx.message.channel_mentions:
                channel = ctx.message.channel_mentions[0]
                
                if not hasattr(bot, 'welcome_settings'):
                    bot.welcome_settings = {}
                if ctx.guild.id not in bot.welcome_settings:
                    bot.welcome_settings[ctx.guild.id] = {}
                
                bot.welcome_settings[ctx.guild.id]['channel_id'] = channel.id
                
                embed = discord.Embed(
                    title="✅ Welcome Channel Updated",
                    description=f"Welcome messages will now be sent to {channel.mention}",
                    color=0x00ff00,
                    timestamp=datetime.utcnow()
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ Please mention a channel like `!setwelcome channel #general`")
        
        elif design_type.lower() == 'style':
            # Apply preset styles
            if not hasattr(bot, 'welcome_settings'):
                bot.welcome_settings = {}
            if ctx.guild.id not in bot.welcome_settings:
                bot.welcome_settings[ctx.guild.id] = {}
            
            style = settings.lower() if settings else ""
            
            if style == 'minimal':
                bot.welcome_settings[ctx.guild.id].update({
                    'color': 0x2f3136,
                    'title': 'Welcome!',
                    'message': 'Welcome to {server_name}, {user_mention}! We\'re glad you\'re here.',
                    'style': 'minimal'
                })
                style_name = "Minimal"
                
            elif style == 'party':
                bot.welcome_settings[ctx.guild.id].update({
                    'color': 0xff69b4,
                    'title': '🎉 PARTY TIME! 🎉',
                    'message': '🎊 WOOHOO! {user_mention} just joined the party at {server_name}! 🎊\n\nLet\'s give them the BIGGEST welcome ever! 🥳',
                    'style': 'party'
                })
                style_name = "Party"
                
            elif style == 'elegant':
                bot.welcome_settings[ctx.guild.id].update({
                    'color': 0x1e1e2e,
                    'title': 'A Warm Welcome',
                    'message': 'We are delighted to welcome {user_mention} to {server_name}. We hope you find our community both engaging and supportive.',
                    'style': 'elegant'
                })
                style_name = "Elegant"
                
            elif style == 'gaming':
                bot.welcome_settings[ctx.guild.id].update({
                    'color': 0x00ff41,
                    'title': '⚡ PLAYER JOINED THE GAME ⚡',
                    'message': '🎮 Epic! {user_mention} has entered {server_name}! 🎮\n\n🏆 Ready to level up and join the adventure? Let\'s game! 🚀',
                    'style': 'gaming'
                })
                style_name = "Gaming"
            else:
                await ctx.send("❌ Available styles: `minimal`, `party`, `elegant`, `gaming`")
                return
            
            embed = discord.Embed(
                title=f"✅ {style_name} Style Applied",
                description=f"Welcome messages now use the {style_name.lower()} style theme!",
                color=bot.welcome_settings[ctx.guild.id]['color'],
                timestamp=datetime.utcnow()
            )
            await ctx.send(embed=embed)
        
        elif design_type.lower() == 'preview':
            # Show current welcome design using proper preview
            await ctx.send("🎨 **Current Welcome Design Preview:**\n💡 *Use `/previewwelcome` for the actual welcome image preview!*")
        
        elif design_type.lower() == 'reset':
            # Reset to default settings
            if hasattr(bot, 'welcome_settings') and ctx.guild.id in bot.welcome_settings:
                del bot.welcome_settings[ctx.guild.id]
            
            embed = discord.Embed(
                title="✅ Welcome Design Reset",
                description="Welcome pages have been reset to the default design.",
                color=0x00ff7f,
                timestamp=datetime.utcnow()
            )
            await ctx.send(embed=embed)
        
        else:
            await ctx.send("❌ Use `!setwelcome` without arguments to see all customization options!")

    # Interactive Welcome Preview Tool
    @bot.tree.command(name="previewwelcome", description="Preview the actual welcome image new members receive")
    @app_commands.describe(
        user="User to preview welcome message for (optional - defaults to you)"
    )
    async def preview_welcome(interaction: discord.Interaction, user: discord.Member = None):
        """Preview the actual welcome image using the same system as new member joins"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Use command author if no user specified
            preview_user = user or interaction.user
            
            # Get the bot instance
            bot_instance = interaction.client
            
            # Load welcome settings if available
            if hasattr(bot_instance, 'load_welcome_settings'):
                bot_instance.load_welcome_settings()
            
            # Generate the actual welcome image using the same system as new member joins
            if hasattr(bot_instance, 'welcome_image_generator'):
                welcome_image_file = await bot_instance.welcome_image_generator.create_welcome_image(preview_user, interaction.guild.name)
                
                if welcome_image_file:
                    # Create the same embed format as the actual welcome system
                    welcome_settings = {}
                    if hasattr(bot_instance, 'welcome_settings') and interaction.guild.id in bot_instance.welcome_settings:
                        welcome_settings = bot_instance.welcome_settings[interaction.guild.id]
                    
                    # Use same color as actual welcome system
                    welcome_color = welcome_settings.get('color', 0xFFD700)  # Gold default
                    
                    # Create same welcome message format
                    if 'message' in welcome_settings:
                        interactive_message = welcome_settings['message']
                        # Format like actual welcome page: clean text without emoji
                        welcome_description = f"**Hey**, **{preview_user.display_name}**! 👋\n\n**Welcome to {interaction.guild.name}**!\n\n{interactive_message}"
                    else:
                        welcome_description = f"**Hey**, **{preview_user.display_name}**! 👋\n\n**Welcome to {interaction.guild.name}**!\n\nThis is exactly how new members will see their welcome message!"
                    
                    # Create embed exactly like actual welcome system
                    embed = discord.Embed(
                        color=welcome_color,
                        description=welcome_description
                    )
                    
                    # Add server logo/icon to match actual welcome
                    if interaction.guild.icon:
                        embed.set_thumbnail(url=interaction.guild.icon.url)
                    
                    # Set the generated welcome image
                    embed.set_image(url='attachment://welcome.png')
                    
                    await interaction.followup.send(
                        content=f"🎨 **This is exactly how {preview_user.display_name}'s welcome message will look!**\n*This uses the same black theme and custom image generator as real welcome messages.*",
                        embed=embed,
                        file=welcome_image_file
                    )
                else:
                    await interaction.followup.send("❌ **Error:** Could not generate welcome image. Please try again.", ephemeral=True)
            else:
                await interaction.followup.send("❌ **Error:** Welcome image generator not available.", ephemeral=True)
                
        except Exception as e:
            await interaction.followup.send(f"❌ **Error creating preview:** {str(e)}", ephemeral=True)
            logger.error(f"Error in preview welcome command: {e}")

class WelcomePreviewView(discord.ui.View):
    """Interactive view for welcome message preview"""
    
    def __init__(self, user, message, color):
        super().__init__(timeout=300)  # 5 minute timeout
        self.user = user
        self.custom_message = message
        self.color = color
    
    @discord.ui.button(label="Change Color", style=discord.ButtonStyle.primary, emoji="🎨")
    async def change_color(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Change the embed color"""
        await interaction.response.send_modal(ColorModal(self.user, self.custom_message))
    
    @discord.ui.button(label="Edit Message", style=discord.ButtonStyle.secondary, emoji="✏️")
    async def edit_message(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Edit the welcome message"""
        await interaction.response.send_modal(MessageModal(self.user, self.color))
    
    @discord.ui.button(label="Test Different User", style=discord.ButtonStyle.secondary, emoji="👤")
    async def test_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Test with a different user"""
        await interaction.response.send_modal(UserModal(self.custom_message, self.color))
    
    @discord.ui.button(label="Style Presets", style=discord.ButtonStyle.secondary, emoji="🎭")
    async def style_presets(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Apply style presets"""
        await interaction.response.send_modal(StylePresetModal(self.user, self.custom_message))
    
    @discord.ui.button(label="Generate Image", style=discord.ButtonStyle.success, emoji="🖼️")
    async def generate_image(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Generate a professional Discord-style welcome image"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Generate professional welcome image
            image_bytes = await create_professional_welcome_image(
                user=self.user,
                guild=interaction.guild,
                color_hex=self.color or "#57F287",
                custom_message=self.custom_message,
                style="professional"
            )
            
            if image_bytes:
                # Create Discord file
                file = discord.File(image_bytes, filename=f"welcome_{self.user.display_name}_{interaction.guild.name}.png")
                
                await interaction.followup.send(
                    f"🖼️ **Professional Welcome Image Generated!**\n"
                    f"*Discord-style welcome image for {self.user.display_name}*\n"
                    f"**Features:** Circular avatar, gradient effects, member count badge, custom colors",
                    file=file,
                    ephemeral=True
                )
            else:
                await interaction.followup.send("❌ Failed to generate welcome image.", ephemeral=True)
                
        except Exception as e:
            await interaction.followup.send(f"❌ Error generating image: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="Save as Default", style=discord.ButtonStyle.success, emoji="💾")
    async def save_default(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Save current settings as server default"""
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You need 'Manage Server' permission to save default settings.", ephemeral=True)
            return
        
        try:
            guild_id = str(interaction.guild.id)
            settings = load_welcome_settings()
            
            if guild_id not in settings:
                settings[guild_id] = {}
            
            if self.custom_message:
                settings[guild_id]['message'] = self.custom_message
            
            save_welcome_settings(settings)
            
            await interaction.response.send_message("✅ **Settings saved!** This preview design is now your server's default welcome message.", ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error saving settings: {str(e)}", ephemeral=True)

async def create_professional_welcome_image(user, guild, color_hex="#57F287", custom_message=None, style="professional"):
    """Create a professional welcome image mimicking Discord welcome page designs"""
    try:
        # Download user avatar and guild icon
        async with aiohttp.ClientSession() as session:
            avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
            async with session.get(str(avatar_url)) as resp:
                avatar_data = await resp.read()
            
            # Download guild/server icon
            guild_icon_data = None
            if guild.icon:
                print(f"DEBUG: Guild has icon, downloading from {guild.icon.url}")
                try:
                    async with session.get(str(guild.icon.url)) as resp:
                        if resp.status == 200:
                            guild_icon_data = await resp.read()
                            print(f"DEBUG: Successfully downloaded {len(guild_icon_data)} bytes of guild icon")
                        else:
                            print(f"DEBUG: Failed to download guild icon: HTTP {resp.status}")
                except Exception as e:
                    print(f"DEBUG: Error downloading guild icon: {e}")
            else:
                print("DEBUG: Guild has no custom icon set")
        
        # Create base image with professional Discord-style dimensions (800x400)
        img = Image.new('RGB', (800, 400), color='#36393F')  # Discord dark theme
        draw = ImageDraw.Draw(img)
        
        # Load fonts with fallbacks FIRST
        try:
            title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
            subtitle_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
            message_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
        except:
            try:
                title_font = ImageFont.truetype("arial.ttf", 36)
                subtitle_font = ImageFont.truetype("arial.ttf", 24)
                message_font = ImageFont.truetype("arial.ttf", 18)
            except:
                title_font = ImageFont.load_default()
                subtitle_font = ImageFont.load_default()
                message_font = ImageFont.load_default()
        
        # Load and process avatar with high quality
        avatar_img = Image.open(io.BytesIO(avatar_data))
        avatar_img = avatar_img.convert('RGBA')
        avatar_size = 120
        avatar_img = avatar_img.resize((avatar_size, avatar_size), Image.Resampling.LANCZOS)
        
        # Create circular mask with smooth edges
        mask = Image.new('L', (avatar_size, avatar_size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)
        
        # Apply anti-aliasing to mask
        mask = mask.filter(Image.Filter.SMOOTH)
        
        # Apply mask to avatar
        avatar_circular = Image.new('RGBA', (avatar_size, avatar_size), (0, 0, 0, 0))
        avatar_circular.paste(avatar_img, mask=mask)
        
        # Add subtle avatar border
        border_size = 4
        avatar_with_border = Image.new('RGBA', (avatar_size + border_size*2, avatar_size + border_size*2), (0, 0, 0, 0))
        border_color = tuple(int(color_hex[1:][i:i+2], 16) for i in (0, 2, 4)) if color_hex.startswith('#') else (87, 242, 135)
        
        # Draw border
        border_draw = ImageDraw.Draw(avatar_with_border)
        border_draw.ellipse((0, 0, avatar_size + border_size*2, avatar_size + border_size*2), fill=border_color)
        avatar_with_border.paste(avatar_circular, (border_size, border_size), avatar_circular)
        
        # Create layout matching dopalaki design: Welcome message at top, avatar centered in black section below
        
        # Welcome text first (top section)
        welcome_title = "Welcome to RIVALZ MLB THE SHOW!"
        title_bbox = draw.textbbox((0, 0), welcome_title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (800 - title_width) // 2
        title_y = 40  # Top section
        
        # Add server logo to the left of welcome text
        guild_icon_size = 48
        logo_x = title_x - guild_icon_size - 15  # 15px gap between logo and text
        logo_y = title_y + (title_bbox[3] - title_bbox[1] - guild_icon_size) // 2  # Center vertically with text
        
        if guild_icon_data:
            print(f"DEBUG: Processing guild icon for placement at ({logo_x}, {logo_y})")
            try:
                guild_icon_img = Image.open(io.BytesIO(guild_icon_data))
                guild_icon_img = guild_icon_img.convert('RGBA')
                guild_icon_img = guild_icon_img.resize((guild_icon_size, guild_icon_size), Image.Resampling.LANCZOS)
                
                # Create circular mask for guild icon
                guild_mask = Image.new('L', (guild_icon_size, guild_icon_size), 0)
                guild_mask_draw = ImageDraw.Draw(guild_mask)
                guild_mask_draw.ellipse((0, 0, guild_icon_size, guild_icon_size), fill=255)
                guild_mask = guild_mask.filter(Image.Filter.SMOOTH)
                
                # Apply mask to guild icon
                guild_icon_circular = Image.new('RGBA', (guild_icon_size, guild_icon_size), (0, 0, 0, 0))
                guild_icon_circular.paste(guild_icon_img, mask=guild_mask)
                
                # Paste the guild icon
                img.paste(guild_icon_circular, (logo_x, logo_y), guild_icon_circular)
                print(f"DEBUG: Successfully placed guild icon")
            except Exception as e:
                print(f"DEBUG: Error processing guild icon: {e}")
                # Create placeholder logo as fallback
                placeholder_logo = Image.new('RGBA', (guild_icon_size, guild_icon_size), (87, 242, 135, 255))
                placeholder_draw = ImageDraw.Draw(placeholder_logo)
                placeholder_draw.ellipse((2, 2, guild_icon_size-2, guild_icon_size-2), fill=(255, 255, 255, 255))
                placeholder_draw.text((guild_icon_size//2-8, guild_icon_size//2-8), "S", font=subtitle_font, fill=(87, 242, 135, 255))
                img.paste(placeholder_logo, (logo_x, logo_y), placeholder_logo)
                print(f"DEBUG: Used placeholder server logo")
        else:
            print("DEBUG: No guild icon data - creating placeholder server logo")
            # Create a placeholder server logo
            placeholder_logo = Image.new('RGBA', (guild_icon_size, guild_icon_size), (87, 242, 135, 255))
            placeholder_draw = ImageDraw.Draw(placeholder_logo)
            placeholder_draw.ellipse((2, 2, guild_icon_size-2, guild_icon_size-2), fill=(255, 255, 255, 255))
            placeholder_draw.text((guild_icon_size//2-8, guild_icon_size//2-8), "S", font=subtitle_font, fill=(87, 242, 135, 255))
            img.paste(placeholder_logo, (logo_x, logo_y), placeholder_logo)
            print(f"DEBUG: Created placeholder server logo at ({logo_x}, {logo_y})")
        
        # Draw welcome title with gold color
        gold_color = (255, 215, 0)  # Gold
        draw.text((title_x + 2, title_y + 2), welcome_title, font=title_font, fill=(0, 0, 0))  # Shadow
        draw.text((title_x, title_y), welcome_title, font=title_font, fill=gold_color)
        
        # Create black background section for avatar (dopalaki style)
        black_section_y = title_y + 80  # Start below welcome message
        black_section_height = 300  # Rest of the image
        draw.rectangle([(0, black_section_y), (800, 400)], fill=(0, 0, 0))  # Pure black background
        
        # Position avatar centered in the black section
        avatar_x = (800 - (avatar_size + border_size*2)) // 2
        avatar_y = black_section_y + (black_section_height - (avatar_size + border_size*2)) // 2
        img.paste(avatar_with_border, (avatar_x, avatar_y), avatar_with_border)
        
        # Fonts already loaded above
        
        # Define color scheme
        primary_color = tuple(int(color_hex[1:][i:i+2], 16) for i in (0, 2, 4)) if color_hex.startswith('#') else (87, 242, 135)
        text_white = (255, 255, 255)
        text_gray = (185, 187, 190)
        accent_color = primary_color
        
        # Username display below avatar in black section (dopalaki style)
        username_text = user.display_name
        username_bbox = draw.textbbox((0, 0), username_text, font=subtitle_font)
        username_width = username_bbox[2] - username_bbox[0]
        username_x = (800 - username_width) // 2
        username_y = avatar_y + (avatar_size + border_size*2) + 20  # Below avatar in black section
        
        # Draw username with shadow effect
        shadow_offset = 2
        draw.text((username_x + shadow_offset, username_y + shadow_offset), username_text, font=subtitle_font, fill=(50, 50, 50))  # Dark shadow on black
        draw.text((username_x, username_y), username_text, font=subtitle_font, fill=text_white)
        
        # Custom message handling
        if custom_message:
            processed_message = custom_message.replace('{username}', user.display_name)
            processed_message = processed_message.replace('{server}', guild.name)
            processed_message = processed_message.replace('{member_count}', str(guild.member_count))
            
            # Word wrap for message
            words = processed_message.split()
            lines = []
            current_line = []
            max_width = 600
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                test_bbox = draw.textbbox((0, 0), test_line, font=message_font)
                test_width = test_bbox[2] - test_bbox[0]
                
                if test_width <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                    else:
                        lines.append(word)
            
            if current_line:
                lines.append(' '.join(current_line))
            
            # Draw message lines
            message_start_y = username_y + 40
            for i, line in enumerate(lines[:2]):  # Max 2 lines for clean design
                line_bbox = draw.textbbox((0, 0), line, font=message_font)
                line_width = line_bbox[2] - line_bbox[0]
                line_x = (800 - line_width) // 2
                line_y = message_start_y + (i * 25)
                
                # Message with subtle shadow
                draw.text((line_x + 1, line_y + 1), line, font=message_font, fill=(0, 0, 0))
                draw.text((line_x, line_y), line, font=message_font, fill=text_gray)
        
        # Add decorative elements (dopalaki style)
        # Green accent border around the image
        border_width = 3
        draw.rectangle([(0, 0), (800, border_width)], fill=accent_color)  # Top
        draw.rectangle([(0, 400-border_width), (800, 400)], fill=accent_color)  # Bottom
        draw.rectangle([(0, 0), (border_width, 400)], fill=accent_color)  # Left
        draw.rectangle([(800-border_width, 0), (800, 400)], fill=accent_color)  # Right
        
        # Add subtle gradient effect (simplified)
        gradient_overlay = Image.new('RGBA', (800, 400), (0, 0, 0, 0))
        gradient_draw = ImageDraw.Draw(gradient_overlay)
        
        # Create subtle vignette effect
        for i in range(50):
            alpha = int(i * 2.5)
            gradient_draw.rectangle([(i, i), (800-i, 400-i)], outline=(0, 0, 0, alpha))
        
        img = Image.alpha_composite(img.convert('RGBA'), gradient_overlay).convert('RGB')
        
        # Server info badge
        member_count_text = f"{guild.member_count} members"
        badge_width = 120
        badge_height = 25
        badge_x = 800 - badge_width - 20
        badge_y = 20
        
        # Draw badge background
        draw.rectangle([(badge_x, badge_y), (badge_x + badge_width, badge_y + badge_height)], 
                      fill=(*accent_color, 180), outline=accent_color)
        
        # Draw badge text
        badge_font = message_font
        badge_text_bbox = draw.textbbox((0, 0), member_count_text, font=badge_font)
        badge_text_width = badge_text_bbox[2] - badge_text_bbox[0]
        badge_text_x = badge_x + (badge_width - badge_text_width) // 2
        badge_text_y = badge_y + 5
        
        draw.text((badge_text_x, badge_text_y), member_count_text, font=badge_font, fill=text_white)
        
        # Save to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG', quality=95)
        img_bytes.seek(0)
        
        return img_bytes
        
    except Exception as e:
        logger.error(f"Error creating professional welcome image: {e}")
        return None

async def create_welcome_image(user, guild, color_hex="#57F287", custom_message=None):
    """Create a welcome image - wrapper that calls the professional version"""
    return await create_professional_welcome_image(user, guild, color_hex, custom_message)

class ColorModal(discord.ui.Modal):
    """Modal for changing embed color"""
    
    def __init__(self, user, message):
        super().__init__(title="Change Embed Color")
        self.user = user
        self.message = message
    
    color_input = discord.ui.TextInput(
        label="Color (hex code or name)",
        placeholder="Enter #57F287, gold, blue, red, purple...",
        default="#57F287",
        max_length=20
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Parse color
            color_value = self.color_input.value.strip()
            embed_color = 0x57F287  # Default
            
            if color_value.startswith('#'):
                embed_color = int(color_value[1:], 16)
            elif color_value.lower() == 'gold':
                embed_color = 0xFFD700
            elif color_value.lower() == 'blue':
                embed_color = 0x5865F2
            elif color_value.lower() == 'red':
                embed_color = 0xED4245
            elif color_value.lower() == 'purple':
                embed_color = 0x5865F2
            
            # Create updated preview
            welcome_description = f"🎉 **Hey there {self.user.mention}!**\n\n✨ **Welcome to {interaction.guild.name}!** ✨\n\nWe're absolutely thrilled to have you join our amazing community! Get ready for awesome conversations, fun events, and great friendships!\n\n🚀 **Your adventure starts here!**"
            
            if self.message:
                processed_message = self.message.replace('{username}', self.user.display_name)
                processed_message = processed_message.replace('{server}', interaction.guild.name)
                processed_message = processed_message.replace('{member_count}', str(interaction.guild.member_count))
                welcome_description = f"Hey {self.user.display_name}!\n\n{processed_message}"
            
            preview_embed = discord.Embed(color=embed_color)
            preview_embed.set_image(url=self.user.avatar.url if self.user.avatar else self.user.default_avatar.url)
            
            member_name_section = f"```\n{self.user.display_name}\n```"
            welcome_text = f"**Welcome to {interaction.guild.name.upper()}!**"
            preview_embed.description = f"{welcome_description}\n\n{member_name_section}\n{welcome_text}"
            
            view = WelcomePreviewView(self.user, self.message, color_value)
            
            await interaction.response.edit_message(
                content=f"🎨 **Updated Preview for {self.user.display_name}** (Color: {color_value})",
                embed=preview_embed,
                view=view
            )
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Invalid color format: {str(e)}", ephemeral=True)

class MessageModal(discord.ui.Modal):
    """Modal for editing welcome message"""
    
    def __init__(self, user, color):
        super().__init__(title="Edit Welcome Message")
        self.user = user
        self.color = color
    
    message_input = discord.ui.TextInput(
        label="Welcome Message",
        placeholder="Enter your custom welcome message...\nUse {username}, {server}, {member_count} for variables",
        style=discord.TextStyle.paragraph,
        max_length=1000
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            custom_message = self.message_input.value.strip()
            
            # Parse color
            embed_color = 0x57F287
            if self.color:
                if self.color.startswith('#'):
                    embed_color = int(self.color[1:], 16)
                elif self.color.lower() == 'gold':
                    embed_color = 0xFFD700
            
            # Process message with variables
            processed_message = custom_message.replace('{username}', self.user.display_name)
            processed_message = processed_message.replace('{server}', interaction.guild.name)
            processed_message = processed_message.replace('{member_count}', str(interaction.guild.member_count))
            welcome_description = f"Hey {self.user.display_name}!\n\n{processed_message}"
            
            preview_embed = discord.Embed(color=embed_color)
            preview_embed.set_image(url=self.user.avatar.url if self.user.avatar else self.user.default_avatar.url)
            
            member_name_section = f"```\n{self.user.display_name}\n```"
            welcome_text = f"**Welcome to {interaction.guild.name.upper()}!**"
            preview_embed.description = f"{welcome_description}\n\n{member_name_section}\n{welcome_text}"
            
            view = WelcomePreviewView(self.user, custom_message, self.color)
            
            await interaction.response.edit_message(
                content=f"✏️ **Updated Preview for {self.user.display_name}** (Custom Message)",
                embed=preview_embed,
                view=view
            )
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error updating message: {str(e)}", ephemeral=True)

class UserModal(discord.ui.Modal):
    """Modal for testing with different user"""
    
    def __init__(self, message, color):
        super().__init__(title="Test Different User")
        self.message = message
        self.color = color
    
    user_input = discord.ui.TextInput(
        label="Username or User ID",
        placeholder="Enter username or user ID to test with...",
        max_length=100
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_query = self.user_input.value.strip()
            
            # Try to find user by mention, username, or ID
            test_user = None
            
            # Remove mention formatting if present
            if user_query.startswith('<@') and user_query.endswith('>'):
                user_id = user_query[2:-1]
                if user_id.startswith('!'):
                    user_id = user_id[1:]
                test_user = interaction.guild.get_member(int(user_id))
            
            # Try by ID
            if not test_user and user_query.isdigit():
                test_user = interaction.guild.get_member(int(user_query))
            
            # Try by username
            if not test_user:
                for member in interaction.guild.members:
                    if member.display_name.lower() == user_query.lower() or member.name.lower() == user_query.lower():
                        test_user = member
                        break
            
            if not test_user:
                await interaction.response.send_message(f"❌ Could not find user: {user_query}", ephemeral=True)
                return
            
            # Create preview with new user
            embed_color = 0x57F287
            if self.color and self.color.startswith('#'):
                embed_color = int(self.color[1:], 16)
            
            welcome_description = f"🎉 **Hey there {test_user.mention}!**\n\n✨ **Welcome to {interaction.guild.name}!** ✨\n\nWe're absolutely thrilled to have you join our amazing community! Get ready for awesome conversations, fun events, and great friendships!\n\n🚀 **Your adventure starts here!**"
            
            if self.message:
                processed_message = self.message.replace('{username}', test_user.display_name)
                processed_message = processed_message.replace('{server}', interaction.guild.name)
                processed_message = processed_message.replace('{member_count}', str(interaction.guild.member_count))
                welcome_description = f"Hey {test_user.display_name}!\n\n{processed_message}"
            
            preview_embed = discord.Embed(color=embed_color)
            preview_embed.set_image(url=test_user.avatar.url if test_user.avatar else test_user.default_avatar.url)
            
            member_name_section = f"```\n{test_user.display_name}\n```"
            welcome_text = f"**Welcome to {interaction.guild.name.upper()}!**"
            preview_embed.description = f"{welcome_description}\n\n{member_name_section}\n{welcome_text}"
            
            view = WelcomePreviewView(test_user, self.message, self.color)
            
            await interaction.response.edit_message(
                content=f"👤 **Preview for {test_user.display_name}**",
                embed=preview_embed,
                view=view
            )
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error finding user: {str(e)}", ephemeral=True)

class StylePresetModal(discord.ui.Modal):
    """Modal for applying style presets"""
    
    def __init__(self, user, message):
        super().__init__(title="Apply Style Preset")
        self.user = user
        self.message = message
    
    preset_input = discord.ui.TextInput(
        label="Style Preset",
        placeholder="Enter: minimal, party, elegant, gaming, professional, dark, light",
        max_length=20
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            preset = self.preset_input.value.strip().lower()
            
            # Define preset styles
            presets = {
                'minimal': {'color': '#36393f', 'description': 'Clean and simple'},
                'party': {'color': '#ff69b4', 'description': 'Fun and colorful'},
                'elegant': {'color': '#800080', 'description': 'Sophisticated and refined'},
                'gaming': {'color': '#00ff41', 'description': 'Gaming theme with green accents'},
                'professional': {'color': '#4169e1', 'description': 'Business and professional'},
                'dark': {'color': '#2c2f33', 'description': 'Dark theme'},
                'light': {'color': '#ffffff', 'description': 'Light and bright'},
                'gold': {'color': '#ffd700', 'description': 'Gold luxury theme'},
                'red': {'color': '#ed4245', 'description': 'Bold red theme'},
                'blue': {'color': '#5865f2', 'description': 'Discord blue theme'}
            }
            
            if preset in presets:
                preset_info = presets[preset]
                embed_color = int(preset_info['color'][1:], 16) if preset_info['color'].startswith('#') else 0x57F287
                
                # Create custom message based on preset
                if preset == 'minimal':
                    custom_message = "Welcome to {server}. We're glad you're here."
                elif preset == 'party':
                    custom_message = "🎉 PARTY TIME! {username} joined the celebration! 🎊 Welcome to {server}! Let's have some fun!"
                elif preset == 'elegant':
                    custom_message = "We cordially welcome {username} to our distinguished community of {server}. We look forward to your contributions."
                elif preset == 'gaming':
                    custom_message = "🎮 PLAYER {username} HAS ENTERED THE GAME! 🚀 Welcome to {server} - Ready to level up?"
                elif preset == 'professional':
                    custom_message = "Welcome {username} to {server}. We're pleased to have you join our professional community."
                elif preset == 'dark':
                    custom_message = "⚫ {username} emerges from the shadows... Welcome to the {server} collective."
                elif preset == 'light':
                    custom_message = "✨ Bright and wonderful! {username} brings light to {server}! Welcome!"
                else:
                    custom_message = self.message or f"Welcome {username} to {server}!"
                
                # Create preview with preset
                processed_message = custom_message.replace('{username}', self.user.display_name)
                processed_message = processed_message.replace('{server}', interaction.guild.name)
                processed_message = processed_message.replace('{member_count}', str(interaction.guild.member_count))
                welcome_description = f"Hey {self.user.display_name}!\n\n{processed_message}"
                
                preview_embed = discord.Embed(color=embed_color)
                preview_embed.set_image(url=self.user.avatar.url if self.user.avatar else self.user.default_avatar.url)
                
                member_name_section = f"```\n{self.user.display_name}\n```"
                welcome_text = f"**Welcome to {interaction.guild.name.upper()}!**"
                preview_embed.description = f"{welcome_description}\n\n{member_name_section}\n{welcome_text}"
                
                view = ExtendedWelcomePreviewView(self.user, custom_message, preset_info['color'])
                
                await interaction.response.edit_message(
                    content=f"🎭 **{preset.title()} Style Preview** - {preset_info['description']}",
                    embed=preview_embed,
                    view=view
                )
            else:
                available_presets = ', '.join(presets.keys())
                await interaction.response.send_message(f"❌ Invalid preset. Available: {available_presets}", ephemeral=True)
                
        except Exception as e:
            await interaction.response.send_message(f"❌ Error applying preset: {str(e)}", ephemeral=True)

class ExtendedWelcomePreviewView(discord.ui.View):
    """Extended interactive view with all buttons organized in multiple rows"""
    
    def __init__(self, user, message, color):
        super().__init__(timeout=300)
        self.user = user
        self.custom_message = message
        self.color = color
    
    # Row 0 - Primary actions
    @discord.ui.button(label="Change Color", style=discord.ButtonStyle.primary, emoji="🎨", row=0)
    async def change_color(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Change the embed color"""
        await interaction.response.send_modal(ColorModal(self.user, self.custom_message))
    
    @discord.ui.button(label="Edit Message", style=discord.ButtonStyle.secondary, emoji="✏️", row=0)
    async def edit_message(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Edit the welcome message"""
        await interaction.response.send_modal(MessageModal(self.user, self.color))
    
    @discord.ui.button(label="Test Different User", style=discord.ButtonStyle.secondary, emoji="👤", row=0)
    async def test_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Test with a different user"""
        await interaction.response.send_modal(UserModal(self.custom_message, self.color))
    
    @discord.ui.button(label="Generate Image", style=discord.ButtonStyle.success, emoji="🖼️", row=0)
    async def generate_image(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Generate a professional Discord-style welcome image"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Generate professional welcome image
            image_bytes = await create_professional_welcome_image(
                user=self.user,
                guild=interaction.guild,
                color_hex=self.color or "#57F287",
                custom_message=self.custom_message,
                style="professional"
            )
            
            if image_bytes:
                # Create Discord file
                file = discord.File(image_bytes, filename=f"welcome_{self.user.display_name}_{interaction.guild.name}.png")
                
                await interaction.followup.send(
                    f"🖼️ **Professional Welcome Image Generated!**\n"
                    f"*Discord-style welcome image for {self.user.display_name}*\n"
                    f"**Features:** Circular avatar, gradient effects, member count badge, custom colors",
                    file=file,
                    ephemeral=True
                )
            else:
                await interaction.followup.send("❌ Failed to generate welcome image.", ephemeral=True)
                
        except Exception as e:
            await interaction.followup.send(f"❌ Error generating image: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="Style Presets", style=discord.ButtonStyle.secondary, emoji="🎭", row=0)
    async def style_presets(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Apply style presets"""
        await interaction.response.send_modal(StylePresetModal(self.user, self.custom_message))
        """Save current settings as server default"""
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You need 'Manage Server' permission to save default settings.", ephemeral=True)
            return
        
        try:
            guild_id = str(interaction.guild.id)
            settings = load_welcome_settings()
            
            if guild_id not in settings:
                settings[guild_id] = {}
            
            if self.custom_message:
                settings[guild_id]['message'] = self.custom_message
            
            save_welcome_settings(settings)
            
            await interaction.response.send_message("✅ **Settings saved!** This preview design is now your server's default welcome message.", ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error saving settings: {str(e)}", ephemeral=True)
    
    # Row 1 - Testing and utility actions
    @discord.ui.button(label="Random User Test", style=discord.ButtonStyle.secondary, emoji="🎲", row=1)
    async def random_user_test(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Test with a random server member"""
        try:
            import random
            members = [m for m in interaction.guild.members if not m.bot]
            if members:
                random_member = random.choice(members)
                
                # Create preview with random user
                embed_color = 0x57F287
                if self.color and self.color.startswith('#'):
                    embed_color = int(self.color[1:], 16)
                
                welcome_description = f"🎉 **Hey there {random_member.mention}!**\n\n✨ **Welcome to {interaction.guild.name}!** ✨\n\nWe're absolutely thrilled to have you join our amazing community! Get ready for awesome conversations, fun events, and great friendships!\n\n🚀 **Your adventure starts here!**"
                
                if self.custom_message:
                    processed_message = self.custom_message.replace('{username}', random_member.display_name)
                    processed_message = processed_message.replace('{server}', interaction.guild.name)
                    processed_message = processed_message.replace('{member_count}', str(interaction.guild.member_count))
                    welcome_description = f"Hey {random_member.display_name}!\n\n{processed_message}"
                
                preview_embed = discord.Embed(color=embed_color)
                preview_embed.set_image(url=random_member.avatar.url if random_member.avatar else random_member.default_avatar.url)
                
                member_name_section = f"```\n{random_member.display_name}\n```"
                welcome_text = f"**Welcome to {interaction.guild.name.upper()}!**"
                preview_embed.description = f"{welcome_description}\n\n{member_name_section}\n{welcome_text}"
                
                view = ExtendedWelcomePreviewView(random_member, self.custom_message, self.color)
                
                await interaction.response.edit_message(
                    content=f"🎲 **Random Preview for {random_member.display_name}**",
                    embed=preview_embed,
                    view=view
                )
            else:
                await interaction.response.send_message("❌ No non-bot members found to test with.", ephemeral=True)
                
        except Exception as e:
            await interaction.response.send_message(f"❌ Error selecting random user: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="Send Test Welcome", style=discord.ButtonStyle.primary, emoji="📤", row=1)
    async def send_test_welcome(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Send a test welcome message to current channel"""
        try:
            embed_color = 0x57F287
            if self.color and self.color.startswith('#'):
                embed_color = int(self.color[1:], 16)
            
            welcome_description = f"🎉 **Hey there {self.user.mention}!**\n\n✨ **Welcome to {interaction.guild.name}!** ✨\n\nWe're absolutely thrilled to have you join our amazing community! Get ready for awesome conversations, fun events, and great friendships!\n\n🚀 **Your adventure starts here!**"
            
            if self.custom_message:
                processed_message = self.custom_message.replace('{username}', self.user.display_name)
                processed_message = processed_message.replace('{server}', interaction.guild.name)
                processed_message = processed_message.replace('{member_count}', str(interaction.guild.member_count))
                welcome_description = f"Hey {self.user.display_name}!\n\n{processed_message}"
            
            test_embed = discord.Embed(color=embed_color)
            test_embed.set_image(url=self.user.avatar.url if self.user.avatar else self.user.default_avatar.url)
            
            member_name_section = f"```\n{self.user.display_name}\n```"
            welcome_text = f"**Welcome to {interaction.guild.name.upper()}!**"
            test_embed.description = f"{welcome_description}\n\n{member_name_section}\n{welcome_text}"
            
            # Send to current channel
            await interaction.channel.send(f"📤 **Test Welcome Message:**", embed=test_embed)
            await interaction.response.send_message("✅ **Test welcome message sent to this channel!**", ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error sending test message: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="Reset to Default", style=discord.ButtonStyle.danger, emoji="🔄", row=1)
    async def reset_preview(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Reset to default welcome design"""
        try:
            # Reset to default design
            embed_color = 0x57F287
            welcome_description = f"🎉 **Hey there {self.user.mention}!**\n\n✨ **Welcome to {interaction.guild.name}!** ✨\n\nWe're absolutely thrilled to have you join our amazing community! Get ready for awesome conversations, fun events, and great friendships!\n\n🚀 **Your adventure starts here!**"
            
            preview_embed = discord.Embed(color=embed_color)
            preview_embed.set_image(url=self.user.avatar.url if self.user.avatar else self.user.default_avatar.url)
            
            member_name_section = f"```\n{self.user.display_name}\n```"
            welcome_text = f"**Welcome to {interaction.guild.name.upper()}!**"
            preview_embed.description = f"{welcome_description}\n\n{member_name_section}\n{welcome_text}"
            
            view = ExtendedWelcomePreviewView(self.user, None, None)
            
            await interaction.response.edit_message(
                content=f"🔄 **Default Preview for {self.user.display_name}** (Reset to Default)",
                embed=preview_embed,
                view=view
            )
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error resetting preview: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="Copy Settings", style=discord.ButtonStyle.secondary, emoji="📋", row=1)
    async def copy_settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Copy current settings as text"""
        try:
            settings_text = f"**Welcome Preview Settings:**\n"
            settings_text += f"**Color:** {self.color or '#57F287 (default green)'}\n"
            settings_text += f"**Message:** {self.custom_message or 'Default welcome message'}\n"
            settings_text += f"**User:** {self.user.display_name}\n"
            settings_text += f"**Server:** {interaction.guild.name}\n\n"
            settings_text += f"**Command to recreate:**\n`/previewwelcome user:{self.user.mention}"
            if self.custom_message:
                settings_text += f" message:{self.custom_message}"
            if self.color:
                settings_text += f" color:{self.color}"
            settings_text += "`"
            
            await interaction.response.send_message(settings_text, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error copying settings: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="Export Config", style=discord.ButtonStyle.secondary, emoji="⬇️", row=1)
    async def export_config(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Export settings as JSON config"""
        try:
            import json
            config = {
                "welcome_settings": {
                    "color": self.color or "#57F287",
                    "message": self.custom_message,
                    "server": interaction.guild.name,
                    "server_id": str(interaction.guild.id),
                    "created_by": self.user.display_name,
                    "created_at": discord.utils.utcnow().isoformat()
                }
            }
            
            config_json = json.dumps(config, indent=2)
            await interaction.response.send_message(f"```json\n{config_json}\n```", ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error exporting config: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="Save as Default", style=discord.ButtonStyle.success, emoji="💾", row=2)
    async def save_default(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Save current settings as server default"""
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You need 'Manage Server' permission to save default settings.", ephemeral=True)
            return
        
        try:
            guild_id = str(interaction.guild.id)
            settings = load_welcome_settings()
            
            if guild_id not in settings:
                settings[guild_id] = {}
            
            if self.custom_message:
                settings[guild_id]['message'] = self.custom_message
            
            save_welcome_settings(settings)
            
            await interaction.response.send_message("✅ **Settings saved!** This preview design is now your server's default welcome message.", ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error saving settings: {str(e)}", ephemeral=True)



async def close_poll_after_duration(message, question, option_list, reactions, duration):
    """Close poll after specified duration and show results"""
    await asyncio.sleep(duration * 60)  # Convert to seconds
    try:
        # Fetch updated message
        updated_message = await message.channel.fetch_message(message.id)
        
        # Create results embed
        results_embed = discord.Embed(
            title=f"📊 Poll Results: {question}",
            color=0xe74c3c,
            timestamp=datetime.utcnow()
        )
        
        results_text = ""
        total_votes = 0
        
        # Count total votes
        for i, option in enumerate(option_list):
            reaction_count = 0
            for reaction in updated_message.reactions:
                if str(reaction.emoji) == reactions[i]:
                    reaction_count = reaction.count - 1  # Subtract bot's reaction
                    break
            total_votes += reaction_count
        
        # Generate final results
        for i, option in enumerate(option_list):
            reaction_count = 0
            for reaction in updated_message.reactions:
                if str(reaction.emoji) == reactions[i]:
                    reaction_count = reaction.count - 1
                    break
            
            percentage = (reaction_count / max(total_votes, 1)) * 100
            bar_length = int(percentage / 10)
            bar = "█" * bar_length + "░" * (10 - bar_length)
            
            results_text += f"{reactions[i]} {option}\n"
            results_text += f"    {bar} {reaction_count} votes ({percentage:.1f}%)\n\n"
        
        results_embed.description = results_text
        results_embed.add_field(name="Total Votes", value=str(total_votes), inline=True)
        results_embed.set_footer(text=f"Poll closed after {duration} minutes")
        
        await updated_message.edit(embed=results_embed)
        await updated_message.clear_reactions()
        
    except discord.NotFound:
        pass  # Message was deleted
    except Exception as e:
        print(f"Error closing poll: {e}")

