from discord.ext import commands
import discord
from discord import app_commands
import config
import os
import time
import json
from hanuko_bot import event_008_breach
import logging
from discord.ext.commands import BucketType, CommandOnCooldown
from db import get_user, update_user

enabled_008_file = "008_enabled_guilds.json"
vault_event_file = "vault_event_channels.json"

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

class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_app_command_error(self, interaction, error):
        if isinstance(error, CommandOnCooldown):
            await interaction.response.send_message(
                f"⏳ You're using this command too quickly! Please slow down. Try again in {error.retry_after:.1f} seconds.",
                ephemeral=True
            )
        else:
            raise error

    # Decorator for all commands in this cog
    @staticmethod
    def slowmode():
        return commands.cooldown(1, 5, BucketType.user)

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

    @app_commands.command(name="commands", description="List all available commands with short descriptions")
    @slowmode.__func__()
    async def commands(self, interaction: discord.Interaction):
        commands_list = [
            ("/profile", "Show your profile."),
            ("/mission", "Complete a mission for XP."),
            ("/daily", "Claim your daily reward."),
            ("/weekly", "Claim your weekly reward."),
            ("/leaderboard", "Show the top 10 users by credits."),
            ("/shop", "View the SCP shop."),
            ("/buy", "Buy an item from the shop."),
            ("/inventory", "View your inventory."),
            ("/setrole", "Assign yourself a custom role from the allowed list."),
            ("/listcustomroles", "List all assignable custom roles for this server."),
            ("/petbattle", "Battle your pet against another user's pet."),
            ("/adoptpet", "Adopt a random pet (gacha)."),
            ("/premiumpets", "Adopt a premium pet (gacha)."),
            ("/quest", "View and claim your daily, weekly, and monthly quest rewards."),
            ("/marketplace list", "List an item for sale on the marketplace."),
            ("/marketplace browse", "Browse all items for sale on the marketplace."),
            ("/marketplace buy", "Buy an item from the marketplace."),
            ("/trade", "Propose a trade to another user."),
            ("/checkcredits", "Check your or another user's credits."),
            ("/bal", "Alias for /checkcredits."),
            ("/inv", "Alias for /inventory."),
            ("/lb", "Alias for /leaderboard."),
        ]
        embed = discord.Embed(title="📖 All Commands", color=discord.Color.blurple())
        for name, desc in commands_list:
            embed.add_field(name=name, value=desc, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="help", description="Show help for all player commands or a specific command")
    @app_commands.describe(command="(Optional) The command to get detailed help for")
    @slowmode.__func__()
    async def help(self, interaction: discord.Interaction, command: str = None):
        if not command:
            embed = discord.Embed(
                title="📝 Hanuko Help",
                description="Here are the main commands you can use, organized by category:",
                color=discord.Color.blurple()
            )
            # General
            embed.add_field(name="__General__", value="/profile\n/mission\n/daily, /weekly\n/leaderboard, /lb\n/checkcredits, /bal", inline=False)
            # Economy & Shop
            embed.add_field(name="__Economy & Shop__", value="/shop, /buy\n/inventory, /inv\n/equipgun", inline=False)
            # Pets
            embed.add_field(name="__Pets__", value="/adoptpet, /premiumpets\n/petbattle\n/trainpet, /equippet, /unequippet, /releasepet\n/pets", inline=False)
            # Roles & Teams
            embed.add_field(name="__Roles & Teams__", value="/setrole, /listcustomroles\n/team, /jointeam, /leaveteam, /inviteteam", inline=False)
            # Marketplace & Trading
            embed.add_field(name="__Marketplace & Trading__", value="/marketplace_list, /marketplace_browse, /marketplace_buy, /marketplace_retrieve\n/trade, /confirmtrade, /canceltrade", inline=False)
            # Gambling & Fun
            embed.add_field(name="__Gambling & Fun__", value="/scp914, /scp294, /scp963, /scp999", inline=False)
            # Quests & Events
            embed.add_field(name="__Quests & Events__", value="/quest\n/recontainscp\n/containmentsuit", inline=False)
            # Vault Event
            embed.add_field(name="__Vault Event__", value="/claimvault (claim airdropped vaults if you have the right keycard)", inline=False)
            embed.add_field(name="⏳ Slowmode Notice", value="Most commands have a 5 second cooldown per user. If you use commands too quickly, you'll see a slow down warning!", inline=False)
            embed.set_footer(text="For more info, ask the developer or use /modhelp if you are a mod.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        # Command-specific help
        command = command.lower()
        help_texts = {
            "profile": "Show your profile, including level, XP, credits, equipped pet, inventory, and more.",
            "mission": "Complete a mission for XP. Usage: /mission",
            "daily": "Claim your daily reward. Usage: /daily",
            "weekly": "Claim your weekly reward. Usage: /weekly",
            "leaderboard": "Show the top 10 users by credits. Usage: /leaderboard",
            "shop": "View the SCP shop. Usage: /shop",
            "buy": "Buy an item from the shop. Usage: /buy item:<item name>",
            "inventory": "View your inventory. Usage: /inventory",
            "inv": "Alias for /inventory.",
            "setrole": "Assign yourself a custom role from the allowed list. Usage: /setrole role_name:<role>",
            "listcustomroles": "List all assignable custom roles for this server. Usage: /listcustomroles",
            "petbattle": "Battle your pet against another user's pet. Usage: /petbattle opponent:@User",
            "adoptpet": "Adopt a random pet (gacha). Usage: /adoptpet",
            "premiumpets": "Adopt a premium pet (gacha). Usage: /premiumpets",
            "quest": "View and claim your daily, weekly, and monthly quest rewards. Usage: /quest",
            "marketplace list": "List an item for sale on the marketplace. Usage: /marketplace_list item:<item> price:<amount>",
            "marketplace browse": "Browse all items for sale on the marketplace. Usage: /marketplace_browse",
            "marketplace buy": "Buy an item from the marketplace. Usage: /marketplace_buy listing_id:<id>",
            "trade": "Propose a trade to another user. Usage: /trade user:@User offer_item:ItemName [offer_pet:PetName] [request_item:ItemName] [request_pet:PetName] [request_credits:Amount]",
            "checkcredits": "Check your or another user's credits. Usage: /checkcredits [user:@User]",
            "bal": "Alias for /checkcredits.",
            "lb": "Alias for /leaderboard.",
            "scp914": "Gamble your credits in SCP-914! Choose a setting for different odds. Usage: /scp914 bet:<amount> setting:<rough|coarse|1:1|fine|very fine>",
            "scp294": "Order a mystery drink from SCP-294 for a random outcome! Usage: /scp294 bet:<amount>",
            "scp963": "Flip Dr. Bright's Coin of Fate! Usage: /scp963 bet:<amount> side:<heads|tails>",
            "scp999": "Hug SCP-999 for a chance at a lucky reward! Usage: /scp999 bet:<amount>",
            "containmentsuit": "Use this during an active SCP-008 breach event to protect yourself (if you have a Containment Suit).",
            "enable008": "(Admin) Enable SCP-008 breach events for your server. Usage: /enable008 channel:#channel",
            "disable008": "(Admin) Disable SCP-008 breach events for your server.",
            "enablevault": "(Admin) Enable Vault Airdrop events for your server. Usage: /enablevault channel:#channel",
            "claimvault": "Claim the currently airdropped vault if you have the right keycard. Usage: /claimvault",
        }
        desc = help_texts.get(command, "Command not found. Use /commands to see all commands.")
        embed = discord.Embed(title=f"Help: /{command}", description=desc, color=discord.Color.blurple())
        embed.add_field(name="⏳ Slowmode Notice", value="Most commands have a 5 second cooldown per user. If you use commands too quickly, you'll see a slow down warning!", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="inv", description="Alias for /inventory")
    @slowmode.__func__()
    async def inv(self, interaction: discord.Interaction):
        user_data = get_user(interaction.user.id)
        embed = discord.Embed(
            title=f"\U0001f392 Inventory: {interaction.user.display_name}",
            color=config.EMBED_COLORS["info"]
        )
        if user_data["inventory"]:
            embed.add_field(name="Items", value=", ".join(user_data["inventory"]), inline=False)
        else:
            embed.add_field(name="Items", value="No items yet. Use /shop and /buy!", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="lb", description="Alias for /leaderboard")
    @slowmode.__func__()
    async def lb(self, interaction: discord.Interaction):
        from cogs.game import Game
        await Game.leaderboard(self.cog, interaction)

    @app_commands.command(name="modhelp", description="Show help for moderator commands")
    @slowmode.__func__()
    async def modhelp(self, interaction: discord.Interaction):
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
        embed.add_field(name="/mute", value="Mute a user for a custom duration. Usage: /mute user duration reason (e.g., /mute @User 10m Spamming). Supports s/m/h/d/y.", inline=False)
        embed.add_field(name="/unmute", value="Unmute a user.", inline=False)
        embed.add_field(name="/addcustomrole", value="Add a custom role to the assignable list (admin only). You can specify a color (hex or name) when creating the role.", inline=False)
        embed.add_field(name="/removecustomrole", value="Remove a custom role from the assignable list (admin only).", inline=False)
        embed.add_field(name="SCP-008 Event Admin", value="/enable008, /disable008 — Enable/disable breach events for your server. Users can use /containmentsuit during a breach.", inline=False)
        embed.add_field(name="Vault Event Admin", value="/enablevault — Enable vault airdrop events for your server. Users can use /claimvault to claim airdropped vaults if they have the right keycard.", inline=False)
        embed.add_field(name="⏳ Slowmode Notice", value="All commands have a 5 second cooldown per user. If users use commands too quickly, they'll see a slow down warning!", inline=False)
        embed.set_footer(text="For more info, see the documentation or ask the bot owner.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="welcome", description="Get an interactive welcome message with buttons!")
    @slowmode.__func__()
    async def welcome(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎉 Welcome to the SCP Foundation!",
            description="Hello there! I'm Hanuko, your SCP Foundation assistant. I'm here to help you with various tasks and activities!",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="🎮 What can I do?",
            value="• **Game Features**: Missions, battles, daily rewards\n• **Economy**: Shop, marketplace, trading\n• **Pets**: Collect and battle SCP-themed pets\n• **Events**: Special SCP containment events\n• **And much more!**",
            inline=False
        )
        embed.add_field(
            name="🚀 Getting Started",
            value="1. Use `/daily` to claim your first reward\n2. Try `/mission` to earn XP\n3. Visit `/shop` to buy items\n4. Use `/adoptpet` to get your first pet!",
            inline=False
        )
        embed.set_footer(text="Click the buttons below to explore different features!")

        # Create buttons for different categories
        view = discord.ui.View(timeout=300)  # 5 minute timeout

        # Game button
        game_button = discord.ui.Button(
            style=discord.ButtonStyle.primary,
            label="🎮 Game Commands",
            custom_id="game_commands"
        )
        
        async def game_callback(interaction: discord.Interaction):
            embed = discord.Embed(
                title="🎮 Game Commands",
                description="Here are the main game commands:",
                color=discord.Color.green()
            )
            embed.add_field(name="Daily Activities", value="• `/daily` - Claim daily reward\n• `/weekly` - Claim weekly reward\n• `/mission` - Complete missions", inline=False)
            embed.add_field(name="Battles & Combat", value="• `/recontainscp` - Battle SCPs\n• `/petbattle` - Battle pets", inline=False)
            embed.add_field(name="Gambling", value="• `/scp914` - SCP-914 gambling\n• `/scp294` - SCP-294 mystery drinks\n• `/scp963` - Dr. Bright's coin\n• `/scp999` - Hug the tickle monster", inline=False)
            embed.add_field(name="Quests", value="• `/quest` - View and claim quests", inline=False)
            await interaction.response.edit_message(embed=embed, view=None)

        game_button.callback = game_callback
        view.add_item(game_button)

        # Economy button
        economy_button = discord.ui.Button(
            style=discord.ButtonStyle.success,
            label="💰 Economy",
            custom_id="economy_commands"
        )
        
        async def economy_callback(interaction: discord.Interaction):
            embed = discord.Embed(
                title="💰 Economy Commands",
                description="Here are the economy-related commands:",
                color=discord.Color.gold()
            )
            embed.add_field(name="Shop & Items", value="• `/shop` - Browse the shop\n• `/buy` - Purchase items\n• `/inventory` - View your items", inline=False)
            embed.add_field(name="Marketplace", value="• `/marketplace_list` - List items for sale\n• `/marketplace_browse` - Browse marketplace\n• `/marketplace_buy` - Buy from marketplace", inline=False)
            embed.add_field(name="Trading", value="• `/trade` - Propose trades\n• `/confirmtrade` - Confirm trades\n• `/canceltrade` - Cancel trades", inline=False)
            embed.add_field(name="Credits", value="• `/checkcredits` - Check your balance\n• `/bal` - Alias for checkcredits", inline=False)
            await interaction.response.edit_message(embed=embed, view=None)

        economy_button.callback = economy_callback
        view.add_item(economy_button)

        # Pets button
        pets_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label="🐾 Pets",
            custom_id="pets_commands"
        )
        
        async def pets_callback(interaction: discord.Interaction):
            embed = discord.Embed(
                title="🐾 Pet Commands",
                description="Here are the pet-related commands:",
                color=discord.Color.purple()
            )
            embed.add_field(name="Adoption", value="• `/adoptpet` - Adopt a random pet\n• `/premiumpets` - Adopt premium pets", inline=False)
            embed.add_field(name="Management", value="• `/pets` - View your pets\n• `/equippet` - Equip a pet\n• `/unequippet` - Unequip current pet\n• `/releasepet` - Release a pet", inline=False)
            embed.add_field(name="Activities", value="• `/petbattle` - Battle other pets\n• `/trainpet` - Train your pets", inline=False)
            await interaction.response.edit_message(embed=embed, view=None)

        pets_button.callback = pets_callback
        view.add_item(pets_button)

        # Profile button
        profile_button = discord.ui.Button(
            style=discord.ButtonStyle.danger,
            label="👤 Profile",
            custom_id="profile_commands"
        )
        
        async def profile_callback(interaction: discord.Interaction):
            embed = discord.Embed(
                title="👤 Profile Commands",
                description="Here are the profile-related commands:",
                color=discord.Color.red()
            )
            embed.add_field(name="Profile", value="• `/profile` - View your profile\n• `/profile @user` - View another user's profile", inline=False)
            embed.add_field(name="Leaderboards", value="• `/leaderboard` - Top 10 by credits\n• `/lb` - Alias for leaderboard", inline=False)
            embed.add_field(name="Roles", value="• `/setrole` - Assign custom roles\n• `/listcustomroles` - View available roles", inline=False)
            await interaction.response.edit_message(embed=embed, view=None)

        profile_button.callback = profile_callback
        view.add_item(profile_button)

        await interaction.response.send_message(embed=embed, view=view)

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
        from hanuko_bot import bot, get_user, update_user, vault_event_state, save_vault_event_state
        user_data = get_user(interaction.user.id)
        vault_type = bot.active_vault.get("type")
        guild_id = bot.active_vault.get("guild_id")
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
                bot.active_vault["type"] = None
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
                bot.active_vault["type"] = None
                vault_event_state[interaction.guild.id] = {"active": False, "last": time.time()}
                save_vault_event_state()
            else:
                await interaction.response.send_message("❌ You need a Keycard Level 2 to claim this vault.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Unknown vault type.", ephemeral=True)

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