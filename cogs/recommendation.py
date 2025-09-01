# recommendation.py
from discord.ext import commands
import discord
from discord import app_commands
import logging

# Try to import config, fall back to config_fallback if not available
try:
    import config
except ImportError:
    import config_fallback as config

# Set up logging for this cog
logger = logging.getLogger(__name__)

class Recommendation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("[DEBUG] Recommendation cog initialized")
        logger.info("Recommendation cog initialized")
        
    async def cog_load(self):
        """Called when the cog is loaded"""
        print("[DEBUG] Recommendation cog loaded successfully")
        logger.info("Recommendation cog loaded successfully")
        
    async def cog_unload(self):
        """Called when the cog is unloaded"""
        print("[DEBUG] Recommendation cog unloaded")
        logger.info("Recommendation cog unloaded")

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
        print(f"[DEBUG] Recommend command called by {interaction.user} in {interaction.guild}")
        logger.info(f"Recommend command called by {interaction.user} in {interaction.guild}")
        
        me = interaction.guild.me if interaction.guild else None
        if not me:
            print("[DEBUG] No guild found in interaction")
            logger.warning("No guild found in interaction")
            await interaction.response.send_message(
                "❌ This command must be used in a server.", ephemeral=True
            )
            return

        perms = channel.permissions_for(me)
        print(f"[DEBUG] Bot permissions in {channel}: view={perms.view_channel}, send={perms.send_messages}, embed={perms.embed_links}")
        logger.info(f"Bot permissions in {channel}: view={perms.view_channel}, send={perms.send_messages}, embed={perms.embed_links}")
        
        missing = []
        if not perms.view_channel:
            missing.append("View Channel")
        if not perms.send_messages:
            missing.append("Send Messages")

        if missing:
            print(f"[DEBUG] Missing permissions: {missing}")
            logger.warning(f"Missing permissions: {missing}")
            await interaction.response.send_message(
                f"❌ I can't post in {channel.mention}. Missing: {', '.join(missing)}.",
                ephemeral=True,
            )
            return

        # Send the URL in message content so Discord auto-embeds it as playable
        message_content = f"🎵 Recommended by {interaction.user.mention}\n{url}"
        print(f"[DEBUG] Sending message to {channel}: {message_content}")
        logger.info(f"Sending message to {channel}: {message_content}")

        try:
            await channel.send(
                message_content,
                allowed_mentions=discord.AllowedMentions.none()
            )
            print(f"[DEBUG] Successfully sent recommendation to {channel}")
            logger.info(f"Successfully sent recommendation to {channel}")
        except discord.Forbidden as e:
            print(f"[DEBUG] Forbidden error when sending to {channel}: {e}")
            logger.error(f"Forbidden error when sending to {channel}: {e}")
            await interaction.response.send_message(
                f"❌ Missing access to post in {channel.mention}. Please grant 'View Channel' and 'Send Messages' to my role.",
                ephemeral=True,
            )
            return
        except Exception as e:
            print(f"[DEBUG] Unexpected error when sending to {channel}: {e}")
            logger.error(f"Unexpected error when sending to {channel}: {e}")
            await interaction.response.send_message(
                f"❌ An error occurred: {e}", ephemeral=True
            )
            return

        await interaction.response.send_message(
            f"✅ Your recommendation has been sent to {channel.mention}!", ephemeral=True
        )

    @app_commands.command(
        name="sync",
        description="Sync slash commands (admin only)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def sync(self, interaction: discord.Interaction):
        """Manually sync slash commands"""
        print(f"[DEBUG] Sync command called by {interaction.user}")
        logger.info(f"Sync command called by {interaction.user}")
        
        try:
            print("[DEBUG] Starting command sync...")
            logger.info("Starting command sync...")
            synced = await self.bot.tree.sync()
            print(f"[DEBUG] Successfully synced {len(synced)} commands: {[cmd.name for cmd in synced]}")
            logger.info(f"Successfully synced {len(synced)} commands: {[cmd.name for cmd in synced]}")
            await interaction.response.send_message(
                f"✅ Synced {len(synced)} commands!", ephemeral=True
            )
        except Exception as e:
            print(f"[DEBUG] Sync failed: {e}")
            logger.error(f"Sync failed: {e}")
            await interaction.response.send_message(
                f"❌ Failed to sync: {e}", ephemeral=True
            )

    @app_commands.command(
        name="debug",
        description="Show debug info about the bot and commands"
    )
    async def debug(self, interaction: discord.Interaction):
        """Show debug information"""
        print(f"[DEBUG] Debug command called by {interaction.user}")
        logger.info(f"Debug command called by {interaction.user}")
        
        # Get all registered commands
        commands = self.bot.tree.get_commands()
        command_names = [cmd.name for cmd in commands]
        
        # Get cog info
        cog_info = f"Cog loaded: {self.__class__.__name__}"
        
        # Get bot info
        bot_info = f"Bot: {self.bot.user} (ID: {self.bot.user.id})"
        
        # Get guild info
        guild_info = f"Guild: {interaction.guild.name} (ID: {interaction.guild.id})" if interaction.guild else "No guild"
        
        debug_text = f"""
**Debug Information:**
{bot_info}
{guild_info}
{cog_info}

**Registered Commands ({len(commands)}):**
{', '.join(command_names) if command_names else 'None'}

**Bot Permissions in this channel:**
View Channel: {interaction.channel.permissions_for(interaction.guild.me).view_channel}
Send Messages: {interaction.channel.permissions_for(interaction.guild.me).send_messages}
Embed Links: {interaction.channel.permissions_for(interaction.guild.me).embed_links}
        """
        
        print(f"[DEBUG] Debug info: {debug_text}")
        logger.info(f"Debug info: {debug_text}")
        
        await interaction.response.send_message(debug_text, ephemeral=True)

    @app_commands.command(
        name="test-recommend",
        description="Test the recommend command functionality"
    )
    async def test_recommend(self, interaction: discord.Interaction):
        """Test command to verify recommend functionality"""
        print(f"[DEBUG] Test-recommend called by {interaction.user}")
        logger.info(f"Test-recommend called by {interaction.user}")
        
        # Test basic functionality
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        test_channel = interaction.channel
        
        print(f"[DEBUG] Testing with URL: {test_url}")
        print(f"[DEBUG] Testing with channel: {test_channel}")
        
        # Simulate the recommend logic
        me = interaction.guild.me if interaction.guild else None
        if not me:
            await interaction.response.send_message("❌ No guild found", ephemeral=True)
            return
            
        perms = test_channel.permissions_for(me)
        print(f"[DEBUG] Test permissions: view={perms.view_channel}, send={perms.send_messages}")
        
        if not perms.view_channel or not perms.send_messages:
            await interaction.response.send_message(
                f"❌ Missing permissions: view={perms.view_channel}, send={perms.send_messages}", 
                ephemeral=True
            )
            return
            
        # Test sending the message
        message_content = f"🎵 Test recommendation by {interaction.user.mention}\n{test_url}"
        
        try:
            await test_channel.send(
                message_content,
                allowed_mentions=discord.AllowedMentions.none()
            )
            await interaction.response.send_message(
                "✅ Test recommendation sent successfully!", ephemeral=True
            )
        except Exception as e:
            print(f"[DEBUG] Test failed: {e}")
            await interaction.response.send_message(
                f"❌ Test failed: {e}", ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Recommendation(bot))