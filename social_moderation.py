"""
Social Features and Advanced Moderation for Discord Bot
Includes: Marriage system, pet adoption, auto-moderation, advanced logging
"""

import discord
from discord import app_commands
from discord.ext import commands, tasks
import asyncio
import re
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict
import json
from db_app import app, with_db_context
from models import *

class AutoModerator:
    """Automatic moderation system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.spam_tracker = {}
        self.bad_words = [
            # Add your bad words here - keeping it clean for the example
            "spam", "example_bad_word"  # Replace with actual moderation words
        ]
        self.max_mentions = 5
        self.max_links = 3
        self.spam_threshold = 5  # Messages in 10 seconds
    
    async def check_message(self, message):
        """Check message for violations"""
        if message.author.bot or not message.guild:
            return
        
        violations = []
        
        # Check for spam
        if await self._check_spam(message):
            violations.append("spam")
        
        # Check for excessive mentions
        if len(message.mentions) + len(message.role_mentions) > self.max_mentions:
            violations.append("excessive_mentions")
        
        # Check for excessive links
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', message.content)
        if len(urls) > self.max_links:
            violations.append("excessive_links")
        
        # Check for bad words
        if any(word.lower() in message.content.lower() for word in self.bad_words):
            violations.append("inappropriate_language")
        
        # Check for caps spam (>70% caps and >10 characters)
        if len(message.content) > 10 and sum(1 for c in message.content if c.isupper()) / len(message.content) > 0.7:
            violations.append("caps_spam")
        
        # Handle violations
        if violations:
            await self._handle_violations(message, violations)
    
    async def _check_spam(self, message):
        """Check for spam patterns"""
        user_id = message.author.id
        now = datetime.now(timezone.utc)
        
        if user_id not in self.spam_tracker:
            self.spam_tracker[user_id] = []
        
        # Clean old messages (older than 10 seconds)
        self.spam_tracker[user_id] = [
            msg_time for msg_time in self.spam_tracker[user_id]
            if (now - msg_time).total_seconds() <= 10
        ]
        
        # Add current message
        self.spam_tracker[user_id].append(now)
        
        # Check if spam threshold exceeded
        return len(self.spam_tracker[user_id]) >= self.spam_threshold
    
    async def _handle_violations(self, message, violations):
        """Handle detected violations"""
        try:
            # Delete the message
            await message.delete()
            
            # Log the violation
            with db.session.begin():
                log = ModerationLog(
                    guild_id=message.guild.id,
                    user_id=message.author.id,
                    action_type="automod",
                    reason=f"Auto-moderation: {', '.join(violations)}",
                    message_content=message.content[:500],
                    channel_id=message.channel.id
                )
                db.session.add(log)
                db.session.commit()
            
            # Send warning to user
            violation_messages = {
                "spam": "Please avoid sending messages too quickly!",
                "excessive_mentions": "Please don't mention too many users at once!",
                "excessive_links": "Please limit the number of links in your messages!",
                "inappropriate_language": "Please watch your language!",
                "caps_spam": "Please don't use excessive CAPS!"
            }
            
            warning_text = "\n".join([f"• {violation_messages.get(v, v)}" for v in violations])
            
            embed = discord.Embed(
                title="⚠️ Auto-Moderation Warning",
                description=f"{message.author.mention}, your message was removed for:\n\n{warning_text}",
                color=0xff9500
            )
            embed.set_footer(text="Please follow server guidelines")
            
            try:
                warning_msg = await message.channel.send(embed=embed, delete_after=10)
            except:
                pass  # Channel might be deleted or no permissions
            
        except Exception as e:
            print(f"Error handling auto-mod violation: {e}")

class SocialView(discord.ui.View):
    """View for social interactions"""
    
    def __init__(self, interaction_type: str, target_user: discord.Member):
        super().__init__(timeout=300)
        self.interaction_type = interaction_type
        self.target_user = target_user
    
    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success, emoji="✅")
    async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Accept the social interaction"""
        if interaction.user.id != self.target_user.id:
            return await interaction.response.send_message("❌ This isn't for you!", ephemeral=True)
        
        await self._handle_response(interaction, True)
    
    @discord.ui.button(label="Decline", style=discord.ButtonStyle.danger, emoji="❌")
    async def decline_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Decline the social interaction"""
        if interaction.user.id != self.target_user.id:
            return await interaction.response.send_message("❌ This isn't for you!", ephemeral=True)
        
        await self._handle_response(interaction, False)
    
    async def _handle_response(self, interaction: discord.Interaction, accepted: bool):
        """Handle the response"""
        requester = interaction.guild.get_member(int(interaction.message.embeds[0].fields[0].value.replace('<@', '').replace('>', '')))
        
        if accepted:
            if self.interaction_type == "marriage":
                await self._handle_marriage(interaction, requester)
            elif self.interaction_type == "friendship":
                await self._handle_friendship(interaction, requester)
        else:
            embed = discord.Embed(
                title=f"💔 {self.interaction_type.title()} Declined",
                description=f"{self.target_user.mention} has declined {requester.mention}'s {self.interaction_type} proposal.",
                color=0xff0000
            )
            await interaction.response.edit_message(embed=embed, view=None)
        
        # Disable all buttons
        for item in self.children:
            item.disabled = True
    
    async def _handle_marriage(self, interaction, requester):
        """Handle marriage acceptance"""
        try:
            # Check if either user is already married
            existing = UserRelationship.query.filter(
                UserRelationship.guild_id == interaction.guild.id,
                UserRelationship.relationship_type == "married",
                db.or_(
                    db.and_(UserRelationship.user1_id == requester.id, UserRelationship.user2_id == self.target_user.id),
                    db.and_(UserRelationship.user1_id == self.target_user.id, UserRelationship.user2_id == requester.id)
                )
            ).first()
            
            if existing:
                return await interaction.response.send_message("❌ You're already married!", ephemeral=True)
            
            # Create marriage
            with db.session.begin():
                marriage = UserRelationship(
                    guild_id=interaction.guild.id,
                    user1_id=requester.id,
                    user2_id=self.target_user.id,
                    relationship_type="married"
                )
                db.session.add(marriage)
                db.session.commit()
            
            embed = discord.Embed(
                title="💒 Congratulations!",
                description=f"🎉 {requester.mention} and {self.target_user.mention} are now married! 🎉\n\nWishing you both a lifetime of happiness! 💕",
                color=0xff69b4,
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text="🌹 Marriage celebrated in " + interaction.guild.name + " 🌹")
            
            await interaction.response.edit_message(embed=embed, view=None)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error processing marriage: {e}", ephemeral=True)
    
    async def _handle_friendship(self, interaction, requester):
        """Handle friendship acceptance"""
        try:
            with db.session.begin():
                friendship = UserRelationship(
                    guild_id=interaction.guild.id,
                    user1_id=requester.id,
                    user2_id=self.target_user.id,
                    relationship_type="friendship"
                )
                db.session.add(friendship)
                db.session.commit()
            
            embed = discord.Embed(
                title="🤝 New Friendship!",
                description=f"🎊 {requester.mention} and {self.target_user.mention} are now friends! 🎊\n\nMay your friendship be filled with joy and laughter! 😊",
                color=0x3498db,
                timestamp=datetime.now(timezone.utc)
            )
            
            await interaction.response.edit_message(embed=embed, view=None)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error processing friendship: {e}", ephemeral=True)

def setup_social_moderation(bot):
    """Setup all social features and advanced moderation"""
    
    # Initialize auto-moderator
    auto_mod = AutoModerator(bot)
    
    # Hook into message events for auto-moderation
    @bot.event
    async def on_message(message):
        await auto_mod.check_message(message)
    
    # ============= SOCIAL FEATURES =============
    
    @bot.tree.command(name="marry", description="Propose marriage to another user")
    @app_commands.describe(user="User to propose to")
    async def marry_command(interaction: discord.Interaction, user: discord.Member):
        """Propose marriage"""
        if user.bot:
            return await interaction.response.send_message("❌ You can't marry bots!", ephemeral=True)
        
        if user.id == interaction.user.id:
            return await interaction.response.send_message("❌ You can't marry yourself! 😅", ephemeral=True)
        
        try:
            # Check if already married
            existing = UserRelationship.query.filter(
                UserRelationship.guild_id == interaction.guild.id,
                UserRelationship.relationship_type == "married",
                db.or_(
                    UserRelationship.user1_id == interaction.user.id,
                    UserRelationship.user2_id == interaction.user.id,
                    UserRelationship.user1_id == user.id,
                    UserRelationship.user2_id == user.id
                )
            ).first()
            
            if existing:
                return await interaction.response.send_message("❌ One of you is already married!", ephemeral=True)
            
            # Create proposal
            embed = discord.Embed(
                title="💍 Marriage Proposal",
                description=f"💕 {interaction.user.mention} is proposing to {user.mention}! 💕\n\nWill you marry them?",
                color=0xff69b4,
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="💒 Proposer", value=interaction.user.mention, inline=True)
            embed.add_field(name="💝 Proposed To", value=user.mention, inline=True)
            embed.set_footer(text="💕 Answer with your heart 💕")
            
            view = SocialView("marriage", user)
            await interaction.response.send_message(embed=embed, view=view)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error creating marriage proposal: {e}", ephemeral=True)
    
    @bot.tree.command(name="divorce", description="End your marriage")
    async def divorce_command(interaction: discord.Interaction):
        """End marriage"""
        try:
            marriage = UserRelationship.query.filter(
                UserRelationship.guild_id == interaction.guild.id,
                UserRelationship.relationship_type == "married",
                db.or_(
                    UserRelationship.user1_id == interaction.user.id,
                    UserRelationship.user2_id == interaction.user.id
                )
            ).first()
            
            if not marriage:
                return await interaction.response.send_message("❌ You're not married!", ephemeral=True)
            
            # Get partner
            partner_id = marriage.user2_id if marriage.user1_id == interaction.user.id else marriage.user1_id
            partner = interaction.guild.get_member(partner_id)
            partner_name = partner.display_name if partner else "Unknown User"
            
            # Delete marriage
            with db.session.begin():
                db.session.delete(marriage)
                db.session.commit()
            
            embed = discord.Embed(
                title="💔 Divorce Finalized",
                description=f"{interaction.user.mention} and **{partner_name}** are no longer married.\n\nWe hope you both find happiness. 💙",
                color=0x95a5a6
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error processing divorce: {e}", ephemeral=True)
    
    @bot.tree.command(name="befriend", description="Send a friendship request")
    @app_commands.describe(user="User to befriend")
    async def befriend_command(interaction: discord.Interaction, user: discord.Member):
        """Send friendship request"""
        if user.bot:
            return await interaction.response.send_message("❌ You can't befriend bots!", ephemeral=True)
        
        if user.id == interaction.user.id:
            return await interaction.response.send_message("❌ You're already your own best friend! 😄", ephemeral=True)
        
        try:
            # Check if already friends
            existing = UserRelationship.query.filter(
                UserRelationship.guild_id == interaction.guild.id,
                UserRelationship.relationship_type == "friendship",
                db.or_(
                    db.and_(UserRelationship.user1_id == interaction.user.id, UserRelationship.user2_id == user.id),
                    db.and_(UserRelationship.user1_id == user.id, UserRelationship.user2_id == interaction.user.id)
                )
            ).first()
            
            if existing:
                return await interaction.response.send_message("❌ You're already friends!", ephemeral=True)
            
            embed = discord.Embed(
                title="🤝 Friendship Request",
                description=f"😊 {interaction.user.mention} wants to be friends with {user.mention}!\n\nWill you accept this friendship?",
                color=0x3498db
            )
            embed.add_field(name="👋 From", value=interaction.user.mention, inline=True)
            embed.add_field(name="💌 To", value=user.mention, inline=True)
            
            view = SocialView("friendship", user)
            await interaction.response.send_message(embed=embed, view=view)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error sending friendship request: {e}", ephemeral=True)
    
    @bot.tree.command(name="adopt", description="Adopt a virtual pet")
    @app_commands.describe(pet_type="Type of pet", pet_name="Name for your pet")
    @app_commands.choices(pet_type=[
        app_commands.Choice(name="🐶 Dog", value="dog"),
        app_commands.Choice(name="🐱 Cat", value="cat"),
        app_commands.Choice(name="🐰 Rabbit", value="rabbit"),
        app_commands.Choice(name="🐦 Bird", value="bird"),
        app_commands.Choice(name="🐠 Fish", value="fish"),
        app_commands.Choice(name="🐹 Hamster", value="hamster")
    ])
    async def adopt_pet(interaction: discord.Interaction, pet_type: str, pet_name: str):
        """Adopt a virtual pet"""
        if len(pet_name) > 20:
            return await interaction.response.send_message("❌ Pet name too long! Max 20 characters.", ephemeral=True)
        
        try:
            # Check if user already has this type of pet
            existing = UserRelationship.query.filter(
                UserRelationship.guild_id == interaction.guild.id,
                UserRelationship.user1_id == interaction.user.id,
                UserRelationship.relationship_type == "pet",
                UserRelationship.pet_type == pet_type
            ).first()
            
            if existing:
                return await interaction.response.send_message(f"❌ You already have a {pet_type}! ({existing.pet_name})", ephemeral=True)
            
            # Adopt pet
            with db.session.begin():
                pet = UserRelationship(
                    guild_id=interaction.guild.id,
                    user1_id=interaction.user.id,
                    user2_id=0,  # Not a user relationship
                    relationship_type="pet",
                    pet_name=pet_name,
                    pet_type=pet_type
                )
                db.session.add(pet)
                db.session.commit()
            
            pet_emojis = {
                "dog": "🐶", "cat": "🐱", "rabbit": "🐰",
                "bird": "🐦", "fish": "🐠", "hamster": "🐹"
            }
            
            embed = discord.Embed(
                title="🎉 Pet Adopted!",
                description=f"Congratulations! {interaction.user.mention} has adopted **{pet_name}** the {pet_emojis.get(pet_type, '🐾')} {pet_type}!\n\nTake good care of your new companion! 💕",
                color=0x00ff00,
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error adopting pet: {e}", ephemeral=True)
    
    @bot.tree.command(name="relationships", description="View your social relationships")
    async def relationships_command(interaction: discord.Interaction):
        """View user relationships"""
        try:
            relationships = UserRelationship.query.filter(
                UserRelationship.guild_id == interaction.guild.id,
                db.or_(
                    UserRelationship.user1_id == interaction.user.id,
                    UserRelationship.user2_id == interaction.user.id
                )
            ).all()
            
            pets = UserRelationship.query.filter(
                UserRelationship.guild_id == interaction.guild.id,
                UserRelationship.user1_id == interaction.user.id,
                UserRelationship.relationship_type == "pet"
            ).all()
            
            if not relationships and not pets:
                return await interaction.response.send_message("💫 You don't have any relationships yet!", ephemeral=True)
            
            embed = discord.Embed(
                title=f"💕 {interaction.user.display_name}'s Relationships",
                color=0xff69b4
            )
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            
            # Group relationships by type
            marriages = []
            friendships = []
            
            for rel in relationships:
                if rel.relationship_type == "pet":
                    continue
                
                partner_id = rel.user2_id if rel.user1_id == interaction.user.id else rel.user1_id
                partner = interaction.guild.get_member(partner_id)
                if partner:
                    if rel.relationship_type == "married":
                        marriages.append(partner)
                    elif rel.relationship_type == "friendship":
                        friendships.append(partner)
            
            if marriages:
                embed.add_field(
                    name="💒 Married To",
                    value="\n".join([f"💕 {p.mention}" for p in marriages]),
                    inline=False
                )
            
            if friendships:
                friends_text = "\n".join([f"🤝 {p.mention}" for p in friendships[:10]])  # Limit to 10
                if len(friendships) > 10:
                    friends_text += f"\n... and {len(friendships) - 10} more"
                embed.add_field(
                    name="👥 Friends",
                    value=friends_text,
                    inline=False
                )
            
            if pets:
                pet_emojis = {
                    "dog": "🐶", "cat": "🐱", "rabbit": "🐰",
                    "bird": "🐦", "fish": "🐠", "hamster": "🐹"
                }
                pets_text = "\n".join([
                    f"{pet_emojis.get(p.pet_type, '🐾')} **{p.pet_name}** the {p.pet_type}"
                    for p in pets
                ])
                embed.add_field(
                    name="🐾 Pets",
                    value=pets_text,
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error fetching relationships: {e}", ephemeral=True)
    
    # ============= SOCIAL INTERACTIONS =============
    
    @bot.tree.command(name="hug", description="Give someone a virtual hug")
    @app_commands.describe(user="User to hug")
    async def hug_command(interaction: discord.Interaction, user: discord.Member):
        """Send a virtual hug"""
        if user.id == interaction.user.id:
            return await interaction.response.send_message("🤗 *hugs yourself* Sometimes we all need self-love!", ephemeral=True)
        
        hug_gifs = [
            "🤗 *gives a warm, gentle hug*",
            "🤗 *wraps you in a big, cozy hug*",
            "🤗 *squeezes you tightly with love*",
            "🤗 *gives you the biggest bear hug*"
        ]
        
        embed = discord.Embed(
            description=f"{interaction.user.mention} {random.choice(hug_gifs)} {user.mention} 💕",
            color=0xff69b4
        )
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="pat", description="Give someone a pat")
    @app_commands.describe(user="User to pat")
    async def pat_command(interaction: discord.Interaction, user: discord.Member):
        """Send a pat"""
        pat_messages = [
            "*gently pats your head* 😊",
            "*gives you a reassuring pat* 🫳",
            "*pats you softly* There, there! 😌",
            "*friendly pat pat* 😄"
        ]
        
        embed = discord.Embed(
            description=f"{interaction.user.mention} {random.choice(pat_messages)} {user.mention}",
            color=0x3498db
        )
        
        await interaction.response.send_message(embed=embed)
    
    # ============= ADVANCED MODERATION =============
    
    @bot.tree.command(name="warn", description="Warn a user")
    @app_commands.describe(user="User to warn", reason="Reason for warning")
    async def warn_command(interaction: discord.Interaction, user: discord.Member, reason: str):
        """Warn a user"""
        if not interaction.user.guild_permissions.moderate_members:
            return await interaction.response.send_message("❌ You need Moderate Members permission!", ephemeral=True)
        
        if user.bot:
            return await interaction.response.send_message("❌ You can't warn bots!", ephemeral=True)
        
        try:
            # Log the warning
            with db.session.begin():
                warning = ModerationLog(
                    guild_id=interaction.guild.id,
                    user_id=user.id,
                    moderator_id=interaction.user.id,
                    action_type="warn",
                    reason=reason
                )
                db.session.add(warning)
                db.session.commit()
            
            # Send warning to user
            try:
                user_embed = discord.Embed(
                    title="⚠️ Warning Received",
                    description=f"You have been warned in **{interaction.guild.name}**",
                    color=0xff9500
                )
                user_embed.add_field(name="Reason", value=reason, inline=False)
                user_embed.add_field(name="Moderator", value=interaction.user.display_name, inline=True)
                user_embed.set_footer(text="Please follow server rules")
                
                await user.send(embed=user_embed)
            except:
                pass  # User might have DMs disabled
            
            # Public response
            embed = discord.Embed(
                title="⚠️ User Warned",
                color=0xff9500
            )
            embed.add_field(name="User", value=user.mention, inline=True)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error issuing warning: {e}", ephemeral=True)
    
    @bot.tree.command(name="warnings", description="View a user's warnings")
    @app_commands.describe(user="User to check warnings for")
    async def warnings_command(interaction: discord.Interaction, user: discord.Member):
        """View user warnings"""
        if not interaction.user.guild_permissions.moderate_members:
            return await interaction.response.send_message("❌ You need Moderate Members permission!", ephemeral=True)
        
        try:
            warnings = ModerationLog.query.filter(
                ModerationLog.guild_id == interaction.guild.id,
                ModerationLog.user_id == user.id,
                ModerationLog.action_type == "warn"
            ).order_by(ModerationLog.created_at.desc()).limit(10).all()
            
            if not warnings:
                return await interaction.response.send_message(f"✅ {user.mention} has no warnings.", ephemeral=True)
            
            embed = discord.Embed(
                title=f"⚠️ {user.display_name}'s Warnings",
                color=0xff9500
            )
            embed.set_thumbnail(url=user.display_avatar.url)
            
            for i, warning in enumerate(warnings, 1):
                moderator = interaction.guild.get_member(warning.moderator_id)
                mod_name = moderator.display_name if moderator else "Unknown Moderator"
                
                embed.add_field(
                    name=f"Warning #{i}",
                    value=f"**Reason:** {warning.reason}\n**By:** {mod_name}\n**Date:** <t:{int(warning.created_at.timestamp())}:R>",
                    inline=False
                )
            
            embed.set_footer(text=f"Total warnings: {len(warnings)}")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error fetching warnings: {e}", ephemeral=True)
    
    @bot.tree.command(name="modlogs", description="View recent moderation logs")
    @app_commands.describe(user="Filter by specific user (optional)")
    async def mod_logs_command(interaction: discord.Interaction, user: Optional[discord.Member] = None):
        """View moderation logs"""
        if not interaction.user.guild_permissions.moderate_members:
            return await interaction.response.send_message("❌ You need Moderate Members permission!", ephemeral=True)
        
        try:
            query = ModerationLog.query.filter_by(guild_id=interaction.guild.id)
            if user:
                query = query.filter_by(user_id=user.id)
            
            logs = query.order_by(ModerationLog.created_at.desc()).limit(10).all()
            
            if not logs:
                return await interaction.response.send_message("📋 No moderation logs found.", ephemeral=True)
            
            embed = discord.Embed(
                title="📋 Moderation Logs",
                color=0x3498db
            )
            
            action_emojis = {
                "warn": "⚠️",
                "mute": "🔇",
                "kick": "👢",
                "ban": "🔨",
                "automod": "🤖"
            }
            
            for log in logs:
                target_user = interaction.guild.get_member(log.user_id)
                target_name = target_user.display_name if target_user else f"User ID: {log.user_id}"
                
                moderator = interaction.guild.get_member(log.moderator_id) if log.moderator_id else None
                mod_name = moderator.display_name if moderator else "System"
                
                embed.add_field(
                    name=f"{action_emojis.get(log.action_type, '📝')} {log.action_type.title()}",
                    value=f"**User:** {target_name}\n**Moderator:** {mod_name}\n**Reason:** {log.reason or 'No reason'}\n**When:** <t:{int(log.created_at.timestamp())}:R>",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error fetching logs: {e}", ephemeral=True)
    
    print("✅ All social and moderation features loaded successfully!")