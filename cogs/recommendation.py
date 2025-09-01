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
        self.recommendations = {}  # {guild_id: [(user, url)]}
        print("[DEBUG] Recommendation cog initialized")

    def get_recommendations(self, guild_id):
        return self.recommendations.setdefault(guild_id, [])

    @app_commands.command(name="recommend", description="Recommend a song in a text channel")
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
        guild = interaction.guild
        recs = self.get_recommendations(guild.id)
        recs.append((interaction.user.mention, url))
        if len(recs) > 10:
            recs.pop(0)  # Remove oldest

        # Clear old bot messages in the chosen channel
        async for msg in channel.history(limit=100):
            if msg.author == self.bot.user:
                await msg.delete()

        embed = discord.Embed(
            title="🎵 Music Recommendations (Latest 10)", color=discord.Color.green()
        )
        for i, (user, song_url) in enumerate(recs, 1):
            embed.add_field(name=f"{i}. {user}", value=song_url, inline=False)

        await channel.send(embed=embed)
        await interaction.response.send_message(
            f"✅ Your recommendation has been added to {channel.mention}!", ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Recommendation(bot))
