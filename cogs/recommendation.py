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
        """Send the recommendation in a way that Discord auto-embeds the link (playable)."""
        # To get a playable preview, the URL must be in the message content (not only inside an embed)
        message_content = (
            f"🎵 Recommended by {interaction.user.mention}\n{url}"
        )

        # Avoid pinging the recommender while still showing a mention
        await channel.send(
            message_content,
            allowed_mentions=discord.AllowedMentions.none()
        )
        
        # Respond ephemerally to the user
        await interaction.response.send_message(
            f"✅ Your recommendation has been sent to {channel.mention}!", ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Recommendation(bot))
