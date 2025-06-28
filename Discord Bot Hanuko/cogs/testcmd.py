import discord
from discord.ext import commands
from discord import app_commands

class TestCmd(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="testslash", description="Test slash command")
    async def testslash(self, interaction: discord.Interaction):
        await interaction.response.send_message("Slash command works!")

async def setup(bot):
    await bot.add_cog(TestCmd(bot)) 