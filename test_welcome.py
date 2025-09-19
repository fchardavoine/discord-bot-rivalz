#!/usr/bin/env python3
"""Test script to see how Discord formats the welcome message"""

import discord
from discord.ext import commands

# Test the exact formatting we're using
def create_test_embed(member_name="TestUser"):
    embed = discord.Embed(
        title="",
        description="Hey TestUser!\n\nWelcome to RIVALZ MLB THE SHOW!\n\nThis is a HOF league that offers a unique experience unlike any other. With team building, free agency, fixed schedules, league leader awards, and intense competition, it's designed for those who want more than just to play baseball. Please consult the #📖-rulebook channel for detailed information about our league, and let us know in the #⏳-waiting-area channel if you would like to join.",
        color=0x57F287,  # Green left border
    )
    
    # Large avatar image
    embed.set_image(url="https://cdn.discordapp.com/embed/avatars/0.png")
    
    # Black section with member name and welcome text
    member_section = f"```ansi\n\u001b[0;37m{member_name}\u001b[0m\n```"
    welcome_text = f"**Welcome to RIVALZ MLB THE SHOW!**"
    
    embed.add_field(
        name="",
        value=f"{member_section}\n{welcome_text}",
        inline=False
    )
    
    # Footer
    embed.set_footer(text="RIVALZ MLB THE SHOW • Welcoming")
    
    return embed

if __name__ == "__main__":
    embed = create_test_embed()
    print("Embed created for testing")
    print(f"Description length: {len(embed.description)}")
    print(f"Field value: {embed.fields[0].value}")