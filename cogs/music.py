# music.py
from discord.ext import commands
import discord
from discord import app_commands
import yt_dlp
import asyncio

# Try to import config, fallback if not available
try:
    import config
except ImportError:
    import config_fallback as config

# Replace with your test server (guild) ID
TEST_GUILD_ID = 123456789012345678  # <- Replace with your actual Discord server ID

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.music_queues = {}  # {guild_id: [(url, title, source)]}
        print("[DEBUG] Music cog initialized")

    def get_queue(self, guild_id):
        return self.music_queues.setdefault(guild_id, [])

    def get_audio_source(self, url: str):
        ydl_opts = {"format": "bestaudio"}
        ffmpeg_opts = {"options": "-vn"}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return discord.FFmpegPCMAudio(info["url"], **ffmpeg_opts), info

    async def play_next(self, guild_id, channel):
        queue = self.get_queue(guild_id)
        vc = channel.guild.voice_client
        if queue:
            url, title, source = queue.pop(0)
            vc.play(
                source,
                after=lambda e: asyncio.run_coroutine_threadsafe(
                    self.play_next(guild_id, channel), self.bot.loop
                )
            )
            embed = discord.Embed(title="🎶 Now Playing", description=f"**{title}**", color=discord.Color.green())
            await channel.send(embed=embed)
        else:
            embed = discord.Embed(title="Queue Finished", description="No more songs in the queue! Leaving voice channel.", color=discord.Color.red())
            await channel.send(embed=embed)
            await vc.disconnect()

    # --- Guild-Specific Slash Commands ---
    @app_commands.command(name="play", description="Play a YouTube song (adds to queue)")
    async def play(self, interaction: discord.Interaction, url: str):
        if not interaction.user.voice:
            await interaction.response.send_message(" You must be in a voice channel!", ephemeral=True)
            return
        channel = interaction.user.voice.channel
        if interaction.guild.voice_client is None:
            await channel.connect()

        source, info = self.get_audio_source(url)
        queue = self.get_queue(interaction.guild.id)
        vc = interaction.guild.voice_client

        if not vc.is_playing():
            vc.play(
                source,
                after=lambda e: asyncio.run_coroutine_threadsafe(
                    self.play_next(interaction.guild.id, channel), self.bot.loop
                )
            )
            embed = discord.Embed(title="🎶 Now Playing", description=f"**{info['title']}**", color=discord.Color.green())
            await interaction.response.send_message(embed=embed)
        else:
            queue.append((url, info["title"], source))
            embed = discord.Embed(title="➕ Added to Queue", description=f"**{info['title']}**", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="queue", description="Show current music queue")
    async def show_queue(self, interaction: discord.Interaction):
        queue = self.get_queue(interaction.guild.id)
        if not queue:
            embed = discord.Embed(title="Queue Empty", description="📭 No songs in the queue.", color=discord.Color.red())
        else:
            msg = "\n".join([f"{i+1}. {title}" for i, (_, title, _) in enumerate(queue)])
            embed = discord.Embed(title="📜 Current Queue", description=msg, color=discord.Color.green())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="skip", description="Skip the current song")
    async def skip(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.stop()
            await interaction.response.send_message("⏭️ Skipped the current song.", ephemeral=True)
        else:
            await interaction.response.send_message("Nothing is playing right now.", ephemeral=True)

    @app_commands.command(name="stop", description="Stop music and clear queue")
    async def stop(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc:
            vc.stop()
            self.music_queues[interaction.guild.id] = []
            await interaction.response.send_message("⏹ Stopped music and cleared queue.", ephemeral=True)
        else:
            await interaction.response.send_message("I'm not in a voice channel.", ephemeral=True)

    @app_commands.command(name="leave", description="Disconnect from voice channel")
    async def leave(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc:
            await vc.disconnect()
            self.music_queues[interaction.guild.id] = []
            await interaction.response.send_message("Disconnected and cleared queue.", ephemeral=True)
        else:
            await interaction.response.send_message("I'm not in a voice channel.", ephemeral=True)

async def setup(bot):
    # Create a test guild object for guild-specific commands
    test_guild = discord.Object(id=TEST_GUILD_ID)
    
    # Add the cog with guild-specific commands
    await bot.add_cog(Music(bot), guild=test_guild)
