#!/usr/bin/env python3
"""
Check and optimize Discord slash command count to stay within 100 limit
"""

import ast
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_command_files():
    """Analyze all command files to count slash commands"""
    command_files = [
        'commands.py',
        'utility_commands.py', 
        'entertainment_commands.py',
        'advanced_features.py',
        'extended_commands.py',
        'interactive_timer.py',
        'autolike_commands.py'
    ]
    
    slash_commands = []
    regular_commands = []
    
    for file_path in command_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Count @bot.tree.command decorators (slash commands)
                slash_count = content.count('@bot.tree.command')
                
                # Count @bot.command decorators (regular commands)  
                regular_count = content.count('@bot.command')
                
                slash_commands.append((file_path, slash_count))
                regular_commands.append((file_path, regular_count))
                
                logger.info(f"{file_path}: {slash_count} slash, {regular_count} regular")
                
            except Exception as e:
                logger.error(f"Error analyzing {file_path}: {e}")
    
    total_slash = sum(count for _, count in slash_commands)
    total_regular = sum(count for _, count in regular_commands)
    
    print("="*60)
    print("DISCORD COMMAND ANALYSIS")
    print("="*60)
    print(f"Total Slash Commands: {total_slash}")
    print(f"Total Regular Commands: {total_regular}")
    print(f"Discord Limit: 100 slash commands")
    print(f"Over Limit: {total_slash - 100 if total_slash > 100 else 0}")
    print("="*60)
    
    return slash_commands, regular_commands, total_slash

def create_priority_system():
    """Create priority list of essential vs optional commands"""
    
    essential_commands = [
        # Core bot functionality
        "ping", "help", "info", "uptime", "invite",
        
        # Basic utility  
        "say", "editmsg", "editembed", "delmsg",
        "everyone", "here", "sendfile_everyone", "sendfile_here",
        
        # Welcome system
        "setwelcome", "previewwelcome", "welcome",
        
        # Interactive timer (core feature)
        "itimer", "quicktimer", "timers", "rotationtimer", "turntimer",
        
        # Essential moderation
        "kick", "ban", "mute", "clear", "warn",
        
        # Popular entertainment
        "joke", "quote", "dice", "choose", "poll"
    ]
    
    optional_commands = [
        # Extended entertainment
        "trivia", "wordle", "hangman", "truthordare", "wouldyourather",
        
        # Advanced utilities
        "translate", "qr", "weather", "shorten", "base64", "hash", "password",
        "color", "random", "text", "convert",
        
        # Advanced moderation
        "bulkban", "softban", "automod", "logs", "analytics",
        "rolemenu", "colorroles", "roleall", "rolecreate", "reactrole",
        
        # Server management
        "clone", "setnsfw", "moderation", "feedback", "tag", "premium"
    ]
    
    return essential_commands, optional_commands

def optimize_commands():
    """Create optimized command loading system"""
    essential, optional = create_priority_system()
    
    optimization_code = '''
# Command priority system to stay within 100 slash command limit
ESSENTIAL_SLASH_COMMANDS = {
    # Core functionality (must have)
    "ping", "help", "info", "uptime", "invite",
    
    # Message management
    "say", "editmsg", "editembed", "delmsg", 
    "everyone", "here", "sendfile_everyone", "sendfile_here",
    
    # Welcome system
    "setwelcome", "previewwelcome", "welcome",
    
    # Interactive timer system
    "itimer", "quicktimer", "timers", "rotationtimer", "turntimer",
    
    # Essential moderation
    "kick", "ban", "mute", "clear", "warn", "poll",
    
    # Popular entertainment  
    "joke", "quote", "dice", "choose", "avatar", "serverinfo", "userinfo"
}

def should_register_slash_command(command_name):
    """Check if slash command should be registered based on priority"""
    return command_name.lower() in ESSENTIAL_SLASH_COMMANDS

def register_conditional_slash_command(bot, name, description, callback):
    """Register slash command only if it's in essential list"""
    if should_register_slash_command(name):
        @bot.tree.command(name=name, description=description)
        async def slash_wrapper(interaction):
            await callback(interaction)
        return True
    return False
'''
    
    return optimization_code

if __name__ == "__main__":
    slash_commands, regular_commands, total_slash = analyze_command_files()
    
    if total_slash > 100:
        print(f"\\nNEED TO REDUCE: {total_slash - 100} slash commands")
        print("\\nRECOMMENDED ACTION:")
        print("1. Keep essential commands as slash commands")
        print("2. Convert optional commands to regular commands only")
        print("3. Prioritize core bot functionality")
        
        essential, optional = create_priority_system()
        print(f"\\nEssential commands: {len(essential)}")
        print(f"Optional commands: {len(optional)}")
        
    else:
        print("\\n✅ Within Discord's 100 slash command limit!")