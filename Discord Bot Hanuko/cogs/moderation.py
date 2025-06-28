from discord.ext import commands
import discord
from discord import app_commands
import config
import json
from datetime import datetime, timedelta
import os
import re

WARNINGS_FILE = "warnings.json"
AUTODETECT_FILE = "autodetect.json"
MUTED_FILE = "muted.json"
FORBIDDEN_WORDS = [
    # Common English profanities and slurs (no religious words)
    "fuck", "shit", "bitch", "nigger", "fag", "faggot", "asshole", "dick", "cunt", "bastard", "slut", "whore", "piss", "cock", "retard", "moron", "douche", "jackass", "twat", "crap", "prick", "wanker", "arse", "dipshit", "dumbass", "jackoff", "jerkoff", "motherfucker", "bullshit", "dildo", "pussy", "tit", "tits", "cum", "suck", "screwed", "screwing", "bimbo", "skank", "tramp", "hoe", "spaz", "spastic"
]

def load_warnings():
    if not os.path.exists(WARNINGS_FILE):
        return {}
    with open(WARNINGS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_warnings(warnings):
    with open(WARNINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(warnings, f, indent=4)

def load_autodetect():
    if not os.path.exists(AUTODETECT_FILE):
        return {}
    with open(AUTODETECT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_autodetect(data):
    with open(AUTODETECT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def load_muted():
    if not os.path.exists(MUTED_FILE):
        return {}
    with open(MUTED_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_muted(muted):
    with open(MUTED_FILE, "w", encoding="utf-8") as f:
        json.dump(muted, f, indent=4)

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.autodetect = load_autodetect()

    async def cog_unload(self):
        save_autodetect(self.autodetect)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        enabled = self.autodetect.get(str(message.guild.id), False)
        if not enabled:
            return
        lowered = message.content.lower()
        found = [w for w in FORBIDDEN_WORDS if w in lowered]
        if found:
            try:
                await message.delete()
            except Exception:
                pass
            warnings = load_warnings()
            entry = {
                "reason": f"Used bad words: {', '.join(found)}",
                "moderator": self.bot.user.id,
                "timestamp": datetime.utcnow().isoformat()
            }
            warnings.setdefault(str(message.author.id), []).append(entry)
            save_warnings(warnings)
            try:
                await message.author.send(f"Your message in {message.guild.name} was deleted for using forbidden words: {', '.join(found)}.")
            except Exception:
                pass
            channel = message.channel
            await channel.send(f"{message.author.mention}, your message was removed for inappropriate language.", delete_after=5)

    @app_commands.command(name="announcement", description="Send a server announcement (mod only)")
    @app_commands.describe(message="The announcement message")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def announcement(self, interaction: discord.Interaction, message: str):
        print(f"[DEBUG] /announcement called by {interaction.user} with message: {message}")
        embed = discord.Embed(
            title="📢 Announcement",
            description=message,
            color=config.EMBED_COLORS["mod"]
        )
        embed.set_footer(text=f"Announcement by {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="warn", description="Warn a user")
    @app_commands.describe(user="The user to warn", reason="Reason for the warning")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warn(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        print(f"[DEBUG] /warn called by {interaction.user} for {user.display_name} reason: {reason}")
        warnings = load_warnings()
        entry = {
            "reason": reason,
            "moderator": interaction.user.id,
            "timestamp": datetime.utcnow().isoformat()
        }
        warnings.setdefault(str(user.id), []).append(entry)
        save_warnings(warnings)
        await interaction.response.send_message(f"⚠️ {user.mention} has been warned for: {reason}")
        try:
            await user.send(f"You have been warned in {interaction.guild.name} for: {reason}")
        except Exception:
            pass

    @app_commands.command(name="warnings", description="List a user's warnings")
    @app_commands.describe(user="The user to check warnings for")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warnings_cmd(self, interaction: discord.Interaction, user: discord.Member):
        print(f"[DEBUG] /warnings called by {interaction.user} for {user.display_name}")
        warnings = load_warnings()
        user_warnings = warnings.get(str(user.id), [])
        if not user_warnings:
            await interaction.response.send_message(f"{user.mention} has no warnings.")
            return
        embed = discord.Embed(
            title=f"Warnings for {user.display_name}",
            color=discord.Color.orange()
        )
        for i, w in enumerate(user_warnings, 1):
            if isinstance(w, dict):
                mod = self.bot.get_user(w.get("moderator"))
                mod_name = mod.display_name if mod else w.get("moderator")
                embed.add_field(
                    name=f"#{i} - {w.get('timestamp', 'N/A')}",
                    value=f"Reason: {w.get('reason', 'N/A')}\nModerator: {mod_name}",
                    inline=False
                )
            else:
                embed.add_field(name=f"#{i}", value=str(w), inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="clearwarnings", description="Clear all warnings for a user")
    @app_commands.describe(user="The user to clear warnings for")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def clearwarnings(self, interaction: discord.Interaction, user: discord.Member):
        print(f"[DEBUG] /clearwarnings called by {interaction.user} for {user.display_name}")
        warnings = load_warnings()
        if str(user.id) in warnings:
            del warnings[str(user.id)]
            save_warnings(warnings)
            await interaction.response.send_message(f"✅ Cleared all warnings for {user.mention}.")
        else:
            await interaction.response.send_message(f"{user.mention} has no warnings.")

    @app_commands.command(name="kick", description="Kick a user from the server")
    @app_commands.describe(user="The user to kick", reason="Reason for the kick")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        print(f"[DEBUG] /kick called by {interaction.user} for {user.display_name} reason: {reason}")
        try:
            await user.kick(reason=reason)
            await interaction.response.send_message(f"👢 {user.mention} has been kicked. Reason: {reason}")
        except Exception as e:
            await interaction.response.send_message(f"Failed to kick {user.mention}: {e}", ephemeral=True)

    @app_commands.command(name="ban", description="Ban a user from the server")
    @app_commands.describe(user="The user to ban", reason="Reason for the ban")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        print(f"[DEBUG] /ban called by {interaction.user} for {user.display_name} reason: {reason}")
        try:
            await user.ban(reason=reason)
            await interaction.response.send_message(f"🔨 {user.mention} has been banned. Reason: {reason}")
        except Exception as e:
            await interaction.response.send_message(f"Failed to ban {user.mention}: {e}", ephemeral=True)

    @app_commands.command(name="unban", description="Unban a user by ID")
    @app_commands.describe(user_id="The ID of the user to unban")
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction, user_id: str):
        print(f"[DEBUG] /unban called by {interaction.user} for user_id: {user_id}")
        try:
            user = await self.bot.fetch_user(int(user_id))
            await interaction.guild.unban(user)
            await interaction.response.send_message(f"✅ Unbanned {user.mention}.")
        except Exception as e:
            await interaction.response.send_message(f"Failed to unban user {user_id}: {e}", ephemeral=True)

    @app_commands.command(name="autodetect", description="Enable or disable auto-detect word filter for this server.")
    @app_commands.describe(state="Enable or disable the filter (on/off)")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def autodetect(self, interaction: discord.Interaction, state: str):
        state = state.lower()
        if state not in ("on", "off"):
            await interaction.response.send_message("State must be 'on' or 'off'.", ephemeral=True)
            return
        self.autodetect[str(interaction.guild.id)] = (state == "on")
        save_autodetect(self.autodetect)
        await interaction.response.send_message(f"Auto-detect word filter is now {'enabled' if state == 'on' else 'disabled'} for this server.")

    @app_commands.command(name="mute", description="Mute a user (mod only)")
    @app_commands.describe(user="The user to mute", duration="Duration of the mute (e.g., 10m, 2h, 1d, 1y, 30s)", reason="Reason for the mute")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def mute(self, interaction: discord.Interaction, user: discord.Member, duration: str, reason: str):
        print(f"[DEBUG] /mute called by {interaction.user} for {user.display_name} duration: {duration} reason: {reason}")
        muted = load_muted()
        # Parse duration
        match = re.match(r"^(\\d+)([smhdy])$", duration.strip().lower())
        if not match:
            await interaction.response.send_message(
                "Invalid duration format. Use number followed by s/m/h/d/y (e.g., 10m, 2h, 1d, 1y, 30s)", ephemeral=True)
            return
        value, unit = int(match.group(1)), match.group(2)
        if unit == 's':
            delta = timedelta(seconds=value)
        elif unit == 'm':
            delta = timedelta(minutes=value)
        elif unit == 'h':
            delta = timedelta(hours=value)
        elif unit == 'd':
            delta = timedelta(days=value)
        elif unit == 'y':
            delta = timedelta(days=365 * value)
        else:
            await interaction.response.send_message(
                "Invalid duration unit. Use s (seconds), m (minutes), h (hours), d (days), or y (years).", ephemeral=True)
            return
        end_time = (datetime.utcnow() + delta).isoformat()
        muted[str(user.id)] = {
            "reason": reason,
            "moderator": interaction.user.id,
            "timestamp": datetime.utcnow().isoformat(),
            "end_time": end_time
        }
        save_muted(muted)
        await interaction.response.send_message(
            f"🔇 {user.mention} has been muted for {duration}. Reason: {reason}")
        try:
            await user.send(f"You have been muted in {interaction.guild.name} for {duration}. Reason: {reason}")
        except Exception:
            pass

    @app_commands.command(name="unmute", description="Unmute a user (mod only)")
    @app_commands.describe(user="The user to unmute")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def unmute(self, interaction: discord.Interaction, user: discord.Member):
        print(f"[DEBUG] /unmute called by {interaction.user} for {user.display_name}")
        muted = load_muted()
        if str(user.id) in muted:
            del muted[str(user.id)]
            save_muted(muted)
            await interaction.response.send_message(f"✅ {user.mention} has been unmuted.")
            try:
                await user.send(f"You have been unmuted in {interaction.guild.name}.")
            except Exception:
                pass
        else:
            await interaction.response.send_message(f"{user.mention} is not muted.")

async def setup(bot):
    await bot.add_cog(Moderation(bot)) 