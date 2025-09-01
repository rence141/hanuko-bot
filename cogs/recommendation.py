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
@app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.guild_id, i.user.id))
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
    """Send the recommendation as an embed."""
    me = interaction.guild.me if interaction.guild else None
    if not me:
        await interaction.response.send_message(
            "❌ This command must be used in a server.", ephemeral=True
        )
        return

    perms = channel.permissions_for(me)
    missing = []
    if not perms.view_channel:
        missing.append("View Channel")
    if not perms.send_messages:
        missing.append("Send Messages")

    if missing:
        await interaction.response.send_message(
            f"❌ I can't post in {channel.mention}. Missing: {', '.join(missing)}.",
            ephemeral=True,
        )
        return

    # Send the URL in message content so Discord auto-embeds it as playable
    message_content = f"🎵 Recommended by {interaction.user.mention}\n{url}"

    try:
        await channel.send(
            message_content,
            allowed_mentions=discord.AllowedMentions.none()
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            f"❌ Missing access to post in {channel.mention}. Please grant 'View Channel' and 'Send Messages' to my role.",
            ephemeral=True,
        )
        return

    await interaction.response.send_message(
        f"✅ Your recommendation has been sent to {channel.mention}!", ephemeral=True
    )
