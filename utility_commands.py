# Utility Commands - Advanced Discord Bot Features
# Comprehensive utility commands covering all possible Discord utilities

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
import json
import time
import datetime
from datetime import timedelta
import aiohttp
import base64
import io
import re
from typing import Optional, Literal, List
import logging
import qrcode
import requests
from urllib.parse import quote

def setup_utility_commands(bot):
    """Setup comprehensive utility commands"""
    
    # ============= TRANSLATION COMMANDS =============
    
    @bot.tree.command(name="translate", description="Translate text to another language")
    @app_commands.describe(
        text="Text to translate",
        target_language="Target language code (e.g., es, fr, de, ja, ko)",
        source_language="Source language code (auto-detect if not specified)"
    )
    async def translate_text(interaction: discord.Interaction, text: str, target_language: str, source_language: str = "auto"):
        """Translate text using Google Translate API"""
        try:
            # Using Google Translate API (would need API key in production)
            # For now, using a free translation service
            
            embed = discord.Embed(
                title="🌐 Translation",
                color=0x4285f4
            )
            embed.add_field(name="Original", value=text[:1024], inline=False)
            embed.add_field(name="Language", value=f"{source_language} → {target_language}", inline=True)
            
            # Note: This would require a translation API key in production
            embed.add_field(name="Translation", value="Translation feature requires API key setup", inline=False)
            embed.set_footer(text="Translation powered by Google Translate")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Translation failed: {e}", ephemeral=True)
    
    # ============= QR CODE GENERATION =============
    
    @bot.tree.command(name="qr", description="Generate a QR code")
    @app_commands.describe(text="Text or URL to encode in QR code")
    async def generate_qr(interaction: discord.Interaction, text: str):
        """Generate a QR code for any text or URL"""
        try:
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(text)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Save to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            file = discord.File(img_bytes, filename="qrcode.png")
            
            embed = discord.Embed(
                title="📱 QR Code Generated",
                description=f"QR code for: `{text[:100]}{'...' if len(text) > 100 else ''}`",
                color=0x000000
            )
            embed.set_image(url="attachment://qrcode.png")
            
            await interaction.response.send_message(embed=embed, file=file)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to generate QR code: {e}", ephemeral=True)
    
    # ============= WEATHER COMMANDS =============
    
    @bot.tree.command(name="weather", description="Get weather information")
    @app_commands.describe(location="City name or coordinates")
    async def get_weather(interaction: discord.Interaction, location: str):
        """Get weather information for a location"""
        try:
            # Note: This would require OpenWeatherMap API key in production
            embed = discord.Embed(
                title=f"🌤️ Weather for {location}",
                description="Weather feature requires API key setup",
                color=0x87CEEB
            )
            embed.add_field(name="Temperature", value="-- °C", inline=True)
            embed.add_field(name="Humidity", value="-- %", inline=True)
            embed.add_field(name="Conditions", value="--", inline=True)
            embed.set_footer(text="Weather data powered by OpenWeatherMap")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Weather lookup failed: {e}", ephemeral=True)
    
    # ============= URL SHORTENER =============
    
    @bot.tree.command(name="shorten", description="Shorten a URL")
    @app_commands.describe(url="URL to shorten")
    async def shorten_url(interaction: discord.Interaction, url: str):
        """Shorten a long URL"""
        try:
            # Basic URL validation
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            embed = discord.Embed(
                title="🔗 URL Shortener",
                color=0x3498db
            )
            embed.add_field(name="Original URL", value=url[:100] + "..." if len(url) > 100 else url, inline=False)
            embed.add_field(name="Shortened URL", value="URL shortening requires API setup", inline=False)
            embed.set_footer(text="URL shortening service")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ URL shortening failed: {e}", ephemeral=True)
    
    # ============= BASE64 ENCODING/DECODING =============
    
    @bot.tree.command(name="base64", description="Encode or decode base64")
    @app_commands.describe(
        action="Encode or decode",
        text="Text to encode/decode"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="Encode", value="encode"),
        app_commands.Choice(name="Decode", value="decode")
    ])
    async def base64_converter(interaction: discord.Interaction, action: str, text: str):
        """Encode or decode base64 text"""
        try:
            if action == "encode":
                result = base64.b64encode(text.encode()).decode()
                action_emoji = "🔒"
                action_name = "Encoded"
            else:
                result = base64.b64decode(text.encode()).decode()
                action_emoji = "🔓"
                action_name = "Decoded"
            
            embed = discord.Embed(
                title=f"{action_emoji} Base64 {action_name}",
                color=0x2ecc71
            )
            embed.add_field(name="Input", value=f"```{text[:500]}```", inline=False)
            embed.add_field(name="Output", value=f"```{result[:500]}```", inline=False)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Base64 operation failed: {e}", ephemeral=True)
    
    # ============= HASH GENERATOR =============
    
    @bot.tree.command(name="hash", description="Generate hash of text")
    @app_commands.describe(
        text="Text to hash",
        algorithm="Hash algorithm"
    )
    @app_commands.choices(algorithm=[
        app_commands.Choice(name="MD5", value="md5"),
        app_commands.Choice(name="SHA1", value="sha1"),
        app_commands.Choice(name="SHA256", value="sha256"),
        app_commands.Choice(name="SHA512", value="sha512")
    ])
    async def generate_hash(interaction: discord.Interaction, text: str, algorithm: str = "sha256"):
        """Generate hash of text using various algorithms"""
        import hashlib
        
        try:
            # Get the hash function
            hash_func = getattr(hashlib, algorithm)
            hash_result = hash_func(text.encode()).hexdigest()
            
            embed = discord.Embed(
                title=f"🔐 {algorithm.upper()} Hash",
                color=0xe74c3c
            )
            embed.add_field(name="Input", value=f"```{text[:200]}```", inline=False)
            embed.add_field(name="Hash", value=f"```{hash_result}```", inline=False)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Hash generation failed: {e}", ephemeral=True)
    
    # ============= PASSWORD GENERATOR =============
    
    @bot.tree.command(name="password", description="Generate a secure password")
    @app_commands.describe(
        length="Password length (8-128)",
        include_symbols="Include symbols",
        include_numbers="Include numbers",
        include_uppercase="Include uppercase letters"
    )
    async def generate_password(interaction: discord.Interaction, length: int = 16, include_symbols: bool = True, include_numbers: bool = True, include_uppercase: bool = True):
        """Generate a secure random password"""
        import string
        
        if length < 8 or length > 128:
            return await interaction.response.send_message("❌ Password length must be between 8 and 128 characters!", ephemeral=True)
        
        try:
            chars = string.ascii_lowercase
            if include_uppercase:
                chars += string.ascii_uppercase
            if include_numbers:
                chars += string.digits
            if include_symbols:
                chars += "!@#$%^&*"
            
            password = ''.join(random.choice(chars) for _ in range(length))
            
            embed = discord.Embed(
                title="🔑 Generated Password",
                description="Your secure password (click to reveal):",
                color=0x2ecc71
            )
            embed.add_field(name="Password", value=f"||`{password}`||", inline=False)
            embed.add_field(name="Length", value=str(length), inline=True)
            embed.add_field(name="Strength", value="Strong" if length >= 12 else "Medium", inline=True)
            embed.set_footer(text="⚠️ Keep this password secure!")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Password generation failed: {e}", ephemeral=True)
    
    # ============= COLOR TOOLS =============
    
    @bot.tree.command(name="color", description="Display color information")
    @app_commands.describe(color="Hex color code (e.g., #ff0000) or color name")
    async def color_info(interaction: discord.Interaction, color: str):
        """Display color information and preview"""
        try:
            # Clean up color input
            if color.startswith('#'):
                hex_color = color
            else:
                # Try to convert color name to hex (basic colors)
                color_map = {
                    'red': '#ff0000', 'green': '#00ff00', 'blue': '#0000ff',
                    'yellow': '#ffff00', 'purple': '#800080', 'orange': '#ffa500',
                    'pink': '#ffc0cb', 'black': '#000000', 'white': '#ffffff'
                }
                hex_color = color_map.get(color.lower(), '#000000')
            
            # Convert hex to RGB
            hex_color = hex_color.lstrip('#')
            rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            
            # Convert to decimal for Discord embed color
            decimal_color = int(hex_color, 16)
            
            embed = discord.Embed(
                title="🎨 Color Information",
                color=decimal_color
            )
            embed.add_field(name="Hex", value=f"#{hex_color.upper()}", inline=True)
            embed.add_field(name="RGB", value=f"rgb({rgb[0]}, {rgb[1]}, {rgb[2]})", inline=True)
            embed.add_field(name="Decimal", value=str(decimal_color), inline=True)
            
            # Create color preview image
            from PIL import Image
            img = Image.new('RGB', (200, 100), rgb)
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            file = discord.File(img_bytes, filename="color_preview.png")
            embed.set_image(url="attachment://color_preview.png")
            
            await interaction.response.send_message(embed=embed, file=file)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Color processing failed: {e}", ephemeral=True)
    
    # ============= RANDOM GENERATORS =============
    
    @bot.tree.command(name="random", description="Generate random data")
    @app_commands.describe(
        data_type="Type of random data to generate",
        count="Number of items to generate"
    )
    @app_commands.choices(data_type=[
        app_commands.Choice(name="Number (1-100)", value="number"),
        app_commands.Choice(name="UUID", value="uuid"),
        app_commands.Choice(name="Word", value="word"),
        app_commands.Choice(name="Color", value="color"),
        app_commands.Choice(name="Name", value="name")
    ])
    async def random_generator(interaction: discord.Interaction, data_type: str, count: int = 1):
        """Generate various types of random data"""
        import uuid
        
        if count < 1 or count > 10:
            return await interaction.response.send_message("❌ Count must be between 1 and 10!", ephemeral=True)
        
        try:
            results = []
            
            for _ in range(count):
                if data_type == "number":
                    results.append(str(random.randint(1, 100)))
                elif data_type == "uuid":
                    results.append(str(uuid.uuid4()))
                elif data_type == "word":
                    words = ["apple", "brave", "cloud", "dream", "eagle", "flame", "grace", "heart", "island", "journey"]
                    results.append(random.choice(words))
                elif data_type == "color":
                    color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
                    results.append(color)
                elif data_type == "name":
                    first_names = ["Alex", "Blake", "Casey", "Drew", "Ellis", "Finley", "Gray", "Harper", "Indigo", "Jules"]
                    results.append(random.choice(first_names))
            
            embed = discord.Embed(
                title=f"🎲 Random {data_type.title()}{'s' if count > 1 else ''}",
                description="\n".join(f"• {result}" for result in results),
                color=0x9b59b6
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Random generation failed: {e}", ephemeral=True)
    
    # ============= TEXT MANIPULATION =============
    # Note: Text manipulation functionality available via /message text group command
    
    # ============= UNIT CONVERTER =============
    
    @bot.tree.command(name="convert", description="Convert between units")
    @app_commands.describe(
        value="Value to convert",
        from_unit="Unit to convert from",
        to_unit="Unit to convert to"
    )
    @app_commands.choices(
        from_unit=[
            app_commands.Choice(name="Celsius", value="celsius"),
            app_commands.Choice(name="Fahrenheit", value="fahrenheit"),
            app_commands.Choice(name="Meters", value="meters"),
            app_commands.Choice(name="Feet", value="feet"),
            app_commands.Choice(name="Kilograms", value="kg"),
            app_commands.Choice(name="Pounds", value="lbs")
        ],
        to_unit=[
            app_commands.Choice(name="Celsius", value="celsius"),
            app_commands.Choice(name="Fahrenheit", value="fahrenheit"),
            app_commands.Choice(name="Meters", value="meters"),
            app_commands.Choice(name="Feet", value="feet"),
            app_commands.Choice(name="Kilograms", value="kg"),
            app_commands.Choice(name="Pounds", value="lbs")
        ]
    )
    async def unit_converter(interaction: discord.Interaction, value: float, from_unit: str, to_unit: str):
        """Convert between different units"""
        try:
            result = None
            
            # Temperature conversions
            if from_unit == "celsius" and to_unit == "fahrenheit":
                result = (value * 9/5) + 32
            elif from_unit == "fahrenheit" and to_unit == "celsius":
                result = (value - 32) * 5/9
            
            # Length conversions
            elif from_unit == "meters" and to_unit == "feet":
                result = value * 3.28084
            elif from_unit == "feet" and to_unit == "meters":
                result = value / 3.28084
            
            # Weight conversions
            elif from_unit == "kg" and to_unit == "lbs":
                result = value * 2.20462
            elif from_unit == "lbs" and to_unit == "kg":
                result = value / 2.20462
            
            if result is None:
                return await interaction.response.send_message("❌ Invalid unit conversion!", ephemeral=True)
            
            embed = discord.Embed(
                title="🔄 Unit Conversion",
                color=0x27ae60
            )
            embed.add_field(name="From", value=f"{value} {from_unit}", inline=True)
            embed.add_field(name="To", value=f"{result:.4f} {to_unit}", inline=True)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Conversion failed: {e}", ephemeral=True)
    
    # ============= MESSAGE EDITING =============
    
    @bot.tree.command(name="editmsg", description="Interactive message editor - select and edit bot messages")
    @app_commands.describe(
        channel="Channel to search for bot messages (optional, defaults to current channel)"
    )
    async def edit_message_interactive(interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None):
        """Interactive bot message editor with message selection and modal input"""
        
        # Check if user has manage messages permission
        if not interaction.guild or not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.manage_messages:
            return await interaction.response.send_message("❌ You need `Manage Messages` permission to edit bot messages!", ephemeral=True)
        
        try:
            # Use provided channel or current channel
            target_channel = channel or interaction.channel
            
            # Fetch recent bot messages from the channel
            recent_messages = []
            async for message in target_channel.history(limit=50):
                if message.author.id == bot.user.id and message.content:
                    # Create a preview of the message content
                    preview = message.content[:50] + ("..." if len(message.content) > 50 else "")
                    timestamp = message.created_at.strftime("%m/%d %H:%M")
                    recent_messages.append({
                        'id': str(message.id),
                        'preview': preview,
                        'timestamp': timestamp,
                        'full_content': message.content,
                        'message': message
                    })
                    
                    # Limit to 25 messages (Discord's select menu limit)
                    if len(recent_messages) >= 25:
                        break
            
            if not recent_messages:
                return await interaction.response.send_message("❌ No recent bot messages found in this channel!", ephemeral=True)
            
            # Create message selection view
            class MessageEditView(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=300)  # 5 minute timeout
                    
                    # Create select menu options
                    options = []
                    for msg_data in recent_messages:
                        options.append(discord.SelectOption(
                            label=f"[{msg_data['timestamp']}] {msg_data['preview']}",
                            value=msg_data['id'],
                            description=f"Message ID: {msg_data['id']}"
                        ))
                    
                    # Add the select menu
                    self.message_select = discord.ui.Select(
                        placeholder="🎯 Select a message to edit...",
                        min_values=1,
                        max_values=1,
                        options=options
                    )
                    self.message_select.callback = self.on_message_select
                    self.add_item(self.message_select)
                
                async def on_message_select(self, interaction: discord.Interaction):
                    """Handle message selection and show edit modal"""
                    if not interaction.data or 'values' not in interaction.data:
                        return await interaction.response.send_message("❌ No message selected!", ephemeral=True)
                    
                    selected_id = interaction.data['values'][0]
                    
                    # Find the selected message data
                    selected_msg_data = next(msg for msg in recent_messages if msg['id'] == selected_id)
                    
                    # Create and show edit modal
                    class MessageEditModal(discord.ui.Modal, title="✏️ Edit Message"):
                        def __init__(self, message_data):
                            super().__init__()
                            self.message_data = message_data
                            
                            # Pre-fill with current content
                            self.new_content = discord.ui.TextInput(
                                label="Message Content",
                                placeholder="Enter the new message content...",
                                default=message_data['full_content'],
                                style=discord.TextStyle.paragraph,
                                max_length=2000,
                                required=True
                            )
                            self.add_item(self.new_content)
                        
                        async def on_submit(self, interaction: discord.Interaction):
                            try:
                                # Edit the message
                                await self.message_data['message'].edit(content=self.new_content.value)
                                
                                # Create success embed
                                embed = discord.Embed(
                                    title="✅ Message Edited Successfully",
                                    description=f"Message edited in {target_channel.mention}",
                                    color=0x27ae60
                                )
                                embed.add_field(name="Message ID", value=self.message_data['id'], inline=True)
                                embed.add_field(name="Channel", value=target_channel.mention, inline=True)
                                embed.add_field(name="New Content", value=self.new_content.value[:200] + ("..." if len(self.new_content.value) > 200 else ""), inline=False)
                                embed.set_footer(text="Message updated successfully!")
                                
                                await interaction.response.send_message(embed=embed, ephemeral=True)
                                
                            except discord.Forbidden:
                                await interaction.response.send_message("❌ I don't have permission to edit that message!", ephemeral=True)
                            except Exception as e:
                                await interaction.response.send_message(f"❌ Failed to edit message: {e}", ephemeral=True)
                    
                    # Show the edit modal
                    modal = MessageEditModal(selected_msg_data)
                    await interaction.response.send_modal(modal)
                
                async def on_timeout(self):
                    # Disable all components when the view times out
                    for item in self.children:
                        item.disabled = True
            
            # Create the embed for the message selector
            embed = discord.Embed(
                title="📝 Interactive Message Editor",
                description=f"Select a bot message from {target_channel.mention} to edit",
                color=0x3498db
            )
            embed.add_field(
                name="📋 Instructions",
                value="• Select a message from the dropdown below\n• A popup editor will appear with the current content\n• Edit the content and save your changes",
                inline=False
            )
            embed.add_field(
                name="📊 Found Messages",
                value=f"Showing {len(recent_messages)} recent bot messages",
                inline=True
            )
            embed.set_footer(text="This selector will expire in 5 minutes")
            
            # Send the interactive message selector
            view = MessageEditView()
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to load message editor: {e}", ephemeral=True)
    
    @bot.tree.command(name="editembed", description="Edit a bot message's embed")
    @app_commands.describe(
        message_id="The ID of the message to edit",
        title="New embed title",
        description="New embed description",
        color="Embed color (hex code without #, e.g., FF0000 for red)",
        channel="Channel containing the message (optional, defaults to current channel)"
    )
    async def edit_embed(interaction: discord.Interaction, message_id: str, title: str = None, description: str = None, color: str = None, channel: Optional[discord.TextChannel] = None):
        """Edit a bot message's embed"""
        
        # Check if user has manage messages permission
        if not interaction.user.guild_permissions.manage_messages:
            return await interaction.response.send_message("❌ You need `Manage Messages` permission to edit bot embeds!", ephemeral=True)
        
        try:
            # Use provided channel or current channel
            target_channel = channel or interaction.channel
            
            # Fetch the message
            message = await target_channel.fetch_message(int(message_id))
            
            # Check if message was sent by the bot
            if message.author.id != bot.user.id:
                return await interaction.response.send_message("❌ I can only edit messages that I sent!", ephemeral=True)
            
            # Check if message has an embed
            if not message.embeds:
                return await interaction.response.send_message("❌ That message doesn't have an embed to edit!", ephemeral=True)
            
            # Get the current embed and modify it
            current_embed = message.embeds[0]
            new_embed = discord.Embed(
                title=title if title else current_embed.title,
                description=description if description else current_embed.description,
                color=int(color, 16) if color else current_embed.color
            )
            
            # Copy fields from original embed
            for field in current_embed.fields:
                new_embed.add_field(name=field.name, value=field.value, inline=field.inline)
            
            # Copy footer and thumbnail if they exist
            if current_embed.footer:
                new_embed.set_footer(text=current_embed.footer.text, icon_url=current_embed.footer.icon_url)
            if current_embed.thumbnail:
                new_embed.set_thumbnail(url=current_embed.thumbnail.url)
            
            # Edit the message
            await message.edit(embed=new_embed)
            
            embed = discord.Embed(
                title="✅ Embed Edited",
                description=f"Successfully edited embed in {target_channel.mention}",
                color=0x27ae60
            )
            embed.add_field(name="Message ID", value=message_id, inline=True)
            if title:
                embed.add_field(name="New Title", value=title, inline=False)
            if description:
                embed.add_field(name="New Description", value=description[:100] + ("..." if len(description) > 100 else ""), inline=False)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except discord.NotFound:
            await interaction.response.send_message("❌ Message not found! Check the message ID and channel.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to edit that message!", ephemeral=True)
        except ValueError as e:
            if "invalid literal for int()" in str(e):
                await interaction.response.send_message("❌ Invalid message ID or color code!", ephemeral=True)
            else:
                await interaction.response.send_message(f"❌ Invalid input: {e}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to edit embed: {e}", ephemeral=True)
    
    @bot.tree.command(name="delmsg", description="Delete a bot message")
    @app_commands.describe(
        message_id="The ID of the message to delete",
        channel="Channel containing the message (optional, defaults to current channel)"
    )
    async def delete_message(interaction: discord.Interaction, message_id: str, channel: Optional[discord.TextChannel] = None):
        """Delete a bot message by ID"""
        
        # Check if user has manage messages permission
        if not interaction.user.guild_permissions.manage_messages:
            return await interaction.response.send_message("❌ You need `Manage Messages` permission to delete bot messages!", ephemeral=True)
        
        try:
            # Use provided channel or current channel
            target_channel = channel or interaction.channel
            
            # Fetch the message
            message = await target_channel.fetch_message(int(message_id))
            
            # Check if message was sent by the bot
            if message.author.id != bot.user.id:
                return await interaction.response.send_message("❌ I can only delete messages that I sent!", ephemeral=True)
            
            # Delete the message
            await message.delete()
            
            embed = discord.Embed(
                title="✅ Message Deleted",
                description=f"Successfully deleted message from {target_channel.mention}",
                color=0xe74c3c
            )
            embed.add_field(name="Message ID", value=message_id, inline=True)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except discord.NotFound:
            await interaction.response.send_message("❌ Message not found! Check the message ID and channel.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to delete that message!", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ Invalid message ID! Please provide a valid message ID.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to delete message: {e}", ephemeral=True)
    
    print("✅ All utility commands loaded successfully!")