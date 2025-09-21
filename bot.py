import discord
from discord.ext import commands
import logging
import asyncio
from commands import setup_commands
from utils import get_prefix
import json
import os

# Import custom welcome image generator
from welcome_image_generator import WelcomeImageGenerator

# Import database and new feature modules
from db_app import init_database

# Import bot_status from main module to update connection status
try:
    from main import bot_status
except ImportError:
    # Fallback if running directly
    bot_status = {
        'connected': False,
        'guilds': 0,
        'commands': 0
    }

# Set up logging
logger = logging.getLogger(__name__)

class DiscordBot(commands.Bot):
    """Main Discord bot class"""
    
    def __init__(self):
        # Use standard intents with message content enabled
        intents = discord.Intents.default()
        intents.message_content = True  # Required for command processing
        intents.members = True  # Required for member events
        intents.guilds = True   # Required for guild events
        logger.info("✅ Standard intents enabled with message content")
        
        # Initialize the bot with command prefix and intents
        super().__init__(
            command_prefix=get_prefix,
            intents=intents,
            help_command=commands.DefaultHelpCommand(),
            case_insensitive=True
        )
        
        # Setup all command modules
        setup_commands(self)
        
        # Setup robust poll system
        from robust_poll_system import setup_robust_polls
        setup_robust_polls(self)
        
        # Enhanced command priority system with all new features
        self.essential_slash_commands = {
            # Core bot functions
            "ping", "help", "info", "uptime", "invite", "message", "editmsg", "editembed", 
            "delmsg", "everyone", "here", "sendfile_everyone", "sendfile_here",
            "setwelcome", "previewwelcome", "welcome", "itimer", "quicktimer", "timers", 
            "rotationtimer", "turntimer", "kick", "ban", "mute", "clear", "warn", "poll",
            "joke", "quote", "dice", "choose", "avatar", "serverinfo", "userinfo",
            "translate", "weather", "qr", "hash", "password", "color", "twitch",
            
            # Economy system
            "balance", "daily", "leaderboard", "blackjack", "slots", "give",
            
            # Community features  
            "suggest", "suggestions", "ticket", "tickets", "event", "events", "birthday", "birthdays",
            
            # Social features
            "marry", "divorce", "befriend", "adopt", "relationships", "hug", "pat",
            
            # Utility enhancements
            "analytics", "tagcreate", "tagshow", "taglist", "remind", "reminders",
            
            # Fun features
            "meme", "filter", "fact", "dadjoke", "compliment", "roast", "inspire", "riddle",
            
            # Music features
            "join", "leave", "play", "queue", "skip", "pause", "resume", "stop", "loop", "shuffle", "soundboard"
        }
        
        # Initialize database first
        logger.info("🗄️ Initializing database...")
        if init_database():
            logger.info("✅ Database initialized successfully!")
        else:
            logger.error("❌ Database initialization failed!")
        
        # Initialize custom welcome image generator
        self.welcome_image_generator = WelcomeImageGenerator()
        
        # Load all command modules with priority system
        try:
            # Import all feature modules
            from advanced_features import setup_advanced_features
            from utility_commands import setup_utility_commands
            from entertainment_commands import setup_entertainment_commands
            from interactive_timer import setup_interactive_timer
            from autolike_commands import setup_autolike_commands
            
            # Import new enhanced feature modules
            from utility_enhancements import setup_utility_enhancements
            from economy_system import setup_economy_system
            from community_features import setup_community_features
            from social_moderation import setup_social_moderation
            from fun_image_features import setup_fun_image_features
            from music_features import setup_music_features
            from twitch_notifications import setup_twitch_notifications
            
            # Setup core command modules only (prioritizing Twitch functionality)
            setup_interactive_timer(self)
            setup_utility_commands(self)
            setup_advanced_features(self)
            # setup_twitch_notifications(self) - moved to setup_hook after command clearing
            
            # Temporarily disabled to prioritize Twitch commands:
            # setup_entertainment_commands(self)
            # setup_autolike_commands(self)
            # setup_utility_enhancements(self)
            # setup_economy_system(self)
            # Temporarily disabled to make room for Twitch commands:
            # setup_community_features(self)
            # setup_social_moderation(self)
            # setup_fun_image_features(self)
            # setup_music_features(self)
            
            logger.info("✅ All command modules loaded successfully!")
            logger.info(f"✅ Enhanced bot with {len(self.essential_slash_commands)} prioritized slash commands")
        except Exception as e:
            logger.error(f"Failed to load command modules: {e}")
        
        # Load welcome settings from file
        self.load_welcome_settings()
        
        # Load goodbye settings from file
        self.load_goodbye_settings()
        
        # Load auto-like settings from file
        self.load_autolike_settings()
        
        # Track bot start time for uptime command
        self.start_time = None
    
    async def setup_hook(self):
        """Called when the bot is starting up to setup commands"""
        logger.info("🔧 Setting up bot commands...")
        
        # Only register commands here (clearing happens in on_ready when guilds are available)
        from twitch_notifications import setup_twitch_notifications
        setup_twitch_notifications(self)
        logger.info("✅ Registered /twitch command group")
        
        logger.info("✅ Bot command setup complete")
        
        # Connection reliability tracking
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 100
        self.reconnect_delay = 5
        self.last_heartbeat = None
        
        # Enhanced connection stability
        self.connection_health = {
            'last_seen': None,
            'connection_count': 0,
            'disconnect_count': 0
        }
        
    def should_register_slash_command(self, command_name):
        """Check if command should be registered as slash command"""
        return command_name.lower() in self.essential_slash_commands
    
    async def ensure_stable_presence(self):
        """Simplified presence setting for stability"""
        try:
            await self.change_presence(
                status=discord.Status.online,
                activity=discord.Game(name="🤖 Ready | !ping")
            )
            logger.info("✅ Bot presence set to online")
        except Exception as e:
            logger.error(f"Failed to set presence: {e}")

    async def on_ready(self):
        """Called when the bot is ready and connected to Discord"""
        if not self.start_time:  # Only set on first ready event
            from datetime import datetime
            self.start_time = datetime.utcnow()
        
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guilds')
        
        # Update global status for web interface
        bot_status['connected'] = True
        bot_status['guilds'] = len(self.guilds)
        
        # Set stable online presence
        await self.ensure_stable_presence()
        
        # ONE-TIME MIGRATION: Clear guild-specific commands (now that self.guilds is populated)
        if not getattr(self, '_command_migration_complete', False):
            logger.info("🧹 Starting one-time command migration...")
            
            # Clear guild-specific commands for each guild
            for guild in self.guilds:
                try:
                    self.tree.clear_commands(guild=guild)
                    await self.tree.sync(guild=guild)
                    logger.info(f"🧹 Cleared guild commands for: {guild.name}")
                    await asyncio.sleep(1)  # Throttle to avoid rate limits
                except Exception as e:
                    logger.error(f"❌ Failed to clear guild commands for {guild.name}: {e}")
            
            # Sync global commands (Discord will automatically update/remove stale commands)
            try:
                global_synced = await self.tree.sync()
                logger.info(f"✅ Migration - Global sync: {len(global_synced)} commands")
            except Exception as e:
                logger.error(f"❌ Migration - Failed to sync global commands: {e}")
            
            # Sync commands to each guild
            for guild in self.guilds:
                try:
                    guild_synced = await self.tree.sync(guild=guild)
                    logger.info(f"✅ Migration - Guild sync for {guild.name}: {len(guild_synced)} commands")
                    await asyncio.sleep(1)  # Throttle to avoid rate limits
                except Exception as e:
                    logger.error(f"❌ Migration - Failed to sync to guild {guild.name}: {e}")
            
            self._command_migration_complete = True
            logger.info("✅ Command migration complete")
        
        # Set bot status to online and active with retry logic
        for attempt in range(3):
            try:
                await self.change_presence(
                    status=discord.Status.online,
                    activity=discord.Game(name="🤖 ONLINE | !help or !ping")
                )
                logger.info(f"✅ Bot status set to ONLINE (attempt {attempt + 1})")
                break
            except Exception as e:
                logger.warning(f"Failed to set bot status (attempt {attempt + 1}): {e}")
                if attempt < 2:
                    await asyncio.sleep(2)
                else:
                    logger.error("Failed to set status after 3 attempts")
        
        # Commands are now synced via migration above (no redundant sync needed)
        
        # Start aggressive heartbeat task to maintain connection
        if not hasattr(self, 'heartbeat_task'):
            self.heartbeat_task = self.loop.create_task(self.heartbeat_loop())
            logger.info("✅ AGGRESSIVE heartbeat system started")
        
        # Force activity update every 30 seconds
        if not hasattr(self, 'activity_task'):
            self.activity_task = self.loop.create_task(self.activity_loop())
            logger.info("✅ Activity refresh system started")
        
        # Update bot status
        try:
            from keep_alive import update_bot_status
            update_bot_status('connected', len(self.guilds))
        except ImportError:
            pass  # Keep-alive module might not be available in all contexts
        
        # Log all available slash commands for debugging (commands already synced in setup_hook)
        try:
            top_level_commands = []
            grouped_commands = []
            
            for command in self.tree.walk_commands():
                if command.parent is None:
                    # This is a true top-level command
                    top_level_commands.append(f"/{command.name}")
                else:
                    # This is a subcommand within a group
                    grouped_commands.append(f"/{command.qualified_name}")
            
            logger.info(f"🔝 Top-level commands ({len(top_level_commands)}): {', '.join(top_level_commands)}")
            if grouped_commands:
                logger.info(f"🏗️ Grouped subcommands ({len(grouped_commands)}): {', '.join(grouped_commands)}")
                
        except Exception as e:
            logger.error(f"Failed to list slash commands: {e}")
        
        # Set bot status
        activity = discord.Game(name="!help or /help for commands")
        await self.change_presence(status=discord.Status.online, activity=activity)
        
        # Log guild information and total commands count
        for guild in self.guilds:
            logger.info(f'🏠 Connected to guild: {guild.name} (ID: {guild.id}) - {guild.member_count} members')
        
        # Update command count in status
        total_commands = len(self.commands) + len(self.tree.get_commands())
        bot_status['commands'] = total_commands
        logger.info(f"🎯 {total_commands} COMMANDS LOADED AND ACTIVE")
        
        # Force final status update
        try:
            await self.change_presence(
                status=discord.Status.online,
                activity=discord.Game(name="🚀 FULLY OPERATIONAL | !ping")
            )
            logger.info("🚀 FINAL STATUS: BOT IS FULLY OPERATIONAL AND VISIBLE")
        except Exception as e:
            logger.error(f"Final status update failed: {e}")
        
        # Log heartbeat status
        from datetime import datetime
        self.last_heartbeat = datetime.utcnow()
        logger.info(f"💚 BOT READY - Connection established at {self.last_heartbeat}")
        
        # Log success message
        logger.info("="*60)
        logger.info("🎉 DISCORD BOT IS NOW LIVE AND RESPONDING TO COMMANDS")
        logger.info("🔥 Bot should now appear ONLINE in Discord")
        logger.info("🏓 Test with: !ping or !help")
        logger.info("="*60)
    
    async def on_disconnect(self):
        """Handle bot disconnection"""
        logger.warning("🔴 Bot disconnected from Discord!")
        bot_status['connected'] = False
        self.reconnect_attempts += 1
        
        if self.reconnect_attempts <= self.max_reconnect_attempts:
            logger.info(f"Attempting reconnection ({self.reconnect_attempts}/{self.max_reconnect_attempts})...")
        else:
            logger.error("Max reconnection attempts reached!")

    async def on_resumed(self):
        """Handle bot reconnection"""
        logger.info("🟢 Bot reconnected to Discord!")
        bot_status['connected'] = True
        self.reconnect_attempts = 0  # Reset counter on successful reconnection
        
        from datetime import datetime
        self.last_heartbeat = datetime.utcnow()
        logger.info(f"✅ Connection restored - heartbeat: {self.last_heartbeat}")

    async def heartbeat_loop(self):
        """Maintain connection with periodic heartbeat"""
        await self.wait_until_ready()
        
        while not self.is_closed():
            try:
                from datetime import datetime
                self.last_heartbeat = datetime.utcnow()
                
                # Update health monitoring status for external monitoring
                try:
                    # Import from main module's globals if available
                    import sys
                    if 'main' in sys.modules:
                        main_module = sys.modules['main']
                        if hasattr(main_module, 'bot_status'):
                            from datetime import datetime
                            # Direct update to bot_status
                            main_module.bot_status['status'] = 'connected'
                            main_module.bot_status['guilds'] = len(self.guilds)
                            main_module.bot_status['discord_connected'] = True
                            main_module.bot_status['last_check'] = datetime.utcnow().isoformat()
                            main_module.bot_status['last_heartbeat'] = datetime.utcnow().isoformat()
                except Exception as e:
                    # Fallback - direct update without logging
                    pass
                
                # Log status every 5 minutes
                if hasattr(self, '_last_status_log'):
                    time_since_log = (self.last_heartbeat - self._last_status_log).total_seconds()
                    if time_since_log >= 300:  # 5 minutes
                        logger.info(f"💓 Heartbeat check - Bot online in {len(self.guilds)} guilds | Commands: {len(self.commands) + len(self.tree.get_commands())}")
                        self._last_status_log = self.last_heartbeat
                else:
                    self._last_status_log = self.last_heartbeat
                    logger.info("💓 Heartbeat system initialized")
                
                # Update status (fallback)
                bot_status['connected'] = not self.is_closed()
                bot_status['guilds'] = len(self.guilds)
                
                # Wait 30 seconds before next heartbeat
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    async def activity_loop(self):
        """Constantly refresh bot activity to ensure visibility"""
        await self.wait_until_ready()
        
        activities = [
            discord.Game(name="🤖 ONLINE | !help or !ping"),
            discord.Game(name="🔥 136 Commands Ready!"),
            discord.Game(name="💬 Ready to respond!"),
            discord.Game(name="⚡ !ping to test connection")
        ]
        
        activity_index = 0
        while not self.is_closed():
            try:
                current_activity = activities[activity_index % len(activities)]
                await self.change_presence(
                    status=discord.Status.online,
                    activity=current_activity
                )
                logger.info(f"🔄 Activity updated: {current_activity.name}")
                activity_index += 1
                
                # Update every 60 seconds
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Activity update error: {e}")
                await asyncio.sleep(30)  # Shorter wait on error
    
    async def on_guild_join(self, guild):
        """Called when the bot joins a new guild"""
        logger.info(f'Joined new guild: {guild.name} (ID: {guild.id})')
        
        # Send a welcome message to the general channel or first available channel
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                embed = discord.Embed(
                    title="Hello! 👋",
                    description="Thanks for adding me to your server! Use `!help` to see available commands.",
                    color=0x00ff00
                )
                await channel.send(embed=embed)
                break
    
    async def on_guild_remove(self, guild):
        """Called when the bot is removed from a guild"""
        logger.info(f'Removed from guild: {guild.name} (ID: {guild.id})')
    
    async def on_member_join(self, member):
        """Called when a member joins a guild - Enhanced Welcome System"""
        logger.info(f'{member} joined {member.guild.name}')
        
        # Auto-assign "Waiting List" role to new members
        waiting_list_role = None
        for role in member.guild.roles:
            if role.name.lower() == "waiting list":
                waiting_list_role = role
                break
        
        if waiting_list_role:
            try:
                await member.add_roles(waiting_list_role)
                logger.info(f'✅ Assigned "Waiting List" role to {member}')
            except Exception as e:
                logger.error(f'❌ Failed to assign "Waiting List" role to {member}: {e}')
        else:
            logger.warning(f'⚠️ "Waiting List" role not found in {member.guild.name}')
        
        # Find the best welcome channel
        welcome_channel = await self.find_welcome_channel(member.guild)
        logger.info(f'Welcome channel found: {welcome_channel.name if welcome_channel else "None"}')
        
        if welcome_channel:
            # Load latest welcome settings from file
            self.load_welcome_settings()
            
            # Get custom welcome settings if they exist
            welcome_settings = {}
            if hasattr(self, 'welcome_settings') and member.guild.id in self.welcome_settings:
                welcome_settings = self.welcome_settings[member.guild.id]
            
            # Use custom settings or defaults
            welcome_color = welcome_settings.get('color', 0x00ff7f)
            welcome_title = None  # Remove title for cleaner look
            
            # Create message exactly like uploaded image format
            if 'message' in welcome_settings:
                # Replace channel references with interactive mentions
                interactive_message = welcome_settings['message']
                
                # Find and replace channel mentions with actual Discord channel links
                for channel in member.guild.text_channels:
                    if 'rulebook' in channel.name.lower() or 'rule' in channel.name.lower():
                        interactive_message = interactive_message.replace('#📋-rulebook', f'<#{channel.id}>')
                        interactive_message = interactive_message.replace('#rulebook', f'<#{channel.id}>')
                    elif 'waiting' in channel.name.lower() or 'wait' in channel.name.lower():
                        interactive_message = interactive_message.replace('#🏟️-waiting-area', f'<#{channel.id}>')
                        interactive_message = interactive_message.replace('#waiting-area', f'<#{channel.id}>')
                        interactive_message = interactive_message.replace('#waiting', f'<#{channel.id}>')
                
                # Format like preview page: clean text without emoji
                welcome_description = f"**Hey**, **{member.display_name}**! 👋\n\n**Welcome to {member.guild.name}**!\n\n{interactive_message}"
            else:
                welcome_description = f"**Hey**, **{member.display_name}**! 👋\n\n**Welcome to {member.guild.name}**!\n\nThis is exactly how new members will see their welcome message!"
            
            # Create embed exactly like uploaded image format
            embed = discord.Embed(
                color=welcome_color,  # Use the gold color from settings
                description=welcome_description
            )
            
            # Add server logo/icon to the top right corner like in uploaded image
            if member.guild.icon:
                embed.set_thumbnail(url=member.guild.icon.url)
            
            # Generate custom welcome image
            embed.set_image(url='attachment://welcome.png')
            
            # Send the welcome message with custom generated image
            try:
                # Generate custom welcome image
                welcome_image_file = await self.welcome_image_generator.create_welcome_image(member, member.guild.name)
                
                if welcome_image_file:
                    await welcome_channel.send(embed=embed, file=welcome_image_file)
                    logger.info(f"Sent custom welcome image for {member}")
                else:
                    # Fallback to sending without image if generation fails
                    embed.set_image(url=member.avatar.url if member.avatar else member.default_avatar.url)
                    await welcome_channel.send(embed=embed)
                    logger.info(f"Sent welcome message (image generation failed) for {member}")
            except Exception as e:
                logger.error(f"Failed to send welcome message: {e}")
            
            # DM welcome disabled to prevent duplicate messages
    
    async def find_welcome_channel(self, guild):
        """Find the best channel for welcome messages"""
        # Check if custom welcome channel is set
        if hasattr(self, 'welcome_settings') and guild.id in self.welcome_settings:
            if 'channel_id' in self.welcome_settings[guild.id] and self.welcome_settings[guild.id]['channel_id']:
                custom_channel = guild.get_channel(self.welcome_settings[guild.id]['channel_id'])
                if custom_channel and custom_channel.permissions_for(guild.me).send_messages:
                    logger.info(f'Using custom welcome channel: {custom_channel.name}')
                    return custom_channel
        
        # Priority channel names
        priority_names = ['welcome', 'general', 'lobby', 'entrance', 'main', 'chat', 'introductions']
        
        # First pass: Look for exact matches with priority names
        for name in priority_names:
            for channel in guild.text_channels:
                if channel.name.lower() == name:
                    if channel.permissions_for(guild.me).send_messages:
                        logger.info(f'Found welcome channel by exact match: {channel.name}')
                        return channel
        
        # Second pass: Look for channels containing priority names
        for name in priority_names:
            for channel in guild.text_channels:
                if name in channel.name.lower():
                    if channel.permissions_for(guild.me).send_messages:
                        logger.info(f'Found welcome channel by partial match: {channel.name}')
                        return channel
        
        # Third pass: Use the first available text channel
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                logger.info(f'Using first available channel: {channel.name}')
                return channel
        
        return None
    
    def load_welcome_settings(self):
        """Load welcome settings from JSON file"""
        try:
            if os.path.exists('welcome_settings.json'):
                with open('welcome_settings.json', 'r') as f:
                    settings_data = json.load(f)
                    
                # Convert string keys to int keys for guild IDs
                self.welcome_settings = {}
                for guild_id_str, settings in settings_data.items():
                    try:
                        guild_id = int(guild_id_str)
                        self.welcome_settings[guild_id] = settings
                    except ValueError:
                        continue
                        
                logger.info(f"Loaded welcome settings for {len(self.welcome_settings)} guilds")
            else:
                self.welcome_settings = {}
        except Exception as e:
            logger.error(f"Failed to load welcome settings: {e}")
            self.welcome_settings = {}
    
    def load_goodbye_settings(self):
        """Load goodbye settings from JSON file"""
        try:
            if os.path.exists('goodbye_settings.json'):
                with open('goodbye_settings.json', 'r') as f:
                    settings_data = json.load(f)
                    
                # Convert string keys to int keys for guild IDs
                self.goodbye_settings = {}
                for guild_id_str, settings in settings_data.items():
                    try:
                        guild_id = int(guild_id_str)
                        self.goodbye_settings[guild_id] = settings
                    except ValueError:
                        continue
                        
                logger.info(f"Loaded goodbye settings for {len(self.goodbye_settings)} guilds")
            else:
                self.goodbye_settings = {}
        except Exception as e:
            logger.error(f"Failed to load goodbye settings: {e}")
            self.goodbye_settings = {}
    
    def save_goodbye_settings(self):
        """Save goodbye settings to JSON file"""
        try:
            # Convert int keys to string keys for JSON serialization
            settings_data = {}
            for guild_id, settings in self.goodbye_settings.items():
                settings_data[str(guild_id)] = settings
                
            with open('goodbye_settings.json', 'w') as f:
                json.dump(settings_data, f, indent=2)
            logger.info("Goodbye settings saved successfully")
        except Exception as e:
            logger.error(f"Failed to save goodbye settings: {e}")
    
    def load_autolike_settings(self):
        """Load auto-like settings from JSON file"""
        try:
            if os.path.exists('autolike_settings.json'):
                with open('autolike_settings.json', 'r') as f:
                    settings_data = json.load(f)
                    
                # Convert string keys to int keys for guild IDs
                self.autolike_settings = {}
                for guild_id_str, settings in settings_data.items():
                    try:
                        guild_id = int(guild_id_str)
                        # Convert channel IDs from strings to ints
                        if 'channels' in settings:
                            settings['channels'] = [int(ch_id) for ch_id in settings['channels']]
                        self.autolike_settings[guild_id] = settings
                    except (ValueError, TypeError):
                        continue
                        
                logger.info(f"Loaded auto-like settings for {len(self.autolike_settings)} guilds")
            else:
                self.autolike_settings = {}
        except Exception as e:
            logger.error(f"Failed to load auto-like settings: {e}")
            self.autolike_settings = {}
    
    def save_autolike_settings(self):
        """Save auto-like settings to JSON file"""
        try:
            # Convert int keys to string keys for JSON serialization
            settings_data = {}
            for guild_id, settings in self.autolike_settings.items():
                # Convert channel IDs to strings for JSON
                settings_copy = settings.copy()
                if 'channels' in settings_copy:
                    settings_copy['channels'] = [str(ch_id) for ch_id in settings_copy['channels']]
                settings_data[str(guild_id)] = settings_copy
                
            with open('autolike_settings.json', 'w') as f:
                json.dump(settings_data, f, indent=2)
            logger.info("Auto-like settings saved successfully")
        except Exception as e:
            logger.error(f"Failed to save auto-like settings: {e}")
    
    async def on_member_remove(self, member):
        """Called when a member leaves a guild - Enhanced Goodbye System"""
        logger.info(f'{member} left {member.guild.name}')
        
        # Find the goodbye channel specifically
        goodbye_channel = await self.find_goodbye_channel(member.guild)
        logger.info(f'Goodbye channel found: {goodbye_channel.name if goodbye_channel else "None"}')
        
        if goodbye_channel:
            # Load latest goodbye settings from file
            self.load_goodbye_settings()
            
            # Get custom goodbye settings if they exist
            goodbye_settings = {}
            if hasattr(self, 'goodbye_settings') and member.guild.id in self.goodbye_settings:
                goodbye_settings = self.goodbye_settings[member.guild.id]
            
            # Use custom settings or defaults
            goodbye_color = goodbye_settings.get('color', 0xff6b6b)  # Default soft red
            goodbye_title = goodbye_settings.get('title', '👋 Member Left')
            
            # Format custom message or use default
            if 'message' in goodbye_settings:
                goodbye_description = goodbye_settings['message'].format(
                    member_name=member.display_name,
                    server_name=member.guild.name,
                    username=member.name
                )
            else:
                goodbye_description = f"**{member.display_name}** has left **{member.guild.name}**.\n\nWe hope they had a great time with us! 🌟"
            
            # Create professional goodbye embed
            embed = discord.Embed(
                title=goodbye_title,
                description=goodbye_description,
                color=goodbye_color,
                timestamp=discord.utils.utcnow()
            )
            
            # Add member avatar
            embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            
            # Add member info based on settings
            show_member_info = goodbye_settings.get('show_member_info', True)
            if show_member_info:
                member_info_fields = goodbye_settings.get('member_info_fields', {})
                info_parts = []
                
                if member_info_fields.get('username', True):
                    info_parts.append(f"**Username:** {member.name}")
                if member_info_fields.get('display_name', True):
                    info_parts.append(f"**Display Name:** {member.display_name}")
                if member_info_fields.get('join_date', True):
                    join_date = member.joined_at.strftime('%B %d, %Y') if member.joined_at else 'Unknown'
                    info_parts.append(f"**Joined:** {join_date}")
                if member_info_fields.get('member_count', False):
                    info_parts.append(f"**Members Now:** {member.guild.member_count}")
                
                if info_parts:
                    embed.add_field(
                        name="Member Info",
                        value="\n".join(info_parts),
                        inline=True
                    )
            
            embed.set_footer(text=f"Goodbye from {member.guild.name}", icon_url=member.guild.icon.url if member.guild.icon else None)
            
            try:
                await goodbye_channel.send(embed=embed)
                logger.info(f"Sent goodbye message for {member} to #{goodbye_channel.name}")
            except Exception as e:
                logger.error(f"Failed to send goodbye message: {e}")
        else:
            logger.info(f"No goodbye channel found for {member.guild.name}")
    
    async def find_goodbye_channel(self, guild):
        """Find the best channel for goodbye messages"""
        # Check if custom goodbye channel is set
        if hasattr(self, 'goodbye_settings') and guild.id in self.goodbye_settings:
            if 'channel_id' in self.goodbye_settings[guild.id] and self.goodbye_settings[guild.id]['channel_id']:
                custom_channel = guild.get_channel(self.goodbye_settings[guild.id]['channel_id'])
                if custom_channel and custom_channel.permissions_for(guild.me).send_messages:
                    logger.info(f'Using custom goodbye channel: {custom_channel.name}')
                    return custom_channel
        
        # Priority channel names for goodbye messages
        priority_channels = [
            'goodbye', 'bye', 'farewell', 'leaving', 'leaves', 
            'member-log', 'member-logs', 'log', 'logs'
        ]
        
        # First, look for dedicated goodbye channels
        for channel_name in priority_channels:
            for channel in guild.text_channels:
                if channel_name in channel.name.lower():
                    if channel.permissions_for(guild.me).send_messages:
                        logger.info(f'Found goodbye channel by exact match: {channel.name}')
                        return channel
        
        # Then look for partial matches
        for channel in guild.text_channels:
            for keyword in priority_channels:
                if keyword in channel.name.lower():
                    if channel.permissions_for(guild.me).send_messages:
                        logger.info(f'Found goodbye channel by partial match: {channel.name}')
                        return channel
        
        # Fallback to welcome channel if goodbye not found
        welcome_channel = await self.find_welcome_channel(guild)
        if welcome_channel:
            logger.info(f'Using welcome channel for goodbye: {welcome_channel.name}')
            return welcome_channel
        
        # Last resort: general or first available channel
        for channel in guild.text_channels:
            if 'general' in channel.name.lower() or 'main' in channel.name.lower():
                if channel.permissions_for(guild.me).send_messages:
                    logger.info(f'Using general channel for goodbye: {channel.name}')
                    return channel
        
        # If all else fails, use first available channel
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                logger.info(f'Using first available channel for goodbye: {channel.name}')
                return channel
        
        return None
    
    
    async def on_command_error(self, ctx, error):
        """Global error handler for commands"""
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("❌ Command not found. Use `!help` to see available commands.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: {error.param}")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ Invalid argument provided.")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"❌ Command is on cooldown. Try again in {error.retry_after:.2f} seconds.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command.")
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("❌ I don't have the required permissions to execute this command.")
        else:
            logger.error(f'Unhandled error in command {ctx.command}: {error}')
            await ctx.send("❌ An unexpected error occurred. Please try again later.")
    
    async def on_message(self, message):
        """Called when a message is sent"""
        # Ignore messages from bots (including self)
        if message.author.bot:
            return
        
        # Log incoming messages for debugging
        if message.content.startswith('!'):
            logger.info(f"Command received: {message.content} from {message.author}")
        
        # Check for auto-like functionality
        await self.handle_autolike(message)
        
        # Process commands
        await self.process_commands(message)
    
    async def handle_autolike(self, message):
        """Handle auto-like functionality for messages and images"""
        try:
            # Check if auto-like is enabled for this guild
            if not hasattr(self, 'autolike_settings') or message.guild.id not in self.autolike_settings:
                return
            
            guild_settings = self.autolike_settings[message.guild.id]
            
            # Check if auto-like is enabled
            if not guild_settings.get('enabled', False):
                return
            
            # Check if this channel is in the auto-like list
            if 'channels' not in guild_settings or message.channel.id not in guild_settings['channels']:
                return
            
            # Get auto-like mode (images_only or all_messages)
            autolike_mode = guild_settings.get('mode', 'images_only')
            
            should_like = False
            
            if autolike_mode == 'all_messages':
                # Like all messages in configured channels
                should_like = True
                logger.info(f"Auto-liked message in #{message.channel.name} from {message.author}")
            else:
                # Default behavior: only like messages with images
                has_image = False
                
                # Check attachments
                for attachment in message.attachments:
                    if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp']):
                        has_image = True
                        break
                
                # Check embeds for images
                if not has_image:
                    for embed in message.embeds:
                        if embed.image or embed.thumbnail:
                            has_image = True
                            break
                
                # Check for image URLs in message content
                if not has_image and message.content:
                    import re
                    image_url_pattern = r'https?://[^\s]+\.(?:png|jpg|jpeg|gif|webp|bmp)'
                    if re.search(image_url_pattern, message.content, re.IGNORECASE):
                        has_image = True
                
                if has_image:
                    should_like = True
                    logger.info(f"Auto-liked image in #{message.channel.name} from {message.author}")
            
            # Add reaction if conditions are met
            if should_like:
                # Get reaction emoji (default to 👍)
                reaction_emoji = guild_settings.get('emoji', '👍')
                
                # Add reaction
                await message.add_reaction(reaction_emoji)
                
        except Exception as e:
            logger.error(f"Error in auto-like handler: {e}")
    
    async def close(self):
        """Clean shutdown of the bot"""
        logger.info("Shutting down bot...")
        await super().close()
