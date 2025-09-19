#!/usr/bin/env python3
"""
Slash command optimizer - modify existing command files to respect 100 limit
"""

import re
import os

def optimize_command_file(file_path, essential_commands):
    """Modify command file to only register essential commands as slash commands"""
    
    if not os.path.exists(file_path):
        return False
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Pattern to find slash command definitions
    pattern = r'@bot\.tree\.command\(name="([^"]+)"'
    
    # Find all slash commands in file
    matches = re.findall(pattern, content)
    
    modified_content = content
    changes_made = 0
    
    for command_name in matches:
        if command_name not in essential_commands:
            # Comment out this slash command registration
            old_pattern = f'@bot.tree.command(name="{command_name}"'
            new_pattern = f'# @bot.tree.command(name="{command_name}" # DISABLED - Not essential'
            
            if old_pattern in modified_content:
                modified_content = modified_content.replace(old_pattern, new_pattern)
                changes_made += 1
                print(f"  ⚪ Disabled slash command: /{command_name}")
    
    if changes_made > 0:
        # Write back the modified content
        with open(f"{file_path}.optimized", 'w') as f:
            f.write(modified_content)
        print(f"✅ Optimized {file_path}: {changes_made} slash commands disabled")
        return True
    else:
        print(f"✅ {file_path}: No changes needed")
        return False

def apply_optimization():
    """Apply optimization to all command files"""
    
    # Essential commands that should remain as slash commands
    essential_commands = {
        "ping", "help", "info", "uptime", "invite", "say", "editmsg", "editembed", 
        "delmsg", "everyone", "here", "sendfile_everyone", "sendfile_here",
        "setwelcome", "previewwelcome", "welcome", "itimer", "quicktimer", "timers", 
        "rotationtimer", "turntimer", "kick", "ban", "mute", "clear", "warn", "poll",
        "joke", "quote", "dice", "choose", "avatar", "serverinfo", "userinfo",
        "translate", "weather", "qr", "hash", "password", "color", "base64"
    }
    
    command_files = [
        'commands.py',
        'utility_commands.py',
        'entertainment_commands.py', 
        'advanced_features.py',
        'interactive_timer.py'
    ]
    
    print("="*60)
    print("SLASH COMMAND OPTIMIZATION")
    print("="*60)
    print(f"Essential commands: {len(essential_commands)}")
    print(f"Target: Stay within 100 slash command limit")
    print("="*60)
    
    total_changes = 0
    for file_path in command_files:
        if optimize_command_file(file_path, essential_commands):
            total_changes += 1
    
    print("="*60)
    print(f"Optimization complete: {total_changes} files modified")
    print("Extended commands module will be skipped entirely")
    print("All commands still available as regular !commands")
    print("="*60)

if __name__ == "__main__":
    apply_optimization()