"""
Community Features for Discord Bot
Includes: Suggestion system, ticket system, event scheduler, birthday tracker
"""

import discord
from discord import app_commands
from discord.ext import commands, tasks
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict
import json
from db_app import app, with_db_context
from models import *

class SuggestionView(discord.ui.View):
    """View for suggestion voting"""
    
    def __init__(self, suggestion_id: int):
        super().__init__(timeout=None)
        self.suggestion_id = suggestion_id
    
    @discord.ui.button(label="👍", style=discord.ButtonStyle.success, custom_id="upvote")
    async def upvote(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle upvote"""
        await self._handle_vote(interaction, "up")
    
    @discord.ui.button(label="👎", style=discord.ButtonStyle.danger, custom_id="downvote")  
    async def downvote(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle downvote"""
        await self._handle_vote(interaction, "down")
    
    async def _handle_vote(self, interaction: discord.Interaction, vote_type: str):
        """Handle voting logic"""
        try:
            user_id = interaction.user.id
            
            # Check if user already voted
            existing_vote = SuggestionVote.query.filter_by(
                suggestion_id=self.suggestion_id,
                user_id=user_id
            ).first()
            
            with db.session.begin():
                suggestion = Suggestion.query.get(self.suggestion_id)
                if not suggestion:
                    return await interaction.response.send_message("❌ Suggestion not found!", ephemeral=True)
                
                if existing_vote:
                    if existing_vote.vote_type == vote_type:
                        return await interaction.response.send_message(f"❌ You already {vote_type}voted this suggestion!", ephemeral=True)
                    
                    # Change vote
                    if existing_vote.vote_type == "up":
                        suggestion.upvotes -= 1
                    else:
                        suggestion.downvotes -= 1
                    
                    existing_vote.vote_type = vote_type
                else:
                    # New vote
                    vote = SuggestionVote(
                        suggestion_id=self.suggestion_id,
                        user_id=user_id,
                        vote_type=vote_type
                    )
                    db.session.add(vote)
                
                # Update counts
                if vote_type == "up":
                    suggestion.upvotes += 1
                else:
                    suggestion.downvotes += 1
            
            # Update embed
            embed = interaction.message.embeds[0]
            for i, field in enumerate(embed.fields):
                if field.name == "📊 Votes":
                    embed.set_field_at(
                        i,
                        name="📊 Votes",
                        value=f"👍 {suggestion.upvotes} | 👎 {suggestion.downvotes}",
                        inline=True
                    )
                    break
            
            await interaction.response.edit_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error processing vote: {e}", ephemeral=True)

class TicketView(discord.ui.View):
    """View for ticket management"""
    
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="🎫 Create Ticket", style=discord.ButtonStyle.primary, custom_id="create_ticket")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Create a new ticket"""
        await interaction.response.send_modal(TicketModal())

class TicketModal(discord.ui.Modal):
    """Modal for creating tickets"""
    
    def __init__(self):
        super().__init__(title="Create Support Ticket", timeout=300)
    
    title_input = discord.ui.TextInput(
        label="Title",
        placeholder="Brief description of your issue",
        max_length=100
    )
    
    description_input = discord.ui.TextInput(
        label="Description",
        placeholder="Detailed description of your issue",
        style=discord.TextStyle.paragraph,
        max_length=1000
    )
    
    category_input = discord.ui.TextInput(
        label="Category",
        placeholder="general, technical, report, other",
        max_length=20,
        default="general"
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle ticket submission"""
        try:
            guild = interaction.guild
            user = interaction.user
            
            # Get next ticket number
            last_ticket = Ticket.query.filter_by(guild_id=guild.id).order_by(Ticket.ticket_number.desc()).first()
            ticket_number = (last_ticket.ticket_number + 1) if last_ticket else 1
            
            # Create ticket channel
            category = discord.utils.get(guild.categories, name="Support Tickets")
            if not category:
                category = await guild.create_category("Support Tickets")
            
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            
            # Add staff permissions (users with manage_messages permission)
            for role in guild.roles:
                if role.permissions.manage_messages:
                    overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            
            channel_name = f"ticket-{ticket_number:04d}"
            channel = await category.create_text_channel(channel_name, overwrites=overwrites)
            
            # Save to database
            with db.session.begin():
                ticket = Ticket(
                    guild_id=guild.id,
                    user_id=user.id,
                    channel_id=channel.id,
                    ticket_number=ticket_number,
                    title=str(self.title_input.value),
                    description=str(self.description_input.value),
                    category=str(self.category_input.value).lower()
                )
                db.session.add(ticket)
            
            # Create ticket embed
            embed = discord.Embed(
                title=f"🎫 Support Ticket #{ticket_number:04d}",
                description=self.description_input.value,
                color=0x3498db,
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="👤 Created by", value=user.mention, inline=True)
            embed.add_field(name="📂 Category", value=self.category_input.value, inline=True)
            embed.add_field(name="📊 Status", value="🟢 Open", inline=True)
            embed.set_thumbnail(url=user.display_avatar.url)
            
            # Add close button
            close_view = discord.ui.View(timeout=None)
            close_button = discord.ui.Button(
                label="🔒 Close Ticket",
                style=discord.ButtonStyle.danger,
                custom_id=f"close_ticket_{ticket.id}"
            )
            close_view.add_item(close_button)
            
            # Send to channel
            await channel.send(f"{user.mention}", embed=embed, view=close_view)
            
            # Acknowledge
            await interaction.response.send_message(
                f"✅ Ticket created! Check {channel.mention}",
                ephemeral=True
            )
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error creating ticket: {e}", ephemeral=True)

class EventView(discord.ui.View):
    """View for event RSVP"""
    
    def __init__(self, event_id: int):
        super().__init__(timeout=None)
        self.event_id = event_id
    
    @discord.ui.button(label="✅ Going", style=discord.ButtonStyle.success, custom_id="going")
    async def going(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_rsvp(interaction, "going")
    
    @discord.ui.button(label="❓ Maybe", style=discord.ButtonStyle.secondary, custom_id="maybe")
    async def maybe(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_rsvp(interaction, "maybe")
    
    @discord.ui.button(label="❌ Not Going", style=discord.ButtonStyle.danger, custom_id="not_going")
    async def not_going(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_rsvp(interaction, "not_going")
    
    async def _handle_rsvp(self, interaction: discord.Interaction, status: str):
        """Handle RSVP response"""
        try:
            user_id = interaction.user.id
            
            with db.session.begin():
                # Check if already RSVP'd
                existing = EventAttendee.query.filter_by(
                    event_id=self.event_id,
                    user_id=user_id
                ).first()
                
                if existing:
                    existing.status = status
                else:
                    attendee = EventAttendee(
                        event_id=self.event_id,
                        user_id=user_id,
                        status=status
                    )
                    db.session.add(attendee)
                
                db.session.commit()
            
            status_text = {
                "going": "✅ Going",
                "maybe": "❓ Maybe",
                "not_going": "❌ Not Going"
            }
            
            await interaction.response.send_message(
                f"Your RSVP has been updated to: **{status_text[status]}**",
                ephemeral=True
            )
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error updating RSVP: {e}", ephemeral=True)

def setup_community_features(bot):
    """Setup all community feature commands"""
    
    # ============= SUGGESTION SYSTEM =============
    
    @bot.tree.command(name="suggest", description="Submit a suggestion for the server")
    @app_commands.describe(title="Brief title for your suggestion", description="Detailed description")
    async def suggest_command(interaction: discord.Interaction, title: str, description: str):
        """Submit a suggestion"""
        if len(title) > 100:
            return await interaction.response.send_message("❌ Title too long! Max 100 characters.", ephemeral=True)
        
        if len(description) > 1000:
            return await interaction.response.send_message("❌ Description too long! Max 1000 characters.", ephemeral=True)
        
        try:
            # Send suggestion embed
            embed = discord.Embed(
                title="💡 New Suggestion",
                description=description,
                color=0x3498db,
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="📋 Title", value=title, inline=False)
            embed.add_field(name="👤 Suggested by", value=interaction.user.mention, inline=True)
            embed.add_field(name="📊 Votes", value="👍 0 | 👎 0", inline=True)
            embed.add_field(name="📊 Status", value="🔄 Pending Review", inline=True)
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            
            # Send to suggestions channel or current channel
            suggestions_channel = discord.utils.get(interaction.guild.channels, name="suggestions")
            target_channel = suggestions_channel or interaction.channel
            
            view = SuggestionView(0)  # Will be updated after DB save
            message = await target_channel.send(embed=embed, view=view)
            
            # Save to database
            with db.session.begin():
                suggestion = Suggestion(
                    guild_id=interaction.guild.id,
                    user_id=interaction.user.id,
                    channel_id=target_channel.id,
                    message_id=message.id,
                    title=title,
                    description=description
                )
                db.session.add(suggestion)
                db.session.commit()
                
                # Update view with correct ID
                view.suggestion_id = suggestion.id
            
            await interaction.response.send_message(
                f"✅ Suggestion submitted! Check it out in {target_channel.mention}",
                ephemeral=True
            )
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error submitting suggestion: {e}", ephemeral=True)
    
    @bot.tree.command(name="suggestions", description="View server suggestions")
    @app_commands.describe(status="Filter by status")
    @app_commands.choices(status=[
        app_commands.Choice(name="All", value="all"),
        app_commands.Choice(name="Pending", value="pending"),
        app_commands.Choice(name="Approved", value="approved"),
        app_commands.Choice(name="Denied", value="denied"),
        app_commands.Choice(name="Implemented", value="implemented")
    ])
    async def suggestions_list(interaction: discord.Interaction, status: str = "all"):
        """List server suggestions"""
        try:
            query = Suggestion.query.filter_by(guild_id=interaction.guild.id)
            if status != "all":
                query = query.filter_by(status=status)
            
            suggestions = query.order_by(Suggestion.created_at.desc()).limit(10).all()
            
            if not suggestions:
                return await interaction.response.send_message(f"📝 No {status} suggestions found.", ephemeral=True)
            
            embed = discord.Embed(
                title=f"💡 Server Suggestions ({status.title()})",
                color=0x3498db
            )
            
            for suggestion in suggestions:
                user = interaction.guild.get_member(suggestion.user_id)
                username = user.display_name if user else "Unknown User"
                
                status_emoji = {
                    "pending": "🔄",
                    "approved": "✅", 
                    "denied": "❌",
                    "implemented": "🎉"
                }
                
                embed.add_field(
                    name=f"{status_emoji.get(suggestion.status, '📝')} {suggestion.title}",
                    value=f"By: {username} | 👍 {suggestion.upvotes} 👎 {suggestion.downvotes}",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error fetching suggestions: {e}", ephemeral=True)
    
    # ============= TICKET SYSTEM =============
    
    @bot.tree.command(name="ticket", description="Create a support ticket")
    async def ticket_command(interaction: discord.Interaction):
        """Create support ticket interface"""
        embed = discord.Embed(
            title="🎫 Support Tickets",
            description="Click the button below to create a new support ticket.\n\nOur staff will assist you as soon as possible!",
            color=0x3498db
        )
        embed.add_field(
            name="📋 Categories",
            value="• **General** - General questions\n• **Technical** - Technical issues\n• **Report** - Report problems\n• **Other** - Other concerns",
            inline=False
        )
        
        view = TicketView()
        await interaction.response.send_message(embed=embed, view=view)
    
    @bot.tree.command(name="tickets", description="View your support tickets")
    async def my_tickets(interaction: discord.Interaction):
        """View user's tickets"""
        try:
            tickets = Ticket.query.filter_by(
                guild_id=interaction.guild.id,
                user_id=interaction.user.id
            ).order_by(Ticket.created_at.desc()).limit(5).all()
            
            if not tickets:
                return await interaction.response.send_message("🎫 You have no support tickets.", ephemeral=True)
            
            embed = discord.Embed(
                title="🎫 Your Support Tickets",
                color=0x3498db
            )
            
            for ticket in tickets:
                status_emoji = {
                    "open": "🟢",
                    "closed": "🔴",
                    "archived": "📦"
                }
                
                channel = interaction.guild.get_channel(ticket.channel_id)
                channel_text = channel.mention if channel else "Channel Deleted"
                
                embed.add_field(
                    name=f"#{ticket.ticket_number:04d} - {ticket.title}",
                    value=f"Status: {status_emoji.get(ticket.status, '❓')} {ticket.status.title()}\nChannel: {channel_text}",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error fetching tickets: {e}", ephemeral=True)
    
    # ============= EVENT SYSTEM =============
    
    @bot.tree.command(name="event", description="Create a server event")
    @app_commands.describe(
        title="Event title",
        description="Event description", 
        date="Date (YYYY-MM-DD)",
        time="Time (HH:MM)",
        duration="Duration in minutes"
    )
    async def create_event(interaction: discord.Interaction, title: str, description: str, date: str, time: str, duration: int = 60):
        """Create a server event"""
        if not interaction.user.guild_permissions.manage_events:
            return await interaction.response.send_message("❌ You need Manage Events permission!", ephemeral=True)
        
        try:
            # Parse datetime
            import re
            date_match = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', date)
            time_match = re.match(r'^(\d{1,2}):(\d{2})$', time)
            
            if not date_match or not time_match:
                return await interaction.response.send_message(
                    "❌ Invalid date/time format! Use YYYY-MM-DD for date and HH:MM for time.",
                    ephemeral=True
                )
            
            year, month, day = map(int, date_match.groups())
            hour, minute = map(int, time_match.groups())
            
            event_datetime = datetime(year, month, day, hour, minute, tzinfo=timezone.utc)
            
            if event_datetime < datetime.now(timezone.utc):
                return await interaction.response.send_message("❌ Event time must be in the future!", ephemeral=True)
            
            # Create event
            with db.session.begin():
                event = Event(
                    guild_id=interaction.guild.id,
                    creator_id=interaction.user.id,
                    title=title,
                    description=description,
                    event_time=event_datetime,
                    duration_minutes=duration
                )
                db.session.add(event)
                db.session.commit()
            
            # Create event embed
            embed = discord.Embed(
                title="📅 New Server Event",
                description=description,
                color=0x00ff00,
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="🎉 Event", value=title, inline=False)
            embed.add_field(name="📅 Date & Time", value=f"<t:{int(event_datetime.timestamp())}:F>", inline=True)
            embed.add_field(name="⏱️ Duration", value=f"{duration} minutes", inline=True)
            embed.add_field(name="👤 Organizer", value=interaction.user.mention, inline=True)
            embed.add_field(name="🎫 RSVP", value="Click buttons below to RSVP!", inline=False)
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            
            view = EventView(event.id)
            await interaction.response.send_message(embed=embed, view=view)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error creating event: {e}", ephemeral=True)
    
    @bot.tree.command(name="events", description="View upcoming server events")
    async def events_list(interaction: discord.Interaction):
        """List upcoming events"""
        try:
            now = datetime.now(timezone.utc)
            events = Event.query.filter(
                Event.guild_id == interaction.guild.id,
                Event.event_time > now,
                Event.is_cancelled == False
            ).order_by(Event.event_time).limit(5).all()
            
            if not events:
                return await interaction.response.send_message("📅 No upcoming events scheduled.", ephemeral=True)
            
            embed = discord.Embed(
                title="📅 Upcoming Events",
                color=0x3498db
            )
            
            for event in events:
                # Get RSVP counts
                attendees = EventAttendee.query.filter_by(event_id=event.id).all()
                going_count = sum(1 for a in attendees if a.status == "going")
                maybe_count = sum(1 for a in attendees if a.status == "maybe")
                
                creator = interaction.guild.get_member(event.creator_id)
                creator_name = creator.display_name if creator else "Unknown"
                
                embed.add_field(
                    name=f"🎉 {event.title}",
                    value=f"**When:** <t:{int(event.event_time.timestamp())}:R>\n**By:** {creator_name}\n**RSVP:** ✅ {going_count} | ❓ {maybe_count}",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error fetching events: {e}", ephemeral=True)
    
    # ============= BIRTHDAY SYSTEM =============
    
    @bot.tree.command(name="birthday", description="Set your birthday")
    @app_commands.describe(
        month="Birth month (1-12)",
        day="Birth day (1-31)",
        year="Birth year (optional, for age calculation)"
    )
    async def set_birthday(interaction: discord.Interaction, month: int, day: int, year: Optional[int] = None):
        """Set user birthday"""
        if not (1 <= month <= 12):
            return await interaction.response.send_message("❌ Month must be between 1-12!", ephemeral=True)
        
        if not (1 <= day <= 31):
            return await interaction.response.send_message("❌ Day must be between 1-31!", ephemeral=True)
        
        if year and (year < 1900 or year > datetime.now().year):
            return await interaction.response.send_message("❌ Invalid year!", ephemeral=True)
        
        try:
            # Validate date
            test_date = datetime(year or 2000, month, day)
            
            with db.session.begin():
                birthday = UserBirthday.query.filter_by(
                    user_id=interaction.user.id,
                    guild_id=interaction.guild.id
                ).first()
                
                if birthday:
                    birthday.birth_month = month
                    birthday.birth_day = day
                    birthday.birth_year = year
                else:
                    birthday = UserBirthday(
                        user_id=interaction.user.id,
                        guild_id=interaction.guild.id,
                        birth_month=month,
                        birth_day=day,
                        birth_year=year
                    )
                    db.session.add(birthday)
                
                db.session.commit()
            
            # Calculate next birthday
            now = datetime.now(timezone.utc)
            next_birthday = datetime(now.year, month, day, tzinfo=timezone.utc)
            if next_birthday < now:
                next_birthday = datetime(now.year + 1, month, day, tzinfo=timezone.utc)
            
            embed = discord.Embed(
                title="🎂 Birthday Set!",
                description=f"Your birthday has been set to **{month}/{day}**" + (f"/{year}" if year else ""),
                color=0xff69b4
            )
            embed.add_field(
                name="🎉 Next Birthday",
                value=f"<t:{int(next_birthday.timestamp())}:R>",
                inline=True
            )
            embed.set_footer(text="You'll get a special birthday message when the day comes!")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except ValueError:
            await interaction.response.send_message("❌ Invalid date!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error setting birthday: {e}", ephemeral=True)
    
    @bot.tree.command(name="birthdays", description="View upcoming birthdays")
    async def upcoming_birthdays(interaction: discord.Interaction):
        """View upcoming birthdays"""
        try:
            now = datetime.now(timezone.utc)
            current_month = now.month
            current_day = now.day
            
            # Get birthdays in the next 30 days
            birthdays = UserBirthday.query.filter_by(
                guild_id=interaction.guild.id,
                is_public=True
            ).all()
            
            upcoming = []
            for birthday in birthdays:
                # Calculate next occurrence
                next_birthday = datetime(now.year, birthday.birth_month, birthday.birth_day, tzinfo=timezone.utc)
                if next_birthday < now:
                    next_birthday = datetime(now.year + 1, birthday.birth_month, birthday.birth_day, tzinfo=timezone.utc)
                
                days_until = (next_birthday - now).days
                if days_until <= 30:
                    user = interaction.guild.get_member(birthday.user_id)
                    if user:
                        upcoming.append((user, next_birthday, days_until, birthday.birth_year))
            
            if not upcoming:
                return await interaction.response.send_message("🎂 No upcoming birthdays in the next 30 days.", ephemeral=True)
            
            # Sort by date
            upcoming.sort(key=lambda x: x[1])
            
            embed = discord.Embed(
                title="🎂 Upcoming Birthdays",
                color=0xff69b4
            )
            
            for user, birthday_date, days_until, birth_year in upcoming[:10]:  # Limit to 10
                age_text = ""
                if birth_year:
                    age = birthday_date.year - birth_year
                    age_text = f" (turning {age})"
                
                if days_until == 0:
                    when_text = "🎉 **TODAY!** 🎉"
                elif days_until == 1:
                    when_text = "🎈 Tomorrow"
                else:
                    when_text = f"In {days_until} days"
                
                embed.add_field(
                    name=f"🎂 {user.display_name}{age_text}",
                    value=f"{when_text}\n{birthday.birth_month}/{birthday.birth_day}",
                    inline=True
                )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error fetching birthdays: {e}", ephemeral=True)
    
    # Background task to check birthdays
    @tasks.loop(hours=1)
    async def check_birthdays():
        """Check for birthdays and send congratulations"""
        try:
            with app.app_context():
                now = datetime.now(timezone.utc)
                today = now.date()
                
                # Find today's birthdays
                birthdays = UserBirthday.query.filter(
                    UserBirthday.birth_month == today.month,
                    UserBirthday.birth_day == today.day,
                    UserBirthday.remind_enabled == True
                ).all()
                
                for birthday in birthdays:
                    try:
                        guild = bot.get_guild(birthday.guild_id)
                        if not guild:
                            continue
                        
                        user = guild.get_member(birthday.user_id)
                        if not user:
                            continue
                        
                        # Find general channel
                        channel = discord.utils.get(guild.channels, name="general") or guild.system_channel
                        if not channel:
                            continue
                        
                        # Calculate age if year provided
                        age_text = ""
                        if birthday.birth_year:
                            age = today.year - birthday.birth_year
                            age_text = f" turning {age}"
                        
                        embed = discord.Embed(
                            title="🎉 Happy Birthday! 🎉",
                            description=f"It's {user.mention}'s birthday{age_text}!\n\nLet's wish them a wonderful day! 🎂✨",
                            color=0xff69b4,
                            timestamp=now
                        )
                        embed.set_thumbnail(url=user.display_avatar.url)
                        embed.set_footer(text="🎈 Birthday wishes from the server! 🎈")
                        
                        await channel.send(f"🎂 {user.mention} 🎂", embed=embed)
                    
                    except Exception as e:
                        print(f"Error sending birthday message: {e}")
                    
        except Exception as e:
            print(f"Error checking birthdays: {e}")
    
    # Start birthday checking task
    if not check_birthdays.is_running():
        check_birthdays.start()
    
    print("✅ All community feature commands loaded successfully!")