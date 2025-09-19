import discord
from discord.ext import commands
from discord import app_commands
import asyncio

class Diagnostic(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context):
        """Prefix command to test responsiveness"""
        await ctx.send(f"Pong! Latency: {round(self.bot.latency * 1000)} ms")

    @app_commands.command(name="hello", description="Say hi to the bot")
    async def hello(self, interaction: discord.Interaction):
        """
        Slash commands must ACK within ~3s. Defer immediately, then follow up.
        """
        try:
            await interaction.response.defer(ephemeral=True)
            await interaction.followup.send(
                f"👋 Hi {interaction.user.mention}! "
                f"Latency: {round(self.bot.latency * 1000)} ms"
            )
        except Exception as e:
            try:
                await interaction.followup.send(f"❌ Error: {e}")
            except Exception:
                pass

async def setup(bot: commands.Bot):
    await bot.add_cog(Diagnostic(bot))
