"""
Database models for Discord bot features
Includes models for: economy, analytics, reminders, tags, suggestions, tickets, events, etc.
"""
import os
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Integer, String, Text, Boolean, DateTime, BigInteger, Float, JSON


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)

# Economy System Models
class UserProfile(db.Model):
    __tablename__ = 'user_profiles'
    
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(BigInteger, unique=True, nullable=False)  # Discord user ID
    guild_id = db.Column(BigInteger, nullable=False)  # Discord guild ID
    username = db.Column(String(100), nullable=False)
    display_name = db.Column(String(100))
    
    # Economy
    coins = db.Column(Integer, default=100)
    xp = db.Column(Integer, default=0)
    level = db.Column(Integer, default=1)
    daily_claimed = db.Column(DateTime)
    weekly_claimed = db.Column(DateTime)
    
    # Activity tracking
    messages_sent = db.Column(Integer, default=0)
    commands_used = db.Column(Integer, default=0)
    voice_time = db.Column(Integer, default=0)  # In minutes
    
    # Timestamps
    created_at = db.Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f'<UserProfile {self.username}>'

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(BigInteger, nullable=False)
    guild_id = db.Column(BigInteger, nullable=False)
    transaction_type = db.Column(String(50), nullable=False)  # 'earn', 'spend', 'gift', 'gamble'
    amount = db.Column(Integer, nullable=False)
    reason = db.Column(String(200))
    created_at = db.Column(DateTime, default=lambda: datetime.now(timezone.utc))

class ShopItem(db.Model):
    __tablename__ = 'shop_items'
    
    id = db.Column(Integer, primary_key=True)
    guild_id = db.Column(BigInteger, nullable=False)
    name = db.Column(String(100), nullable=False)
    description = db.Column(Text)
    price = db.Column(Integer, nullable=False)
    item_type = db.Column(String(50), nullable=False)  # 'role', 'perk', 'cosmetic'
    item_data = db.Column(JSON)  # Store role IDs, colors, etc.
    stock = db.Column(Integer, default=-1)  # -1 = unlimited
    is_active = db.Column(Boolean, default=True)
    created_at = db.Column(DateTime, default=lambda: datetime.now(timezone.utc))

# Server Analytics Models
class ServerStats(db.Model):
    __tablename__ = 'server_stats'
    
    id = db.Column(Integer, primary_key=True)
    guild_id = db.Column(BigInteger, nullable=False)
    date = db.Column(DateTime, nullable=False)
    
    # Daily metrics
    messages_count = db.Column(Integer, default=0)
    unique_users = db.Column(Integer, default=0)
    new_members = db.Column(Integer, default=0)
    left_members = db.Column(Integer, default=0)
    commands_used = db.Column(Integer, default=0)
    voice_minutes = db.Column(Integer, default=0)
    
    created_at = db.Column(DateTime, default=lambda: datetime.now(timezone.utc))

class CommandUsage(db.Model):
    __tablename__ = 'command_usage'
    
    id = db.Column(Integer, primary_key=True)
    guild_id = db.Column(BigInteger, nullable=False)
    user_id = db.Column(BigInteger, nullable=False)
    command_name = db.Column(String(100), nullable=False)
    channel_id = db.Column(BigInteger, nullable=False)
    timestamp = db.Column(DateTime, default=lambda: datetime.now(timezone.utc))

# Custom Tags System
class CustomTag(db.Model):
    __tablename__ = 'custom_tags'
    
    id = db.Column(Integer, primary_key=True)
    guild_id = db.Column(BigInteger, nullable=False)
    name = db.Column(String(50), nullable=False)
    content = db.Column(Text, nullable=False)
    embed_data = db.Column(JSON)  # For rich embeds
    
    # Metadata
    created_by = db.Column(BigInteger, nullable=False)
    created_at = db.Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    uses = db.Column(Integer, default=0)

# Reminder System
class Reminder(db.Model):
    __tablename__ = 'reminders'
    
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(BigInteger, nullable=False)
    guild_id = db.Column(BigInteger, nullable=False)
    channel_id = db.Column(BigInteger, nullable=False)
    
    content = db.Column(Text, nullable=False)
    remind_at = db.Column(DateTime, nullable=False)
    is_recurring = db.Column(Boolean, default=False)
    recurring_interval = db.Column(String(20))  # 'daily', 'weekly', 'monthly'
    
    is_completed = db.Column(Boolean, default=False)
    created_at = db.Column(DateTime, default=lambda: datetime.now(timezone.utc))

# Suggestion System
class Suggestion(db.Model):
    __tablename__ = 'suggestions'
    
    id = db.Column(Integer, primary_key=True)
    guild_id = db.Column(BigInteger, nullable=False)
    user_id = db.Column(BigInteger, nullable=False)
    channel_id = db.Column(BigInteger, nullable=False)
    message_id = db.Column(BigInteger, nullable=False)
    
    title = db.Column(String(100), nullable=False)
    description = db.Column(Text, nullable=False)
    status = db.Column(String(20), default='pending')  # 'pending', 'approved', 'denied', 'implemented'
    
    upvotes = db.Column(Integer, default=0)
    downvotes = db.Column(Integer, default=0)
    
    admin_response = db.Column(Text)
    responded_by = db.Column(BigInteger)
    responded_at = db.Column(DateTime)
    
    created_at = db.Column(DateTime, default=lambda: datetime.now(timezone.utc))

class SuggestionVote(db.Model):
    __tablename__ = 'suggestion_votes'
    
    id = db.Column(Integer, primary_key=True)
    suggestion_id = db.Column(Integer, db.ForeignKey('suggestions.id'), nullable=False)
    user_id = db.Column(BigInteger, nullable=False)
    vote_type = db.Column(String(10), nullable=False)  # 'up' or 'down'
    created_at = db.Column(DateTime, default=lambda: datetime.now(timezone.utc))

# Ticket System
class Ticket(db.Model):
    __tablename__ = 'tickets'
    
    id = db.Column(Integer, primary_key=True)
    guild_id = db.Column(BigInteger, nullable=False)
    user_id = db.Column(BigInteger, nullable=False)
    channel_id = db.Column(BigInteger, nullable=False)
    
    ticket_number = db.Column(Integer, nullable=False)
    title = db.Column(String(100), nullable=False)
    description = db.Column(Text)
    category = db.Column(String(50), default='general')
    
    status = db.Column(String(20), default='open')  # 'open', 'closed', 'archived'
    priority = db.Column(String(20), default='medium')  # 'low', 'medium', 'high', 'urgent'
    
    assigned_to = db.Column(BigInteger)
    closed_by = db.Column(BigInteger)
    closed_at = db.Column(DateTime)
    
    created_at = db.Column(DateTime, default=lambda: datetime.now(timezone.utc))

# Event System
class Event(db.Model):
    __tablename__ = 'events'
    
    id = db.Column(Integer, primary_key=True)
    guild_id = db.Column(BigInteger, nullable=False)
    creator_id = db.Column(BigInteger, nullable=False)
    
    title = db.Column(String(100), nullable=False)
    description = db.Column(Text)
    event_time = db.Column(DateTime, nullable=False)
    duration_minutes = db.Column(Integer, default=60)
    
    location = db.Column(String(100))  # Virtual or physical location
    max_attendees = db.Column(Integer)
    
    is_recurring = db.Column(Boolean, default=False)
    recurring_pattern = db.Column(String(20))  # 'daily', 'weekly', 'monthly'
    
    reminder_sent = db.Column(Boolean, default=False)
    is_cancelled = db.Column(Boolean, default=False)
    
    created_at = db.Column(DateTime, default=lambda: datetime.now(timezone.utc))

class EventAttendee(db.Model):
    __tablename__ = 'event_attendees'
    
    id = db.Column(Integer, primary_key=True)
    event_id = db.Column(Integer, db.ForeignKey('events.id'), nullable=False)
    user_id = db.Column(BigInteger, nullable=False)
    status = db.Column(String(20), default='going')  # 'going', 'maybe', 'not_going'
    joined_at = db.Column(DateTime, default=lambda: datetime.now(timezone.utc))

# Birthday System
class UserBirthday(db.Model):
    __tablename__ = 'user_birthdays'
    
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(BigInteger, unique=True, nullable=False)
    guild_id = db.Column(BigInteger, nullable=False)
    
    birth_month = db.Column(Integer, nullable=False)  # 1-12
    birth_day = db.Column(Integer, nullable=False)    # 1-31
    birth_year = db.Column(Integer)  # Optional
    
    timezone = db.Column(String(50), default='UTC')
    is_public = db.Column(Boolean, default=True)
    remind_enabled = db.Column(Boolean, default=True)
    
    created_at = db.Column(DateTime, default=lambda: datetime.now(timezone.utc))

# Social Features
class UserRelationship(db.Model):
    __tablename__ = 'user_relationships'
    
    id = db.Column(Integer, primary_key=True)
    guild_id = db.Column(BigInteger, nullable=False)
    user1_id = db.Column(BigInteger, nullable=False)
    user2_id = db.Column(BigInteger, nullable=False)
    
    relationship_type = db.Column(String(20), nullable=False)  # 'married', 'friendship', 'pet'
    established_at = db.Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Marriage specific
    anniversary_channel = db.Column(BigInteger)
    
    # Pet specific  
    pet_name = db.Column(String(50))
    pet_type = db.Column(String(20))  # 'cat', 'dog', 'bird', etc.

# Auto Moderation Logs
class ModerationLog(db.Model):
    __tablename__ = 'moderation_logs'
    
    id = db.Column(Integer, primary_key=True)
    guild_id = db.Column(BigInteger, nullable=False)
    user_id = db.Column(BigInteger, nullable=False)
    moderator_id = db.Column(BigInteger)
    
    action_type = db.Column(String(50), nullable=False)  # 'warn', 'mute', 'kick', 'ban', 'automod'
    reason = db.Column(Text)
    duration = db.Column(String(50))  # For temporary actions
    
    message_content = db.Column(Text)  # For automod actions
    channel_id = db.Column(BigInteger)
    
    expires_at = db.Column(DateTime)  # For temporary punishments
    is_active = db.Column(Boolean, default=True)
    
    created_at = db.Column(DateTime, default=lambda: datetime.now(timezone.utc))

# URL Preview Cache
class UrlPreview(db.Model):
    __tablename__ = 'url_previews'
    
    id = db.Column(Integer, primary_key=True)
    url_hash = db.Column(String(64), unique=True, nullable=False)
    original_url = db.Column(Text, nullable=False)
    
    title = db.Column(String(200))
    description = db.Column(Text)
    image_url = db.Column(Text)
    site_name = db.Column(String(100))
    
    cached_at = db.Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(DateTime, nullable=False)

# Game Statistics (for economy games)
class GameStats(db.Model):
    __tablename__ = 'game_stats'
    
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(BigInteger, nullable=False)
    guild_id = db.Column(BigInteger, nullable=False)
    game_type = db.Column(String(50), nullable=False)  # 'blackjack', 'slots', 'rps', etc.
    
    games_played = db.Column(Integer, default=0)
    games_won = db.Column(Integer, default=0)
    total_bet = db.Column(Integer, default=0)
    total_won = db.Column(Integer, default=0)
    
    biggest_win = db.Column(Integer, default=0)
    biggest_loss = db.Column(Integer, default=0)
    current_streak = db.Column(Integer, default=0)
    best_streak = db.Column(Integer, default=0)
    
    last_played = db.Column(DateTime, default=lambda: datetime.now(timezone.utc))