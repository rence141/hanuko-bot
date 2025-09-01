import discord
from discord.ext import commands
import json
import os

CONFIG_FILE = "welcome_config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = load_config()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_id = str(member.guild.id)
        conf = self.config.get(guild_id, {})
        channel_id = conf.get("channel_id")
        message = conf.get("message", "Welcome to the server, {member}!")
        emoji = conf.get("emoji", "🎉")
        gif_url = conf.get("gif_url", None)

        channel = member.guild.get_channel(channel_id) if channel_id else discord.utils.get(member.guild.text_channels, name='general')
        if channel:
            embed = discord.Embed(description=f"{emoji} {message.format(member=member.mention)}")
            if gif_url:
                embed.set_image(url=gif_url)
            await channel.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setwelcome(self, ctx, *, message):
        """Set the welcome message. Use {member} for the new member mention."""
        guild_id = str(ctx.guild.id)
        self.config.setdefault(guild_id, {})["message"] = message
        save_config(self.config)
        await ctx.send("Welcome message updated!")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setwelcomeemoji(self, ctx, emoji):
        """Set the emoji for the welcome message."""
        guild_id = str(ctx.guild.id)
        self.config.setdefault(guild_id, {})["emoji"] = emoji
        save_config(self.config)
        await ctx.send("Welcome emoji updated!")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setwelcomegif(self, ctx, gif_url):
        """Set the GIF URL for the welcome embed."""
        guild_id = str(ctx.guild.id)
        self.config.setdefault(guild_id, {})["gif_url"] = gif_url
        save_config(self.config)
        await ctx.send("Welcome GIF updated!")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setwelcomechannel(self, ctx, channel: discord.TextChannel):
        """Set the channel for welcome messages."""
        guild_id = str(ctx.guild.id)
        self.config.setdefault(guild_id, {})["channel_id"] = channel.id
        save_config(self.config)
        await ctx.send(f"Welcome channel set to {channel.mention}")

def setup(bot):
    bot.add_cog(Welcome(bot))