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

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.music_queues = {}  # {guild_id: [(url, title, source)]}
        print("[DEBUG] Music cog initialized")

    def get_queue(self, guild_id):
        return self.music_queues.setdefault(guild_id, [])

    def get_audio_source(self, url: str):
        # Updated yt-dlp options to handle bot detection
        ydl_opts = {
            "format": "bestaudio/best",
            "noplaylist": True,
            "nocheckcertificate": True,
            "ignoreerrors": False,
            "logtostderr": False,
            "quiet": True,
            "no_warnings": True,
            "default_search": "auto",
            "source_address": "0.0.0.0",
            "force_ipv4": True,
            "extract_flat": False,
            # Add user agent to avoid bot detection
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        }
        
        ffmpeg_opts = {
            "options": "-vn -b:a 192k"
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info:
                    return discord.FFmpegPCMAudio(info["url"], **ffmpeg_opts), info
                else:
                    raise Exception("Could not extract video info")
        except Exception as e:
            # If the first attempt fails, try with different options
            print(f"[DEBUG] First attempt failed: {e}")
            ydl_opts["format"] = "worstaudio/worst"
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if info:
                        return discord.FFmpegPCMAudio(info["url"], **ffmpeg_opts), info
            except Exception as e2:
                print(f"[DEBUG] Second attempt failed: {e2}")
                raise Exception(f"Failed to download video: {str(e2)}")

    async def play_next(self, guild_id, channel):
        queue = self.get_queue(guild_id)
        vc = channel.guild.voice_client
        if queue:
            url, title, source = queue.pop(0)
            try:
                vc.play(
                    source,
                    after=lambda e: asyncio.run_coroutine_threadsafe(
                        self.play_next(guild_id, channel), self.bot.loop
                    )
                )
                embed = discord.Embed(title="🎶 Now Playing", description=f"**{title}**", color=discord.Color.green())
                await channel.send(embed=embed)
            except Exception as e:
                print(f"[ERROR] Error playing next song: {e}")
                await channel.send(f" Error playing song >:V {title}")
                # Try to play next song
                await self.play_next(guild_id, channel)
        else:
            embed = discord.Embed(title="Queue Finished", description="No more songs in the queue! Leaving voice channel.", color=discord.Color.red())
            await channel.send(embed=embed)
            await vc.disconnect()

    # --- Slash Commands ---
    @app_commands.command(name="play", description="Play a YouTube song (adds to queue)")
    async def play(self, interaction: discord.Interaction, url: str):
        await interaction.response.defer()
        
        if not interaction.user.voice:
            await interaction.followup.send("❌ You must be in a voice channel!", ephemeral=True)
            return
            
        try:
            channel = interaction.user.voice.channel
            if interaction.guild.voice_client is None:
                await channel.connect()

            # Try to get audio source
            try:
                source, info = self.get_audio_source(url)
            except Exception as e:
                error_msg = str(e)
                if "Sign in to confirm you're not a bot" in error_msg:
                    await interaction.followup.send(
                        "❌ **YouTube Bot Detection Error**\n"
                        "YouTube is blocking this video due to bot detection. "
                        "Try a different video or check if the URL is valid.\n\n"
                        "**Alternative:** Try using a different YouTube video URL.",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        f"❌ **Download Error**\n"
                        f"Could not download the video: {error_msg}\n\n"
                        f"**Possible solutions:**\n"
                        f"• Check if the URL is valid\n"
                        f"• Try a different video\n"
                        f"• Make sure the video is not age-restricted",
                        ephemeral=True
                    )
                return

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
                await interaction.followup.send(embed=embed)
            else:
                queue.append((url, info["title"], source))
                embed = discord.Embed(title="➕ Added to Queue", description=f"**{info['title']}**", color=discord.Color.blue())
                await interaction.followup.send(embed=embed)
                
        except Exception as e:
            print(f"[ERROR] Play command error: {e}")
            await interaction.followup.send(f"❌ An error occurred: {str(e)}", ephemeral=True)

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
            await interaction.response.send_message("❌ Nothing is playing right now.", ephemeral=True)

    @app_commands.command(name="stop", description="Stop music and clear queue")
    async def stop(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc:
            vc.stop()
            self.music_queues[interaction.guild.id] = []
            await interaction.response.send_message("⏹️ Stopped music and cleared queue.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ I'm not in a voice channel.", ephemeral=True)

    @app_commands.command(name="leave", description="Disconnect from voice channel")
    async def leave(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc:
            await vc.disconnect()
            self.music_queues[interaction.guild.id] = []
            await interaction.response.send_message("👋 Disconnected and cleared queue.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ I'm not in a voice channel.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Music(bot))
