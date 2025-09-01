# recommendation.py
from discord.ext import commands
import discord
from discord import app_commands

# Try to import config, fall back to config_fallback if not available
try:
    import config
except ImportError:
    import config_fallback as config

class Recommendation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("[DEBUG] Recommendation cog initialized")

    @app_commands.command(
        name="recommend",
        description="Recommend a song in a text channel"
    )
    @app_commands.describe(
        url="The YouTube/Spotify/etc. link you want to recommend",
        channel="The channel where the recommendation will appear"
    )
    async def recommend(
        self,
        interaction: discord.Interaction,
        url: str,
        channel: discord.TextChannel
    ):
        """Send the recommendation with playable video embed."""
        # Send just the URL for clean auto-embed (playable preview)
        await channel.send(url)
        
        # Respond to user
        await interaction.response.send_message(
            f"✅ Your recommendation has been sent to {channel.mention}!", ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Recommendation(bot))
