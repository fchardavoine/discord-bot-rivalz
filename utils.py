import discord
from discord.ext import commands
import logging

logger = logging.getLogger(__name__)

def get_prefix(bot, message):
    """Get command prefix for the bot"""
    # You can customize prefixes per server here
    # For now, using a simple static prefix
    prefixes = ['!', '?', '.']
    
    # Allow bot to be mentioned as prefix
    return commands.when_mentioned_or(*prefixes)(bot, message)

def format_time(seconds):
    """Format seconds into a readable time string"""
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes:.0f} minutes"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours:.0f} hours {minutes:.0f} minutes"

def create_error_embed(title, description, color=0xff0000):
    """Create a standardized error embed"""
    embed = discord.Embed(
        title=f"❌ {title}",
        description=description,
        color=color
    )
    return embed

def create_success_embed(title, description, color=0x00ff00):
    """Create a standardized success embed"""
    embed = discord.Embed(
        title=f"✅ {title}",
        description=description,
        color=color
    )
    return embed

def create_info_embed(title, description, color=0x0099ff):
    """Create a standardized info embed"""
    embed = discord.Embed(
        title=f"ℹ️ {title}",
        description=description,
        color=color
    )
    return embed

def is_owner():
    """Check if user is bot owner (decorator)"""
    async def predicate(ctx):
        return await ctx.bot.is_owner(ctx.author)
    return commands.check(predicate)

def log_command_usage(ctx):
    """Log command usage for analytics"""
    logger.info(f"Command '{ctx.command}' used by {ctx.author} ({ctx.author.id}) in {ctx.guild.name if ctx.guild else 'DM'}")

# Cooldown decorators for common use cases
def cooldown_per_user(rate, per):
    """Cooldown per user"""
    return commands.cooldown(rate, per, commands.BucketType.user)

def cooldown_per_guild(rate, per):
    """Cooldown per guild"""
    return commands.cooldown(rate, per, commands.BucketType.guild)

def cooldown_per_channel(rate, per):
    """Cooldown per channel"""
    return commands.cooldown(rate, per, commands.BucketType.channel)
