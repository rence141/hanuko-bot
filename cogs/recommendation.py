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
        # Validate bot permissions for the target channel first
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

        # To get a playable preview, the URL must be in the message content (not only inside an embed)
        message_content = f"🎵 Recommended by {interaction.user.mention}\n{url}"

        # Warn the user if embeds are disabled for the bot in that channel
        embed_warning = None
        if not perms.embed_links:
            embed_warning = (
                "⚠️ I don't have Embed Links in that channel. The link will send, "
                "but Discord may not show a playable preview."
            )

        try:
            # Avoid pinging the recommender while still showing a mention
            await channel.send(
                message_content,
                allowed_mentions=discord.AllowedMentions.none(),
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                f"❌ Missing access to post in {channel.mention}. Please grant 'View Channel' and 'Send Messages' to my role.",
                ephemeral=True,
            )
            return

        # Respond ephemerally to the user
        if embed_warning:
            await interaction.response.send_message(
                f"✅ Sent to {channel.mention}. {embed_warning}", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"✅ Your recommendation has been sent to {channel.mention}!", ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Recommendation(bot))
