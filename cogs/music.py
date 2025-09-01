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
        # Multiple yt-dlp configurations to try
        configs = [
            # Config 1: Standard with user agent
            {
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
                "http_headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
            },
            # Config 2: More aggressive settings
            {
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
                "http_headers": {
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-us,en;q=0.5",
                    "Accept-Encoding": "gzip,deflate",
                    "Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.7",
                    "Connection": "keep-alive",
                }
            },
            # Config 3: Minimal settings
            {
                "format": "worstaudio/worst",
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
                "http_headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            }
        ]
        
        ffmpeg_opts = {
            "options": "-vn -b:a 192k -bufsize 3072k"
        }
        
        # Try each configuration
        for i, ydl_opts in enumerate(configs):
            try:
                print(f"[DEBUG] Trying config {i+1} for URL: {url}")
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if info and info.get("url"):
                        print(f"[DEBUG] Success with config {i+1}")
                        return discord.FFmpegPCMAudio(info["url"], **ffmpeg_opts), info
                    else:
                        print(f"[DEBUG] Config {i+1} failed - no valid info")
            except Exception as e:
                print(f"[DEBUG] Config {i+1} failed: {e}")
                continue
        
        # If all configs fail, try with a different approach
        try:
            print("[DEBUG] Trying alternative approach with direct format selection")
            ydl_opts = {
                "format": "251/250/249",  # Opus formats
                "noplaylist": True,
                "nocheckcertificate": True,
                "ignoreerrors": False,
                "logtostderr": False,
                "quiet": True,
                "no_warnings": True,
                "http_headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info and info.get("url"):
                    return discord.FFmpegPCMAudio(info["url"], **ffmpeg_opts), info
        except Exception as e:
            print(f"[DEBUG] Alternative approach failed: {e}")
        
        raise Exception("All streaming methods failed. YouTube may be blocking this video.")

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
                await channel.send(f"❌ Error playing song: {title}")
                # Try to play next song
                await self.play_next(guild_id, channel)
        else:
            embed = discord.Embed(title="Queue Finished", description="No more songs in the queue! Leaving voice channel.", color=discord.Color.red())
            await channel.send(embed=embed)
            await vc.disconnect()

    async def check_empty_voice_channel(self, guild):
        """Check if voice channel is empty and leave if so"""
        vc = guild.voice_client
        if vc and vc.channel:
            # Count non-bot users in the voice channel
            members = [m for m in vc.channel.members if not m.bot]
            if len(members) == 0:
                embed = discord.Embed(title="👋 Auto-Disconnect", description="No users in voice channel. Leaving automatically.", color=discord.Color.orange())
                try:
                    await vc.channel.send(embed=embed)
                except:
                    pass
                await vc.disconnect()
                # Clear the queue
                if guild.id in self.music_queues:
                    self.music_queues[guild.id] = []

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Auto-leave when no users are in voice channel"""
        if member.bot:
            return
            
        # Check if someone left a voice channel
        if before.channel and not after.channel:
            # Someone left a voice channel, check if it's empty now
            await self.check_empty_voice_channel(member.guild)
        
        # Check if someone joined a voice channel (in case bot was alone)
        elif not before.channel and after.channel:
            # Someone joined, but we still need to check if bot should leave
            await self.check_empty_voice_channel(member.guild)

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
                        "This video is blocked by YouTube's bot detection.\n\n"
                        "**Try these solutions:**\n"
                        "• Use a different YouTube video\n"
                        "• Try popular/trending videos\n"
                        "• Avoid age-restricted content\n"
                        "• Use shorter videos\n\n"
                        "**Note:** This is a YouTube limitation, not a bot issue.",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        f"❌ **Streaming Error**\n"
                        f"Could not stream the video.\n\n"
                        f"**Error:** {error_msg}\n\n"
                        f"**Try:**\n"
                        "• Different video URL\n"
                        "• Popular videos\n"
                        "• Check if URL is valid",
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
