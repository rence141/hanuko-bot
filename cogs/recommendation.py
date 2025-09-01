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
        """Send the recommendation as an embed with link preview."""
        # Build an embed that shows the URL and who recommended it
        embed = discord.Embed(
            title=f"🎵 Recommended by {interaction.user.display_name}",
            description=url,
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Recommended in {channel.name}")
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)

        # Send embed to the target channel
        await channel.send(embed=embed)
        
        # Respond ephemerally to the user
        await interaction.response.send_message(
            f"✅ Your recommendation has been sent to {channel.mention}!", ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Recommendation(bot))
