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
        # Create embed with recommendation info
        embed = discord.Embed(
            title="🎵 Music Recommendation",
            description=f"**Recommended by {interaction.user.mention}**",
            color=discord.Color.green()
        )
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        
        # Send embed and URL separately for clean video embed
        await channel.send(embed=embed)
        await channel.send(url)
        
        # Respond to user
        await interaction.response.send_message(
            f"✅ Your recommendation has been sent to {channel.mention}!", ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Recommendation(bot))
