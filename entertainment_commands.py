# Entertainment Commands - Fun and Interactive Features
# Comprehensive entertainment commands for Discord bot

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

def setup_entertainment_commands(bot):
    """Setup comprehensive entertainment commands"""
    
    # ============= ADVANCED GAMES =============
    
    @bot.tree.command(name="trivia", description="Start a trivia question")
    @app_commands.describe(category="Trivia category", difficulty="Question difficulty")
    @app_commands.choices(
        category=[
            app_commands.Choice(name="General Knowledge", value="general"),
            app_commands.Choice(name="Science", value="science"),
            app_commands.Choice(name="History", value="history"),
            app_commands.Choice(name="Sports", value="sports"),
            app_commands.Choice(name="Entertainment", value="entertainment")
        ],
        difficulty=[
            app_commands.Choice(name="Easy", value="easy"),
            app_commands.Choice(name="Medium", value="medium"),
            app_commands.Choice(name="Hard", value="hard")
        ]
    )
    async def trivia_game(interaction: discord.Interaction, category: str = "general", difficulty: str = "medium"):
        """Start a trivia question game"""
        
        # Sample trivia questions (in production, would use trivia API)
        trivia_db = {
            "general": {
                "easy": [
                    {"question": "What is the capital of France?", "correct": "Paris", "options": ["London", "Berlin", "Paris", "Madrid"]},
                    {"question": "How many continents are there?", "correct": "7", "options": ["5", "6", "7", "8"]}
                ],
                "medium": [
                    {"question": "What is the largest planet in our solar system?", "correct": "Jupiter", "options": ["Earth", "Jupiter", "Saturn", "Neptune"]},
                    {"question": "In what year did World War II end?", "correct": "1945", "options": ["1943", "1944", "1945", "1946"]}
                ],
                "hard": [
                    {"question": "What is the smallest country in the world?", "correct": "Vatican City", "options": ["Monaco", "Nauru", "Vatican City", "San Marino"]},
                    {"question": "Who wrote the novel '1984'?", "correct": "George Orwell", "options": ["Aldous Huxley", "George Orwell", "Ray Bradbury", "Philip K. Dick"]}
                ]
            }
        }
        
        try:
            questions = trivia_db.get(category, trivia_db["general"])
            question_data = random.choice(questions.get(difficulty, questions["medium"]))
            
            embed = discord.Embed(
                title="🧠 Trivia Time!",
                description=question_data["question"],
                color=0x3498db
            )
            
            # Add options as fields
            for i, option in enumerate(question_data["options"], 1):
                embed.add_field(name=f"{i}️⃣", value=option, inline=True)
            
            embed.set_footer(text=f"Category: {category.title()} | Difficulty: {difficulty.title()} | You have 30 seconds!")
            
            await interaction.response.send_message(embed=embed)
            message = await interaction.original_response()
            
            # Add reaction options
            reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
            for reaction in reactions:
                await message.add_reaction(reaction)
            
            # Wait for reaction
            def check(reaction, user):
                return user == interaction.user and str(reaction.emoji) in reactions and reaction.message.id == message.id
            
            try:
                reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=check)
                
                # Check answer
                selected_index = reactions.index(str(reaction.emoji))
                selected_answer = question_data["options"][selected_index]
                is_correct = selected_answer == question_data["correct"]
                
                result_embed = discord.Embed(
                    title="✅ Correct!" if is_correct else "❌ Incorrect!",
                    description=f"**Your answer:** {selected_answer}\n**Correct answer:** {question_data['correct']}",
                    color=0x00ff00 if is_correct else 0xff0000
                )
                
                await interaction.followup.send(embed=result_embed)
                
            except asyncio.TimeoutError:
                timeout_embed = discord.Embed(
                    title="⏰ Time's Up!",
                    description=f"The correct answer was: **{question_data['correct']}**",
                    color=0xffa500
                )
                await interaction.followup.send(embed=timeout_embed)
                
        except Exception as e:
            await interaction.response.send_message(f"❌ Trivia failed: {e}", ephemeral=True)
    
    # ============= WORD GAMES =============
    
    @bot.tree.command(name="wordle", description="Play a Wordle-style word guessing game")
    async def wordle_game(interaction: discord.Interaction):
        """Start a Wordle-style word guessing game"""
        
        word_list = ["ABOUT", "AFTER", "AGAIN", "BELOW", "COULD", "EVERY", "FIRST", "FOUND", "GREAT", "GROUP", 
                     "HOUSE", "LARGE", "LOCAL", "NEVER", "OTHER", "PUBLIC", "RIGHT", "SHALL", "SMALL", "SOUND",
                     "STILL", "THEIR", "THESE", "THINK", "THREE", "UNDER", "WATER", "WHERE", "WHICH", "WORLD"]
        
        target_word = random.choice(word_list)
        attempts = []
        max_attempts = 6
        
        embed = discord.Embed(
            title="🎯 Wordle Game",
            description="Guess the 5-letter word! You have 6 attempts.\nUse `/guess [word]` to make a guess.",
            color=0x538d22
        )
        embed.add_field(name="Rules", value="🟩 = Correct letter in correct position\n🟨 = Correct letter in wrong position\n⬜ = Letter not in word", inline=False)
        embed.add_field(name="Attempts", value=f"0/{max_attempts}", inline=True)
        
        await interaction.response.send_message(embed=embed)
        
        # Note: In a real implementation, you'd store the game state and handle guesses with a separate command
    
    @bot.tree.command(name="hangman", description="Play hangman word guessing game")
    @app_commands.describe(category="Word category")
    @app_commands.choices(category=[
        app_commands.Choice(name="Animals", value="animals"),
        app_commands.Choice(name="Countries", value="countries"),
        app_commands.Choice(name="Food", value="food"),
        app_commands.Choice(name="Movies", value="movies")
    ])
    async def hangman_game(interaction: discord.Interaction, category: str = "animals"):
        """Start a hangman word guessing game"""
        
        word_categories = {
            "animals": ["ELEPHANT", "GIRAFFE", "PENGUIN", "DOLPHIN", "BUTTERFLY"],
            "countries": ["AUSTRALIA", "BRAZIL", "CANADA", "DENMARK", "EGYPT"],
            "food": ["PIZZA", "HAMBURGER", "SPAGHETTI", "CHOCOLATE", "STRAWBERRY"],
            "movies": ["AVATAR", "TITANIC", "INCEPTION", "INTERSTELLAR", "GLADIATOR"]
        }
        
        target_word = random.choice(word_categories.get(category, word_categories["animals"]))
        guessed_letters = []
        wrong_guesses = 0
        max_wrong = 6
        
        # Create display word
        display_word = " ".join("_" if letter != " " else " " for letter in target_word)
        
        hangman_stages = [
            "```\n  +---+\n  |   |\n      |\n      |\n      |\n      |\n=========```",
            "```\n  +---+\n  |   |\n  O   |\n      |\n      |\n      |\n=========```",
            "```\n  +---+\n  |   |\n  O   |\n  |   |\n      |\n      |\n=========```",
            "```\n  +---+\n  |   |\n  O   |\n /|   |\n      |\n      |\n=========```",
            "```\n  +---+\n  |   |\n  O   |\n /|\\  |\n      |\n      |\n=========```",
            "```\n  +---+\n  |   |\n  O   |\n /|\\  |\n /    |\n      |\n=========```",
            "```\n  +---+\n  |   |\n  O   |\n /|\\  |\n / \\  |\n      |\n=========```"
        ]
        
        embed = discord.Embed(
            title="🎮 Hangman Game",
            description=f"**Category:** {category.title()}\n**Word:** `{display_word}`",
            color=0xe74c3c
        )
        embed.add_field(name="Hangman", value=hangman_stages[wrong_guesses], inline=False)
        embed.add_field(name="Wrong Guesses", value=f"{wrong_guesses}/{max_wrong}", inline=True)
        embed.add_field(name="Guessed Letters", value="None" if not guessed_letters else ", ".join(guessed_letters), inline=True)
        embed.set_footer(text="Type letters to guess! Use reactions or type in chat.")
        
        await interaction.response.send_message(embed=embed)
        
        # Note: In a real implementation, you'd handle letter guessing with reactions or message events
    
    # ============= RANDOM GENERATORS =============
    
    @bot.tree.command(name="joke", description="Get a random joke")
    @app_commands.describe(category="Joke category")
    @app_commands.choices(category=[
        app_commands.Choice(name="Dad Jokes", value="dad"),
        app_commands.Choice(name="Programming", value="programming"),
        app_commands.Choice(name="General", value="general"),
        app_commands.Choice(name="Science", value="science")
    ])
    async def random_joke(interaction: discord.Interaction, category: str = "general"):
        """Get a random joke from various categories"""
        
        jokes = {
            "dad": [
                "Why don't scientists trust atoms? Because they make up everything!",
                "Did you hear about the mathematician who's afraid of negative numbers? He'll stop at nothing to avoid them!",
                "Why do we tell actors to 'break a leg?' Because every play has a cast!",
                "What do you call a fake noodle? An impasta!",
                "Why did the scarecrow win an award? He was outstanding in his field!"
            ],
            "programming": [
                "Why do programmers prefer dark mode? Because light attracts bugs!",
                "How many programmers does it take to change a light bulb? None, that's a hardware problem!",
                "Why do Java developers wear glasses? Because they can't C#!",
                "There are only 10 types of people in the world: those who understand binary and those who don't.",
                "A SQL query goes into a bar, walks up to two tables and asks... 'Can I join you?'"
            ],
            "general": [
                "Why don't eggs tell jokes? They'd crack each other up!",
                "What do you call a bear with no teeth? A gummy bear!",
                "Why did the bicycle fall over? It was two tired!",
                "What do you call a sleeping bull? A bulldozer!",
                "Why don't skeletons fight each other? They don't have the guts!"
            ],
            "science": [
                "Why can't you trust an atom? Because they make up everything!",
                "What did the biologist wear to impress their date? Designer genes!",
                "Why are chemists excellent for solving problems? They have all the solutions!",
                "What do you call an educated tube? A graduated cylinder!",
                "Why did the physics teacher break up with the biology teacher? There was no chemistry!"
            ]
        }
        
        joke = random.choice(jokes.get(category, jokes["general"]))
        
        embed = discord.Embed(
            title="😂 Random Joke",
            description=joke,
            color=0xf39c12
        )
        embed.set_footer(text=f"Category: {category.title()}")
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="quote", description="Get an inspirational quote")
    async def random_quote(interaction: discord.Interaction):
        """Get a random inspirational quote"""
        
        quotes = [
            {"text": "The only way to do great work is to love what you do.", "author": "Steve Jobs"},
            {"text": "Life is what happens to you while you're busy making other plans.", "author": "John Lennon"},
            {"text": "The future belongs to those who believe in the beauty of their dreams.", "author": "Eleanor Roosevelt"},
            {"text": "It is during our darkest moments that we must focus to see the light.", "author": "Aristotle"},
            {"text": "The only impossible journey is the one you never begin.", "author": "Tony Robbins"},
            {"text": "In the middle of difficulty lies opportunity.", "author": "Albert Einstein"},
            {"text": "Success is not final, failure is not fatal: it is the courage to continue that counts.", "author": "Winston Churchill"},
            {"text": "The way to get started is to quit talking and begin doing.", "author": "Walt Disney"},
            {"text": "Innovation distinguishes between a leader and a follower.", "author": "Steve Jobs"},
            {"text": "Your time is limited, don't waste it living someone else's life.", "author": "Steve Jobs"}
        ]
        
        quote = random.choice(quotes)
        
        embed = discord.Embed(
            title="💭 Inspirational Quote",
            description=f"*\"{quote['text']}\"*",
            color=0x9b59b6
        )
        embed.set_footer(text=f"— {quote['author']}")
        
        await interaction.response.send_message(embed=embed)
    
    # ============= DICE AND RANDOM =============
    
    @bot.tree.command(name="dice", description="Roll dice with custom sides and count")
    @app_commands.describe(
        sides="Number of sides on the dice",
        count="Number of dice to roll",
        modifier="Modifier to add to the total"
    )
    async def roll_dice(interaction: discord.Interaction, sides: int = 6, count: int = 1, modifier: int = 0):
        """Roll dice with custom parameters"""
        
        if sides < 2 or sides > 100:
            return await interaction.response.send_message("❌ Dice sides must be between 2 and 100!", ephemeral=True)
        
        if count < 1 or count > 20:
            return await interaction.response.send_message("❌ Number of dice must be between 1 and 20!", ephemeral=True)
        
        rolls = [random.randint(1, sides) for _ in range(count)]
        total = sum(rolls) + modifier
        
        embed = discord.Embed(
            title="🎲 Dice Roll",
            color=0xe74c3c
        )
        
        if count == 1:
            embed.add_field(name="Roll", value=f"**{rolls[0]}**", inline=True)
        else:
            embed.add_field(name="Individual Rolls", value=" + ".join(map(str, rolls)), inline=False)
            embed.add_field(name="Sum", value=str(sum(rolls)), inline=True)
        
        if modifier != 0:
            embed.add_field(name="Modifier", value=f"{modifier:+d}", inline=True)
            embed.add_field(name="Final Total", value=f"**{total}**", inline=True)
        elif count > 1:
            embed.add_field(name="Total", value=f"**{total}**", inline=True)
        
        embed.set_footer(text=f"{count}d{sides}{f' {modifier:+d}' if modifier != 0 else ''}")
        
        await interaction.response.send_message(embed=embed)
    
    # ============= CHOICE MAKERS =============
    
    @bot.tree.command(name="choose", description="Choose randomly from options")
    @app_commands.describe(options="Options separated by commas or semicolons")
    async def random_choose(interaction: discord.Interaction, options: str):
        """Choose randomly from a list of options"""
        
        # Split by comma or semicolon
        if ';' in options:
            choices = [choice.strip() for choice in options.split(';') if choice.strip()]
        else:
            choices = [choice.strip() for choice in options.split(',') if choice.strip()]
        
        if len(choices) < 2:
            return await interaction.response.send_message("❌ Please provide at least 2 options separated by commas!", ephemeral=True)
        
        if len(choices) > 20:
            return await interaction.response.send_message("❌ Too many options! Please provide 20 or fewer.", ephemeral=True)
        
        chosen = random.choice(choices)
        
        embed = discord.Embed(
            title="🎯 Random Choice",
            description=f"I choose: **{chosen}**",
            color=0x3498db
        )
        embed.add_field(name="Options", value="\n".join(f"• {choice}" for choice in choices), inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    # ============= TRUTH OR DARE =============
    
    @bot.tree.command(name="truthordare", description="Get a truth or dare challenge")
    @app_commands.describe(type="Choose truth or dare")
    @app_commands.choices(type=[
        app_commands.Choice(name="Truth", value="truth"),
        app_commands.Choice(name="Dare", value="dare"),
        app_commands.Choice(name="Random", value="random")
    ])
    async def truth_or_dare(interaction: discord.Interaction, type: str = "random"):
        """Get a truth or dare challenge"""
        
        truths = [
            "What's the most embarrassing thing you've ever done?",
            "What's your biggest fear?",
            "What's the weirdest dream you've ever had?",
            "What's your most unpopular opinion?",
            "What's the biggest lie you've ever told?",
            "What's your most embarrassing childhood memory?",
            "What's the strangest thing you've ever eaten?",
            "What's your biggest pet peeve?",
            "What's the most trouble you've ever gotten into?",
            "What's your most irrational fear?"
        ]
        
        dares = [
            "Do 10 push-ups",
            "Sing your favorite song out loud",
            "Do your best impression of a celebrity",
            "Dance for 30 seconds without music",
            "Say the alphabet backwards",
            "Do your best animal impression",
            "Try to lick your elbow",
            "Stand on one foot for 1 minute",
            "Say something in a different accent",
            "Do 5 jumping jacks"
        ]
        
        if type == "random":
            type = random.choice(["truth", "dare"])
        
        if type == "truth":
            challenge = random.choice(truths)
            color = 0x3498db
            emoji = "🤔"
        else:
            challenge = random.choice(dares)
            color = 0xe74c3c
            emoji = "💪"
        
        embed = discord.Embed(
            title=f"{emoji} {type.title()}",
            description=challenge,
            color=color
        )
        embed.set_footer(text=f"Challenge for {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)
    
    # ============= WOULD YOU RATHER =============
    
    @bot.tree.command(name="wouldyourather", description="Get a 'Would You Rather' question")
    async def would_you_rather(interaction: discord.Interaction):
        """Get a 'Would You Rather' question"""
        
        questions = [
            {"option1": "Have the ability to fly", "option2": "Have the ability to be invisible"},
            {"option1": "Always be 10 minutes late", "option2": "Always be 20 minutes early"},
            {"option1": "Be able to read minds", "option2": "Be able to predict the future"},
            {"option1": "Have unlimited money", "option2": "Have unlimited time"},
            {"option1": "Live in the past", "option2": "Live in the future"},
            {"option1": "Be famous but poor", "option2": "Be rich but unknown"},
            {"option1": "Never be able to use a smartphone", "option2": "Never be able to use a computer"},
            {"option1": "Always have to say everything on your mind", "option2": "Never be able to speak again"},
            {"option1": "Be able to speak any language", "option2": "Be able to talk to animals"},
            {"option1": "Have the power of super strength", "option2": "Have the power of super speed"}
        ]
        
        question = random.choice(questions)
        
        embed = discord.Embed(
            title="🤔 Would You Rather...",
            description=f"**Option 1:** {question['option1']}\n\n**Option 2:** {question['option2']}",
            color=0x9b59b6
        )
        embed.set_footer(text="React with 1️⃣ or 2️⃣ to vote!")
        
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        await message.add_reaction("1️⃣")
        await message.add_reaction("2️⃣")
    
    print("✅ All entertainment commands loaded successfully!")