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
        # Validate guild context
        if not interaction.guild:
            await interaction.response.send_message(
                "❌ This command must be used in a server.", ephemeral=True
            )
            return

        # Check bot permissions in target channel
        bot_member = interaction.guild.me
        perms = channel.permissions_for(bot_member)
        
        missing_perms = []
        if not perms.view_channel:
            missing_perms.append("View Channel")
        if not perms.send_messages:
            missing_perms.append("Send Messages")
        if not perms.embed_links:
            missing_perms.append("Embed Links")

        if missing_perms:
            await interaction.response.send_message(
                f"❌ I can't post in {channel.mention}. Missing permissions: {', '.join(missing_perms)}",
                ephemeral=True
            )
            return

        # Validate URL format
        if not (url.startswith(('http://', 'https://')) and 
                any(domain in url.lower() for domain in ['youtube.com', 'youtu.be', 'spotify.com', 'soundcloud.com', 'bandcamp.com'])):
            await interaction.response.send_message(
                "❌ Please provide a valid music/video URL (YouTube, Spotify, SoundCloud, etc.)",
                ephemeral=True
            )
            return

        try:
            # Send the URL in message content for Discord auto-embed (playable preview)
            message_content = f"🎵 **Recommended by {interaction.user.mention}**\n{url}"
            
            await channel.send(
                message_content,
                allowed_mentions=discord.AllowedMentions.none()
            )
            
            # Respond to user
            await interaction.response.send_message(
                f"✅ Your recommendation has been sent to {channel.mention}!", ephemeral=True
            )
            
        except discord.Forbidden:
            await interaction.response.send_message(
                f"❌ Missing access to post in {channel.mention}. Please check my permissions.",
                ephemeral=True
            )
        except discord.HTTPException as e:
            await interaction.response.send_message(
                f"❌ Failed to send message: {e}",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ An unexpected error occurred: {e}",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Recommendation(bot))
