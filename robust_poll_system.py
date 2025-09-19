"""
Comprehensive Poll System for Discord Bot
Features: Multiple poll types, 20+ options, real-time updates, advanced voting features
"""

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union, Set
import json
import time

# -------------------------------------------------
# THEME / BRANDING
# Set this to your logo/theme color (embed color)
# Example: 0xFFA500 (orange), 0x5865F2 (Discord blurple)
# -------------------------------------------------
BRAND_COLOR = 0xFFA500  # change to match your logo brand color

# ---------------------------
# Modal to collect options
# ---------------------------

class MoreOptionsModal(discord.ui.Modal):
    def __init__(self, poll_type: str = "standard", question: str = "", duration: Optional[int] = None,
                 anonymous: bool = False, allowedrole: Optional[str] = None):
        super().__init__(title="📝 Poll Setup - Add Your Options")
        self.poll_type = poll_type
        self.question = question
        self.duration = duration
        self.anonymous = anonymous
        self.allowedrole = allowedrole

        self.bulk_options = discord.ui.TextInput(
            label="Enter All Your Options",
            placeholder="Type each option on a new line:\nOption A\nOption B\nOption C\n...(up to 20 total)",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=2000
        )
        self.add_item(self.bulk_options)

    async def on_submit(self, interaction: discord.Interaction):
        lines = self.bulk_options.value.strip().split('\n')
        options_list = [line.strip() for line in lines if line.strip()]

        if len(options_list) < 2:
            await interaction.response.send_message("❌ You need at least 2 options for a poll!", ephemeral=True)
            return

        if len(options_list) > 20:
            await interaction.response.send_message("❌ Maximum 20 options allowed! Please reduce your list.", ephemeral=True)
            return

        await self._create_poll_with_options(interaction, options_list)

    async def _create_poll_with_options(self, interaction: discord.Interaction, options_list: List[str]):
        poll_data = {
            'type': self.poll_type,
            'question': self.question,
            'options': options_list,
            'multiple_choice': False,
            'anonymous': self.anonymous,
            'creator_id': interaction.user.id,
            'creator_name': interaction.user.display_name,
            'created_at': time.time(),
            'votes': {},
            'allowedrole': getattr(self, 'allowedrole', None),
            'theme_color': BRAND_COLOR,  # apply branding color
        }

        if self.duration:
            poll_data['duration'] = self.duration
            poll_data['end_time'] = time.time() + (self.duration * 60)

        await send_poll_response(interaction, poll_data, self.duration)

# ---------------------------
# Setup view (launch modal)
# ---------------------------

class PollSetupView(discord.ui.View):
    def __init__(self, poll_type: str = "standard", question: str = "", duration: Optional[int] = None,
                 anonymous: bool = False, allowedrole: Optional[str] = None):
        super().__init__(timeout=300)
        self.poll_type = poll_type
        self.question = question
        self.duration = duration
        self.anonymous = anonymous
        self.allowedrole = allowedrole

    @discord.ui.button(label="📝 Poll Setup (2-20 options)", style=discord.ButtonStyle.primary, emoji="✨")
    async def poll_setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = MoreOptionsModal(
            poll_type=self.poll_type,
            question=self.question,
            duration=self.duration,
            anonymous=self.anonymous,
            allowedrole=self.allowedrole
        )
        await interaction.response.send_modal(modal)

# ---------------------------
# Main poll view + buttons
# ---------------------------

class PollView(discord.ui.View):
    def __init__(self, poll_data: Dict[str, Any], timeout: Optional[float] = None):
        super().__init__(timeout=timeout)
        self.poll_data = poll_data
        self.poll_type = poll_data.get('type', 'standard')
        self.votes: Dict[str, List[int]] = poll_data.get('votes', {})  # user_id -> [indices]
        self.multiple_choice = poll_data.get('multiple_choice', False)
        self.anonymous = poll_data.get('anonymous', False)
        self.message: Optional[discord.InteractionMessage] = None

        # Track users who have ever voted (only for Manage eligibility, NOT to block revotes)
        self.has_ever_voted: Set[str] = set(poll_data.get('has_ever_voted', list(self.votes.keys())))
        self._setup_buttons()

    def _persist_voting_state(self):
        self.poll_data['has_ever_voted'] = list(self.has_ever_voted)

    def _get_vote_counts(self):
        options = self.poll_data.get('options', [])
        vote_counts = [0] * len(options)
        for user_votes in self.votes.values():
            for idx in user_votes:
                if 0 <= idx < len(vote_counts):
                    vote_counts[idx] += 1
        return vote_counts

    def _setup_buttons(self):
        options = self.poll_data.get('options', [])
        _ = self._get_vote_counts()

        if self.poll_type == 'rating':
            rating_emojis = ['1️⃣','2️⃣','3️⃣','4️⃣','5️⃣','6️⃣','7️⃣','8️⃣','9️⃣','🔟']
            scale = self.poll_data.get('scale', 5)
            for i in range(1, scale + 1):
                emoji = rating_emojis[i-1] if i-1 < len(rating_emojis) else str(i)
                self.add_item(RatingButton(emoji, i))
        else:
            alphabet = [chr(ord('A') + i) for i in range(20)]
            for i, _opt in enumerate(options[:20]):
                letter = alphabet[i] if i < len(alphabet) else f"{i+1}"
                self.add_item(VoteButton(None, letter, i))

        # Utility buttons
        manage_button = ViewResultsButton()
        manage_button.label = "Manage Vote"  # Capitalized V
        self.add_item(manage_button)

        creator_id = self.poll_data.get('creator_id')
        if creator_id:
            voters_button = ParticipantsButton(len(self.votes))
            voters_button.label = "Voters"
            self.add_item(voters_button)

        self._update_button_labels()

    def _update_button_labels(self):
        vote_counts = self._get_vote_counts()
        alphabet = [chr(ord('A') + i) for i in range(20)]

        voting_buttons = [c for c in self.children if isinstance(c, (VoteButton, RatingButton))]
        for i, button in enumerate(voting_buttons):
            if i < len(vote_counts):
                if isinstance(button, RatingButton):
                    button.label = f"{vote_counts[i]}"
                    button.style = discord.ButtonStyle.primary
                else:
                    button.label = alphabet[i] if i < len(alphabet) else f"{i+1}"
                    button.style = discord.ButtonStyle.primary

        for button in self.children:
            if isinstance(button, ParticipantsButton):
                button.label = f"Voters ({len(self.votes)})"

class VoteButton(discord.ui.Button):
    def __init__(self, emoji: Optional[str], label: str, option_index: int):
        if emoji is None:
            super().__init__(style=discord.ButtonStyle.primary, label=label[:80])
        else:
            super().__init__(style=discord.ButtonStyle.primary, emoji=emoji, label=label[:80])
        self.option_index = option_index

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if not isinstance(view, PollView):
            await interaction.response.send_message("❌ Poll view error. Please try again.", ephemeral=True)
            return

        user_id = str(interaction.user.id)

        # Allow revote AFTER clearing: only block if the user currently has a vote
        if user_id in view.votes:
            await interaction.response.send_message("🔒 You already voted! Use **Manage Vote** to change it.", ephemeral=True)
            return

        view.votes[user_id] = [self.option_index]
        view.has_ever_voted.add(user_id)
        view._persist_voting_state()

        view._update_button_labels()
        embed = await generate_poll_embed(view.poll_data, view.votes, show_results=False)
        await interaction.response.edit_message(embed=embed, view=view)

class RatingButton(discord.ui.Button):
    def __init__(self, emoji: str, rating: int):
        super().__init__(style=discord.ButtonStyle.primary, emoji=emoji, label="0")
        self.rating = rating

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if not isinstance(view, PollView):
            await interaction.response.send_message("❌ Poll view error. Please try again.", ephemeral=True)
            return

        user_id = str(interaction.user.id)
        if user_id in view.votes:
            await interaction.response.send_message("🔒 You already voted! Use **Manage Vote** to change it.", ephemeral=True)
            return

        view.votes[user_id] = [self.rating - 1]  # 0-based
        view.has_ever_voted.add(user_id)
        view._persist_voting_state()

        view._update_button_labels()
        embed = await generate_poll_embed(view.poll_data, view.votes, show_results=False)
        await interaction.response.edit_message(embed=embed, view=view)

class ViewResultsButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.secondary, label="Manage Vote", row=4)  # Capitalized V

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if not isinstance(view, PollView):
            await interaction.response.send_message("❌ Poll view error. Please try again.", ephemeral=True)
            return

        user_id = str(interaction.user.id)
        user_votes = view.votes.get(user_id, [])

        # Allow if they have ever voted (even if currently cleared)
        if not user_votes and user_id not in view.has_ever_voted:
            await interaction.response.send_message("❌ You haven't voted in this poll yet!", ephemeral=True)
            return

        options = view.poll_data.get('options', [])
        alphabet = [chr(ord('A') + i) for i in range(20)]

        if user_votes:
            vote_display = []
            for vote_index in user_votes:
                if 0 <= vote_index < len(options):
                    letter = alphabet[vote_index] if vote_index < len(alphabet) else f"{vote_index+1}"
                    vote_display.append(f"{letter}) {options[vote_index]}")
            desc = f"You voted for: {', '.join(vote_display)}\n\nYou can change or clear your vote below."
            embed = discord.Embed(title="🗳️ Your Current Vote", description=desc, color=BRAND_COLOR)
        else:
            embed = discord.Embed(
                title="🗳️ Vote Management",
                description="Your vote has been cleared.\n\nUse the selector below to set a new one.",
                color=BRAND_COLOR
            )

        manage_view = VoteManagementView(user_id, view)
        await interaction.response.send_message(embed=embed, view=manage_view, ephemeral=True)

class VoteManagementView(discord.ui.View):
    def __init__(self, user_id: str, poll_view: PollView):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.poll_view = poll_view

        user_votes = poll_view.votes.get(user_id, [])

        if poll_view.poll_type == 'rating':
            scale = poll_view.poll_data.get('scale', 5)
            options = []
            for i in range(1, scale+1):
                idx = i - 1
                label = f"✅ Rating: {i}" if idx in user_votes else f"Rating: {i}"
                options.append(discord.SelectOption(label=label, value=str(idx)))
        else:
            poll_options = poll_view.poll_data.get('options', [])
            alphabet = [chr(ord('A') + i) for i in range(20)]
            options = []
            for i, option in enumerate(poll_options[:20]):
                letter = alphabet[i] if i < len(alphabet) else f"{i+1}"
                label = f"✅ {letter}: {option}" if i in user_votes else f"{letter}: {option}"
                options.append(discord.SelectOption(label=label, value=str(i)))

        if options:
            select = ChangeVoteSelect(self.user_id, self.poll_view, options)
            self.add_item(select)

    @discord.ui.button(label="Clear My Vote", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def clear_vote(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.user_id in self.poll_view.votes:
            del self.poll_view.votes[self.user_id]

        self.poll_view._update_button_labels()
        embed = await generate_poll_embed(self.poll_view.poll_data, self.poll_view.votes, show_results=False)

        try:
            if self.poll_view.message:
                await self.poll_view.message.edit(embed=embed, view=self.poll_view)
        except Exception as e:
            print(f"Error updating poll message: {e}")

        await interaction.response.send_message("✅ Your vote has been cleared! You can vote again now.", ephemeral=True)

    @discord.ui.button(label="Close", style=discord.ButtonStyle.secondary, emoji="❌")
    async def close_manage(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Vote management closed.", embed=None, view=None)

class ChangeVoteSelect(discord.ui.Select):
    def __init__(self, user_id: str, poll_view: PollView, options: List[discord.SelectOption]):
        super().__init__(placeholder="Select a new choice…", options=options)
        self.user_id = user_id
        self.poll_view = poll_view

    async def callback(self, interaction: discord.Interaction):
        new_vote_index = int(self.values[0])
        self.poll_view.votes[self.user_id] = [new_vote_index]

        self.poll_view._update_button_labels()
        embed = await generate_poll_embed(self.poll_view.poll_data, self.poll_view.votes, show_results=False)

        try:
            if self.poll_view.message:
                await self.poll_view.message.edit(embed=embed, view=self.poll_view)
        except Exception as e:
            print(f"Error updating poll message: {e}")

        # Confirmation
        if self.poll_view.poll_type == 'rating':
            selected_label = f"Rating: {new_vote_index + 1}"
        else:
            options = self.poll_view.poll_data.get('options', [])
            alphabet = [chr(ord('A') + i) for i in range(20)]
            if 0 <= new_vote_index < len(options):
                letter = alphabet[new_vote_index] if new_vote_index < len(alphabet) else f"{new_vote_index+1}"
                selected_label = f"{letter}: {options[new_vote_index]}"
            else:
                selected_label = "Unknown"
        await interaction.response.send_message(f"✅ Your vote has been changed to: {selected_label}", ephemeral=True)

# “Creator-only” participants list (non-anonymous)
class ParticipantsButton(discord.ui.Button):
    def __init__(self, participant_count: int = 0):
        super().__init__(style=discord.ButtonStyle.secondary, label=f"Participants ({participant_count})", row=4)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if not isinstance(view, PollView):
            await interaction.response.send_message("❌ Poll view error. Please try again.", ephemeral=True)
            return

        creator_id = view.poll_data.get('creator_id')
        if creator_id != interaction.user.id:
            await interaction.response.send_message("🔒 Only the poll creator can see the voters list.", ephemeral=True)
            return

        if view.anonymous:
            await interaction.response.send_message("🕵️ This poll is anonymous - participants are hidden!", ephemeral=True)
            return

        if not interaction.guild:
            await interaction.response.send_message("❌ This can only be used in servers.", ephemeral=True)
            return

        embed = await generate_voters_embed(view.poll_data, view.votes, interaction.guild)
        await interaction.response.send_message(embed=embed, ephemeral=True)

# ---------------------------
# Embeds
# ---------------------------

async def generate_poll_embed(poll_data: Dict[str, Any], votes: Dict[str, List[int]], show_results: bool = False) -> discord.Embed:
    poll_type = poll_data.get('type', 'standard')
    question = poll_data.get('question', 'Poll')
    color = poll_data.get('theme_color', BRAND_COLOR)  # use theme color

    embed = discord.Embed(
        title=question,
        description="Vote by clicking the buttons below.",
        color=color
    )

    creator_name = poll_data.get('creator_name', 'Unknown')
    embed.set_author(name=f"Poll by {creator_name}")

    options = poll_data.get('options', [])
    alphabet = [chr(ord('A') + i) for i in range(20)]
    choice_lines = []

    for i, option in enumerate(options):
        if poll_type == 'rating':
            choice_lines.append(f"{i+1}: {option}")
        else:
            letter = alphabet[i] if i < len(alphabet) else f"{i+1}"
            choice_lines.append(f"{letter}: {option}")

    embed.add_field(name="Options", value='\n'.join(choice_lines) + '\n\u200b', inline=False)

    settings_text = "Multiple choice" if poll_data.get('multiple_choice') else "Single choice"
    if poll_data.get('anonymous'):
        settings_text += " • Anonymous"
    embed.add_field(name="Settings", value=settings_text + '\n\u200b', inline=False)

    end_time = poll_data.get('end_time')
    if end_time:
        embed.add_field(name="Ends", value=f"<t:{int(end_time)}:R>" + '\n\u200b', inline=False)

    poll_id = poll_data.get('poll_id')
    if not poll_id:
        import random, string
        poll_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        poll_data['poll_id'] = poll_id
    embed.add_field(name="Poll ID", value=poll_id, inline=False)

    unique_voters = len(votes)
    total_votes = sum(len(user_votes) for user_votes in votes.values())
    embed.set_footer(text=f"👥 {unique_voters} participants • 🗳️ {total_votes} votes")

    return embed

async def generate_detailed_results_embed(poll_data: Dict[str, Any], votes: Dict[str, List[int]]) -> discord.Embed:
    embed = discord.Embed(
        title=f"📊 Detailed Results: {poll_data.get('question', 'Poll')}",
        color=BRAND_COLOR,
        timestamp=datetime.utcnow()
    )

    options = poll_data.get('options', [])
    vote_counts = [0] * len(options)
    total_votes = 0

    for user_votes in votes.values():
        for vote_index in user_votes:
            if 0 <= vote_index < len(vote_counts):
                vote_counts[vote_index] += 1
                total_votes += 1

    if total_votes > 0:
        results_text = ""
        for i, option in enumerate(options):
            count = vote_counts[i]
            percentage = (count / total_votes) * 100 if total_votes else 0.0
            bar_len = int(percentage / 2.5)
            bar = "█" * bar_len + "░" * (40 - bar_len)
            results_text += f"**{option}**\n`{bar}` **{count}** votes ({percentage:.2f}%)\n\n"

        embed.description = results_text
        embed.add_field(
            name="Statistics",
            value=(
                f"**Total Votes**: {total_votes}\n"
                f"**Unique Voters**: {len(votes)}\n"
                f"**Participation Rate**: "
                f"{(len(votes) / max(1, poll_data.get('max_voters', len(votes)))) * 100:.1f}%"
            ),
            inline=False
        )
    else:
        embed.description = "No votes have been cast yet. All options start at **0 votes**."

    return embed

async def generate_voters_embed(poll_data: Dict[str, Any], votes: Dict[str, List[int]], guild: discord.Guild) -> discord.Embed:
    embed = discord.Embed(
        title=f"👥 Voters: {poll_data.get('question', 'Poll')}",
        color=0x95a5a6,
        timestamp=datetime.utcnow()
    )

    if not votes:
        embed.description = "No votes have been cast yet."
        return embed

    options = poll_data.get('options', [])
    voters_by_option: Dict[str, List[str]] = {}

    for user_id, user_votes in votes.items():
        member = guild.get_member(int(user_id))
        username = member.display_name if member else f"User {user_id}"
        for vote_index in user_votes:
            if 0 <= vote_index < len(options):
                opt = options[vote_index]
                voters_by_option.setdefault(opt, []).append(username)

    for option, voters in voters_by_option.items():
        voter_list = ", ".join(voters)
        if len(voter_list) > 1000:
            voter_list = voter_list[:997] + "..."
        embed.add_field(name=f"{option} ({len(voters)} votes)", value=voter_list, inline=False)

    return embed

async def generate_creator_results_embed(poll_data: Dict[str, Any], votes: Dict[str, List[int]], guild: Optional[discord.Guild] = None) -> discord.Embed:
    question = poll_data.get('question', 'Poll')
    embed = discord.Embed(title=f"📊 Creator Results: {question}", color=BRAND_COLOR)

    options = poll_data.get('options', [])
    vote_counts = [0] * len(options)
    total_votes = 0

    for user_votes in votes.values():
        for vote_index in user_votes:
            if 0 <= vote_index < len(options):
                vote_counts[vote_index] += 1
                total_votes += 1

    if total_votes > 0:
        voters_by_option: Dict[int, List[str]] = {}
        alphabet = [chr(ord('A') + i) for i in range(20)]

        for user_id, user_votes in votes.items():
            username = f"User {user_id}"
            if guild:
                member = guild.get_member(int(user_id))
                if member:
                    username = member.display_name
            for vote_index in user_votes:
                if 0 <= vote_index < len(options):
                    voters_by_option.setdefault(vote_index, []).append(username)

        for i, option in enumerate(options):
            count = vote_counts[i]
            letter = alphabet[i] if i < len(alphabet) else f"{i+1}"
            if i in voters_by_option and voters_by_option[i]:
                voter_list = ", ".join(voters_by_option[i])
                if len(voter_list) > 150:
                    voter_list = voter_list[:147] + "..."
                embed.add_field(name=f"{letter}) {option} - {count} votes", value=voter_list, inline=False)
            else:
                embed.add_field(name=f"{letter}) {option} - {count} votes", value="No votes", inline=False)

        embed.set_footer(text=f"Total votes: {total_votes} • Unique voters: {len(votes)}")
    else:
        embed.description = "No votes have been cast yet."

    return embed

# ---------------------------
# Ranked Choice helpers
# ---------------------------

def calculate_irv_winner(votes: Dict[str, List[int]], options: List[str]) -> Dict[str, Any]:
    if not votes:
        return {"winner": None, "rounds": [], "total_votes": 0}

    remaining = list(range(len(options)))
    rounds = []

    while len(remaining) > 1:
        counts = {i: 0 for i in remaining}
        valid_votes = 0

        for ranking in votes.values():
            for choice in ranking:
                if choice in remaining:
                    counts[choice] += 1
                    valid_votes += 1
                    break

        if valid_votes == 0:
            break

        majority = valid_votes / 2
        for idx, c in counts.items():
            if c > majority:
                rounds.append({
                    "round": len(rounds) + 1,
                    "counts": {options[i]: counts[i] for i in remaining},
                    "eliminated": None,
                    "winner": options[idx]
                })
                return {"winner": options[idx], "rounds": rounds, "total_votes": len(votes), "method": "IRV"}

        min_votes = min(counts.values())
        eliminated = [i for i, c in counts.items() if c == min_votes][0]
        rounds.append({
            "round": len(rounds) + 1,
            "counts": {options[i]: counts[i] for i in remaining},
            "eliminated": options[eliminated],
            "winner": None
        })
        remaining.remove(eliminated)

    winner = remaining[0] if remaining else None
    return {"winner": options[winner] if winner is not None else None, "rounds": rounds, "total_votes": len(votes), "method": "IRV"}

def calculate_borda_count(votes: Dict[str, List[int]], options: List[str]) -> Dict[str, Any]:
    if not votes:
        return {"winner": None, "scores": {}, "total_votes": 0}

    n = len(options)
    scores = {i: 0 for i in range(n)}

    for ranking in votes.values():
        for pos, opt_idx in enumerate(ranking):
            points = max(0, n - pos - 1)
            if 0 <= opt_idx < n:
                scores[opt_idx] += points

    winner_idx = None if not any(v > 0 for v in scores.values()) else max(scores, key=lambda k: scores[k])
    return {"winner": options[winner_idx] if winner_idx is not None else None,
            "scores": {options[i]: scores[i] for i in range(n)},
            "total_votes": len(votes),
            "method": "Borda Count"}

async def generate_ranking_results_embed(poll_data: Dict[str, Any], votes: Dict[str, List[int]]) -> discord.Embed:
    options = poll_data.get('options', [])
    method = poll_data.get('ranking_method', 'irv')

    if method == 'irv':
        results = calculate_irv_winner(votes, options)
        title = "🏆 IRV Results (Instant Runoff Voting)"
        color = 0xf39c12
    else:
        results = calculate_borda_count(votes, options)
        title = "🏆 Borda Count Results"
        color = 0xe67e22

    embed = discord.Embed(
        title=title,
        description=f"Poll: **{poll_data.get('question', 'Ranked Choice Poll')}**",
        color=color,
        timestamp=datetime.utcnow()
    )

    winner = results.get('winner')
    embed.add_field(name=("🎉 Winner" if winner else "Result"),
                    value=(f"**{winner}**" if winner else "No clear winner"),
                    inline=False)

    if method == 'irv' and 'rounds' in results:
        rounds_text = ""
        for rd in results['rounds']:
            rounds_text += f"**Round {rd['round']}:**\n"
            for opt, cnt in sorted(rd['counts'].items(), key=lambda x: x[1], reverse=True):
                rounds_text += f"• {opt}: {cnt} votes\n"
            if rd.get('eliminated'):
                rounds_text += f"❌ Eliminated: {rd['eliminated']}\n"
            rounds_text += "\n"

        if len(rounds_text) > 1024:
            parts = rounds_text.split('\n\n')
            for i, part in enumerate(parts):
                if part.strip():
                    embed.add_field(name=("IRV Rounds" if i == 0 else f"IRV Rounds {i+1}"),
                                    value=part[:1024],
                                    inline=False)
        else:
            if rounds_text.strip():
                embed.add_field(name="IRV Rounds", value=rounds_text, inline=False)

    elif method == 'borda' and 'scores' in results:
        scores_text = ""
        for opt, sc in sorted(results['scores'].items(), key=lambda x: x[1], reverse=True):
            scores_text += f"• **{opt}**: {sc} points\n"
        embed.add_field(name="Borda Count Scores", value=scores_text, inline=False)

    embed.add_field(name="Participation", value=f"**{results.get('total_votes', 0)}** voters participated", inline=True)
    embed.set_footer(text=f"Method: {results.get('method', method.upper())}")

    return embed

# ---------------------------
# Send + auto-close
# ---------------------------

async def send_poll_response(interaction: discord.Interaction, poll_data: Dict[str, Any], duration: Optional[int]):
    view = PollView(poll_data, timeout=duration * 60 if duration else None)
    embed = await generate_poll_embed(poll_data, {}, show_results=False)
    content = poll_data.get('allowedrole') or None
    await interaction.response.send_message(content=content, embed=embed, view=view)

    try:
        view.message = await interaction.original_response()
    except Exception as e:
        print(f"Warning: Could not store poll message reference: {e}")

    if duration:
        asyncio.create_task(auto_close_poll(interaction, view, duration))
    return view

async def auto_close_poll(interaction: discord.Interaction, view: PollView, duration: int):
    await asyncio.sleep(duration * 60)

    for item in view.children:
        if isinstance(item, discord.ui.Button):
            item.disabled = True

    poll_type = view.poll_data.get('type', 'standard')
    if poll_type == 'ranked':
        embed = await generate_ranking_results_embed(view.poll_data, view.votes)
        embed.title = f"🔒 CLOSED: {embed.title}"
    else:
        embed = await generate_poll_embed(view.poll_data, view.votes, show_results=True)
        embed.title = f"🔒 CLOSED: {view.poll_data.get('question', 'Poll')}"
    embed.color = 0x95a5a6

    try:
        await interaction.edit_original_response(embed=embed, view=view)
    except Exception as e:
        print(f"Error updating closed poll: {e}")

# ---------------------------
# Command setup
# ---------------------------

def setup_robust_polls(bot: commands.Bot):
    @bot.tree.command(name="poll")
    @app_commands.describe(
        question="Your poll question",
        poll_type="Choose the type of poll you want",
        duration="Poll duration in minutes (optional)",
        anonymous="Hide who voted for what",
        allowedrole="Restrict poll to specific role (optional)"
    )
    @app_commands.choices(poll_type=[
        app_commands.Choice(name="📊 Standard Poll (Custom Options)", value="standard"),
        app_commands.Choice(name="⭐ Rating Scale (1-5 Stars)", value="rating5"),
        app_commands.Choice(name="🔢 Rating Scale (1-10 Points)", value="rating10"),
        app_commands.Choice(name="🏆 Ranked Choice (IRV Voting)", value="ranked_irv"),
        app_commands.Choice(name="📈 Ranked Choice (Borda Count)", value="ranked_borda"),
        app_commands.Choice(name="🎭 Server Roles Poll", value="roles")
    ])
    async def unified_poll(
        interaction: discord.Interaction,
        question: str,
        poll_type: str = "standard",
        duration: Optional[int] = None,
        anonymous: bool = False,
        allowedrole: Optional[discord.Role] = None
    ):
        # Rating
        if poll_type.startswith("rating"):
            scale = 10 if poll_type == "rating10" else 5
            poll_options = [f"Rating {i}" for i in range(1, scale + 1)]
            poll_data = {
                'type': "rating",
                'question': question,
                'options': poll_options,
                'scale': scale,
                'multiple_choice': False,
                'anonymous': anonymous,
                'creator_id': interaction.user.id,
                'creator_name': interaction.user.display_name,
                'created_at': time.time(),
                'votes': {},
                'allowedrole': allowedrole.mention if allowedrole else None,
                'theme_color': BRAND_COLOR,
            }
            if duration:
                poll_data['duration'] = duration
                poll_data['end_time'] = time.time() + (duration * 60)
            await send_poll_response(interaction, poll_data, duration)

        # Roles
        elif poll_type == "roles":
            guild = interaction.guild
            if not guild:
                await interaction.response.send_message("❌ Role polls can only be used in servers!", ephemeral=True)
                return

            roles = [r for r in guild.roles if r.name != "@everyone" and not r.is_bot_managed()][:20]
            if not roles:
                await interaction.response.send_message("❌ No suitable roles found for polling!", ephemeral=True)
                return

            poll_data = {
                'type': 'roles',
                'question': question,
                'options': [r.name for r in roles],
                'role_objects': [{"id": r.id, "name": r.name, "color": r.color.value} for r in roles],
                'multiple_choice': False,
                'anonymous': anonymous,
                'creator_id': interaction.user.id,
                'creator_name': interaction.user.display_name,
                'created_at': time.time(),
                'votes': {},
                'allowedrole': allowedrole.mention if allowedrole else None,
                'theme_color': BRAND_COLOR,
            }
            if duration:
                poll_data['duration'] = duration
                poll_data['end_time'] = time.time() + (duration * 60)
            await send_poll_response(interaction, poll_data, duration)

        # Standard / Ranked
        else:
            setup_embed = discord.Embed(
                title="✨ Poll Setup",
                description=f"**Question:** {question}\n**Type:** {poll_type.replace('_', ' ').title()}\n\nChoose how you want to add your poll options:",
                color=BRAND_COLOR
            )
            features = []
            if anonymous:
                features.append("🕵️ Anonymous Voting")
            if duration:
                features.append(f"⏰ Duration: {duration} minutes")
            if features:
                setup_embed.add_field(name="Poll Settings", value="\n".join(features), inline=False)
            setup_embed.set_footer(text="Choose your preferred option setup method below!")

            actual_type = "ranked" if poll_type.startswith("ranked") else "standard"
            view = PollSetupView(
                poll_type=actual_type,
                question=question,
                duration=duration,
                anonymous=anonymous,
                allowedrole=allowedrole.mention if allowedrole else None
            )
            await interaction.response.send_message(embed=setup_embed, view=view, ephemeral=True)

print("✅ Robust poll system loaded successfully!")
