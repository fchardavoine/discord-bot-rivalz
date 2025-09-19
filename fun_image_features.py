"""
Fun Interactive Features and Image Manipulation for Discord Bot
Includes: Meme generation, image filters, custom image generation, fun commands
"""

import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import asyncio
import io
import random
from datetime import datetime, timezone
from typing import Optional, List
import json
import base64
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import requests

class MemeGenerator:
    """Generate custom memes"""
    
    @staticmethod
    def create_meme(template: str, top_text: str = "", bottom_text: str = ""):
        """Create a meme with text overlay"""
        try:
            # Create a basic meme template (500x500 with white background)
            width, height = 500, 500
            img = Image.new('RGB', (width, height), color='white')
            draw = ImageDraw.Draw(img)
            
            # Try to load a basic font, fallback to default
            try:
                font_size = 40
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            # Draw background based on template
            templates = {
                "drake": MemeGenerator._create_drake_template(img, draw),
                "expanding_brain": MemeGenerator._create_brain_template(img, draw),
                "distracted_boyfriend": MemeGenerator._create_boyfriend_template(img, draw),
                "woman_yelling_at_cat": MemeGenerator._create_woman_cat_template(img, draw),
                "two_buttons": MemeGenerator._create_buttons_template(img, draw)
            }
            
            if template in templates:
                img = templates[template]
                draw = ImageDraw.Draw(img)
            
            # Add text
            if top_text:
                MemeGenerator._add_text_to_image(draw, top_text, width//2, 50, font, width-20)
            if bottom_text:
                MemeGenerator._add_text_to_image(draw, bottom_text, width//2, height-100, font, width-20)
            
            # Convert to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            return img_bytes
            
        except Exception as e:
            print(f"Meme generation error: {e}")
            return None
    
    @staticmethod
    def _add_text_to_image(draw, text, x, y, font, max_width):
        """Add text with word wrapping"""
        lines = []
        words = text.split()
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        # Draw text with outline
        for i, line in enumerate(lines):
            text_y = y + (i * 50)
            # Black outline
            for dx in [-2, -1, 0, 1, 2]:
                for dy in [-2, -1, 0, 1, 2]:
                    if dx != 0 or dy != 0:
                        draw.text((x + dx, text_y + dy), line, font=font, fill='black', anchor="mm")
            # White text
            draw.text((x, text_y), line, font=font, fill='white', anchor="mm")
    
    @staticmethod
    def _create_drake_template(img, draw):
        """Create Drake meme template"""
        draw.rectangle([0, 0, 250, 250], fill='lightblue')
        draw.rectangle([250, 0, 500, 250], fill='white')
        draw.rectangle([0, 250, 250, 500], fill='lightgreen')
        draw.rectangle([250, 250, 500, 500], fill='white')
        draw.text((125, 125), "👎", font=ImageFont.load_default(), fill='black', anchor="mm")
        draw.text((125, 375), "👍", font=ImageFont.load_default(), fill='black', anchor="mm")
        return img
    
    @staticmethod
    def _create_brain_template(img, draw):
        """Create expanding brain template"""
        colors = ['lightgray', 'yellow', 'orange', 'gold']
        for i in range(4):
            y = i * 125
            draw.rectangle([0, y, 500, y+125], fill=colors[i])
            draw.text((50, y+62), f"🧠", font=ImageFont.load_default(), fill='black', anchor="mm")
        return img
    
    @staticmethod
    def _create_buttons_template(img, draw):
        """Create two buttons template"""
        draw.rectangle([0, 0, 500, 200], fill='lightblue')
        draw.ellipse([100, 250, 200, 350], fill='red')
        draw.ellipse([300, 250, 400, 350], fill='blue')
        draw.text((150, 300), "A", font=ImageFont.load_default(), fill='white', anchor="mm")
        draw.text((350, 300), "B", font=ImageFont.load_default(), fill='white', anchor="mm")
        return img

class ImageManipulator:
    """Image manipulation and filters"""
    
    @staticmethod
    async def apply_filter(image_url: str, filter_type: str):
        """Apply filter to an image"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status != 200:
                        return None
                    
                    image_data = await response.read()
                    img = Image.open(io.BytesIO(image_data))
                    
                    # Convert to RGB if necessary
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # Apply filters
                    if filter_type == "blur":
                        img = img.filter(ImageFilter.BLUR)
                    elif filter_type == "sharpen":
                        img = img.filter(ImageFilter.SHARPEN)
                    elif filter_type == "emboss":
                        img = img.filter(ImageFilter.EMBOSS)
                    elif filter_type == "sepia":
                        img = ImageManipulator._apply_sepia(img)
                    elif filter_type == "grayscale":
                        img = img.convert('L').convert('RGB')
                    elif filter_type == "invert":
                        from PIL import ImageOps
                        img = ImageOps.invert(img)
                    elif filter_type == "brightness":
                        enhancer = ImageEnhance.Brightness(img)
                        img = enhancer.enhance(1.5)
                    elif filter_type == "contrast":
                        enhancer = ImageEnhance.Contrast(img)
                        img = enhancer.enhance(1.5)
                    
                    # Convert back to bytes
                    img_bytes = io.BytesIO()
                    img.save(img_bytes, format='PNG')
                    img_bytes.seek(0)
                    
                    return img_bytes
                    
        except Exception as e:
            print(f"Image filter error: {e}")
            return None
    
    @staticmethod
    def _apply_sepia(img):
        """Apply sepia effect"""
        pixels = img.load()
        for y in range(img.height):
            for x in range(img.width):
                r, g, b = pixels[x, y]
                tr = int(0.393 * r + 0.769 * g + 0.189 * b)
                tg = int(0.349 * r + 0.686 * g + 0.168 * b)
                tb = int(0.272 * r + 0.534 * g + 0.131 * b)
                pixels[x, y] = (min(255, tr), min(255, tg), min(255, tb))
        return img

class FunCommands:
    """Various fun interactive commands"""
    
    @staticmethod
    def get_random_fact():
        """Get a random fun fact"""
        facts = [
            "🦑 Octopuses have three hearts and blue blood!",
            "🍯 Honey never spoils. Archaeologists have found edible honey in ancient Egyptian tombs!",
            "🐧 Penguins have knees, but you can't see them because they're inside their bodies!",
            "🌙 A day on Venus is longer than its year!",
            "🦋 Butterflies taste with their feet!",
            "🐨 Koalas sleep up to 22 hours a day!",
            "🐙 The plural of octopus can be octopi, octopuses, or octopodes!",
            "🧠 Your brain uses about 20% of your body's energy!",
            "🌈 There are more possible games of chess than atoms in the observable universe!",
            "🐛 Some caterpillars can shoot their poop up to 6 feet away!"
        ]
        return random.choice(facts)
    
    @staticmethod
    def get_random_joke():
        """Get a random dad joke"""
        jokes = [
            ("Why don't scientists trust atoms?", "Because they make up everything! 😄"),
            ("What do you call a fake noodle?", "An impasta! 🍝"),
            ("Why don't eggs tell jokes?", "They'd crack each other up! 🥚"),
            ("What do you call a bear with no teeth?", "A gummy bear! 🐻"),
            ("Why did the scarecrow win an award?", "He was outstanding in his field! 🌾"),
            ("What's orange and sounds like a parrot?", "A carrot! 🥕"),
            ("Why don't skeletons fight each other?", "They don't have the guts! 💀"),
            ("What do you call a dinosaur that crashes his car?", "Tyrannosaurus Wrecks! 🦕"),
            ("Why did the math book look so sad?", "Because it had too many problems! 📚"),
            ("What do you call a sleeping bull?", "A bulldozer! 🐂")
        ]
        return random.choice(jokes)

def setup_fun_image_features(bot):
    """Setup all fun and image manipulation commands"""
    
    meme_gen = MemeGenerator()
    img_manipulator = ImageManipulator()
    fun_commands = FunCommands()
    
    # ============= MEME GENERATION =============
    
    @bot.tree.command(name="meme", description="Generate a custom meme")
    @app_commands.describe(
        template="Meme template to use",
        top_text="Text for top of meme",
        bottom_text="Text for bottom of meme"
    )
    @app_commands.choices(template=[
        app_commands.Choice(name="Drake Pointing", value="drake"),
        app_commands.Choice(name="Expanding Brain", value="expanding_brain"),
        app_commands.Choice(name="Two Buttons", value="two_buttons"),
        app_commands.Choice(name="Woman Yelling at Cat", value="woman_yelling_at_cat"),
        app_commands.Choice(name="Distracted Boyfriend", value="distracted_boyfriend")
    ])
    async def meme_command(interaction: discord.Interaction, template: str, top_text: str = "", bottom_text: str = ""):
        """Generate a custom meme"""
        if len(top_text) > 100 or len(bottom_text) > 100:
            return await interaction.response.send_message("❌ Text too long! Max 100 characters each.", ephemeral=True)
        
        try:
            await interaction.response.defer()
            
            meme_image = meme_gen.create_meme(template, top_text, bottom_text)
            
            if not meme_image:
                return await interaction.followup.send("❌ Failed to generate meme!", ephemeral=True)
            
            file = discord.File(meme_image, filename=f"meme_{template}.png")
            
            embed = discord.Embed(
                title="😂 Custom Meme Generated!",
                color=0xff6b6b,
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_image(url=f"attachment://meme_{template}.png")
            embed.set_footer(text=f"Created by {interaction.user.display_name}")
            
            await interaction.followup.send(embed=embed, file=file)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error generating meme: {e}", ephemeral=True)
    
    # ============= IMAGE FILTERS =============
    
    @bot.tree.command(name="filter", description="Apply a filter to an image")
    @app_commands.describe(
        image_url="URL of the image to filter (or attach an image)",
        filter_type="Type of filter to apply"
    )
    @app_commands.choices(filter_type=[
        app_commands.Choice(name="Blur", value="blur"),
        app_commands.Choice(name="Sharpen", value="sharpen"),
        app_commands.Choice(name="Emboss", value="emboss"),
        app_commands.Choice(name="Sepia", value="sepia"),
        app_commands.Choice(name="Grayscale", value="grayscale"),
        app_commands.Choice(name="Invert", value="invert"),
        app_commands.Choice(name="Brightness", value="brightness"),
        app_commands.Choice(name="Contrast", value="contrast")
    ])
    async def filter_command(interaction: discord.Interaction, filter_type: str, image_url: Optional[str] = None):
        """Apply filter to image"""
        try:
            await interaction.response.defer()
            
            # Get image URL from attachment or parameter
            if not image_url:
                if not interaction.message or not interaction.message.attachments:
                    return await interaction.followup.send("❌ Please provide an image URL or attach an image!", ephemeral=True)
                image_url = interaction.message.attachments[0].url
            
            # Validate URL
            if not any(image_url.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                return await interaction.followup.send("❌ Invalid image format! Use PNG, JPG, JPEG, GIF, or WebP.", ephemeral=True)
            
            filtered_image = await img_manipulator.apply_filter(image_url, filter_type)
            
            if not filtered_image:
                return await interaction.followup.send("❌ Failed to process image!", ephemeral=True)
            
            file = discord.File(filtered_image, filename=f"filtered_{filter_type}.png")
            
            embed = discord.Embed(
                title=f"🎨 {filter_type.title()} Filter Applied",
                color=0x9b59b6,
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_image(url=f"attachment://filtered_{filter_type}.png")
            embed.set_footer(text=f"Filter applied by {interaction.user.display_name}")
            
            await interaction.followup.send(embed=embed, file=file)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error applying filter: {e}", ephemeral=True)
    
    # ============= FUN COMMANDS =============
    
    @bot.tree.command(name="fact", description="Get a random fun fact")
    async def fact_command(interaction: discord.Interaction):
        """Get a random fun fact"""
        fact = fun_commands.get_random_fact()
        
        embed = discord.Embed(
            title="🧠 Fun Fact!",
            description=fact,
            color=0x3498db
        )
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="dadjoke", description="Get a random dad joke")
    async def dad_joke_command(interaction: discord.Interaction):
        """Get a random dad joke"""
        setup, punchline = fun_commands.get_random_joke()
        
        embed = discord.Embed(
            title="😂 Dad Joke Time!",
            color=0xf39c12
        )
        embed.add_field(name="Setup", value=setup, inline=False)
        embed.add_field(name="Punchline", value=punchline, inline=False)
        embed.set_footer(text="Ba dum tss! 🥁")
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="compliment", description="Give someone a compliment")
    @app_commands.describe(user="User to compliment")
    async def compliment_command(interaction: discord.Interaction, user: Optional[discord.Member] = None):
        """Give a compliment"""
        target = user or interaction.user
        
        compliments = [
            "You're absolutely amazing! ✨",
            "Your smile could light up a room! 😊",
            "You have great taste in everything! 👌",
            "You're incredibly thoughtful! 💕",
            "Your positive energy is contagious! ⚡",
            "You make everything better just by being you! 🌟",
            "You're one of a kind! 🦄",
            "Your creativity knows no bounds! 🎨",
            "You have an awesome sense of humor! 😄",
            "You're simply wonderful! 🌈"
        ]
        
        compliment = random.choice(compliments)
        
        embed = discord.Embed(
            title="💝 Compliment Time!",
            description=f"{target.mention}, {compliment}",
            color=0xe91e63,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text=f"Compliment from {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="roast", description="Get a light-hearted roast")
    @app_commands.describe(user="User to playfully roast")
    async def roast_command(interaction: discord.Interaction, user: Optional[discord.Member] = None):
        """Give a playful roast"""
        target = user or interaction.user
        
        roasts = [
            "You're like a software update. Whenever I see you, I immediately think 'not now!' 😅",
            "I'd agree with you, but then we'd both be wrong! 🤷‍♂️",
            "You're not stupid, you just have bad luck thinking! 🧠",
            "I'm not saying you're old, but your birth certificate is in Roman numerals! 📜",
            "You're like a broken pencil... completely pointless! ✏️",
            "I'd explain it to you, but I left my English-to-Duh dictionary at home! 📚",
            "You're about as useful as a chocolate teapot! 🍫☕",
            "If ignorance is bliss, you must be the happiest person alive! 😊",
            "You're not completely useless - you can always serve as a bad example! 👎",
            "I'm not insulting you, I'm describing you! 🔍"
        ]
        
        roast = random.choice(roasts)
        
        embed = discord.Embed(
            title="🔥 Playful Roast!",
            description=f"{target.mention}, {roast}",
            color=0xff4757,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text="All in good fun! 😄")
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="inspire", description="Get an inspirational quote")
    async def inspire_command(interaction: discord.Interaction):
        """Get an inspirational quote"""
        quotes = [
            ("The only way to do great work is to love what you do.", "Steve Jobs"),
            ("Life is what happens to you while you're busy making other plans.", "John Lennon"),
            ("The future belongs to those who believe in the beauty of their dreams.", "Eleanor Roosevelt"),
            ("It is during our darkest moments that we must focus to see the light.", "Aristotle"),
            ("The way to get started is to quit talking and begin doing.", "Walt Disney"),
            ("Your time is limited, don't waste it living someone else's life.", "Steve Jobs"),
            ("If life were predictable it would cease to be life, and be without flavor.", "Eleanor Roosevelt"),
            ("The only impossible journey is the one you never begin.", "Tony Robbins"),
            ("In the end, we will remember not the words of our enemies, but the silence of our friends.", "Martin Luther King Jr."),
            ("Success is not final, failure is not fatal: it is the courage to continue that counts.", "Winston Churchill")
        ]
        
        quote, author = random.choice(quotes)
        
        embed = discord.Embed(
            title="💫 Daily Inspiration",
            description=f"*\"{quote}\"*\n\n— {author}",
            color=0x00d2d3,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="Stay motivated! ✨")
        
        await interaction.response.send_message(embed=embed)
    
    # ============= INTERACTIVE GAMES =============
    
    @bot.tree.command(name="riddle", description="Get a riddle to solve")
    async def riddle_command(interaction: discord.Interaction):
        """Get a riddle"""
        riddles = [
            ("I speak without a mouth and hear without ears. I have no body, but come alive with wind. What am I?", "An echo"),
            ("The more you take, the more you leave behind. What am I?", "Footsteps"),
            ("I'm tall when I'm young and short when I'm old. What am I?", "A candle"),
            ("What has keys but no locks, space but no room, you can enter but can't go inside?", "A keyboard"),
            ("What gets wet while drying?", "A towel"),
            ("I have cities, but no houses. I have mountains, but no trees. I have water, but no fish. What am I?", "A map"),
            ("What comes once in a minute, twice in a moment, but never in a thousand years?", "The letter M"),
            ("What has a head, a tail, is brown, and has no legs?", "A penny"),
            ("What gets bigger the more you take away from it?", "A hole"),
            ("I'm not alive, but I can grow. I don't have lungs, but I need air. What am I?", "Fire")
        ]
        
        riddle, answer = random.choice(riddles)
        
        embed = discord.Embed(
            title="🤔 Riddle Time!",
            description=f"**{riddle}**",
            color=0x9b59b6
        )
        embed.set_footer(text="Think you know the answer? 🧩")
        
        # Create view with reveal button
        view = RiddleView(answer)
        
        await interaction.response.send_message(embed=embed, view=view)

class RiddleView(discord.ui.View):
    """View for riddle answer reveal"""
    
    def __init__(self, answer: str):
        super().__init__(timeout=300)
        self.answer = answer
    
    @discord.ui.button(label="Reveal Answer", style=discord.ButtonStyle.primary, emoji="💡")
    async def reveal_answer(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Reveal the riddle answer"""
        embed = discord.Embed(
            title="💡 Riddle Answer Revealed!",
            description=f"**The answer is:** {self.answer}",
            color=0x00ff00
        )
        embed.set_footer(text="How did you do? 🤓")
        
        # Disable button
        button.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)

def setup_fun_image_features(bot):
    """Setup all fun and image features - exported function"""
    setup_fun_image_features(bot)
    
    print("✅ All fun and image manipulation features loaded successfully!")