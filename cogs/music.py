# cogs/music.py
import discord
from discord.ext import commands

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def pingmusic(self, ctx):
        """Simple test command for the music cog"""
        await ctx.send("🎵 Music cog is loaded!")

async def setup(bot):
    await bot.add_cog(Music(bot))
