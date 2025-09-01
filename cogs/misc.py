from discord.ext import commands, tasks
import discord
from discord import app_commands

# Try to import config, fall back to config_fallback if not available
try:
    import config
except ImportError:
    import config_fallback as config

import os
import time
import json
from hanuko_bot import event_008_breach
import logging
from discord.ext.commands import BucketType, CommandOnCooldown
from db import get_user, update_user
from datetime import datetime, timedelta
import asyncio
import re

enabled_008_file = "008_enabled_guilds.json"
vault_event_file = "vault_event_channels.json"
afk_file = "afk_status.json"
polls_file = "polls.json"
ALLOWED_CHANNEL_ID = 123456789012345678  # Replace with your channel's ID

def load_enabled_008():
    if not os.path.exists(enabled_008_file):
        return {}
    with open(enabled_008_file, "r", encoding="utf-8") as f:
        return json.load(f)

def save_enabled_008(guild_ids):
    with open(enabled_008_file, "w", encoding="utf-8") as f:
        json.dump(guild_ids, f, indent=4)

def load_vault_event_channels():
    if not os.path.exists(vault_event_file):
        return {}
    with open(vault_event_file, "r", encoding="utf-8") as f:
        return json.load(f)

def save_vault_event_channels(guild_channels):
    with open(vault_event_file, "w", encoding="utf-8") as f:
        json.dump(guild_channels, f, indent=4)

def load_afk_status():
    if not os.path.exists(afk_file):
        return {}
    with open(afk_file, "r", encoding="utf-8") as f:
        return json.load(f)

def save_afk_status(afk_data):
    with open(afk_file, "w", encoding="utf-8") as f:
        json.dump(afk_data, f, indent=4)

def load_polls():
    if not os.path.exists(polls_file):
        return {}
    with open(polls_file, "r", encoding="utf-8") as f:
        return json.load(f)

def save_polls(polls_data):
    with open(polls_file, "w", encoding="utf-8") as f:
        json.dump(polls_data, f, indent=4)

class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_app_command_error(self, interaction, error):
        if isinstance(error, CommandOnCooldown):
            try:
                await interaction.response.send_message(
                    f"⏳ You're using this command too quickly! Please slow down. Try again in {error.retry_after:.1f} seconds.",
                    ephemeral=True
                )
            except:
                # If interaction already responded, try to follow up
                try:
                    await interaction.followup.send(
                        f"⏳ You're using this command too quickly! Please slow down. Try again in {error.retry_after:.1f} seconds.",
                        ephemeral=True
                    )
                except:
                    pass
        elif "Unknown interaction" in str(error) or "404 Not Found" in str(error):
            # Interaction expired, can't respond
            print(f"[WARNING] Interaction expired for user {interaction.user}")
            return
        else:
            try:
                await interaction.response.send_message(
                    f"❌ An error occurred: {str(error)}",
                    ephemeral=True
                )
            except:
                # If interaction already responded, try to follow up
                try:
                    await interaction.followup.send(
                        f"❌ An error occurred: {str(error)}",
                        ephemeral=True
                    )
                except:
                    pass
            raise error

    # Decorator for all commands in this cog
    @staticmethod
    def slowmode():
        return commands.cooldown(1, 5, BucketType.user)

    def parse_time(self, time_str):
        """Parse time string like '5m', '2h', '1d', etc."""
        time_str = time_str.lower().strip()
        match = re.match(r"^(\d+)([smhd])$", time_str)
        if not match:
            return None
        
        value, unit = int(match.group(1)), match.group(2)
        if unit == 's':
            return timedelta(seconds=value)
        elif unit == 'm':
            return timedelta(minutes=value)
        elif unit == 'h':
            return timedelta(hours=value)
        elif unit == 'd':
            return timedelta(days=value)
        return None

    @app_commands.command(name="afk", description="Set your AFK status with a custom message")
    @app_commands.describe(message="Your AFK message (optional)")
    @slowmode.__func__()
    async def afk(self, interaction: discord.Interaction, message: str = None):
        print(f"[DEBUG] /afk called by {interaction.user}")
        
        afk_data = load_afk_status()
        user_id = str(interaction.user.id)
        
        # Set AFK status
        afk_data[user_id] = {
            "message": message or "AFK",
            "timestamp": datetime.utcnow().isoformat(),
            "guild_id": str(interaction.guild.id),
            "channel_id": str(interaction.channel.id)
        }
        save_afk_status(afk_data)
        
        embed = discord.Embed(
            title="😴 AFK Status Set",
            description=f"You are now AFK: **{message or 'AFK'}**",
            color=discord.Color.orange()
        )
        embed.add_field(name="Set at", value=f"<t:{int(time.time())}:F>", inline=True)
        embed.set_footer(text="You'll be automatically removed from AFK when you send a message")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="return", description="Manually return from AFK status")
    @slowmode.__func__()
    async def return_from_afk(self, interaction: discord.Interaction):
        print(f"[DEBUG] /return called by {interaction.user}")
        
        afk_data = load_afk_status()
        user_id = str(interaction.user.id)
        
        if user_id not in afk_data:
            await interaction.response.send_message("You are not currently AFK.", ephemeral=True)
            return
        
        # Get AFK info before removing
        afk_info = afk_data[user_id]
        afk_message = afk_info.get("message", "AFK")
        afk_timestamp = afk_info.get("timestamp")
        
        # Calculate time spent AFK
        if afk_timestamp:
            try:
                afk_time = datetime.fromisoformat(afk_timestamp)
                time_spent = datetime.utcnow() - afk_time
                time_str = str(time_spent).split('.')[0]  # Remove microseconds
            except:
                time_str = "Unknown"
        else:
            time_str = "Unknown"
        
        # Remove AFK status
        del afk_data[user_id]
        save_afk_status(afk_data)
        
        embed = discord.Embed(
            title="👋 Welcome Back!",
            description=f"You are no longer AFK",
            color=discord.Color.green()
        )
        embed.add_field(name="AFK Message", value=afk_message, inline=True)
        embed.add_field(name="Time Spent AFK", value=time_str, inline=True)
        embed.set_footer(text="Welcome back to the Foundation!")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="afklist", description="Show all currently AFK users")
    @slowmode.__func__()
    async def afk_list(self, interaction: discord.Interaction):
        print(f"[DEBUG] /afklist called by {interaction.user}")
        
        afk_data = load_afk_status()
        
        if not afk_data:
            embed = discord.Embed(
                title="😴 AFK Status",
                description="No users are currently AFK",
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title="😴 Currently AFK Users",
            color=discord.Color.orange()
        )
        
        for user_id, afk_info in afk_data.items():
            try:
                user = await self.bot.fetch_user(int(user_id))
                message = afk_info.get("message", "AFK")
                timestamp = afk_info.get("timestamp")
                
                if timestamp:
                    try:
                        afk_time = datetime.fromisoformat(timestamp)
                        time_ago = datetime.utcnow() - afk_time
                        time_str = str(time_ago).split('.')[0]
                    except:
                        time_str = "Unknown"
                else:
                    time_str = "Unknown"
                
                embed.add_field(
                    name=f"👤 {user.display_name}",
                    value=f"**Message:** {message}\n**AFK for:** {time_str}",
                    inline=False
                )
            except:
                # User not found, skip
                continue
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        # Check if user is AFK and remove them
        afk_data = load_afk_status()
        user_id = str(message.author.id)
        
        if user_id in afk_data:
            afk_info = afk_data[user_id]
            afk_message = afk_info.get("message", "AFK")
            afk_timestamp = afk_info.get("timestamp")
            
            # Calculate time spent AFK
            if afk_timestamp:
                try:
                    afk_time = datetime.fromisoformat(afk_timestamp)
                    time_spent = datetime.utcnow() - afk_time
                    time_str = str(time_spent).split('.')[0]
                except:
                    time_str = "Unknown"
            else:
                time_str = "Unknown"
            
            # Remove AFK status
            del afk_data[user_id]
            save_afk_status(afk_data)
            
            # Send welcome back message
            embed = discord.Embed(
                title="👋 Welcome Back!",
                description=f"{message.author.mention} is no longer AFK",
                color=discord.Color.green()
            )
            embed.add_field(name="AFK Message", value=afk_message, inline=True)
            embed.add_field(name="Time Spent AFK", value=time_str, inline=True)
            embed.set_footer(text="Welcome back to the Foundation!")
            
            await message.channel.send(embed=embed, delete_after=10)
        
        # Check if message mentions an AFK user
        for mentioned_user in message.mentions:
            mentioned_user_id = str(mentioned_user.id)
            if mentioned_user_id in afk_data:
                afk_info = afk_data[mentioned_user_id]
                afk_message = afk_info.get("message", "AFK")
                afk_timestamp = afk_info.get("timestamp")
                
                # Calculate time spent AFK
                if afk_timestamp:
                    try:
                        afk_time = datetime.fromisoformat(afk_timestamp)
                        time_spent = datetime.utcnow() - afk_time
                        time_str = str(time_spent).split('.')[0]
                    except:
                        time_str = "Unknown"
                else:
                    time_str = "Unknown"
                
                # Send AFK status message
                embed = discord.Embed(
                    title="😴 AFK Status",
                    description=f"{mentioned_user.mention} is currently AFK",
                    color=discord.Color.orange()
                )
                embed.add_field(name="AFK Message", value=afk_message, inline=True)
                embed.add_field(name="AFK for", value=time_str, inline=True)
                embed.set_footer(text="They'll be back when they send a message!")
                
                await message.channel.send(embed=embed, delete_after=15)
        
        # Continue processing the message for other events
        await self.bot.process_commands(message)

    @app_commands.command(name="ping", description="Check if the bot is alive")
    @slowmode.__func__()
    async def ping(self, interaction: discord.Interaction):
        print(f"[DEBUG] /ping called by {interaction.user}")
        await interaction.response.send_message("Pong!")

    @app_commands.command(name="botdetails", description="Show information about the bot and its creator")
    @slowmode.__func__()
    async def botdetails(self, interaction: discord.Interaction):
        print(f"[DEBUG] /botdetails called by {interaction.user}")
        bot_user = interaction.client.user
        embed = discord.Embed(
            title=f"🤖 {bot_user.display_name} Bot Details",
            description="A modular SCP-themed Discord bot.",
            color=discord.Color.blurple()
        )
        embed.set_thumbnail(url=bot_user.display_avatar.url)
        embed.add_field(name="Creator", value="Rence / notreiiii", inline=True)
        embed.add_field(name="Bot ID", value=str(bot_user.id), inline=True)
        embed.add_field(name="Bot Tag", value=str(bot_user), inline=True)
        embed.set_footer(text="Thank you for using Hanuko!")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="serverinfo", description="Show detailed information about this server")
    @slowmode.__func__()
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        total_members = guild.member_count
        online_members = len([m for m in guild.members if m.status != discord.Status.offline])
        bot_count = len([m for m in guild.members if m.bot])
        human_count = total_members - bot_count
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        role_count = len(guild.roles)
        boost_level = guild.premium_tier
        boost_count = guild.premium_subscription_count
        embed = discord.Embed(
            title=f"🏠 Server Information: {guild.name}",
            color=discord.Color.blue()
        )
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
        embed.add_field(name="Created", value=f"<t:{int(guild.created_at.timestamp())}:F>", inline=True)
        embed.add_field(name="Server ID", value=str(guild.id), inline=True)
        embed.add_field(name="Total Members", value=f"{total_members:,}", inline=True)
        embed.add_field(name="Online Members", value=f"{online_members:,}", inline=True)
        embed.add_field(name="Humans", value=f"{human_count:,}", inline=True)
        embed.add_field(name="Bots", value=f"{bot_count:,}", inline=True)
        embed.add_field(name="Text Channels", value=text_channels, inline=True)
        embed.add_field(name="Voice Channels", value=voice_channels, inline=True)
        embed.add_field(name="Categories", value=categories, inline=True)
        embed.add_field(name="Roles", value=role_count, inline=True)
        embed.add_field(name="Boost Level", value=f"Level {boost_level}", inline=True)
        embed.add_field(name="Boosts", value=boost_count, inline=True)
        verification_levels = {
            discord.VerificationLevel.none: "None",
            discord.VerificationLevel.low: "Low",
            discord.VerificationLevel.medium: "Medium", 
            discord.VerificationLevel.high: "High",
            discord.VerificationLevel.highest: "Highest"
        }
        embed.add_field(name="Verification Level", value=verification_levels.get(guild.verification_level, "Unknown"), inline=True)
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="commands", description="List all available commands with short descriptions")
    @slowmode.__func__()
    async def commands(self, interaction: discord.Interaction):
        commands_list = [
            # Game & Profile
            ("/profile", "Show your profile."),
            ("/mission", "Complete a mission for XP."),
            ("/daily", "Claim your daily reward."),
            ("/weekly", "Claim your weekly reward."),
            ("/leaderboard", "Show the top 10 users by level."),
            ("/gleaderboard", "Show global top 10 users across all servers."),
            ("/quest", "View and claim your daily, weekly, and monthly quest rewards."),
            
            # Economy & Shop
            ("/shop", "View the SCP shop."),
            ("/buy", "Buy an item from the shop."),
            ("/inventory", "View your inventory."),
            ("/checkcredits", "Check your or another user's credits."),
            ("/equipgun", "Equip a gun from your inventory."),
            ("/equipgear", "Equip a gear item from your inventory."),
            ("/upgrade", "Upgrade an item in your inventory."),
            ("/removeitem", "Remove an item from your inventory."),
            ("/gunsmith", "Repair a damaged weapon for 10% of its shop price."),
            ("/checkgun", "Check the condition of a gun you own."),
            ("/inventoryvalue", "Check the total value of your inventory."),
            
            # Marketplace & Trading
            ("/marketplace_list", "List an item for sale on the marketplace."),
            ("/marketplace_browse", "Browse all items for sale on the marketplace."),
            ("/marketplace_buy", "Buy an item from the marketplace."),
            ("/marketplace_retrieve", "Retrieve your item from the marketplace."),
            ("/trade", "Propose a trade to another user."),
            ("/confirmtrade", "Confirm and execute a pending trade."),
            ("/canceltrade", "Cancel a pending trade you initiated."),
            
            # Pets
            ("/adoptpet", "Adopt a random pet (gacha)."),
            ("/adoptpet10x", "Adopt 10 random pets at once (5% discount)."),
            ("/premiumpets", "Adopt a premium pet (gacha)."),
            ("/premiumpets10x", "Adopt 10 premium pets at once (5% discount)."),
            ("/pets", "View your adopted pets."),
            ("/equippet", "Equip up to 2 pets to show on your profile."),
            ("/unequippet", "Unequip a pet from your equipped slots."),
            ("/equippedpets", "View and manage your equipped pets (up to 2 slots)."),
            ("/petbattle", "Battle your pet against another user's equipped pet."),
            ("/petbattleteam", "Set up your pet battle team (up to 3 pets)."),
            ("/trainpet", "Train one of your pets (1h cooldown)."),
            ("/releasepet", "Release a pet you own."),
            ("/comparepet", "Compare the stats of two pets by name."),
            
            # Teams
            ("/createteam", "Create a new team."),
            ("/inviteteam", "Invite a user to your team."),
            ("/jointeam", "Join an existing team by name (if invited)."),
            ("/team", "View your current team info."),
            ("/promote", "Promote a team member to Officer or Deputy."),
            ("/demote", "Demote a team member to Member."),
            
            # Roles
            ("/setrole", "Assign yourself a custom role from the allowed list."),
            ("/listcustomroles", "List all assignable custom roles for this server."),
            
            # Gambling & Fun
            ("/scp914", "Gamble your credits in SCP-914! Choose a setting for different odds."),
            ("/scp294", "Order a mystery drink from SCP-294 for a random outcome!"),
            ("/scp963", "Flip Dr. Bright's Coin of Fate!"),
            ("/scp999", "Hug SCP-999 for a chance at a lucky reward!"),
            ("/recontainscp", "Battle an SCP in a containment event!"),
            ("/easyrecontain", "Complete 5 easy SCP containment tasks (no weapon required)."),
            
            # Events
            ("/containmentsuit", "Respond to an active SCP-008 breach event."),
            ("/claimvault", "Claim the currently airdropped vault if you have the right keycard!"),
            
            # AFK System
            ("/afk", "Set your AFK status with a custom message."),
            ("/return", "Manually return from AFK status."),
            ("/afklist", "Show all currently AFK users."),
            
            
            # Polls
            ("/poll", "Create a poll with multiple options."),
            ("/vote", "Vote on a poll."),
            ("/pollresults", "View poll results."),
            ("/endpoll", "End a poll early (creator only)."),
            ("/listpolls", "List active polls in this server."),
            
            # Utility
            ("/ping", "Check if the bot is alive."),
            ("/botdetails", "Show information about the bot and its creator."),
            ("/serverinfo", "Show detailed information about this server."),
            ("/textme", "Send a custom message as an embed."),
            ("/recommend", "Recommend a song in a text channel."),
        ]
        embed = discord.Embed(title="📖 All Commands", color=discord.Color.blurple())
        for name, desc in commands_list:
            embed.add_field(name=name, value=desc, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def help_command_autocomplete(self, interaction: discord.Interaction, current: str):
        # List of all available commands for autocomplete
        command_names = [
            "profile", "mission", "daily", "weekly", "leaderboard", "gleaderboard", "quest",
            "shop", "buy", "inventory", "checkcredits", "equipgun", "equipgear", "upgrade", "removeitem", "gunsmith", "checkgun", "inventoryvalue",
            "marketplace_list", "marketplace_browse", "marketplace_buy", "marketplace_retrieve", "trade", "confirmtrade", "canceltrade",
            "adoptpet", "adoptpet10x", "premiumpets", "premiumpets10x", "pets", "equippet", "unequippet", "equippedpets", "petbattle", "petbattleteam", "trainpet", "releasepet", "comparepet",
            "createteam", "inviteteam", "jointeam", "team", "promote", "demote",
            "setrole", "listcustomroles",
            "scp914", "scp294", "scp963", "scp999", "recontainscp", "easyrecontain",
            "containmentsuit", "claimvault",
            "afk", "return", "afklist",
            "play", "queue", "skip", "stop", "leave",
            "poll", "vote", "pollresults", "endpoll", "listpolls",
            "ping", "botdetails", "serverinfo", "textme", "recommend"
        ]
        return [
            app_commands.Choice(name=cmd, value=cmd)
            for cmd in command_names if current.lower() in cmd.lower()
        ][:25]

    @app_commands.command(name="help", description="Show help for all player commands or a specific command")
    @app_commands.describe(command="(Optional) The command to get detailed help for")
    @app_commands.autocomplete(command=help_command_autocomplete)
    @slowmode.__func__()
    async def help(self, interaction: discord.Interaction, command: str = None):
        if not command:
            embed = discord.Embed(
                title="📝 Hanuko Help",
                description="Here are the main commands you can use, organized by category:",
                color=discord.Color.blurple()
            )
            # Game & Profile
            embed.add_field(name="__Game & Profile__", value="/profile\n/mission\n/daily, /weekly\n/leaderboard, /gleaderboard\n/quest", inline=False)
            # Economy & Shop
            embed.add_field(name="__Economy & Shop__", value="/shop, /buy\n/inventory\n/checkcredits\n/equipgun, /equipgear\n/upgrade, /removeitem\n/gunsmith, /checkgun\n/inventoryvalue", inline=False)
            # Marketplace & Trading
            embed.add_field(name="__Marketplace & Trading__", value="/marketplace_list, /marketplace_browse\n/marketplace_buy, /marketplace_retrieve\n/trade, /confirmtrade, /canceltrade", inline=False)
            # Pets
            embed.add_field(name="__Pets__", value="/adoptpet, /adoptpet10x\n/premiumpets, /premiumpets10x\n/pets, /equippet, /unequippet, /equippedpets\n/petbattle, /petbattleteam\n/trainpet, /releasepet, /comparepet", inline=False)
            # Teams
            embed.add_field(name="__Teams__", value="/createteam, /inviteteam, /jointeam\n/team, /promote, /demote", inline=False)
            # Roles
            embed.add_field(name="__Roles__", value="/setrole, /listcustomroles", inline=False)
            # Gambling & Fun
            embed.add_field(name="__Gambling & Fun__", value="/scp914, /scp294, /scp963, /scp999\n/recontainscp, /easyrecontain", inline=False)
            # Events
            embed.add_field(name="__Events__", value="/containmentsuit\n/claimvault", inline=False)
            # AFK System
            embed.add_field(name="__AFK System__", value="/afk, /return, /afklist", inline=False)
            # Polls
            embed.add_field(name="__Polls__", value="/poll, /vote, /pollresults\n/endpoll, /listpolls", inline=False)
            # Utility
            embed.add_field(name="__Utility__", value="/ping, /botdetails, /serverinfo\n/textme, /recommend", inline=False)
            embed.add_field(name="⏳ Slowmode Notice", value="Most commands have a 5 second cooldown per user. If you use commands too quickly, you'll see a slow down warning!", inline=False)
            embed.set_footer(text="For more info, ask the developer or use /modhelp if you are a mod.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        # Command-specific help
        command = command.lower()
        help_texts = {
            # Game & Profile
            "profile": "Show your profile, including level, XP, credits, equipped pet, inventory, and more. Usage: /profile [user:@User]",
            "mission": "Complete a mission for XP. Usage: /mission",
            "daily": "Claim your daily reward. Usage: /daily",
            "weekly": "Claim your weekly reward. Usage: /weekly",
            "leaderboard": "Show the top 10 users by level. Usage: /leaderboard",
            "gleaderboard": "Show global top 10 users across all servers. Usage: /gleaderboard",
            "quest": "View and claim your daily, weekly, and monthly quest rewards. Usage: /quest",
            
            # Economy & Shop
            "shop": "View the SCP shop. Usage: /shop",
            "buy": "Buy an item from the shop. Usage: /buy item:<item name>",
            "inventory": "View your inventory. Usage: /inventory",
            "checkcredits": "Check your or another user's credits. Usage: /checkcredits [user:@User]",
            "equipgun": "Equip a gun from your inventory. Usage: /equipgun gun:<gun name>",
            "equipgear": "Equip a gear item from your inventory. Usage: /equipgear gear:<gear name>",
            "upgrade": "Upgrade an item in your inventory. Usage: /upgrade item:<item name>",
            "removeitem": "Remove an item from your inventory. Usage: /removeitem item:<item name>",
            "gunsmith": "Repair a damaged weapon for 10% of its shop price. Usage: /gunsmith weapon:<weapon name>",
            "checkgun": "Check the condition of a gun you own. Usage: /checkgun gun:<gun name>",
            "inventoryvalue": "Check the total value of your inventory. Usage: /inventoryvalue",
            
            # Marketplace & Trading
            "marketplace_list": "List an item for sale on the marketplace. Usage: /marketplace_list item:<item> price:<amount>",
            "marketplace_browse": "Browse all items for sale on the marketplace. Usage: /marketplace_browse",
            "marketplace_buy": "Buy an item from the marketplace. Usage: /marketplace_buy listing_id:<id>",
            "marketplace_retrieve": "Retrieve your item from the marketplace. Usage: /marketplace_retrieve listing_id:<id>",
            "trade": "Propose a trade to another user. Usage: /trade user:@User offer_item:ItemName [offer_pet:PetName] [request_item:ItemName] [request_pet:PetName] [request_credits:Amount]",
            "confirmtrade": "Confirm and execute a pending trade. Usage: /confirmtrade trade_id:<id>",
            "canceltrade": "Cancel a pending trade you initiated. Usage: /canceltrade trade_id:<id>",
            
            # Pets
            "adoptpet": "Adopt a random pet (gacha). Usage: /adoptpet",
            "adoptpet10x": "Adopt 10 random pets at once with 5% discount. Usage: /adoptpet10x",
            "premiumpets": "Adopt a premium pet (gacha). Usage: /premiumpets",
            "premiumpets10x": "Adopt 10 premium pets at once with 5% discount. Usage: /premiumpets10x",
            "pets": "View your adopted pets. Usage: /pets",
            "equippet": "Equip up to 2 pets to show on your profile. Usage: /equippet pet:<pet name>",
            "unequippet": "Unequip a pet from your equipped slots. Usage: /unequippet pet:<pet name>",
            "equippedpets": "View and manage your equipped pets (up to 2 slots). Usage: /equippedpets",
            "petbattle": "Battle your pet against another user's equipped pet. Usage: /petbattle mypet:<your pet> opponent:@User",
            "petbattleteam": "Set up your pet battle team (up to 3 pets). Usage: /petbattleteam",
            "trainpet": "Train one of your pets (1h cooldown). Usage: /trainpet pet:<pet name>",
            "releasepet": "Release a pet you own. Usage: /releasepet pet:<pet name>",
            "comparepet": "Compare the stats of two pets by name. Usage: /comparepet pet1:<name> pet2:<name>",
            
            # Teams
            "createteam": "Create a new team. Usage: /createteam name:<team name>",
            "inviteteam": "Invite a user to your team. Usage: /inviteteam user:@User",
            "jointeam": "Join an existing team by name (if invited). Usage: /jointeam team:<team name>",
            "team": "View your current team info. Usage: /team",
            "promote": "Promote a team member to Officer or Deputy. Usage: /promote user:@User role:<officer|deputy>",
            "demote": "Demote a team member to Member. Usage: /demote user:@User",
            
            # Roles
            "setrole": "Assign yourself a custom role from the allowed list. Usage: /setrole role_name:<role>",
            "listcustomroles": "List all assignable custom roles for this server. Usage: /listcustomroles",
            
            # Gambling & Fun
            "scp914": "Gamble your credits in SCP-914! Choose a setting for different odds. Usage: /scp914 bet:<amount> setting:<rough|coarse|1:1|fine|very fine>",
            "scp294": "Order a mystery drink from SCP-294 for a random outcome! Usage: /scp294 bet:<amount>",
            "scp963": "Flip Dr. Bright's Coin of Fate! Usage: /scp963 bet:<amount> side:<heads|tails>",
            "scp999": "Hug SCP-999 for a chance at a lucky reward! Usage: /scp999 bet:<amount>",
            "recontainscp": "Battle an SCP in a containment event! Usage: /recontainscp",
            "easyrecontain": "Complete 5 easy SCP containment tasks (no weapon required). Usage: /easyrecontain",
            
            # Events
            "containmentsuit": "Use this during an active SCP-008 breach event to protect yourself (if you have a Containment Suit). Usage: /containmentsuit",
            "claimvault": "Claim the currently airdropped vault if you have the right keycard. Usage: /claimvault",
            
            # AFK System
            "afk": "Set your AFK status with a custom message. You'll be automatically removed from AFK when you send a message. Usage: /afk [message]",
            "return": "Manually return from AFK status. Usage: /return",
            "afklist": "Show all currently AFK users. Usage: /afklist",
            
            
            # Polls
            "poll": "Create a poll with multiple options. Usage: /poll question:<question> options:<option1,option2,...> [duration:<time>]",
            "vote": "Vote on a poll. Usage: /vote poll_id:<id> option_number:<1-10>",
            "pollresults": "View poll results. Usage: /pollresults poll_id:<id>",
            "endpoll": "End a poll early (creator only). Usage: /endpoll poll_id:<id>",
            "listpolls": "List active polls in this server. Usage: /listpolls",
            
            # Utility
            "ping": "Check if the bot is alive. Usage: /ping",
            "botdetails": "Show information about the bot and its creator. Usage: /botdetails",
            "serverinfo": "Show detailed information about this server. Usage: /serverinfo",
            "textme": "Send a custom message as an embed. Usage: /textme text:<message>",
            "recommend": "Recommend a song in a text channel. Usage: /recommend song:<song name>",
        }
        desc = help_texts.get(command, "Command not found. Use /commands to see all commands.")
        embed = discord.Embed(title=f"Help: /{command}", description=desc, color=discord.Color.blurple())
        embed.add_field(name="⏳ Slowmode Notice", value="Most commands have a 5 second cooldown per user. If you use commands too quickly, you'll see a slow down warning!", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # Removed /inv shortcut to reduce command count

    @app_commands.command(name="modhelp", description="Show help for moderator commands or a specific mod command")
    @app_commands.describe(command="(Optional) The mod command to get detailed help for")
    @app_commands.autocomplete(command=help_command_autocomplete)
    @slowmode.__func__()
    async def modhelp(self, interaction: discord.Interaction, command: str = None):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You do not have administrator permissions to view these commands.", ephemeral=True)
            return
        embed = discord.Embed(
            title="🛡️ Hanuko Administrator Help",
            description="Here are the main administrator commands:",
            color=discord.Color.red()
        )
        embed.add_field(name="/announcement", value="Send a server announcement.", inline=False)
        embed.add_field(name="/warn", value="Warn a user.", inline=False)
        embed.add_field(name="/warnings", value="List a user's warnings.", inline=False)
        embed.add_field(name="/clearwarnings", value="Clear all warnings for a user.", inline=False)
        embed.add_field(name="/kick", value="Kick a user from the server.", inline=False)
        embed.add_field(name="/ban", value="Ban a user from the server.", inline=False)
        embed.add_field(name="/unban", value="Unban a user by ID.", inline=False)
        embed.add_field(name="/autodetect", value="Enable or disable auto-detect word filter.", inline=False)
        embed.add_field(name="/automod", value="Configure auto-moderation features (spam/caps/emoji/links). Usage: /automod <feature> <on/off>", inline=False)
        embed.add_field(name="/alloweddomains", value="Set allowed domains for link filtering. Usage: /alloweddomains <domain1,domain2,...>", inline=False)
        embed.add_field(name="/automodstatus", value="Show current auto-moderation settings.", inline=False)
        embed.add_field(name="/mute", value="Mute a user for a custom duration. Usage: /mute user duration reason (e.g., /mute @User 10m Spamming). Supports s/m/h/d/y.", inline=False)
        embed.add_field(name="/unmute", value="Unmute a user.", inline=False)
        embed.add_field(name="/addcustomrole", value="Add a custom role to the assignable list (admin only). You can specify a color (hex or name) when creating the role.", inline=False)
        embed.add_field(name="/removecustomrole", value="Remove a custom role from the assignable list (admin only).", inline=False)
        embed.add_field(name="SCP-008 Event Admin", value="/enable008, /disable008 — Enable/disable breach events for your server. Users can use /containmentsuit during a breach.", inline=False)
        embed.add_field(name="Vault Event Admin", value="/enablevault — Enable vault airdrop events for your server. Users can use /claimvault to claim airdropped vaults if they have the right keycard.", inline=False)
        embed.add_field(name="⏳ Slowmode Notice", value="All commands have a 5 second cooldown per user. If users use commands too quickly, they'll see a slow down warning!", inline=False)
        embed.set_footer(text="For more info, see the documentation or ask the bot owner.")
        await interaction.response.send_message(embed=embed, ephemeral=True)



    @app_commands.command(name="enable008", description="Enable SCP-008 breach event for this server (admin only)")
    @app_commands.describe(channel="The channel where breach events will be announced")
    @app_commands.checks.has_permissions(administrator=True)
    @slowmode.__func__()
    async def enable008(self, interaction: discord.Interaction, channel: discord.TextChannel):
        try:
            enabled_guilds = load_enabled_008()
            if not isinstance(enabled_guilds, dict):
                enabled_guilds = {}
            guild_id = str(interaction.guild.id)
            if guild_id not in enabled_guilds or enabled_guilds[guild_id] != channel.id:
                enabled_guilds[guild_id] = channel.id
                save_enabled_008(enabled_guilds)
                await interaction.response.send_message(f"SCP-008 event enabled for this server in {channel.mention}.")
            else:
                await interaction.response.send_message("SCP-008 event is already enabled in that channel.")
        except Exception as e:
            print(f"[ERROR] /enable008: {e}")
            await interaction.response.send_message("❌ An error occurred while enabling SCP-008 event. Please check the bot logs.", ephemeral=True)

    @app_commands.command(name="disable008", description="Disable SCP-008 breach event for this server (admin only)")
    @app_commands.checks.has_permissions(administrator=True)
    @slowmode.__func__()
    async def disable008(self, interaction: discord.Interaction):
        try:
            enabled_guilds = load_enabled_008()
            if not isinstance(enabled_guilds, dict):
                enabled_guilds = {}
            guild_id = str(interaction.guild.id)
            if guild_id in enabled_guilds:
                del enabled_guilds[guild_id]
                save_enabled_008(enabled_guilds)
                await interaction.response.send_message("SCP-008 event disabled for this server.")
            else:
                await interaction.response.send_message("SCP-008 event is already disabled.")
        except Exception as e:
            print(f"[ERROR] /disable008: {e}")
            await interaction.response.send_message("❌ An error occurred while disabling SCP-008 event. Please check the bot logs.", ephemeral=True)

    @app_commands.command(name="containmentsuit", description="Respond to an active SCP-008 breach event.")
    @slowmode.__func__()
    async def containmentsuit(self, interaction: discord.Interaction):
        state = event_008_breach.get(interaction.guild.id, {"active": False})
        if not state["active"]:
            await interaction.response.send_message("There is no active SCP-008 breach event right now.", ephemeral=True)
            return
        user_data = get_user(interaction.user.id)
        inventory = user_data.get("inventory", [])
        channel = interaction.channel
        if "Containment Suit" in inventory:
            logging.debug(f"[DEBUG] {interaction.user} used a Containment Suit in guild {interaction.guild.id}")
            user_data["credits"] = user_data.get("credits", 0) + 100
            user_data["xp"] = user_data.get("xp", 0) + 50
            update_user(interaction.user.id, credits=user_data["credits"], xp=user_data["xp"])
            await interaction.response.send_message("✅ You used your Containment Suit and survived the breach! You gained 100 credits and 50 XP.", ephemeral=True)
            await channel.send(f"{interaction.user.mention} used a Containment Suit and survived the SCP-008 breach! Event is now over.")
            event_008_breach[interaction.guild.id] = {"active": False, "last": time.time()}
        else:
            await interaction.response.send_message("⚠️ You do not have a Containment Suit in your inventory! Purchase one from the shop to survive breaches.", ephemeral=True)

    @app_commands.command(name="enablevault", description="Enable Vault Airdrop event for this server (admin only)")
    @app_commands.describe(channel="The channel where vault airdrop events will be announced")
    @app_commands.checks.has_permissions(administrator=True)
    @slowmode.__func__()
    async def enablevault(self, interaction: discord.Interaction, channel: discord.TextChannel):
        try:
            vault_channels = load_vault_event_channels()
            if not isinstance(vault_channels, dict):
                vault_channels = {}
            guild_id = str(interaction.guild.id)
            if guild_id not in vault_channels or vault_channels[guild_id] != channel.id:
                vault_channels[guild_id] = channel.id
                save_vault_event_channels(vault_channels)
                await interaction.response.send_message(f"Vault Airdrop event enabled for this server in {channel.mention}.")
            else:
                await interaction.response.send_message("Vault Airdrop event is already enabled in that channel.")
        except Exception as e:
            print(f"[ERROR] /enablevault: {e}")
            await interaction.response.send_message("❌ An error occurred while enabling Vault Airdrop event. Please check the bot logs.", ephemeral=True)

    @app_commands.command(name="claimvault", description="Claim the currently airdropped vault if you have the right keycard!")
    @slowmode.__func__()
    async def claimvault(self, interaction: discord.Interaction):
        from db import get_user, update_user, vault_event_state, save_vault_event_state
        user_data = get_user(interaction.user.id)
        active_vault = getattr(interaction.client, "active_vault", None)
        if not active_vault:
            await interaction.response.send_message("❌ There is no active vault to claim right now.", ephemeral=True)
            return
        vault_type = active_vault.get("type")
        guild_id = active_vault.get("guild_id")
        if guild_id != interaction.guild.id:
            await interaction.response.send_message("❌ There is no active vault to claim right now.", ephemeral=True)
            return
        if not vault_type:
            await interaction.response.send_message("❌ There is no active vault to claim right now.", ephemeral=True)
            return
        inventory = user_data.get("inventory", [])
        if vault_type == "level1":
            if "Keycard Level 1" in inventory:
                user_data["credits"] = user_data.get("credits", 0) + 50
                user_data["xp"] = user_data.get("xp", 0) + 20
                update_user(interaction.user.id, credits=user_data["credits"], xp=user_data["xp"])
                await interaction.response.send_message("✅ You claimed the Level 1 Vault! You received 50 credits and 20 XP.", ephemeral=True)
                interaction.client.active_vault["type"] = None
                vault_event_state[interaction.guild.id] = {"active": False, "last": time.time()}
                save_vault_event_state()
            else:
                await interaction.response.send_message("❌ You need a Keycard Level 1 to claim this vault.", ephemeral=True)
        elif vault_type == "level2":
            if "Keycard Level 2" in inventory:
                user_data["credits"] = user_data.get("credits", 0) + 150
                user_data["xp"] = user_data.get("xp", 0) + 60
                update_user(interaction.user.id, credits=user_data["credits"], xp=user_data["xp"])
                await interaction.response.send_message("✅ You claimed the Level 2 Vault! You received 150 credits and 60 XP.", ephemeral=True)
                interaction.client.active_vault["type"] = None
                vault_event_state[interaction.guild.id] = {"active": False, "last": time.time()}
                save_vault_event_state()
            else:
                await interaction.response.send_message("❌ You need a Keycard Level 2 to claim this vault.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Unknown vault type.", ephemeral=True)

    @app_commands.command(name="textme", description="Send a custom message as an embed.")
    @app_commands.describe(text="The message to send")
    async def textme(self, interaction: discord.Interaction, text: str):
        print(f"[DEBUG] /textme called by {interaction.user} (ID: {interaction.user.id})")
        print(f"[DEBUG] Text content: {text}")
        print(f"[DEBUG] Guild: {interaction.guild.name} (ID: {interaction.guild.id})")
        print(f"[DEBUG] Channel: {interaction.channel.name} (ID: {interaction.channel.id})")
        
        user = interaction.user
        bot_user = interaction.client.user
        
        print(f"[DEBUG] User display_name: {user.display_name}")
        print(f"[DEBUG] User name: {user.name}")
        print(f"[DEBUG] User ID: {user.id}")
        print(f"[DEBUG] Bot display_name: {bot_user.display_name}")
        print(f"[DEBUG] Bot name: {bot_user.name}")
        print(f"[DEBUG] Bot ID: {bot_user.id}")

        # Debug: print the user's avatar URL
        print(f"[DEBUG] User display_avatar exists: {hasattr(user, 'display_avatar')}")
        print(f"[DEBUG] User display_avatar: {user.display_avatar}")
        print(f"[DEBUG] User display_avatar.url: {user.display_avatar.url if user.display_avatar else 'None'}")

        # Debug: print the bot's avatar URL
        icon_url = None
        print(f"[DEBUG] Bot display_avatar exists: {hasattr(bot_user, 'display_avatar')}")
        print(f"[DEBUG] Bot display_avatar: {bot_user.display_avatar}")
        if hasattr(bot_user, "display_avatar") and bot_user.display_avatar:
            icon_url = bot_user.display_avatar.url
            print(f"[DEBUG] Using bot display_avatar.url: {icon_url}")
        elif hasattr(bot_user, "avatar") and bot_user.avatar:
            icon_url = bot_user.avatar.url
            print(f"[DEBUG] Using bot avatar.url: {icon_url}")
        else:
            print(f"[DEBUG] No bot avatar found, icon_url will be None")
        
        print(f"[DEBUG] Final icon_url: {icon_url}")
        
        try:
            embed = discord.Embed(
                description=text,
                color=discord.Color.blurple()
            )
            print(f"[DEBUG] Created embed with description: {text}")
            
            embed.set_author(
                name=user.display_name,
                icon_url=user.display_avatar.url
            )
            print(f"[DEBUG] Set author: {user.display_name} with icon_url: {user.display_avatar.url}")
            
            embed.set_footer(
                text=bot_user.display_name
            )
            print(f"[DEBUG] Set footer: {bot_user.display_name} (no icon due to GIF avatar)")
            
            print(f"[DEBUG] About to send embed...")
            await interaction.response.send_message(embed=embed)
            print(f"[DEBUG] Embed sent successfully!")
            
        except Exception as e:
            print(f"[ERROR] Failed to create or send embed: {e}")
            print(f"[ERROR] Exception type: {type(e)}")
            import traceback
            print(f"[ERROR] Full traceback: {traceback.format_exc()}")
            await interaction.response.send_message(f"❌ Error creating embed: {str(e)}", ephemeral=True)

    @app_commands.command(name="poll", description="Create a poll with multiple options")
    @app_commands.describe(question="The poll question", options="Options separated by commas (max 10)", duration="How long the poll should run (e.g., 1h, 1d)")
    @slowmode.__func__()
    async def poll(self, interaction: discord.Interaction, question: str, options: str, duration: str = "24h"):
        print(f"[DEBUG] /poll called by {interaction.user}")
        
        # Parse options
        option_list = [opt.strip() for opt in options.split(",") if opt.strip()]
        if len(option_list) < 2:
            await interaction.response.send_message("❌ You need at least 2 options for a poll.", ephemeral=True)
            return
        if len(option_list) > 10:
            await interaction.response.send_message("❌ You can have at most 10 options.", ephemeral=True)
            return
        
        # Parse duration
        delta = self.parse_time(duration)
        if not delta:
            await interaction.response.send_message(
                "❌ Invalid duration format. Use: number + s/m/h/d (e.g., 1h, 1d)",
                ephemeral=True
            )
            return
        
        # Check if duration is too long (max 7 days)
        if delta > timedelta(days=7):
            await interaction.response.send_message(
                "❌ Polls can only run for up to 7 days.",
                ephemeral=True
            )
            return
        
        # Calculate end time
        end_time = datetime.utcnow() + delta
        
        # Generate unique poll ID
        poll_id = f"{interaction.guild.id}_{int(time.time())}"
        
        # Create poll data
        poll_data = {
            "question": question,
            "options": option_list,
            "votes": {str(i): [] for i in range(len(option_list))},
            "created_by": str(interaction.user.id),
            "created_at": datetime.utcnow().isoformat(),
            "end_time": end_time.isoformat(),
            "channel_id": str(interaction.channel.id),
            "message_id": None,
            "active": True
        }
        
        # Save poll
        polls = load_polls()
        polls[poll_id] = poll_data
        save_polls(polls)
        
        # Create poll embed
        embed = discord.Embed(
            title="📊 Poll Created",
            description=f"**{question}**",
            color=discord.Color.blue()
        )
        
        # Add options with emoji numbers
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        options_text = ""
        for i, option in enumerate(option_list):
            options_text += f"{emojis[i]} {option}\n"
        
        embed.add_field(name="Options", value=options_text, inline=False)
        embed.add_field(name="Ends", value=f"<t:{int(end_time.timestamp())}:F>", inline=True)
        embed.add_field(name="In", value=f"<t:{int(end_time.timestamp())}:R>", inline=True)
        embed.add_field(name="Vote", value=f"Use `/vote {poll_id} <option_number>` to vote", inline=False)
        embed.set_footer(text=f"Poll ID: {poll_id} • Created by {interaction.user.display_name}")
        
        # Send poll message
        poll_message = await interaction.channel.send(embed=embed)
        
        # Update poll with message ID
        polls[poll_id]["message_id"] = str(poll_message.id)
        save_polls(polls)
        
        await interaction.response.send_message(f"✅ Poll created! Poll ID: `{poll_id}`", ephemeral=True)

    @app_commands.command(name="vote", description="Vote on a poll")
    @app_commands.describe(poll_id="The poll ID (from the poll message)", option_number="The option number to vote for (1-10)")
    @slowmode.__func__()
    async def vote(self, interaction: discord.Interaction, poll_id: str, option_number: int):
        print(f"[DEBUG] /vote called by {interaction.user}")
        
        if option_number < 1 or option_number > 10:
            await interaction.response.send_message("❌ Option number must be between 1 and 10.", ephemeral=True)
            return
        
        polls = load_polls()
        if poll_id not in polls:
            await interaction.response.send_message("❌ Poll not found.", ephemeral=True)
            return
        
        poll = polls[poll_id]
        if not poll["active"]:
            await interaction.response.send_message("❌ This poll has ended.", ephemeral=True)
            return
        
        # Check if poll has ended
        end_time = datetime.fromisoformat(poll["end_time"])
        if datetime.utcnow() >= end_time:
            poll["active"] = False
            save_polls(polls)
            await interaction.response.send_message("❌ This poll has ended.", ephemeral=True)
            return
        
        # Check if option exists
        option_index = str(option_number - 1)
        if option_index not in poll["votes"]:
            await interaction.response.send_message("❌ Invalid option number.", ephemeral=True)
            return
        
        user_id = str(interaction.user.id)
        
        # Remove user's previous vote if any
        for votes in poll["votes"].values():
            if user_id in votes:
                votes.remove(user_id)
        
        # Add new vote
        poll["votes"][option_index].append(user_id)
        save_polls(polls)
        
        embed = discord.Embed(
            title="✅ Vote Cast",
            description=f"Your vote has been recorded for option {option_number}.",
            color=discord.Color.green()
        )
        embed.add_field(name="Poll", value=poll["question"], inline=False)
        embed.add_field(name="Your Choice", value=poll["options"][option_number - 1], inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="pollresults", description="View poll results")
    @app_commands.describe(poll_id="The poll ID (from the poll message)")
    @slowmode.__func__()
    async def pollresults(self, interaction: discord.Interaction, poll_id: str):
        print(f"[DEBUG] /pollresults called by {interaction.user}")
        
        polls = load_polls()
        if poll_id not in polls:
            await interaction.response.send_message("❌ Poll not found.", ephemeral=True)
            return
        
        poll = polls[poll_id]
        
        embed = discord.Embed(
            title="📊 Poll Results",
            description=f"**{poll['question']}**",
            color=discord.Color.blue()
        )
        
        # Calculate total votes
        total_votes = sum(len(votes) for votes in poll["votes"].values())
        
        # Add results for each option
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        for i, option in enumerate(poll["options"]):
            votes = len(poll["votes"][str(i)])
            percentage = (votes / total_votes * 100) if total_votes > 0 else 0
            bar_length = int(percentage / 10)  # 10% per bar segment
            bar = "█" * bar_length + "░" * (10 - bar_length)
            
            embed.add_field(
                name=f"{emojis[i]} {option}",
                value=f"Votes: {votes} ({percentage:.1f}%)\n{bar}",
                inline=False
            )
        
        embed.add_field(name="Total Votes", value=str(total_votes), inline=True)
        embed.add_field(name="Status", value="🟢 Active" if poll["active"] else "🔴 Ended", inline=True)
        
        if poll["active"]:
            end_time = datetime.fromisoformat(poll["end_time"])
            embed.add_field(name="Ends", value=f"<t:{int(end_time.timestamp())}:R>", inline=True)
        
        embed.set_footer(text=f"Poll ID: {poll_id}")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="endpoll", description="End a poll early (creator only)")
    @app_commands.describe(poll_id="The poll ID to end")
    @slowmode.__func__()
    async def endpoll(self, interaction: discord.Interaction, poll_id: str):
        print(f"[DEBUG] /endpoll called by {interaction.user}")
        
        polls = load_polls()
        if poll_id not in polls:
            await interaction.response.send_message("❌ Poll not found.", ephemeral=True)
            return
        
        poll = polls[poll_id]
        if not poll["active"]:
            await interaction.response.send_message("❌ This poll has already ended.", ephemeral=True)
            return
        
        if poll["created_by"] != str(interaction.user.id):
            await interaction.response.send_message("❌ Only the poll creator can end the poll.", ephemeral=True)
            return
        
        # End the poll
        poll["active"] = False
        save_polls(polls)
        
        embed = discord.Embed(
            title="🔴 Poll Ended",
            description=f"Poll has been ended early by the creator.",
            color=discord.Color.red()
        )
        embed.add_field(name="Poll", value=poll["question"], inline=False)
        embed.add_field(name="Use", value=f"`/pollresults {poll_id}` to see final results", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="listpolls", description="List active polls in this server")
    @slowmode.__func__()
    async def listpolls(self, interaction: discord.Interaction):
        print(f"[DEBUG] /listpolls called by {interaction.user}")
        
        polls = load_polls()
        guild_polls = [
            (poll_id, poll) for poll_id, poll in polls.items()
            if poll["channel_id"] == str(interaction.channel.id) and poll["active"]
        ]
        
        if not guild_polls:
            embed = discord.Embed(
                title="📊 Active Polls",
                description="No active polls in this channel.",
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title="📊 Active Polls",
            color=discord.Color.blue()
        )
        
        for poll_id, poll in guild_polls[:5]:  # Show max 5 polls
            end_time = datetime.fromisoformat(poll["end_time"])
            embed.add_field(
                name=f"Poll: {poll['question'][:50]}...",
                value=f"**ID:** `{poll_id}`\n**Ends:** <t:{int(end_time.timestamp())}:R>\n**Options:** {len(poll['options'])}",
                inline=False
            )
        
        if len(guild_polls) > 5:
            embed.add_field(name="Note", value=f"There are {len(guild_polls) - 5} more active polls...", inline=False)
        
        embed.set_footer(text="Use /pollresults <poll_id> to see results")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="givecredits", description="Give credits to a user (admin only)")
    @app_commands.describe(user="The user to give credits to", amount="The amount of credits to give")
    @app_commands.checks.has_permissions(administrator=True)
    async def givecredits(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        if amount <= 0:
            await interaction.response.send_message("Amount must be positive.", ephemeral=True)
            return
        user_data = get_user(user.id)
        user_data["credits"] = user_data.get("credits", 0) + amount
        update_user(user.id, credits=user_data["credits"])
        await interaction.response.send_message(f"Gave {amount} credits to {user.mention}. New balance: {user_data['credits']}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Misc(bot))

class HanukoBot(commands.Bot):
    async def setup_hook(self):
        # Load cogs
        for ext in initial_extensions:
            await self.load_extension(ext)
        # Sync commands
        try:
            synced = await self.tree.sync()
            print(f"[DEBUG] Synced {len(synced)} slash commands with Discord.")
        except Exception as e:
            print(f"[ERROR] Failed to sync commands: {e}")

intents = discord.Intents.all()
bot = HanukoBot(command_prefix=config.DEFAULT_PREFIX, intents=intents)

@bot.event
async def on_ready():
    print(f"[DEBUG] Bot is ready. Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"[DEBUG] Loaded {len(bot.commands)} legacy commands and {len(bot.tree.get_commands())} slash commands.")

async def main():
    TOKEN = os.environ.get("DISCORD_BOT_TOKEN", config.BOT_TOKEN)
    await bot.start(TOKEN)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 