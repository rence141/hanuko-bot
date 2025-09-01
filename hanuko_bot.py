import discord
from discord.ext import commands, tasks
# Try to import config, fall back to config_fallback if not available
try:
    import config
except ImportError:
    import config_fallback as config
import os
import asyncio
import random
from db import get_user, update_user, get_all_users
from discord import app_commands
import time
import json
import logging
from datetime import datetime, timedelta
import aiohttp
from aiohttp import web
import threading

logging.basicConfig(level=logging.WARNING)

initial_extensions = [
    "cogs.moderation",
    "cogs.game",
    "cogs.shop",
    "cogs.pets",
    "cogs.teams", 
    "cogs.misc",
    "cogs.roles",
    "cogs.music",
    "cogs.recommendation",
]

class HanukoBot(commands.Bot):
    async def setup_hook(self):
        # Setup database tables
        print("[DEBUG] Setting up database...")
        try:
            from setup_database import create_tables
            create_tables()
            print("[DEBUG] Database setup complete!")
        except Exception as e:
            print(f"[ERROR] Database setup failed: {e}")
        
        # Load cogs
        for ext in initial_extensions:
            await self.load_extension(ext)
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            print(f"[DEBUG] Synced {len(synced)} slash commands with Discord.")
        except Exception as e:
            print(f"[ERROR] Failed to sync commands: {e}")

        # Global vault state
        self.active_vault = {"type": None}

        # Background tasks: START THEM HERE!
        vault_airdrop_announcement.start()
        scp_008_breach_event.start()

intents = discord.Intents.all()
bot = HanukoBot(command_prefix=config.DEFAULT_PREFIX, intents=intents)

@bot.event
async def on_ready():
    print(f"[DEBUG] Bot is ready. Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"[DEBUG] Loaded {len(bot.commands)} legacy commands and {len(bot.tree.get_commands())} slash commands.")
    
    # Set custom presence - SCP Foundation themed
    scp_activities = [
        discord.Activity(type=discord.ActivityType.playing, name="SCP: Containment Breach"),
        discord.Activity(type=discord.ActivityType.playing, name="SCP: Roleplay"),
        discord.Activity(type=discord.ActivityType.playing, name="SCP Foundation"),
        discord.Activity(type=discord.ActivityType.playing, name="Site-19 Operations"),
        discord.Activity(type=discord.ActivityType.playing, name="Anomaly Containment"),
        discord.Activity(type=discord.ActivityType.playing, name="SCP: Secret Laboratory"),
        discord.Activity(type=discord.ActivityType.watching, name="SCP-173"),
        discord.Activity(type=discord.ActivityType.watching, name="Containment Procedures"),
        discord.Activity(type=discord.ActivityType.listening, name="Foundation Radio"),
        discord.Activity(type=discord.ActivityType.playing, name="SCP: Unity")
    ]
    
    # Set initial presence
    await bot.change_presence(activity=scp_activities[0])
    
    # Start a background task to rotate presence every 30 seconds
    async def rotate_presence():
        while True:
            try:
                activity = random.choice(scp_activities)
                await bot.change_presence(activity=activity)
                await asyncio.sleep(30)  # Change every 30 seconds
            except Exception as e:
                print(f"[ERROR] Failed to update presence: {e}")
                await asyncio.sleep(60)  # Wait longer if there's an error
    
    # Start the presence rotation task
    bot.loop.create_task(rotate_presence())

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Remove bot mention from start of message for easier parsing
    content = message.content
    mention_str = f'<@{bot.user.id}>'
    if content.startswith(mention_str):
        content = content[len(mention_str):].strip()
    content_lower = content.lower()

    # --- Personnel file check (priority, works with or without mention) ---
    if content_lower.startswith("who's ") or content_lower.startswith("who is "):
        name = content_lower.replace("who's ", "").replace("who is ", "").strip().replace("?", "")
        personnel = ["gamer", "kel", "rafi", "jaggy", "jag", "shyshi", "jason", "fah"]
        if name in personnel:
            user_data = get_user(message.author.id)
            has_keycard = "Keycard Level 05" in user_data.get("inventory", [])
            if has_keycard:
                personnel_files = {
                    "kel": {
                        "name": "Kel",
                        "title": "05-2 Rapid Reaction Task Force",
                        "clearance": "Level 5",
                        "department": "Rapid Reaction Task Force",
                        "status": "Active",
                        "notes": "Specializes in rapid response to containment breaches. Trusted with high-level emergencies. [REDACTED] - Level 05-2.",
                        "specialization": "Crisis Response & Tactical Operations"
                    },
                    "gamer": {
                        "name": "Gamer",
                        "title": "O5-10 — The Archivist",
                        "clearance": "Level 5",
                        "department": "Records and Information Security Administration",
                        "status": "Active",
                        "notes": (
                            "O5-10, known as 'The Archivist', is the custodian of the Foundation's deepest records, including the history of previous timelines and K-Class events. "
                            "Their true identity is unknown, and even among the O5 Council, O5-10 is considered enigmatic. "
                            "Rumored to possess near-perfect recall and access to the Wanderer's Library, O5-10 is said to have knowledge of every major event the Foundation has ever faced. "
                            "Some believe O5-10 is capable of magic learned from forbidden tomes, and that the Foundation's ability to survive repeated apocalypses is due in part to their secret interventions. "
                            "O5-10 is rarely seen in public, and is often accompanied by an assistant/decoy known only as 'Salt'. "
                            "Their records are so sensitive that most of the Council does not have access to them."
                        ),
                        "specialization": "Timeline Management, K-Class Event Documentation, Anomalous Archives"
                    },
                    "jaggy": {
                        "name": "Jaggy",
                        "title": "05-1 (The Administrator)",
                        "clearance": "Level 5",
                        "department": "Administration",
                        "status": "Active",
                        "notes": "The Administrator of the Foundation. [REDACTED] - All other info classified.",
                        "specialization": "Administration & Oversight"
                    },
                    "syshi": {
                        "name": "Syshi",
                        "title": "05-8 Overseer of Health and Anomaly",
                        "clearance": "Level 5",
                        "department": "Health & Anomaly",
                        "status": "Active",
                        "notes": "Overseer of Health and Anomaly. [REDACTED] - Details classified.",
                        "specialization": "Health & Anomaly Oversight"
                    },
                    "e-t": {
                        "name": "E-T",
                        "title": "05-[UNKNOWN]",
                        "clearance": "Level 5",
                        "department": "Unknown",
                        "status": "Unknown",
                        "notes": "Info last seen in [REDACTED].",
                        "specialization": "Unknown"
                    },
                    "lorenzezz": {
                        "name": "lorenzezz",
                        "title": "05-6 Head And Department of Artificial Intelligence",
                        "clearance": "Level 5",
                        "department": "Artificial Intelligence",
                        "status": "Active",
                        "notes": "MY CREATOR. Info unknown.",
                        "specialization": "AI Development & Oversight"
                    },
                    "rafi": {
                        "name": "Rafi",
                        "title": "Research Coordinator",
                        "clearance": "Level 4",
                        "department": "Research Division",
                        "status": "Active",
                        "notes": "Coordinates research efforts across multiple SCPs. [REDACTED] - Claims to have seen SCP-096's face and survived. Investigation ongoing.",
                        "specialization": "Cross-SCP Research & Data Analysis"
                    },
                   
                    "jason": {
                        "name": "Jason",
                        "title": "Technical Specialist",
                        "clearance": "Level 3",
                        "department": "Technical Division",
                        "status": "Active",
                        "notes": "Maintains and develops containment technology. [REDACTED] - Has modified SCP-914 without authorization. Results were... interesting.",
                        "specialization": "Containment Technology & System Maintenance"
                    },
                    "fah": {
                        "name": "Fah",
                        "title": "Classified Information Specialist",
                        "clearance": "Level 5",
                        "department": "Information Security",
                        "status": "Active",
                        "notes": "Manages the most sensitive Foundation data. [REDACTED] - Has access to SCP-001 files. Identity verification required for all interactions.",
                        "specialization": "Information Security & Data Classification"
                    }
                }
                file = personnel_files[name]
                embed = discord.Embed(
                    title=f"🔒 CLASSIFIED PERSONNEL FILE: {file['name']}",
                    color=discord.Color.dark_red()
                )
                embed.add_field(name="Title", value=file['title'], inline=True)
                embed.add_field(name="Clearance", value=file['clearance'], inline=True)
                embed.add_field(name="Department", value=file['department'], inline=True)
                embed.add_field(name="Status", value=file['status'], inline=True)
                embed.add_field(name="Specialization", value=file['specialization'], inline=True)
                embed.add_field(name="Notes", value=file['notes'], inline=False)
                embed.set_footer(text="CLASSIFIED - Level 05 Access Required")
                await message.channel.send(embed=embed)
            else:
                embed = discord.Embed(
                    title=f"🔒 PERSONNEL FILE: {name.title()}",
                    description="**ACCESS DENIED** - Insufficient clearance level.",
                    color=discord.Color.dark_grey()
                )
                embed.add_field(name="Status", value="[REDACTED]", inline=True)
                embed.add_field(name="Department", value="[REDACTED]", inline=True)
                embed.add_field(name="Clearance", value="[REDACTED]", inline=True)
                embed.add_field(name="Notes", value="[REDACTED] - This information requires Level 05 clearance.", inline=False)
                embed.set_footer(text="Purchase Keycard Level 05 from /shop to access classified personnel files")
                await message.channel.send(embed=embed)
            return

    # --- Enhanced mention handling ---
    if bot.user.mentioned_in(message):
        user_data = get_user(message.author.id)
        if message.content.startswith(f'<@{bot.user.id}>'):
            await message.channel.send("🔍 Type `/help` to see all available commands!")
            return
        if "help" in content_lower:
            await message.channel.send("🛡️ Need assistance? Try `/help` for command list!")
        elif any(word in content_lower for word in ["hi", "hello", "hey"]):
            greetings = [
                f"⚡ Hello {message.author.display_name}! Ready for duty?",
                f"🔬 Greetings {message.author.display_name}! The Foundation awaits your command.",
                f"🛡️ {message.author.display_name} reporting for duty!"
            ]
            await message.channel.send(random.choice(greetings))
        elif "thank" in content_lower:
            await message.channel.send("💖 The Foundation appreciates your gratitude!")
        elif "scp" in content_lower:
            await message.channel.send("🔍 Remember: Secure, Contain, Protect!")
        else:
            responses = [
                f"🔍 {message.author.mention} How may I assist? Try `/help` for commands.",
                f"⚡ {message.author.mention} Awaiting your command. Need `/help`?",
                f"🛡️ {message.author.mention} The Foundation is listening. Use `/commands` for options."
            ]
            await message.channel.send(random.choice(responses))
        return

    await bot.process_commands(message)

@bot.event
async def on_reaction_add(reaction, user):
    # Ignore bot's own reactions
    if user == bot.user:
        return
    
    # Respond to certain emoji reactions
    emoji = str(reaction.emoji)
    
    if emoji in ["👋", "👋", "🤖", "🎮", "🔬"]:
        if random.random() < 0.3:  # 30% chance to respond
            responses = [
                "👋 Hello there!",
                "🎮 Hi! Ready for some SCP action?",
                "🔬 Greetings, Foundation member!",
                "⚡ Hey! Need help with containment?",
                "🛡️ Hello! The Foundation is at your service!"
            ]
            await reaction.message.channel.send(random.choice(responses))
    
    elif emoji in ["❤️", "💖", "💕", "💗"]:
        if random.random() < 0.4:  # 40% chance to respond
            love_responses = [
                "💖 Aww, thank you! The Foundation appreciates your support!",
                "❤️ Your dedication to the Foundation is noted!",
                "💕 The SCP Foundation loves its members too!",
                "💗 Your enthusiasm for containment is admirable!",
                "💖 Thanks! Remember: Secure, Contain, Protect!"
            ]
            await reaction.message.channel.send(random.choice(love_responses))
    
    elif emoji in ["😄", "😂", "🤣", "😊"]:
        if random.random() < 0.3:  # 30% chance to respond
            happy_responses = [
                "😄 Glad you're having fun with the Foundation!",
                "😂 SCP containment can be quite entertaining!",
                "😊 Your positive attitude helps with containment!",
                "😄 The Foundation appreciates your enthusiasm!",
                "😊 Keep that smile! It helps with SCP morale!"
            ]
            await reaction.message.channel.send(random.choice(happy_responses))

def load_vault_event_channels():
    if not os.path.exists("vault_event_channels.json"):
        return {}
    with open("vault_event_channels.json", "r", encoding="utf-8") as f:
        return json.load(f)

vault_event_state_file = "vault_event_state.json"

def save_vault_event_state():
    with open(vault_event_state_file, "w", encoding="utf-8") as f:
        json.dump(vault_event_state, f, indent=4)

def load_vault_event_state():
    global vault_event_state
    if os.path.exists(vault_event_state_file):
        with open(vault_event_state_file, "r", encoding="utf-8") as f:
            vault_event_state = {int(k): v for k, v in json.load(f).items()}
    else:
        vault_event_state = {}

# Load vault_event_state on startup
load_vault_event_state()

@tasks.loop(minutes=2)
async def vault_airdrop_announcement():
    await bot.wait_until_ready()
    vault_channels = load_vault_event_channels()
    now = time.time()
    for guild in bot.guilds:
        guild_id = str(guild.id)
        if guild_id not in vault_channels:
            continue
        channel_id = vault_channels[guild_id]
        channel = guild.get_channel(channel_id)
        if channel is None:
            continue
        state = vault_event_state.get(guild.id, {"active": False, "last": 0})
        # Only trigger if NOT active and enough time has passed since the last vault
        if state["active"]:
            continue  # Don't trigger if already active
        if now - state["last"] < 10 * 60:
            continue  # Don't trigger if last vault was less than 10 minutes ago
        # Otherwise, trigger a new vault event
        vault_type = random.choice(["level1", "level2"])
        bot.active_vault["type"] = vault_type
        bot.active_vault["guild_id"] = guild.id
        if vault_type == "level1":
            await channel.send(
                "🚨 **A Random Vault has been airdropped! Only those with a Keycard Level 1 can access it! First to claim gets the reward!**"
            )
        else:
            await channel.send(
                "🚨 **A Random Vault has been airdropped! Only those with a Keycard Level 2 can access it! First to claim gets the reward!**"
            )
        vault_event_state[guild.id] = {"active": True, "last": now}
        save_vault_event_state()

@app_commands.command(name="claimvault", description="Claim the currently airdropped vault if you have the right keycard!")
async def claimvault(interaction):
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

# File to store enabled guilds for 008 event
enabled_008_file = "008_enabled_guilds.json"
def load_enabled_008():
    if not os.path.exists(enabled_008_file):
        return {}
    with open(enabled_008_file, "r", encoding="utf-8") as f:
        return json.load(f)
def save_enabled_008(guild_ids):
    with open(enabled_008_file, "w", encoding="utf-8") as f:
        json.dump(guild_ids, f, indent=4)

# Per-guild 008 breach state
event_008_breach_file = "event_008_breach.json"

def save_event_008_breach():
    with open(event_008_breach_file, "w", encoding="utf-8") as f:
        json.dump(event_008_breach, f, indent=4)

def load_event_008_breach():
    global event_008_breach
    if os.path.exists(event_008_breach_file):
        with open(event_008_breach_file, "r", encoding="utf-8") as f:
            event_008_breach = {int(k): v for k, v in json.load(f).items()}
    else:
        event_008_breach = {}

# Load event_008_breach on startup
load_event_008_breach()

@tasks.loop(minutes=10)
async def scp_008_breach_event():
    await bot.wait_until_ready()
    enabled_guilds = load_enabled_008()  # Now a dict: {guild_id: channel_id}
    now = time.time()
    for guild in bot.guilds:
        guild_id = str(guild.id)
        if guild_id not in enabled_guilds:
            continue
        channel_id = enabled_guilds[guild_id]
        channel = guild.get_channel(channel_id) or guild.system_channel or next((c for c in guild.text_channels if c.permissions_for(guild.me).send_messages), None)
        if channel is None:
            continue
        state = event_008_breach.get(guild.id, {"active": False, "last": 0})
        # Only trigger if NOT active and enough time has passed since the last breach
        if state["active"]:
            continue  # Don't trigger if already active
        if now - state["last"] < 12 * 3600:
            continue  # Don't trigger if last breach was less than 12 hours ago
        # Otherwise, trigger a new breach
        await channel.send("☣️ **SCP-008 has breached containment! Use /containmentsuit to protect yourself!**")
        logging.debug(f"[DEBUG] Breach event set active for guild {guild.id}")
        event_008_breach[guild.id] = {"active": True, "last": now}
        save_event_008_breach()

@app_commands.command(name="enable008", description="Enable SCP-008 breach event for this server (admin only)")
@app_commands.checks.has_permissions(administrator=True)
async def enable008(interaction):
    enabled_guilds = load_enabled_008()
    if str(interaction.guild.id) not in enabled_guilds:
        enabled_guilds.append(str(interaction.guild.id))
        save_enabled_008(enabled_guilds)
        await interaction.response.send_message("SCP-008 event enabled for this server.")
    else:
        await interaction.response.send_message("SCP-008 event is already enabled.")

@app_commands.command(name="disable008", description="Disable SCP-008 breach event for this server (admin only)")
@app_commands.checks.has_permissions(administrator=True)
async def disable008(interaction):
    enabled_guilds = load_enabled_008()
    if str(interaction.guild.id) in enabled_guilds:
        enabled_guilds.remove(str(interaction.guild.id))
        save_enabled_008(enabled_guilds)
        await interaction.response.send_message("SCP-008 event disabled for this server.")
    else:
        await interaction.response.send_message("SCP-008 event is already disabled.")

@app_commands.command(name="containmentsuit", description="Respond to an active SCP-008 breach event.")
async def containmentsuit(interaction):
    state = event_008_breach.get(interaction.guild.id, {"active": False})
    if not state["active"]:
        await interaction.response.send_message("There is no active SCP-008 breach event right now.", ephemeral=True)
        return
    user_data = get_user(interaction.user.id)
    inventory = user_data.get("inventory", [])
    channel = interaction.channel
    if "Containment Suit" in inventory:
        user_data["credits"] = user_data.get("credits", 0) + 100
        user_data["xp"] = user_data.get("xp", 0) + 50
        update_user(interaction.user.id, credits=user_data["credits"], xp=user_data["xp"])
        await interaction.response.send_message("✅ You used your Containment Suit and survived the breach! You gained 100 credits and 50 XP.", ephemeral=True)
        await channel.send(f"{interaction.user.mention} used a Containment Suit and survived the SCP-008 breach! Event is now over.")
    else:
        user_data["credits"] = max(0, user_data.get("credits", 0) - 50)
        user_data["xp"] = max(0, user_data.get("xp", 0) - 100)
        update_user(interaction.user.id, credits=user_data["credits"], xp=user_data["xp"])
        await interaction.response.send_message("❌ You did not have a Containment Suit and suffered the effects of SCP-008! You lost 50 credits and 100 XP.", ephemeral=True)
        await channel.send(f"{interaction.user.mention} failed to protect themselves from SCP-008! Event is now over.")
    event_008_breach[interaction.guild.id] = {"active": False, "last": time.time()}
    save_event_008_breach()

# Add web server for ping functionality
async def web_server():
    """Simple web server to handle ping requests and keep bot awake"""
    app = web.Application()
    
    async def ping_handler(request):
        return web.Response(text="Bot is alive! 🟢")
    
    async def status_handler(request):
        return web.json_response({
            "status": "online",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime": str(datetime.utcnow() - bot.start_time) if hasattr(bot, 'start_time') else "Unknown"
        })
    
    app.router.add_get('/', ping_handler)
    app.router.add_get('/ping', ping_handler)
    app.router.add_get('/status', status_handler)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get('PORT', 8080)))
    await site.start()
    print(f"🌐 Web server started on port {os.environ.get('PORT', 8080)}")

@bot.event
async def on_app_command_error(interaction, error):
    """Global error handler for app commands"""
    if "Unknown interaction" in str(error) or "404 Not Found" in str(error):
        # Interaction expired, can't respond
        print(f"[WARNING] Interaction expired for user {interaction.user}")
        return
    
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

async def main():
    TOKEN = os.environ.get("DISCORD_BOT_TOKEN", config.BOT_TOKEN)
    
    # Set bot start time for uptime tracking
    bot.start_time = datetime.utcnow()
    
    # Start web server in background
    asyncio.create_task(web_server())
    
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())