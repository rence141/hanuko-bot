from discord.ext import commands, tasks
import discord
from discord import app_commands

# Try to import config, fall back to config_fallback if not available
try:
    import config
except ImportError:
    import config_fallback as config

import json
import os
import time
from datetime import datetime, timedelta
from collections import defaultdict, deque
import re

WARNINGS_FILE = "warnings.json"
AUTODETECT_FILE = "autodetect.json"
MUTED_FILE = "muted.json"
AUTOMOD_CONFIG_FILE = "automod_config.json"
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

def load_automod_config():
    if not os.path.exists(AUTOMOD_CONFIG_FILE):
        return {}
    with open(AUTOMOD_CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_automod_config(config_data):
    with open(AUTOMOD_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=4)

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.autodetect = load_autodetect()
        self.automod_config = load_automod_config()
        # Spam tracking: {guild_id: {user_id: deque of timestamps}}
        self.spam_tracker = defaultdict(lambda: defaultdict(lambda: deque(maxlen=10)))
        # Message tracking for caps and emoji spam
        self.message_tracker = defaultdict(lambda: defaultdict(lambda: deque(maxlen=5)))

    async def cog_unload(self):
        save_autodetect(self.autodetect)
        save_automod_config(self.automod_config)

    def get_guild_config(self, guild_id):
        """Get automod config for a guild, with defaults"""
        guild_config = self.automod_config.get(str(guild_id), {})
        return {
            "spam_detection": guild_config.get("spam_detection", False),
            "caps_detection": guild_config.get("caps_detection", False),
            "emoji_spam_detection": guild_config.get("emoji_spam_detection", False),
            "link_filtering": guild_config.get("link_filtering", False),
            "allowed_domains": guild_config.get("allowed_domains", []),
            "spam_threshold": guild_config.get("spam_threshold", 5),  # messages in 10 seconds
            "caps_threshold": guild_config.get("caps_threshold", 0.7),  # 70% caps
            "emoji_threshold": guild_config.get("emoji_threshold", 0.5),  # 50% emojis
        }

    def is_spam(self, guild_id, user_id):
        """Check if user is spamming"""
        timestamps = self.spam_tracker[guild_id][user_id]
        if len(timestamps) < 3:
            return False
        
        # Check if 3+ messages in last 10 seconds
        now = datetime.utcnow()
        recent_messages = [ts for ts in timestamps if (now - ts).total_seconds() <= 10]
        return len(recent_messages) >= 3

    def is_caps_spam(self, content):
        """Check if message is mostly caps"""
        if len(content) < 10:
            return False
        
        letters = [c for c in content if c.isalpha()]
        if not letters:
            return False
        
        caps_count = sum(1 for c in letters if c.isupper())
        return caps_count / len(letters) > 0.7

    def is_emoji_spam(self, content):
        """Check if message is mostly emojis"""
        if len(content) < 5:
            return False
        
        # Count emojis (both unicode and custom)
        emoji_pattern = re.compile(r'<a?:.+?:\d+>|[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002600-\U000027BF\U0001F900-\U0001F9FF]')
        emojis = emoji_pattern.findall(content)
        
        # Remove emojis to get text length
        text_content = emoji_pattern.sub('', content).strip()
        
        if not text_content and len(emojis) > 0:
            return True
        
        if len(text_content) > 0:
            return len(emojis) / (len(emojis) + len(text_content)) > 0.5
        
        return False

    def contains_links(self, content):
        """Check if message contains links"""
        url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        return bool(url_pattern.search(content))

    def is_allowed_link(self, content, allowed_domains):
        """Check if link is in allowed domains"""
        if not allowed_domains:
            return False
        
        url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        urls = url_pattern.findall(content)
        
        for url in urls:
            domain = url.split('/')[2].lower()
            if not any(allowed_domain.lower() in domain for allowed_domain in allowed_domains):
                return False
        return True

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        
        guild_id = str(message.guild.id)
        user_id = str(message.author.id)
        content = message.content
        
        # Get guild automod config
        config = self.get_guild_config(guild_id)
        
        # Track message for spam detection
        self.spam_tracker[guild_id][user_id].append(datetime.utcnow())
        
        # Spam detection
        if config["spam_detection"] and self.is_spam(guild_id, user_id):
            try:
                await message.delete()
                await message.channel.send(f"{message.author.mention}, please slow down your messages.", delete_after=5)
                return
            except Exception:
                pass
        
        # Caps lock detection
        if config["caps_detection"] and self.is_caps_spam(content):
            try:
                await message.delete()
                await message.channel.send(f"{message.author.mention}, please avoid excessive caps lock.", delete_after=5)
                return
            except Exception:
                pass
        
        # Emoji spam detection
        if config["emoji_spam_detection"] and self.is_emoji_spam(content):
            try:
                await message.delete()
                await message.channel.send(f"{message.author.mention}, please avoid excessive emoji usage.", delete_after=5)
                return
            except Exception:
                pass
        
        # Link filtering
        if config["link_filtering"] and self.contains_links(content):
            if not self.is_allowed_link(content, config["allowed_domains"]):
                try:
                    await message.delete()
                    await message.channel.send(f"{message.author.mention}, links are not allowed in this channel.", delete_after=5)
                    return
                except Exception:
                    pass
        
        # Original word filter
        enabled = self.autodetect.get(guild_id, False)
        if enabled:
            lowered = content.lower()
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
                warnings.setdefault(user_id, []).append(entry)
                save_warnings(warnings)
                try:
                    await message.author.send(f"Your message in {message.guild.name} was deleted for using forbidden words: {', '.join(found)}.")
                except Exception:
                    pass
                await message.channel.send(f"{message.author.mention}, your message was removed for inappropriate language.", delete_after=5)

    @app_commands.command(name="announcement", description="Send a server announcement (mod only)")
    @app_commands.describe(announcement_text="The announcement message to send (supports multiple lines)")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def announcement(self, interaction: discord.Interaction, announcement_text: str):
        print(f"[DEBUG] /announcement called by {interaction.user} with message: {announcement_text}")
        
        # Handle multi-line text properly
        formatted_text = announcement_text.replace('\n', '\n')  # Preserve line breaks
        
        embed = discord.Embed(
            title="📢 Announcement",
            description=formatted_text,
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

    @app_commands.command(name="automod", description="Configure auto-moderation features")
    @app_commands.describe(
        feature="The feature to configure (spam/caps/emoji/links)",
        state="Enable or disable the feature (on/off)"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def automod(self, interaction: discord.Interaction, feature: str, state: str):
        print(f"[DEBUG] /automod called by {interaction.user}")
        
        feature = feature.lower()
        state = state.lower()
        
        if state not in ("on", "off"):
            await interaction.response.send_message("State must be 'on' or 'off'.", ephemeral=True)
            return
        
        if feature not in ["spam", "caps", "emoji", "links"]:
            await interaction.response.send_message("Feature must be: spam, caps, emoji, or links.", ephemeral=True)
            return
        
        guild_id = str(interaction.guild.id)
        if guild_id not in self.automod_config:
            self.automod_config[guild_id] = {}
        
        feature_map = {
            "spam": "spam_detection",
            "caps": "caps_detection", 
            "emoji": "emoji_spam_detection",
            "links": "link_filtering"
        }
        
        self.automod_config[guild_id][feature_map[feature]] = (state == "on")
        save_automod_config(self.automod_config)
        
        await interaction.response.send_message(f"Auto-moderation {feature} detection is now {'enabled' if state == 'on' else 'disabled'} for this server.")

    @app_commands.command(name="alloweddomains", description="Set allowed domains for link filtering")
    @app_commands.describe(domains="Comma-separated list of allowed domains (e.g., discord.com,youtube.com)")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def alloweddomains(self, interaction: discord.Interaction, domains: str):
        print(f"[DEBUG] /alloweddomains called by {interaction.user}")
        
        domain_list = [domain.strip() for domain in domains.split(",") if domain.strip()]
        
        guild_id = str(interaction.guild.id)
        if guild_id not in self.automod_config:
            self.automod_config[guild_id] = {}
        
        self.automod_config[guild_id]["allowed_domains"] = domain_list
        save_automod_config(self.automod_config)
        
        embed = discord.Embed(
            title="✅ Allowed Domains Updated",
            description=f"Set {len(domain_list)} allowed domain(s) for link filtering.",
            color=discord.Color.green()
        )
        embed.add_field(name="Domains", value=", ".join(domain_list) if domain_list else "None", inline=False)
        embed.add_field(name="Note", value="Link filtering must be enabled with `/automod links on`", inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="automodstatus", description="Show current auto-moderation settings")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def automodstatus(self, interaction: discord.Interaction):
        print(f"[DEBUG] /automodstatus called by {interaction.user}")
        
        guild_id = str(interaction.guild.id)
        config = self.get_guild_config(guild_id)
        
        embed = discord.Embed(
            title="🛡️ Auto-Moderation Status",
            description=f"Current settings for {interaction.guild.name}",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Word Filter", 
            value="🟢 Enabled" if self.autodetect.get(guild_id, False) else "🔴 Disabled", 
            inline=True
        )
        embed.add_field(
            name="Spam Detection", 
            value="🟢 Enabled" if config["spam_detection"] else "🔴 Disabled", 
            inline=True
        )
        embed.add_field(
            name="Caps Detection", 
            value="🟢 Enabled" if config["caps_detection"] else "🔴 Disabled", 
            inline=True
        )
        embed.add_field(
            name="Emoji Spam", 
            value="🟢 Enabled" if config["emoji_spam_detection"] else "🔴 Disabled", 
            inline=True
        )
        embed.add_field(
            name="Link Filtering", 
            value="🟢 Enabled" if config["link_filtering"] else "🔴 Disabled", 
            inline=True
        )
        
        if config["allowed_domains"]:
            embed.add_field(
                name="Allowed Domains", 
                value=", ".join(config["allowed_domains"]), 
                inline=False
            )
        
        embed.add_field(
            name="Commands", 
            value="Use `/automod <feature> <on/off>` to configure\nUse `/alloweddomains <domains>` to set allowed domains", 
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

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