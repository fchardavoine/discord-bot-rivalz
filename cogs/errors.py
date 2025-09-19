import traceback
import discord
from discord.ext import commands
from discord import app_commands

class ErrorHandler(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        tb = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        print(f"[PREFIX ERROR] {ctx.command} in #{getattr(ctx.channel,'name',ctx.channel)}: {error}\n{tb}")
        try:
            await ctx.reply("❌ Something went wrong. Check logs for details.")
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        tb = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        print(f"[SLASH ERROR] {interaction.command} in #{getattr(interaction.channel,'name',interaction.channel)}: {error}\n{tb}")
        try:
            if interaction.response.is_done():
                await interaction.followup.send("❌ Something went wrong with this command.", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Something went wrong with this command.", ephemeral=True)
        except Exception:
            pass

async def setup(bot: commands.Bot):
    await bot.add_cog(ErrorHandler(bot))
