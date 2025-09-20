# Interactive Timer System for Discord Bot
# Advanced timer with buttons, countdowns, and notifications

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import datetime
from datetime import timedelta
import time
import re

# Global storage for active timers
active_timers = {}

class TimerView(discord.ui.View):
    def __init__(self, duration_seconds, label, user_id, rotation_users=None, auto_reset=False):
        super().__init__(timeout=duration_seconds + 60)  # Give extra time for cleanup
        self.duration_seconds = duration_seconds
        self.original_duration = duration_seconds
        self.label = label
        self.user_id = user_id
        self.start_time = time.time()
        self.paused = False
        self.pause_time = 0
        self.total_paused = 0
        self.rotation_users = rotation_users or []
        self.auto_reset = auto_reset
        self.current_turn_index = 0
        
    def disable_next_button_if_needed(self):
        # Disable Next button if no rotation users
        if not self.rotation_users:
            for item in self.children:
                if hasattr(item, 'label') and '⏭️' in item.label:
                    item.disabled = True
        
    @discord.ui.button(label='⏸️ Pause', style=discord.ButtonStyle.secondary)
    async def pause_timer(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Only the timer creator can control this timer!", ephemeral=True)
        
        if not self.paused:
            self.paused = True
            self.pause_time = time.time()
            button.label = '▶️ Resume'
            button.style = discord.ButtonStyle.success
            
            # Update embed to show paused state
            embed = discord.Embed(
                title="⏸️ Timer PAUSED",
                description=f"**{self.label}**\n\nTimer is currently paused.",
                color=0xffa500
            )
            
            elapsed = time.time() - self.start_time - self.total_paused
            remaining = max(0, self.duration_seconds - elapsed)
            
            embed.add_field(name="Time Remaining", value=f"{int(remaining//60):02d}:{int(remaining%60):02d}", inline=True)
            embed.add_field(name="Status", value="⏸️ PAUSED", inline=True)
            embed.set_footer(text=f"Timer by {interaction.user.display_name}")
            
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            self.paused = False
            self.total_paused += time.time() - self.pause_time
            button.label = '⏸️ Pause'
            button.style = discord.ButtonStyle.secondary
            
            await interaction.response.send_message("▶️ Timer resumed!", ephemeral=True)
    
    @discord.ui.button(label='➕ Add Time', style=discord.ButtonStyle.primary)
    async def add_time(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Only the timer creator can control this timer!", ephemeral=True)
        
        # Add 1 minute to the timer
        self.duration_seconds += 60
        await interaction.response.send_message("➕ Added 1 minute to the timer!", ephemeral=True)
    

    
    @discord.ui.button(label='⏭️ Next', style=discord.ButtonStyle.primary)
    async def next_turn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Only the timer creator can control this timer!", ephemeral=True)
        
        # Only available for rotation timers
        if not self.rotation_users:
            return await interaction.response.send_message("❌ Next button is only available for rotation timers!", ephemeral=True)
        
        # Check if we're at the final person
        if self.current_turn_index >= len(self.rotation_users) - 1:
            # Final person - complete the rotation
            embed = discord.Embed(
                title="🏁 Rotation Complete!",
                description=f"**{self.label}**\n\n🎉 All players have completed their turns!",
                color=0x00ff00
            )
            embed.add_field(name="Total Players", value=str(len(self.rotation_users)), inline=True)
            embed.add_field(name="Status", value="✅ COMPLETED", inline=True)
            embed.set_footer(text=f"Rotation completed manually by {interaction.user.display_name}")
            
            # Disable all buttons since rotation is complete
            for item in self.children:
                item.disabled = True
            
            await interaction.response.edit_message(embed=embed, view=self)
            await interaction.followup.send(f"🏁 **{self.label}** rotation is complete! All players have finished their turns.", ephemeral=False)
            return
        
        # Move to next person in rotation
        self.current_turn_index = (self.current_turn_index + 1) % len(self.rotation_users)
        
        # Safety check to prevent array out of bounds
        if self.current_turn_index >= len(self.rotation_users):
            print(f"❌ ERROR: Next button index {self.current_turn_index} exceeds user list length {len(self.rotation_users)}")
            return
            
        next_user_id = self.rotation_users[self.current_turn_index]
        
        try:
            # Get next user
            next_user = interaction.guild.get_member(next_user_id)
            if not next_user:
                return await interaction.response.send_message("❌ Could not find the next user in rotation!", ephemeral=True)
            
            # Reset timer for next person
            self.start_time = time.time()
            self.paused = False
            self.pause_time = 0
            self.total_paused = 0
            self.duration_seconds = self.original_duration
            
            # Reset pause button if it was in resume state
            for item in self.children:
                if hasattr(item, 'label') and '▶️' in item.label:
                    item.label = '⏸️ Pause'
                    item.style = discord.ButtonStyle.secondary
            
            # Update embed for next person's turn
            embed = discord.Embed(
                title="⏭️ Next Turn!",
                description=f"**{self.label}**\n\n🎯 {next_user.mention} you're up next!",
                color=0x2ecc71
            )
            embed.add_field(name="Duration", value=format_duration(self.original_duration), inline=True)
            embed.add_field(name="Turn", value=f"{self.current_turn_index + 1}/{len(self.rotation_users)}", inline=True)
            
            # Show rotation order with current player highlighted
            user_names = []
            for i, uid in enumerate(self.rotation_users):
                user = interaction.guild.get_member(uid)
                if user:
                    if i == self.current_turn_index:
                        user_names.append(f"**→ {user.display_name} ←**")
                    else:
                        user_names.append(user.display_name)
            
            embed.add_field(name="Rotation", value=" → ".join(user_names), inline=False)
            embed.set_footer(text=f"Advanced to next turn by {interaction.user.display_name}")
            
            await interaction.response.edit_message(embed=embed, view=self)
            
            # Notify next user
            await interaction.followup.send(f"⏭️ {next_user.mention} Your turn! Timer has been reset and is counting down.", ephemeral=False)
            
        except Exception as e:
            return await interaction.response.send_message(f"❌ Error advancing to next turn: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label='⏹️ Stop', style=discord.ButtonStyle.danger)
    async def stop_timer(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Only the timer creator can control this timer!", ephemeral=True)
        
        # Stop the timer
        if str(interaction.message.id) in active_timers:
            active_timers[str(interaction.message.id)]['cancelled'] = True
        
        embed = discord.Embed(
            title="⏹️ Timer Stopped",
            description=f"**{self.label}**\n\nTimer has been stopped by the user.",
            color=0xff0000
        )
        embed.set_footer(text=f"Stopped by {interaction.user.display_name}")
        
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)

def parse_duration(duration_str):
    """Parse duration string like '5m', '1h30m', '45s' into seconds"""
    duration_str = duration_str.lower().strip()
    
    # Pattern to match time components
    pattern = r'(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?'
    match = re.match(pattern, duration_str)
    
    if not match:
        # Try simple number (assume minutes)
        try:
            return int(duration_str) * 60
        except:
            return None
    
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    
    total_seconds = hours * 3600 + minutes * 60 + seconds
    return total_seconds if total_seconds > 0 else None

def format_duration(seconds):
    """Format seconds into readable duration"""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds//60)}m {int(seconds%60)}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours}h {minutes}m {secs}s"

async def run_timer(bot, channel, message, duration_seconds, label, user, rotation_users=None, auto_reset=False, role=None, existing_view=None):
    """Run the timer with live updates and rotation support"""
    timer_id = str(message.id)
    active_timers[timer_id] = {'cancelled': False}
    
    # Use existing view if provided, otherwise create new one
    if existing_view:
        view = existing_view
        print(f"🔄 REUSING VIEW: Current turn index {view.current_turn_index}")
    else:
        view = TimerView(duration_seconds, label, user.id, rotation_users, auto_reset)
        print(f"🆕 NEW VIEW: Starting with turn index {view.current_turn_index}")
    original_duration = duration_seconds
    
    try:
        while duration_seconds > 0:
            if active_timers.get(timer_id, {}).get('cancelled'):
                return
            
            # Check if paused
            if view.paused:
                await asyncio.sleep(1)
                continue
            
            # Calculate actual remaining time considering pauses
            elapsed = time.time() - view.start_time - view.total_paused
            remaining = max(0, view.duration_seconds - elapsed)
            
            if remaining <= 0:
                break
            
            # Update embed more frequently for rotation timers to show real-time countdown
            should_update = remaining <= 60 or int(remaining) % 5 == 0
            
            # For rotation timers, update every second to show interactive time
            if rotation_users:
                should_update = True
            
            if should_update:
                progress_percentage = (view.duration_seconds - remaining) / view.duration_seconds
                progress_bars = int(progress_percentage * 20)
                progress_bar = "█" * progress_bars + "░" * (20 - progress_bars)
                
                # Color changes based on remaining time
                if remaining <= 30:
                    color = 0xff0000  # Red
                elif remaining <= 120:
                    color = 0xffa500  # Orange
                else:
                    color = 0x00ff00  # Green
                
                # Special formatting for rotation timers to show current user prominently
                if rotation_users and len(rotation_users) > 0:
                    try:
                        current_user_id = rotation_users[view.current_turn_index]
                        current_user_obj = None
                        
                        # Try to get the current user from the channel's guild
                        if hasattr(channel, 'guild') and channel.guild:
                            current_user_obj = channel.guild.get_member(current_user_id)
                        
                        current_user_name = current_user_obj.display_name if current_user_obj else f"User {current_user_id}"
                        current_user_mention = current_user_obj.mention if current_user_obj else f"<@{current_user_id}>"
                        
                        # Create more prominent display for rotation timer
                        embed = discord.Embed(
                            title="🔄 Rotation Timer - Current Turn",
                            description=f"**{label}**\n\n🎯 **{current_user_mention}'s Turn**\n\n`{progress_bar}`",
                            color=color
                        )
                        
                        # Make time remaining very prominent for current user
                        embed.add_field(
                            name="⏰ Time Left For Current Player", 
                            value=f"# **{int(remaining//60):02d}:{int(remaining%60):02d}**", 
                            inline=False
                        )
                        embed.add_field(
                            name="👥 Rotation Progress", 
                            value=f"Player {view.current_turn_index + 1} of {len(rotation_users)}", 
                            inline=True
                        )
                        embed.add_field(
                            name="⏱️ Turn Duration", 
                            value=format_duration(view.duration_seconds), 
                            inline=True
                        )
                        embed.add_field(
                            name="📊 Status", 
                            value="🔥 ACTIVE" if remaining > 30 else "⚠️ ENDING SOON", 
                            inline=True
                        )
                        
                        embed.set_footer(text=f"Timer by {user.display_name} • {current_user_name} - your time is running!")
                        
                    except (IndexError, ValueError):
                        # Fallback to regular timer display if rotation data is invalid
                        embed = discord.Embed(
                            title="⏱️ Interactive Timer",
                            description=f"**{label}**\n\n`{progress_bar}`",
                            color=color
                        )
                        embed.add_field(
                            name="Time Remaining", 
                            value=f"**{int(remaining//60):02d}:{int(remaining%60):02d}**", 
                            inline=True
                        )
                        embed.set_footer(text=f"Timer by {user.display_name} • Click buttons to control")
                else:
                    # Regular timer display for non-rotation timers
                    embed = discord.Embed(
                        title="⏱️ Interactive Timer",
                        description=f"**{label}**\n\n`{progress_bar}`",
                        color=color
                    )
                    
                    embed.add_field(
                        name="Time Remaining", 
                        value=f"**{int(remaining//60):02d}:{int(remaining%60):02d}**", 
                        inline=True
                    )
                    embed.add_field(
                        name="Total Duration", 
                        value=format_duration(view.duration_seconds), 
                        inline=True
                    )
                    embed.add_field(
                        name="Status", 
                        value="🔥 ACTIVE" if remaining > 30 else "⚠️ ENDING SOON", 
                        inline=True
                    )
                    
                    embed.set_footer(text=f"Timer by {user.display_name} • Click buttons to control")
                
                try:
                    await message.edit(embed=embed, view=view)
                except:
                    pass  # Message might be deleted
            
            await asyncio.sleep(1)
            duration_seconds = remaining - 1
        
        # Timer completed
        if not active_timers.get(timer_id, {}).get('cancelled'):
            # Handle rotation and auto-reset
            if view.rotation_users and view.auto_reset:
                # DEBUG: Add logging to understand the issue
                current_user = view.rotation_users[view.current_turn_index] if view.current_turn_index < len(view.rotation_users) else "INVALID"
                print(f"🔍 ROTATION DEBUG: User {current_user} (index {view.current_turn_index}) completed. Total users: {len(view.rotation_users)}")
                
                # Check if we've reached the final person (index == last index)
                if view.current_turn_index >= len(view.rotation_users) - 1:
                    # Final person completed - stop the rotation
                    print(f"🏁 ROTATION COMPLETE: Final user at index {view.current_turn_index} finished")
                    embed = discord.Embed(
                        title="🏁 Rotation Complete!",
                        description=f"**{label}**\n\n🎉 All players have completed their turns!",
                        color=0x00ff00
                    )
                    embed.add_field(name="Total Players", value=str(len(view.rotation_users)), inline=True)
                    embed.add_field(name="Status", value="✅ COMPLETED", inline=True)
                    embed.set_footer(text=f"Rotation finished - all {len(view.rotation_users)} players completed")
                    
                    # Disable all buttons since rotation is complete
                    for item in view.children:
                        item.disabled = True
                    
                    try:
                        await message.edit(embed=embed, view=view)
                        # Send final notification
                        final_message = f"🏁 **{label}** rotation is complete! All players have finished their turns."
                        if role:
                            final_message = f"{role.mention} {final_message}"
                        await channel.send(final_message)
                    except:
                        pass
                    return
                
                # Move to next person in rotation (only if not at final person)
                view.current_turn_index += 1
                
                # Safety check to prevent array out of bounds
                if view.current_turn_index >= len(view.rotation_users):
                    print(f"❌ ERROR: Index {view.current_turn_index} exceeds user list length {len(view.rotation_users)}")
                    return
                
                next_user_id = view.rotation_users[view.current_turn_index]
                print(f"➡️ ROTATION ADVANCE: Moving to user {next_user_id} at index {view.current_turn_index}")
                
                try:
                    next_user = bot.get_user(next_user_id) or await bot.fetch_user(next_user_id)
                    if next_user:
                        # Auto-reset for next person
                        view.start_time = time.time()
                        view.paused = False
                        view.pause_time = 0
                        view.total_paused = 0
                        view.duration_seconds = original_duration
                        
                        # Update embed for next person's turn
                        embed = discord.Embed(
                            title="🔄 Next Turn!",
                            description=f"**{label}**\n\n🎯 {next_user.mention} it's your turn!",
                            color=0x3498db
                        )
                        embed.add_field(name="Duration", value=format_duration(original_duration), inline=True)
                        embed.add_field(name="Turn", value=f"{view.current_turn_index + 1}/{len(view.rotation_users)}", inline=True)
                        embed.set_footer(text=f"Timer rotating to {next_user.display_name}")
                        
                        try:
                            await message.edit(embed=embed, view=view)
                            # Send notification with mention
                            await channel.send(f"🎯 {next_user.mention} Your turn is starting! Timer has been reset.")
                        except:
                            pass
                        
                        # Continue timer for next person - pass the updated view to maintain state
                        bot.loop.create_task(run_timer(
                            bot, channel, message, original_duration, label, user, 
                            view.rotation_users, view.auto_reset, role, existing_view=view
                        ))
                        return
                except:
                    pass
            
            # Standard timer completion (no rotation or rotation failed)
            embed = discord.Embed(
                title="⏰ Timer Complete!",
                description=f"**{label}**\n\n🎉 Your timer has finished!",
                color=0x00ff00
            )
            embed.add_field(name="Duration", value=format_duration(view.duration_seconds), inline=True)
            embed.set_footer(text=f"Timer completed for {user.display_name}")
            
            # Disable all buttons if not auto-rotating
            if not (view.rotation_users and view.auto_reset):
                for item in view.children:
                    item.disabled = True
            
            try:
                await message.edit(embed=embed, view=view)
                # Send notification
                notification_message = f"⏰ {user.mention} Your timer **{label}** has finished!"
                if role:
                    notification_message = f"{role.mention} {notification_message}"
                await channel.send(notification_message)
            except:
                pass
    
    finally:
        # Clean up
        if timer_id in active_timers:
            del active_timers[timer_id]

def setup_interactive_timer(bot):
    """Setup the interactive timer command"""
    
    @bot.tree.command(name="itimer", description="Start an interactive countdown timer")
    @app_commands.describe(
        duration="Timer duration (e.g., '5m', '1h30m', '45s')",
        label="Optional label for the timer"
    )
    async def interactive_timer(interaction: discord.Interaction, duration: str, label: str = "Timer"):
        """Start an interactive countdown timer with controls"""
        
        # Parse duration
        duration_seconds = parse_duration(duration)
        if not duration_seconds:
            return await interaction.response.send_message(
                "❌ Invalid duration format! Use formats like: `5m`, `1h30m`, `45s`, or just `10` (minutes)", 
                ephemeral=True
            )
        
        if duration_seconds > 86400:  # 24 hours
            return await interaction.response.send_message(
                "❌ Timer duration cannot exceed 24 hours!", 
                ephemeral=True
            )
        
        if duration_seconds < 5:
            return await interaction.response.send_message(
                "❌ Timer duration must be at least 5 seconds!", 
                ephemeral=True
            )
        
        # Create initial embed
        embed = discord.Embed(
            title="⏱️ Interactive Timer Starting...",
            description=f"**{label}**\n\nPreparing your timer...",
            color=0x3498db
        )
        embed.add_field(name="Duration", value=format_duration(duration_seconds), inline=True)
        embed.set_footer(text=f"Timer by {interaction.user.display_name}")
        
        view = TimerView(duration_seconds, label, interaction.user.id)
        view.disable_next_button_if_needed()  # Disable Next button for single timers
        await interaction.response.send_message(embed=embed, view=view)
        
        # Get the message and start the timer
        message = await interaction.original_response()
        
        # Start the timer in background
        bot.loop.create_task(run_timer(
            bot, interaction.channel, message, duration_seconds, label, interaction.user
        ))
    
    @bot.tree.command(name="quicktimer", description="Quick timer presets")
    @app_commands.describe(preset="Quick timer preset")
    @app_commands.choices(preset=[
        app_commands.Choice(name="5 minutes", value="5m"),
        app_commands.Choice(name="10 minutes", value="10m"),
        app_commands.Choice(name="15 minutes", value="15m"),
        app_commands.Choice(name="30 minutes", value="30m"),
        app_commands.Choice(name="1 hour", value="1h"),
        app_commands.Choice(name="Pomodoro (25m)", value="25m"),
        app_commands.Choice(name="Short break (5m)", value="5m"),
        app_commands.Choice(name="Long break (15m)", value="15m")
    ])
    async def quick_timer(interaction: discord.Interaction, preset: str):
        """Start a quick timer with common presets"""
        
        preset_labels = {
            "5m": "5 Minute Timer",
            "10m": "10 Minute Timer", 
            "15m": "15 Minute Timer",
            "30m": "30 Minute Timer",
            "1h": "1 Hour Timer",
            "25m": "Pomodoro Session"
        }
        
        duration_seconds = parse_duration(preset)
        label = preset_labels.get(preset, f"{preset} Timer")
        
        # Create initial embed
        embed = discord.Embed(
            title="⚡ Quick Timer Starting...",
            description=f"**{label}**\n\nStarting your quick timer...",
            color=0xe74c3c
        )
        embed.add_field(name="Duration", value=format_duration(duration_seconds), inline=True)
        embed.set_footer(text=f"Quick timer by {interaction.user.display_name}")
        
        view = TimerView(duration_seconds, label, interaction.user.id)
        view.disable_next_button_if_needed()  # Disable Next button for single timers
        await interaction.response.send_message(embed=embed, view=view)
        
        # Get the message and start the timer
        message = await interaction.original_response()
        
        # Start the timer in background
        bot.loop.create_task(run_timer(
            bot, interaction.channel, message, duration_seconds, label, interaction.user
        ))
    
    @bot.tree.command(name="timers", description="View all active timers")
    async def list_timers(interaction: discord.Interaction):
        """List all active timers in the server"""
        
        if not active_timers:
            embed = discord.Embed(
                title="⏱️ Active Timers",
                description="No active timers running.",
                color=0x95a5a6
            )
            return await interaction.response.send_message(embed=embed)
        
        embed = discord.Embed(
            title="⏱️ Active Timers",
            description=f"Currently running **{len(active_timers)}** timer(s)",
            color=0x3498db
        )
        
        count = 0
        for timer_id, timer_data in list(active_timers.items()):
            count += 1
            if count > 10:  # Limit to 10 timers shown
                embed.set_footer(text=f"... and {len(active_timers) - 10} more")
                break
            
            embed.add_field(
                name=f"Timer #{count}",
                value=f"ID: {timer_id[:8]}...\nStatus: {'⏸️ Paused' if timer_data.get('paused') else '🔥 Running'}",
                inline=True
            )
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="rotationtimer", description="Create a rotating timer that tags the next person")
    @app_commands.describe(
        duration="Timer duration (e.g., '5m', '1h30m', '45s')",
        users="Users to rotate between (mention them: @user1 @user2 @user3)",
        label="Optional label for the timer",
        role="Optional role to ping when timer completes"
    )
    async def rotation_timer(interaction: discord.Interaction, duration: str, users: str, label: str = "Turn Timer", role: discord.Role = None):
        """Create a rotating timer that automatically tags the next person and resets"""
        
        # Parse duration
        duration_seconds = parse_duration(duration)
        if not duration_seconds:
            return await interaction.response.send_message(
                "❌ Invalid duration format! Use formats like: `5m`, `1h30m`, `45s`, or just `10` (minutes)", 
                ephemeral=True
            )
        
        if duration_seconds > 3600:  # 1 hour max for rotation timers
            return await interaction.response.send_message(
                "❌ Rotation timer duration cannot exceed 1 hour!", 
                ephemeral=True
            )
        
        if duration_seconds < 10:
            return await interaction.response.send_message(
                "❌ Rotation timer duration must be at least 10 seconds!", 
                ephemeral=True
            )
        
        # Parse user mentions
        import re
        user_mentions = re.findall(r'<@!?(\d+)>', users)
        
        if len(user_mentions) < 2:
            return await interaction.response.send_message(
                "❌ You need at least 2 users for rotation! Mention them like: @user1 @user2 @user3", 
                ephemeral=True
            )
        
        # Optional warning for very large rotations
        if len(user_mentions) > 50:
            await interaction.response.send_message(
                f"⚠️ Large rotation detected ({len(user_mentions)} users)! This may take a while to complete.",
                ephemeral=True
            )
        
        # Convert to integers and validate users exist
        rotation_user_ids = []
        user_names = []
        
        for user_id_str in user_mentions:
            try:
                user_id = int(user_id_str)
                user = interaction.guild.get_member(user_id)
                if user:
                    rotation_user_ids.append(user_id)
                    user_names.append(user.display_name)
                else:
                    return await interaction.response.send_message(
                        f"❌ Could not find user with ID {user_id} in this server!", 
                        ephemeral=True
                    )
            except ValueError:
                continue
        
        if len(rotation_user_ids) < 2:
            return await interaction.response.send_message(
                "❌ Could not find enough valid users for rotation!", 
                ephemeral=True
            )
        
        # Create initial embed
        first_user = interaction.guild.get_member(rotation_user_ids[0])
        embed = discord.Embed(
            title="🔄 Rotation Timer Starting...",
            description=f"**{label}**\n\n🎯 {first_user.mention} you're up first!",
            color=0xe74c3c
        )
        embed.add_field(name="Duration", value=format_duration(duration_seconds), inline=True)
        embed.add_field(name="Turn", value=f"1/{len(rotation_user_ids)}", inline=True)
        embed.add_field(name="Rotation", value=" → ".join(user_names), inline=False)
        embed.set_footer(text=f"Rotation timer by {interaction.user.display_name}")
        
        view = TimerView(duration_seconds, label, interaction.user.id, rotation_user_ids, True)
        await interaction.response.send_message(embed=embed, view=view)
        
        # Get the message and start the timer
        message = await interaction.original_response()
        
        # Notify first user
        await interaction.followup.send(f"🎯 {first_user.mention} Your turn is starting!", ephemeral=False)
        
        # Start the rotation timer
        bot.loop.create_task(run_timer(
            bot, interaction.channel, message, duration_seconds, label, interaction.user, 
            rotation_user_ids, True
        ))
    
    @bot.tree.command(name="turntimer", description="Quick turn-based timer for games and activities")
    @app_commands.describe(
        preset="Quick timer preset",
        users="Users to rotate between (mention them: @user1 @user2)"
    )
    @app_commands.choices(preset=[
        app_commands.Choice(name="30 seconds", value="30s"),
        app_commands.Choice(name="1 minute", value="1m"),
        app_commands.Choice(name="2 minutes", value="2m"),
        app_commands.Choice(name="3 minutes", value="3m"),
        app_commands.Choice(name="5 minutes", value="5m"),
        app_commands.Choice(name="Game turn (45s)", value="45s"),
        app_commands.Choice(name="Speaking turn (2m)", value="2m"),
        app_commands.Choice(name="Presentation (5m)", value="5m")
    ])
    async def turn_timer(interaction: discord.Interaction, preset: str, users: str):
        """Quick turn-based timer with common presets"""
        
        duration_seconds = parse_duration(preset)
        
        # Parse user mentions
        import re
        user_mentions = re.findall(r'<@!?(\d+)>', users)
        
        if len(user_mentions) < 2:
            return await interaction.response.send_message(
                "❌ You need at least 2 users for turns! Mention them like: @user1 @user2", 
                ephemeral=True
            )
        
        rotation_user_ids = [int(uid) for uid in user_mentions]  # No limit on users
        user_names = []
        
        for user_id in rotation_user_ids:
            user = interaction.guild.get_member(user_id)
            if user:
                user_names.append(user.display_name)
        
        preset_labels = {
            "30s": "Quick Turn",
            "1m": "1 Minute Turn", 
            "2m": "2 Minute Turn",
            "3m": "3 Minute Turn",
            "5m": "5 Minute Turn",
            "45s": "Game Turn"
        }
        
        label = preset_labels.get(preset, f"{preset} Turn")
        first_user = interaction.guild.get_member(rotation_user_ids[0])
        
        # Create initial embed
        embed = discord.Embed(
            title="⚡ Turn Timer Starting...",
            description=f"**{label}**\n\n🎯 {first_user.mention} you're up!",
            color=0x9b59b6
        )
        embed.add_field(name="Duration", value=format_duration(duration_seconds), inline=True)
        embed.add_field(name="Players", value=f"{len(rotation_user_ids)} players", inline=True)
        embed.add_field(name="Order", value=" → ".join(user_names), inline=False)
        embed.set_footer(text=f"Turn timer by {interaction.user.display_name}")
        
        view = TimerView(duration_seconds, label, interaction.user.id, rotation_user_ids, True)
        await interaction.response.send_message(embed=embed, view=view)
        
        # Get the message and start the timer
        message = await interaction.original_response()
        
        # Start the turn timer
        bot.loop.create_task(run_timer(
            bot, interaction.channel, message, duration_seconds, label, interaction.user, 
            rotation_user_ids, True, role
        ))
    
    print("✅ Interactive timer system loaded successfully!")