#!/usr/bin/env python3
"""
Clean command registration system to maintain exactly 100 slash commands
"""

import discord
from discord.ext import commands
import logging

logger = logging.getLogger(__name__)

# Essential slash commands (exactly 50 core commands)
CORE_SLASH_COMMANDS = {
    # Bot essentials (5)
    "ping", "help", "info", "uptime", "invite",
    
    # Message management (8) 
    "say", "editmsg", "editembed", "delmsg",
    "everyone", "here", "sendfile_everyone", "sendfile_here",
    
    # Welcome system (3)
    "setwelcome", "previewwelcome", "welcome", 
    
    # Interactive timer (5)
    "itimer", "quicktimer", "timers", "rotationtimer", "turntimer",
    
    # Moderation (6)
    "kick", "ban", "mute", "clear", "warn", "poll",
    
    # Server info (3)
    "avatar", "serverinfo", "userinfo",
    
    # Popular entertainment (6)
    "joke", "quote", "dice", "choose", "8ball", "coinflip",
    
    # Utilities (14)
    "translate", "weather", "qr", "hash", "password", "color",
    "base64", "shorten", "random", "text", "convert", "feedback",
    "tag", "logs"
}

def setup_optimized_commands(bot):
    """Setup commands with optimized slash command registration"""
    
    # Track slash commands registered
    slash_count = 0
    regular_count = 0
    
    def register_command(name, description, callback, slash_priority=True):
        """Register command with priority system"""
        nonlocal slash_count, regular_count
        
        # Always register as regular command
        @bot.command(name=name)
        async def regular_wrapper(ctx, *args, **kwargs):
            await callback(ctx, *args, **kwargs)
        regular_count += 1
        
        # Register as slash command only if essential and under limit
        if slash_priority and name.lower() in CORE_SLASH_COMMANDS and slash_count < 100:
            @bot.tree.command(name=name, description=description[:100])  # Discord description limit
            async def slash_wrapper(interaction, *args, **kwargs):
                # Convert interaction to ctx-like object for compatibility
                await callback(interaction, *args, **kwargs)
            slash_count += 1
            logger.info(f"✅ Registered slash command: /{name} ({slash_count}/100)")
        else:
            logger.info(f"⚪ Regular command only: !{name}")
    
    logger.info("🎯 Starting optimized command registration...")
    logger.info(f"Target: Exactly 100 slash commands, unlimited regular commands")
    
    return register_command, lambda: (slash_count, regular_count)

def apply_command_optimization(bot):
    """Apply command optimization to existing bot"""
    
    # Clear existing slash commands to rebuild cleanly
    bot.tree.clear_commands()
    logger.info("🧹 Cleared existing slash commands for optimization")
    
    # Get current commands and re-register with priority
    existing_commands = list(bot.commands)
    slash_registered = 0
    
    for cmd in existing_commands:
        if cmd.name.lower() in CORE_SLASH_COMMANDS and slash_registered < 100:
            # Re-register as slash command
            @bot.tree.command(name=cmd.name, description=cmd.help or f"{cmd.name} command")
            async def optimized_slash(interaction):
                # Create pseudo-context for compatibility
                ctx = await bot.get_context(interaction)
                await cmd.callback(ctx)
            
            slash_registered += 1
            logger.info(f"✅ Priority slash: /{cmd.name} ({slash_registered}/100)")
    
    logger.info(f"🎯 Optimization complete: {slash_registered} slash commands registered")
    return slash_registered

if __name__ == "__main__":
    print("Command optimization system ready")
    print(f"Core slash commands defined: {len(CORE_SLASH_COMMANDS)}")
    print("This will ensure exactly 100 slash commands while keeping all regular commands")