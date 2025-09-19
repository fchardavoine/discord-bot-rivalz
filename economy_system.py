"""
Economy and Engagement System for Discord Bot
Includes: XP/Level system, virtual currency, mini-games, shop system, daily rewards
"""

import discord
from discord import app_commands
from discord.ext import commands, tasks
import random
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict
import json
from db_app import app, with_db_context
from models import *

class EconomyGame:
    """Base class for economy games"""
    
    @staticmethod
    async def update_game_stats(user_id: int, guild_id: int, game_type: str, won: bool, bet: int, winnings: int):
        """Update game statistics"""
        try:
            with db.session.begin():
                stats = GameStats.query.filter_by(
                    user_id=user_id,
                    guild_id=guild_id,
                    game_type=game_type
                ).first()
                
                if not stats:
                    stats = GameStats(
                        user_id=user_id,
                        guild_id=guild_id,
                        game_type=game_type
                    )
                    db.session.add(stats)
                
                stats.games_played += 1
                stats.total_bet += bet
                stats.last_played = datetime.now(timezone.utc)
                
                if won:
                    stats.games_won += 1
                    stats.total_won += winnings
                    stats.current_streak += 1
                    if stats.current_streak > stats.best_streak:
                        stats.best_streak = stats.current_streak
                    if winnings > stats.biggest_win:
                        stats.biggest_win = winnings
                else:
                    stats.current_streak = 0
                    if bet > stats.biggest_loss:
                        stats.biggest_loss = bet
                
                db.session.commit()
        except Exception as e:
            print(f"Error updating game stats: {e}")

class Blackjack(EconomyGame):
    """Blackjack mini-game"""
    
    def __init__(self):
        self.deck = self._create_deck()
        self.player_hand = []
        self.dealer_hand = []
    
    def _create_deck(self):
        """Create a standard deck of cards"""
        suits = ['♠️', '♥️', '♦️', '♣️']
        ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        deck = []
        for suit in suits:
            for rank in ranks:
                deck.append({'rank': rank, 'suit': suit, 'value': self._get_card_value(rank)})
        random.shuffle(deck)
        return deck
    
    def _get_card_value(self, rank):
        """Get numeric value of card"""
        if rank in ['J', 'Q', 'K']:
            return 10
        elif rank == 'A':
            return 11  # Aces are handled specially
        else:
            return int(rank)
    
    def _calculate_hand_value(self, hand):
        """Calculate hand value, handling Aces"""
        value = sum(card['value'] for card in hand)
        aces = sum(1 for card in hand if card['rank'] == 'A')
        
        # Adjust for Aces
        while value > 21 and aces > 0:
            value -= 10
            aces -= 1
        
        return value
    
    def deal_initial_cards(self):
        """Deal initial 2 cards to player and dealer"""
        self.player_hand = [self.deck.pop(), self.deck.pop()]
        self.dealer_hand = [self.deck.pop(), self.deck.pop()]
    
    def hit(self, is_dealer=False):
        """Draw a card"""
        card = self.deck.pop()
        if is_dealer:
            self.dealer_hand.append(card)
        else:
            self.player_hand.append(card)
        return card
    
    def get_hand_string(self, hand, hide_first=False):
        """Convert hand to display string"""
        if hide_first:
            cards = ['🎴'] + [f"{card['rank']}{card['suit']}" for card in hand[1:]]
        else:
            cards = [f"{card['rank']}{card['suit']}" for card in hand]
        return ' '.join(cards)
    
    def play_dealer(self):
        """Play dealer hand automatically"""
        while self._calculate_hand_value(self.dealer_hand) < 17:
            self.hit(is_dealer=True)
    
    def determine_winner(self):
        """Determine game outcome"""
        player_value = self._calculate_hand_value(self.player_hand)
        dealer_value = self._calculate_hand_value(self.dealer_hand)
        
        if player_value > 21:
            return 'bust'
        elif dealer_value > 21:
            return 'dealer_bust'
        elif player_value == dealer_value:
            return 'push'
        elif player_value > dealer_value:
            return 'win'
        else:
            return 'lose'

class SlotMachine(EconomyGame):
    """Slot machine mini-game"""
    
    def __init__(self):
        self.symbols = {
            '🍒': {'weight': 30, 'multiplier': 2},
            '🍋': {'weight': 25, 'multiplier': 3},
            '🍊': {'weight': 20, 'multiplier': 4},
            '🍇': {'weight': 15, 'multiplier': 5},
            '🔔': {'weight': 8, 'multiplier': 10},
            '⭐': {'weight': 2, 'multiplier': 50}
        }
    
    def spin(self):
        """Spin the slot machine"""
        symbols = list(self.symbols.keys())
        weights = [self.symbols[s]['weight'] for s in symbols]
        
        result = []
        for _ in range(3):
            result.append(random.choices(symbols, weights=weights)[0])
        
        return result
    
    def calculate_winnings(self, result, bet):
        """Calculate winnings from spin result"""
        # Check for three of a kind
        if result[0] == result[1] == result[2]:
            multiplier = self.symbols[result[0]]['multiplier']
            return bet * multiplier
        
        # Check for two of a kind (smaller payout)
        if result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
            symbol = result[0] if result[0] == result[1] else (result[1] if result[1] == result[2] else result[0])
            multiplier = self.symbols[symbol]['multiplier'] // 2
            return bet * max(1, multiplier)
        
        return 0

def setup_economy_system(bot):
    """Setup all economy and engagement commands"""
    
    # ============= ECONOMY MANAGEMENT =============
    
    async def get_or_create_user(user_id: int, guild_id: int, username: str, display_name: str = None) -> UserProfile:
        """Get or create user profile"""
        user = UserProfile.query.filter_by(user_id=user_id, guild_id=guild_id).first()
        
        if not user:
            with db.session.begin():
                user = UserProfile(
                    user_id=user_id,
                    guild_id=guild_id,
                    username=username,
                    display_name=display_name or username
                )
                db.session.add(user)
                db.session.commit()
        
        return user
    
    async def add_transaction(user_id: int, guild_id: int, amount: int, transaction_type: str, reason: str = None):
        """Add a transaction record"""
        try:
            with db.session.begin():
                transaction = Transaction(
                    user_id=user_id,
                    guild_id=guild_id,
                    transaction_type=transaction_type,
                    amount=amount,
                    reason=reason
                )
                db.session.add(transaction)
                db.session.commit()
        except Exception as e:
            print(f"Error adding transaction: {e}")
    
    @bot.tree.command(name="balance", description="Check your coin balance and level")
    @app_commands.describe(user="User to check balance for (optional)")
    async def balance_command(interaction: discord.Interaction, user: Optional[discord.Member] = None):
        """Check balance and level"""
        target_user = user or interaction.user
        
        try:
            profile = await get_or_create_user(
                target_user.id,
                interaction.guild.id,
                target_user.name,
                target_user.display_name
            )
            
            # Calculate XP needed for next level
            current_level_xp = (profile.level - 1) ** 2 * 100
            next_level_xp = profile.level ** 2 * 100
            xp_progress = profile.xp - current_level_xp
            xp_needed = next_level_xp - current_level_xp
            
            embed = discord.Embed(
                title=f"💰 {target_user.display_name}'s Profile",
                color=0xffd700
            )
            embed.set_thumbnail(url=target_user.display_avatar.url)
            
            embed.add_field(
                name="💰 Balance",
                value=f"**{profile.coins:,}** coins",
                inline=True
            )
            
            embed.add_field(
                name="📈 Level",
                value=f"Level **{profile.level}**\nXP: {profile.xp:,}",
                inline=True
            )
            
            embed.add_field(
                name="⭐ Progress",
                value=f"{xp_progress}/{xp_needed} XP\n{'█' * int(xp_progress/xp_needed*10)}{'░' * (10-int(xp_progress/xp_needed*10))}",
                inline=True
            )
            
            embed.add_field(
                name="📊 Activity",
                value=f"Messages: {profile.messages_sent:,}\nCommands: {profile.commands_used:,}",
                inline=True
            )
            
            # Check if they can claim daily
            can_claim_daily = True
            if profile.daily_claimed:
                time_since = datetime.now(timezone.utc) - profile.daily_claimed
                can_claim_daily = time_since.total_seconds() >= 86400
            
            if can_claim_daily:
                embed.add_field(
                    name="🎁 Daily Reward",
                    value="✅ Available! Use `/daily`",
                    inline=True
                )
            else:
                next_daily = profile.daily_claimed + timedelta(days=1)
                embed.add_field(
                    name="🎁 Daily Reward",
                    value=f"<t:{int(next_daily.timestamp())}:R>",
                    inline=True
                )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error checking balance: {e}", ephemeral=True)
    
    @bot.tree.command(name="daily", description="Claim your daily coin reward")
    async def daily_reward(interaction: discord.Interaction):
        """Claim daily reward"""
        try:
            profile = await get_or_create_user(
                interaction.user.id,
                interaction.guild.id,
                interaction.user.name,
                interaction.user.display_name
            )
            
            # Check if already claimed today
            now = datetime.now(timezone.utc)
            if profile.daily_claimed:
                time_since = now - profile.daily_claimed
                if time_since.total_seconds() < 86400:  # 24 hours
                    next_claim = profile.daily_claimed + timedelta(days=1)
                    return await interaction.response.send_message(
                        f"⏰ You already claimed your daily reward! Next claim: <t:{int(next_claim.timestamp())}:R>",
                        ephemeral=True
                    )
            
            # Calculate reward (base + level bonus)
            base_reward = 100
            level_bonus = profile.level * 10
            total_reward = base_reward + level_bonus
            
            # Update profile
            with db.session.begin():
                profile.coins += total_reward
                profile.daily_claimed = now
            
            # Add transaction
            await add_transaction(
                interaction.user.id,
                interaction.guild.id,
                total_reward,
                'earn',
                'Daily reward'
            )
            
            embed = discord.Embed(
                title="🎁 Daily Reward Claimed!",
                description=f"You received **{total_reward:,}** coins!",
                color=0x00ff00
            )
            embed.add_field(
                name="💰 New Balance",
                value=f"{profile.coins:,} coins",
                inline=True
            )
            embed.add_field(
                name="📈 Breakdown",
                value=f"Base: {base_reward}\nLevel Bonus: {level_bonus}",
                inline=True
            )
            embed.set_footer(text="Come back tomorrow for another reward!")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error claiming daily reward: {e}", ephemeral=True)
    
    @bot.tree.command(name="leaderboard", description="View the server's richest members")
    @app_commands.describe(category="Leaderboard category")
    @app_commands.choices(category=[
        app_commands.Choice(name="Coins", value="coins"),
        app_commands.Choice(name="Level", value="level"),
        app_commands.Choice(name="Messages", value="messages"),
        app_commands.Choice(name="Commands", value="commands")
    ])
    async def leaderboard_command(interaction: discord.Interaction, category: str = "coins"):
        """Display server leaderboard"""
        try:
            # Query top users
            if category == "coins":
                users = UserProfile.query.filter_by(guild_id=interaction.guild.id).order_by(UserProfile.coins.desc()).limit(10).all()
                title = "💰 Coin Leaderboard"
                value_key = "coins"
                emoji = "💰"
            elif category == "level":
                users = UserProfile.query.filter_by(guild_id=interaction.guild.id).order_by(UserProfile.level.desc(), UserProfile.xp.desc()).limit(10).all()
                title = "📈 Level Leaderboard"
                value_key = "level"
                emoji = "⭐"
            elif category == "messages":
                users = UserProfile.query.filter_by(guild_id=interaction.guild.id).order_by(UserProfile.messages_sent.desc()).limit(10).all()
                title = "💬 Message Leaderboard"
                value_key = "messages_sent"
                emoji = "💬"
            else:  # commands
                users = UserProfile.query.filter_by(guild_id=interaction.guild.id).order_by(UserProfile.commands_used.desc()).limit(10).all()
                title = "🤖 Command Leaderboard"
                value_key = "commands_used"
                emoji = "🤖"
            
            if not users:
                return await interaction.response.send_message("📊 No leaderboard data available yet.", ephemeral=True)
            
            embed = discord.Embed(
                title=title,
                color=0xffd700
            )
            
            leaderboard_text = ""
            for i, user_profile in enumerate(users, 1):
                user = interaction.guild.get_member(user_profile.user_id)
                if user:
                    value = getattr(user_profile, value_key)
                    if i == 1:
                        medal = "🥇"
                    elif i == 2:
                        medal = "🥈"
                    elif i == 3:
                        medal = "🥉"
                    else:
                        medal = f"{i}."
                    
                    leaderboard_text += f"{medal} **{user.display_name}** - {emoji} {value:,}\n"
            
            embed.description = leaderboard_text
            embed.set_footer(text=f"Leaderboard for {interaction.guild.name}")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error generating leaderboard: {e}", ephemeral=True)
    
    # ============= GAMBLING GAMES =============
    
    @bot.tree.command(name="blackjack", description="Play blackjack with your coins")
    @app_commands.describe(bet="Amount of coins to bet")
    async def blackjack_command(interaction: discord.Interaction, bet: int):
        """Play blackjack game"""
        if bet < 10:
            return await interaction.response.send_message("❌ Minimum bet is 10 coins!", ephemeral=True)
        
        if bet > 1000:
            return await interaction.response.send_message("❌ Maximum bet is 1000 coins!", ephemeral=True)
        
        try:
            # Check user balance
            profile = await get_or_create_user(
                interaction.user.id,
                interaction.guild.id,
                interaction.user.name,
                interaction.user.display_name
            )
            
            if profile.coins < bet:
                return await interaction.response.send_message(
                    f"❌ Insufficient balance! You have {profile.coins:,} coins.",
                    ephemeral=True
                )
            
            # Start game
            game = Blackjack()
            game.deal_initial_cards()
            
            player_value = game._calculate_hand_value(game.player_hand)
            dealer_value = game._calculate_hand_value([game.dealer_hand[0]])  # Only show first card
            
            embed = discord.Embed(
                title="🃏 Blackjack",
                color=0xff0000
            )
            embed.add_field(
                name="Your Hand",
                value=f"{game.get_hand_string(game.player_hand)}\n**Value:** {player_value}",
                inline=True
            )
            embed.add_field(
                name="Dealer Hand",
                value=f"{game.get_hand_string(game.dealer_hand, hide_first=True)}\n**Showing:** {dealer_value}",
                inline=True
            )
            embed.add_field(
                name="Bet",
                value=f"{bet:,} coins",
                inline=True
            )
            
            # Check for blackjack
            if player_value == 21:
                game.play_dealer()
                dealer_final = game._calculate_hand_value(game.dealer_hand)
                
                embed.add_field(
                    name="Result",
                    value="🎉 **BLACKJACK!** You win!",
                    inline=False
                )
                
                winnings = int(bet * 2.5)  # Blackjack pays 2.5x
                
                # Update balance
                with db.session.begin():
                    profile.coins = profile.coins - bet + winnings
                
                await EconomyGame.update_game_stats(interaction.user.id, interaction.guild.id, 'blackjack', True, bet, winnings)
                await add_transaction(interaction.user.id, interaction.guild.id, winnings - bet, 'gamble', 'Blackjack win')
                
                embed.add_field(name="Winnings", value=f"+{winnings:,} coins", inline=True)
                embed.add_field(name="New Balance", value=f"{profile.coins:,} coins", inline=True)
                
                return await interaction.response.send_message(embed=embed)
            
            # Create view with hit/stand buttons
            view = BlackjackView(game, bet, profile, interaction.user.id, interaction.guild.id)
            await interaction.response.send_message(embed=embed, view=view)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error starting blackjack: {e}", ephemeral=True)
    
    @bot.tree.command(name="slots", description="Play the slot machine")
    @app_commands.describe(bet="Amount of coins to bet")
    async def slots_command(interaction: discord.Interaction, bet: int):
        """Play slot machine"""
        if bet < 5:
            return await interaction.response.send_message("❌ Minimum bet is 5 coins!", ephemeral=True)
        
        if bet > 500:
            return await interaction.response.send_message("❌ Maximum bet is 500 coins!", ephemeral=True)
        
        try:
            # Check user balance
            profile = await get_or_create_user(
                interaction.user.id,
                interaction.guild.id,
                interaction.user.name,
                interaction.user.display_name
            )
            
            if profile.coins < bet:
                return await interaction.response.send_message(
                    f"❌ Insufficient balance! You have {profile.coins:,} coins.",
                    ephemeral=True
                )
            
            # Play slots
            slots = SlotMachine()
            result = slots.spin()
            winnings = slots.calculate_winnings(result, bet)
            
            # Update balance
            with db.session.begin():
                profile.coins = profile.coins - bet + winnings
                db.session.commit()
            
            # Update stats
            await EconomyGame.update_game_stats(
                interaction.user.id,
                interaction.guild.id,
                'slots',
                winnings > 0,
                bet,
                winnings
            )
            
            # Add transaction
            net_change = winnings - bet
            if net_change != 0:
                await add_transaction(
                    interaction.user.id,
                    interaction.guild.id,
                    net_change,
                    'gamble',
                    f"Slots {'win' if net_change > 0 else 'loss'}"
                )
            
            # Create result embed
            embed = discord.Embed(
                title="🎰 Slot Machine",
                color=0xffd700 if winnings > 0 else 0xff0000
            )
            
            slot_display = f"┏━━━━━━━━━┓\n┃ {result[0]} ┃ {result[1]} ┃ {result[2]} ┃\n┗━━━━━━━━━┛"
            embed.add_field(
                name="Result",
                value=f"```{slot_display}```",
                inline=False
            )
            
            if winnings > 0:
                embed.add_field(
                    name="🎉 Winner!",
                    value=f"You won **{winnings:,}** coins!\n(Profit: +{winnings - bet:,})",
                    inline=True
                )
                embed.color = 0x00ff00
            else:
                embed.add_field(
                    name="😔 No luck",
                    value=f"You lost **{bet:,}** coins.\nBetter luck next time!",
                    inline=True
                )
            
            embed.add_field(
                name="Balance",
                value=f"{profile.coins:,} coins",
                inline=True
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error playing slots: {e}", ephemeral=True)
    
    # ============= COIN TRANSFER =============
    
    @bot.tree.command(name="give", description="Give coins to another user")
    @app_commands.describe(user="User to give coins to", amount="Amount of coins to give")
    async def give_coins(interaction: discord.Interaction, user: discord.Member, amount: int):
        """Give coins to another user"""
        if user.bot:
            return await interaction.response.send_message("❌ You can't give coins to bots!", ephemeral=True)
        
        if user.id == interaction.user.id:
            return await interaction.response.send_message("❌ You can't give coins to yourself!", ephemeral=True)
        
        if amount < 1:
            return await interaction.response.send_message("❌ Amount must be positive!", ephemeral=True)
        
        if amount > 10000:
            return await interaction.response.send_message("❌ Maximum transfer is 10,000 coins!", ephemeral=True)
        
        try:
            # Get profiles
            giver_profile = await get_or_create_user(
                interaction.user.id,
                interaction.guild.id,
                interaction.user.name,
                interaction.user.display_name
            )
            
            receiver_profile = await get_or_create_user(
                user.id,
                interaction.guild.id,
                user.name,
                user.display_name
            )
            
            if giver_profile.coins < amount:
                return await interaction.response.send_message(
                    f"❌ Insufficient balance! You have {giver_profile.coins:,} coins.",
                    ephemeral=True
                )
            
            # Transfer coins
            with db.session.begin():
                giver_profile.coins -= amount
                receiver_profile.coins += amount
                db.session.commit()
            
            # Add transactions
            await add_transaction(interaction.user.id, interaction.guild.id, -amount, 'gift', f'Gift to {user.display_name}')
            await add_transaction(user.id, interaction.guild.id, amount, 'gift', f'Gift from {interaction.user.display_name}')
            
            embed = discord.Embed(
                title="💝 Coin Transfer",
                description=f"**{interaction.user.display_name}** gave **{amount:,}** coins to **{user.display_name}**!",
                color=0x00ff00
            )
            embed.add_field(
                name=f"{interaction.user.display_name}'s Balance",
                value=f"{giver_profile.coins:,} coins",
                inline=True
            )
            embed.add_field(
                name=f"{user.display_name}'s Balance",
                value=f"{receiver_profile.coins:,} coins",
                inline=True
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error transferring coins: {e}", ephemeral=True)
    
    print("✅ All economy system commands loaded successfully!")

# Blackjack View for interactive gameplay
class BlackjackView(discord.ui.View):
    def __init__(self, game, bet, profile, user_id, guild_id):
        super().__init__(timeout=60)
        self.game = game
        self.bet = bet
        self.profile = profile
        self.user_id = user_id
        self.guild_id = guild_id
    
    @discord.ui.button(label="Hit", style=discord.ButtonStyle.primary, emoji="🃏")
    async def hit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ This isn't your game!", ephemeral=True)
        
        # Player hits
        self.game.hit()
        player_value = self.game._calculate_hand_value(self.game.player_hand)
        
        embed = discord.Embed(title="🃏 Blackjack", color=0xff0000)
        embed.add_field(
            name="Your Hand",
            value=f"{self.game.get_hand_string(self.game.player_hand)}\n**Value:** {player_value}",
            inline=True
        )
        embed.add_field(
            name="Dealer Hand",
            value=f"{self.game.get_hand_string(self.game.dealer_hand, hide_first=True)}",
            inline=True
        )
        embed.add_field(name="Bet", value=f"{self.bet:,} coins", inline=True)
        
        # Check for bust
        if player_value > 21:
            await self._end_game(interaction, embed, "bust")
        else:
            await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="Stand", style=discord.ButtonStyle.secondary, emoji="✋")
    async def stand_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ This isn't your game!", ephemeral=True)
        
        # Player stands, dealer plays
        self.game.play_dealer()
        
        embed = discord.Embed(title="🃏 Blackjack - Final Results", color=0xff0000)
        embed.add_field(
            name="Your Hand",
            value=f"{self.game.get_hand_string(self.game.player_hand)}\n**Value:** {self.game._calculate_hand_value(self.game.player_hand)}",
            inline=True
        )
        embed.add_field(
            name="Dealer Hand",
            value=f"{self.game.get_hand_string(self.game.dealer_hand)}\n**Value:** {self.game._calculate_hand_value(self.game.dealer_hand)}",
            inline=True
        )
        embed.add_field(name="Bet", value=f"{self.bet:,} coins", inline=True)
        
        result = self.game.determine_winner()
        await self._end_game(interaction, embed, result)
    
    async def _end_game(self, interaction, embed, result):
        """End the game and update balances"""
        won = False
        winnings = 0
        
        if result == "bust":
            embed.add_field(name="Result", value="💥 **BUST!** You lose!", inline=False)
            winnings = 0
        elif result == "dealer_bust":
            embed.add_field(name="Result", value="🎉 **DEALER BUST!** You win!", inline=False)
            winnings = self.bet * 2
            won = True
        elif result == "win":
            embed.add_field(name="Result", value="🎉 **YOU WIN!**", inline=False)
            winnings = self.bet * 2
            won = True
        elif result == "lose":
            embed.add_field(name="Result", value="😔 **YOU LOSE!**", inline=False)
            winnings = 0
        elif result == "push":
            embed.add_field(name="Result", value="🤝 **PUSH!** It's a tie!", inline=False)
            winnings = self.bet  # Return bet
        
        # Update balance
        from models import db
        with db.session.begin():
            self.profile.coins = self.profile.coins - self.bet + winnings
            db.session.commit()
        
        # Update stats
        await EconomyGame.update_game_stats(self.user_id, self.guild_id, 'blackjack', won, self.bet, winnings)
        
        # Add transaction
        net_change = winnings - self.bet
        if net_change != 0:
            from economy_system import add_transaction
            await add_transaction(self.user_id, self.guild_id, net_change, 'gamble', f'Blackjack {result}')
        
        embed.add_field(name="New Balance", value=f"{self.profile.coins:,} coins", inline=True)
        
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)