"""
Music and Audio Features for Discord Bot
Includes: Music player, soundboard, voice channel utilities
"""

import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import aiohttp
import random
from datetime import datetime, timezone
from typing import Optional, List, Dict
import json
import yt_dlp
from urllib.parse import urlparse

class MusicQueue:
    """Music queue management"""
    
    def __init__(self):
        self.queue = []
        self.current = None
        self.loop = False
        self.shuffle = False
    
    def add(self, song):
        """Add song to queue"""
        self.queue.append(song)
    
    def get_next(self):
        """Get next song from queue"""
        if not self.queue:
            return None
        
        if self.shuffle:
            song = random.choice(self.queue)
            self.queue.remove(song)
        else:
            song = self.queue.pop(0)
        
        if self.loop and self.current:
            self.queue.append(self.current)
        
        self.current = song
        return song
    
    def clear(self):
        """Clear the queue"""
        self.queue.clear()
        self.current = None
    
    def remove(self, index):
        """Remove song at index"""
        if 0 <= index < len(self.queue):
            return self.queue.pop(index)
        return None
    
    def get_queue_display(self, max_songs=10):
        """Get formatted queue display"""
        if not self.queue:
            return "Queue is empty"
        
        display = []
        for i, song in enumerate(self.queue[:max_songs], 1):
            display.append(f"`{i}.` {song['title'][:50]}...")
        
        if len(self.queue) > max_songs:
            display.append(f"... and {len(self.queue) - max_songs} more songs")
        
        return "\n".join(display)

class YouTubeSource:
    """YouTube audio source handler"""
    
    YTDL_OPTIONS = {
        'format': 'bestaudio/best',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0'
    }
    
    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
    }
    
    ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)
    
    @classmethod
    async def search(cls, query: str, loop=None):
        """Search for YouTube videos"""
        loop = loop or asyncio.get_event_loop()
        
        try:
            data = await loop.run_in_executor(
                None, 
                lambda: cls.ytdl.extract_info(f"ytsearch:{query}", download=False)
            )
            
            if 'entries' in data and data['entries']:
                entry = data['entries'][0]
                return {
                    'title': entry.get('title', 'Unknown'),
                    'url': entry.get('url'),
                    'duration': entry.get('duration', 0),
                    'webpage_url': entry.get('webpage_url', ''),
                    'uploader': entry.get('uploader', 'Unknown'),
                    'view_count': entry.get('view_count', 0)
                }
        except Exception as e:
            print(f"YouTube search error: {e}")
        
        return None
    
    @classmethod
    async def get_source(cls, url: str, loop=None):
        """Get audio source from URL"""
        loop = loop or asyncio.get_event_loop()
        
        try:
            data = await loop.run_in_executor(
                None,
                lambda: cls.ytdl.extract_info(url, download=False)
            )
            
            if 'entries' in data:
                data = data['entries'][0]
            
            return discord.FFmpegPCMAudio(data['url'], **cls.FFMPEG_OPTIONS)
        except Exception as e:
            print(f"Audio source error: {e}")
            return None

class MusicPlayer:
    """Music player for a guild"""
    
    def __init__(self, bot, guild_id):
        self.bot = bot
        self.guild_id = guild_id
        self.queue = MusicQueue()
        self.voice_client = None
        self.current_message = None
        self.is_playing = False
        self.is_paused = False
        self.volume = 0.5
    
    async def connect(self, channel):
        """Connect to voice channel"""
        if self.voice_client and self.voice_client.is_connected():
            await self.voice_client.move_to(channel)
        else:
            self.voice_client = await channel.connect()
    
    async def disconnect(self):
        """Disconnect from voice channel"""
        if self.voice_client:
            await self.voice_client.disconnect()
            self.voice_client = None
    
    async def play_next(self):
        """Play next song in queue"""
        if not self.voice_client:
            return
        
        song = self.queue.get_next()
        if not song:
            self.is_playing = False
            return
        
        try:
            source = await YouTubeSource.get_source(song['url'])
            if source:
                self.voice_client.play(
                    source,
                    after=lambda e: asyncio.run_coroutine_threadsafe(
                        self.play_next(), self.bot.loop
                    ).result() if not e else print(f"Player error: {e}")
                )
                self.is_playing = True
                await self.update_now_playing(song)
            else:
                await self.play_next()  # Try next song
        except Exception as e:
            print(f"Play error: {e}")
            await self.play_next()
    
    async def update_now_playing(self, song):
        """Update now playing message"""
        if not self.current_message:
            return
        
        embed = discord.Embed(
            title="🎵 Now Playing",
            description=f"**{song['title']}**",
            color=0x1db954
        )
        embed.add_field(name="Duration", value=f"{song.get('duration', 0)//60}:{song.get('duration', 0)%60:02d}", inline=True)
        embed.add_field(name="Uploader", value=song.get('uploader', 'Unknown'), inline=True)
        embed.add_field(name="Queue", value=f"{len(self.queue.queue)} songs", inline=True)
        
        try:
            await self.current_message.edit(embed=embed)
        except:
            pass
    
    def pause(self):
        """Pause playback"""
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.pause()
            self.is_paused = True
    
    def resume(self):
        """Resume playback"""
        if self.voice_client and self.voice_client.is_paused():
            self.voice_client.resume()
            self.is_paused = False
    
    def stop(self):
        """Stop playback"""
        if self.voice_client:
            self.voice_client.stop()
            self.is_playing = False
    
    def skip(self):
        """Skip current song"""
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.stop()

class Soundboard:
    """Soundboard functionality"""
    
    def __init__(self):
        self.sounds = {
            "applause": "https://www.soundjay.com/misc/sounds/applause-1.wav",
            "drums": "https://www.soundjay.com/misc/sounds/drum-roll-1.wav", 
            "airhorn": "https://www.soundjay.com/misc/sounds/air-horn-1.wav",
            "tada": "https://www.soundjay.com/misc/sounds/ta-da.wav",
            "wow": "https://www.soundjay.com/misc/sounds/wow.wav"
        }
    
    async def play_sound(self, voice_client, sound_name):
        """Play a sound effect"""
        if sound_name not in self.sounds:
            return False
        
        try:
            source = discord.FFmpegPCMAudio(self.sounds[sound_name])
            voice_client.play(source)
            return True
        except Exception as e:
            print(f"Soundboard error: {e}")
            return False

def setup_music_features(bot):
    """Setup all music and audio commands"""
    
    # Guild music players
    music_players = {}
    soundboard = Soundboard()
    
    def get_player(guild_id):
        """Get or create music player for guild"""
        if guild_id not in music_players:
            music_players[guild_id] = MusicPlayer(bot, guild_id)
        return music_players[guild_id]
    
    # ============= MUSIC COMMANDS =============
    
    @bot.tree.command(name="join", description="Join your voice channel")
    async def join_command(interaction: discord.Interaction):
        """Join voice channel"""
        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.response.send_message("❌ You need to be in a voice channel!", ephemeral=True)
        
        channel = interaction.user.voice.channel
        player = get_player(interaction.guild.id)
        
        try:
            await player.connect(channel)
            
            embed = discord.Embed(
                title="🎵 Joined Voice Channel",
                description=f"Connected to **{channel.name}**!",
                color=0x1db954
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to join channel: {e}", ephemeral=True)
    
    @bot.tree.command(name="leave", description="Leave the voice channel")
    async def leave_command(interaction: discord.Interaction):
        """Leave voice channel"""
        player = get_player(interaction.guild.id)
        
        if not player.voice_client:
            return await interaction.response.send_message("❌ I'm not in a voice channel!", ephemeral=True)
        
        try:
            await player.disconnect()
            player.queue.clear()
            
            embed = discord.Embed(
                title="👋 Left Voice Channel",
                description="Disconnected and cleared the queue!",
                color=0xe74c3c
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to leave channel: {e}", ephemeral=True)
    
    @bot.tree.command(name="play", description="Play music from YouTube")
    @app_commands.describe(query="Song name or YouTube URL")
    async def play_command(interaction: discord.Interaction, query: str):
        """Play music"""
        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.response.send_message("❌ You need to be in a voice channel!", ephemeral=True)
        
        try:
            await interaction.response.defer()
            
            player = get_player(interaction.guild.id)
            
            # Connect if not connected
            if not player.voice_client:
                await player.connect(interaction.user.voice.channel)
            
            # Search for song
            song = await YouTubeSource.search(query)
            if not song:
                return await interaction.followup.send("❌ No results found for that search!", ephemeral=True)
            
            # Add to queue
            player.queue.add(song)
            
            embed = discord.Embed(
                title="➕ Added to Queue",
                description=f"**{song['title']}**",
                color=0x1db954
            )
            embed.add_field(name="Duration", value=f"{song.get('duration', 0)//60}:{song.get('duration', 0)%60:02d}", inline=True)
            embed.add_field(name="Position", value=f"{len(player.queue.queue)}", inline=True)
            embed.add_field(name="Uploader", value=song.get('uploader', 'Unknown'), inline=True)
            
            await interaction.followup.send(embed=embed)
            
            # Start playing if not already
            if not player.is_playing:
                await player.play_next()
                
        except Exception as e:
            await interaction.followup.send(f"❌ Error playing music: {e}", ephemeral=True)
    
    @bot.tree.command(name="queue", description="View the music queue")
    async def queue_command(interaction: discord.Interaction):
        """View music queue"""
        player = get_player(interaction.guild.id)
        
        embed = discord.Embed(
            title="🎵 Music Queue",
            color=0x1db954
        )
        
        if player.queue.current:
            embed.add_field(
                name="🎶 Now Playing",
                value=f"**{player.queue.current['title']}**",
                inline=False
            )
        
        queue_display = player.queue.get_queue_display()
        embed.add_field(
            name=f"📋 Up Next ({len(player.queue.queue)} songs)",
            value=queue_display,
            inline=False
        )
        
        embed.add_field(
            name="⚙️ Settings",
            value=f"Loop: {'✅' if player.queue.loop else '❌'} | Shuffle: {'✅' if player.queue.shuffle else '❌'}",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="skip", description="Skip the current song")
    async def skip_command(interaction: discord.Interaction):
        """Skip current song"""
        player = get_player(interaction.guild.id)
        
        if not player.voice_client or not player.is_playing:
            return await interaction.response.send_message("❌ Nothing is playing!", ephemeral=True)
        
        current_song = player.queue.current
        player.skip()
        
        embed = discord.Embed(
            title="⏭️ Song Skipped",
            description=f"Skipped **{current_song['title'] if current_song else 'Unknown'}**",
            color=0xf39c12
        )
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="pause", description="Pause the music")
    async def pause_command(interaction: discord.Interaction):
        """Pause music"""
        player = get_player(interaction.guild.id)
        
        if not player.voice_client or not player.is_playing:
            return await interaction.response.send_message("❌ Nothing is playing!", ephemeral=True)
        
        if player.is_paused:
            return await interaction.response.send_message("❌ Music is already paused!", ephemeral=True)
        
        player.pause()
        
        embed = discord.Embed(
            title="⏸️ Music Paused",
            description="Use `/resume` to continue playing!",
            color=0xf39c12
        )
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="resume", description="Resume the music")
    async def resume_command(interaction: discord.Interaction):
        """Resume music"""
        player = get_player(interaction.guild.id)
        
        if not player.voice_client:
            return await interaction.response.send_message("❌ I'm not in a voice channel!", ephemeral=True)
        
        if not player.is_paused:
            return await interaction.response.send_message("❌ Music is not paused!", ephemeral=True)
        
        player.resume()
        
        embed = discord.Embed(
            title="▶️ Music Resumed",
            description="Continuing playback!",
            color=0x00ff00
        )
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="stop", description="Stop the music and clear queue")
    async def stop_command(interaction: discord.Interaction):
        """Stop music"""
        player = get_player(interaction.guild.id)
        
        if not player.voice_client:
            return await interaction.response.send_message("❌ I'm not in a voice channel!", ephemeral=True)
        
        player.stop()
        player.queue.clear()
        
        embed = discord.Embed(
            title="⏹️ Music Stopped",
            description="Stopped playback and cleared the queue!",
            color=0xe74c3c
        )
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="loop", description="Toggle loop mode")
    async def loop_command(interaction: discord.Interaction):
        """Toggle loop"""
        player = get_player(interaction.guild.id)
        
        player.queue.loop = not player.queue.loop
        
        embed = discord.Embed(
            title="🔄 Loop Mode",
            description=f"Loop is now {'**enabled**' if player.queue.loop else '**disabled**'}!",
            color=0x3498db
        )
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="shuffle", description="Toggle shuffle mode")
    async def shuffle_command(interaction: discord.Interaction):
        """Toggle shuffle"""
        player = get_player(interaction.guild.id)
        
        player.queue.shuffle = not player.queue.shuffle
        
        embed = discord.Embed(
            title="🔀 Shuffle Mode",
            description=f"Shuffle is now {'**enabled**' if player.queue.shuffle else '**disabled**'}!",
            color=0x9b59b6
        )
        
        await interaction.response.send_message(embed=embed)
    
    # ============= SOUNDBOARD COMMANDS =============
    
    @bot.tree.command(name="soundboard", description="Play a sound effect")
    @app_commands.describe(sound="Sound effect to play")
    @app_commands.choices(sound=[
        app_commands.Choice(name="👏 Applause", value="applause"),
        app_commands.Choice(name="🥁 Drum Roll", value="drums"),
        app_commands.Choice(name="📯 Air Horn", value="airhorn"),
        app_commands.Choice(name="🎉 Ta-da!", value="tada"),
        app_commands.Choice(name="😲 Wow", value="wow")
    ])
    async def soundboard_command(interaction: discord.Interaction, sound: str):
        """Play sound effect"""
        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.response.send_message("❌ You need to be in a voice channel!", ephemeral=True)
        
        try:
            player = get_player(interaction.guild.id)
            
            # Connect if not connected
            if not player.voice_client:
                await player.connect(interaction.user.voice.channel)
            
            # Stop current music temporarily
            was_playing = player.is_playing
            if was_playing:
                player.voice_client.pause()
            
            # Play sound effect
            success = await soundboard.play_sound(player.voice_client, sound)
            
            if success:
                sound_names = {
                    "applause": "👏 Applause",
                    "drums": "🥁 Drum Roll", 
                    "airhorn": "📯 Air Horn",
                    "tada": "🎉 Ta-da!",
                    "wow": "😲 Wow"
                }
                
                embed = discord.Embed(
                    title="🔊 Sound Effect Played",
                    description=f"Playing: **{sound_names.get(sound, sound)}**",
                    color=0xff6b6b
                )
                
                await interaction.response.send_message(embed=embed)
                
                # Resume music after a delay
                if was_playing:
                    await asyncio.sleep(3)  # Wait for sound effect to finish
                    player.voice_client.resume()
            else:
                await interaction.response.send_message("❌ Failed to play sound effect!", ephemeral=True)
                
        except Exception as e:
            await interaction.response.send_message(f"❌ Error playing sound: {e}", ephemeral=True)
    
    # ============= VOICE UTILITIES =============
    
    @bot.tree.command(name="moveall", description="Move all users from one voice channel to another")
    @app_commands.describe(from_channel="Source voice channel", to_channel="Destination voice channel")
    async def move_all_command(interaction: discord.Interaction, from_channel: discord.VoiceChannel, to_channel: discord.VoiceChannel):
        """Move all users between voice channels"""
        if not interaction.user.guild_permissions.move_members:
            return await interaction.response.send_message("❌ You need Move Members permission!", ephemeral=True)
        
        try:
            moved_count = 0
            failed_count = 0
            
            for member in from_channel.members:
                try:
                    await member.move_to(to_channel)
                    moved_count += 1
                except:
                    failed_count += 1
            
            embed = discord.Embed(
                title="📤 Members Moved",
                color=0x00ff00
            )
            embed.add_field(name="From", value=from_channel.mention, inline=True)
            embed.add_field(name="To", value=to_channel.mention, inline=True)
            embed.add_field(name="Stats", value=f"✅ Moved: {moved_count}\n❌ Failed: {failed_count}", inline=True)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error moving members: {e}", ephemeral=True)
    
    @bot.tree.command(name="voicekick", description="Disconnect a user from voice")
    @app_commands.describe(user="User to disconnect from voice")
    async def voice_kick_command(interaction: discord.Interaction, user: discord.Member):
        """Kick user from voice"""
        if not interaction.user.guild_permissions.move_members:
            return await interaction.response.send_message("❌ You need Move Members permission!", ephemeral=True)
        
        if not user.voice or not user.voice.channel:
            return await interaction.response.send_message("❌ User is not in a voice channel!", ephemeral=True)
        
        try:
            channel_name = user.voice.channel.name
            await user.move_to(None)
            
            embed = discord.Embed(
                title="🔇 User Disconnected",
                description=f"**{user.display_name}** has been disconnected from **{channel_name}**",
                color=0xff6b6b
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error disconnecting user: {e}", ephemeral=True)
    
    print("✅ All music and audio features loaded successfully!")