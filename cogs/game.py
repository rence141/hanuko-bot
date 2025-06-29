from discord.ext import commands, tasks
import discord
from discord import app_commands
import traceback

# Try to import config, fall back to config_fallback if not available
try:
    import config
except ImportError:
    import config_fallback as config

from db import get_user, update_user, get_all_users, get_team, get_all_teams, calculate_inventory_value, update_inventory_value
from datetime import datetime, timedelta
import asyncio
import os
import random
from cogs.pets import get_pet_by_name, get_pet_rarity_color
import json
import calendar
import time

SCP_LIST = [
    {"name": "SCP-173", "hp": 80, "atk": 15, "desc": "The Sculpture. Moves when not observed."},
    {"name": "SCP-096", "hp": 120, "atk": 25, "desc": "The Shy Guy. Becomes enraged when seen."},
    {"name": "SCP-106", "hp": 150, "atk": 30, "desc": "The Old Man. Can pass through matter."},
    {"name": "SCP-049", "hp": 90, "atk": 18, "desc": "The Plague Doctor. Believes everyone is infected."},
    {"name": "SCP-939", "hp": 110, "atk": 22, "desc": "With Many Voices. Mimics human speech."},
    {"name": "SCP-999", "hp": 50, "atk": 5, "desc": "The Tickle Monster. Brings happiness!"},
    {"name": "SCP-131", "hp": 30, "atk": 0, "desc": "The Eye Pods. Harmless and friendly."},
    {"name": "SCP-529", "hp": 20, "atk": 0, "desc": "Josie the Half-Cat. Only the front half exists."},
    {"name": "SCP-085", "hp": 25, "atk": 0, "desc": "Cassy. A sentient 2D drawing."},
    {"name": "SCP-999-J", "hp": 10, "atk": 0, "desc": "The Joke Tickle Monster. Even less dangerous!"},
    {"name": "SCP-040", "hp": 40, "atk": 0, "desc": "Evie. A child with anomalous abilities, but harmless."},
    {"name": "SCP-2521", "hp": 140, "atk": 28, "desc": "Can't be described in text. Takes those who speak about it."},
    {"name": "SCP-303", "hp": 75, "atk": 14, "desc": "The Doorman. Blocks passage and induces fear."},
    {"name": "SCP-178", "hp": 65, "atk": 11, "desc": "3D Specs. Allows you to see hostile entities."},
    {"name": "SCP-409", "hp": 100, "atk": 19, "desc": "Crystal that causes living things to crystallize and shatter."}
]

WEAPON_BONUS = {
    "Stun Baton": 5,
    "Pistol": 10,
    "SMG": 15,
    "Shotgun": 18,
    "Rifle": 22,
}
SUIT_BONUS = 20  # Bonus HP for Containment Suit

GUN_CONDITIONS = ["Excellent", "Great", "Good", "Damaged", "Unrepairable"]

def get_gun_condition(user_data, gun_name):
    # gun_conditions is a dict: {gun_name: percentage}
    gun_conditions = user_data.get("gun_conditions", {})
    percentage = gun_conditions.get(gun_name, 100)  # Default 100% (Excellent)
    
    if percentage >= 100:
        return "Excellent"
    elif percentage >= 95:
        return "Great"
    elif percentage >= 90:
        return "Good"
    elif percentage >= 85:
        return "Damaged"
    else:
        return "Unrepairable"

def get_gun_percentage(user_data, gun_name):
    # Get the actual percentage value
    gun_conditions = user_data.get("gun_conditions", {})
    return gun_conditions.get(gun_name, 100)  # Default 100%

QUESTS_FILE = "quests.json"

def load_quests():
    if not os.path.exists(QUESTS_FILE):
        return {}
    with open(QUESTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_quests(data):
    with open(QUESTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# Utility function to check for boosts
def apply_xp_boost(user_data, base_xp):
    if user_data.get("xp_boost", 0) > time.time():
        return int(base_xp * 2)
    return base_xp

def apply_credit_boost(user_data, base_credits):
    if user_data.get("credit_boost", 0) > time.time():
        return int(base_credits * 2)
    return base_credits

def check_level_up(interaction, user_data):
    leveled_up = False
    level_up_messages = []
    XP_PER_LEVEL = 100
    while user_data.get("xp", 0) >= XP_PER_LEVEL:
        user_data["xp"] -= XP_PER_LEVEL
        user_data["level"] = user_data.get("level", 1) + 1
        leveled_up = True
        level_up_messages.append(user_data["level"])
    if leveled_up:
        update_user(interaction.user.id, xp=user_data["xp"], level=user_data["level"])
        embed = discord.Embed(
            title="🎉 Level Up!",
            description=f"Congratulations {interaction.user.mention}, you reached **Level {user_data['level']}**!",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        return embed
    return None

class Game(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="profile", description="Show a user's profile")
    @app_commands.describe(user="The user to view (leave blank for yourself)")
    async def profile(self, interaction: discord.Interaction, user: discord.Member = None):
        print(f"[DEBUG] /profile called by {interaction.user} (ID: {interaction.user.id}) for {user.display_name if user else 'self'}")
        try:
            print("PROFILE COMMAND TRIGGERED")
            if user is None:
                user = interaction.user
            print(f"[DEBUG] Fetching user data for {user.display_name} (ID: {user.id})")
            user_data = get_user(user.id)
            print(f"[DEBUG] User data: {user_data}")
            # Check mute status
            muted = False
            silly_message = None
            if os.path.exists("muted.json"):
                with open("muted.json", "r", encoding="utf-8") as f:
                    muted_data = json.load(f)
                if str(user.id) in muted_data:
                    muted = True
                    silly_options = [
                        "Shhh! This user is on vocal lockdown. 🤫",
                        "This player got hit with a mod mute. Sucks to be like that. LOL"
                    ]
                    silly_message = random.choice(silly_options)
            # Equipped pet logic
            equipped_pets = user_data.get("equipped_pets", [])
            pet_objs = []
            total_pet_atk = 0
            pet_names = []
            
            for pet_name in equipped_pets:
                if pet_name in user_data.get("pets", []):
                    pet_obj = get_pet_by_name(pet_name)
                    if pet_obj:
                        pet_objs.append(pet_obj)
                        total_pet_atk += pet_obj["atk"]
                        pet_names.append(pet_obj["name"])
            
            # Default color
            pet_color = config.EMBED_COLORS["info"]
            rarity_emojis = {
                "Common": "🟩",
                "Uncommon": "🟦",
                "Rare": "🟧",
                "Legendary": "🟨",
                "Epic": "🟪",
                "Mythic": "🟥",
                "Classified": "⬛"
            }
            rarity_colors = {
                "Common": discord.Color.green(),
                "Uncommon": discord.Color.blue(),
                "Rare": discord.Color.orange(),
                "Legendary": discord.Color.gold(),
                "Epic": discord.Color.purple(),
                "Mythic": discord.Color.red(),
                "Classified": discord.Color.default()  # Black/neutral
            }
            if pet_objs:
                pet_display = ", ".join([f"{rarity_emojis.get(pet_obj['rarity'], '')} [{pet_obj['name']}] ({pet_obj['rarity']})" for pet_obj in pet_objs])
                pet_color = rarity_colors.get(pet_objs[0]['rarity'], config.EMBED_COLORS["info"]) if pet_objs else config.EMBED_COLORS["info"]
            else:
                pet_display = "None"
            print(f"[DEBUG] Pet display: {pet_display}, pet color: {pet_color}")
            # Inventory with gun condition
            inventory_display = []
            for item in user_data.get("inventory", []):
                if item in WEAPON_BONUS:
                    cond = get_gun_condition(user_data, item)
                    inventory_display.append(f"{item} [{cond}]")
                else:
                    inventory_display.append(item)
            print(f"[DEBUG] Inventory display: {inventory_display}")
            embed = discord.Embed(
                title=f"🎮 Profile: {user.display_name}",
                color=pet_color
            )
            embed.set_thumbnail(url=user.display_avatar.url)
            embed.add_field(name="Level", value=user_data.get("level", 1), inline=True)
            embed.add_field(name="XP", value=user_data.get("xp", 0), inline=True)
            embed.add_field(name="Credits", value=user_data.get("credits", 0), inline=True)
            
            # Add streak information
            daily_streak = user_data.get("daily_streak", 0)
            weekly_streak = user_data.get("weekly_streak", 0)
            embed.add_field(name="Daily Streak", value=f"🔥 {daily_streak} days", inline=True)
            embed.add_field(name="Weekly Streak", value=f"🔥 {weekly_streak} weeks", inline=True)
            
            embed.add_field(name="Equipped Pets", value=pet_display, inline=False)
            # Inventory with gun condition
            inventory_display = []
            for item in user_data.get("inventory", []):
                if item in WEAPON_BONUS:
                    cond = get_gun_condition(user_data, item)
                    inventory_display.append(f"{item} [{cond}]")
                else:
                    inventory_display.append(item)
            embed.add_field(name="Inventory", value=", ".join(inventory_display) or "None", inline=False)
            
            # Add inventory value
            inventory_value = user_data.get("inventory_value", 0)
            print(f"[DEBUG] Inventory value: {inventory_value}")
            if inventory_value > 0:
                embed.add_field(name="Inventory Value", value=f"💰 {inventory_value:,} credits", inline=True)
            else:
                embed.add_field(name="Inventory Value", value="💰 0 credits", inline=True)

            # Team info
            team_name = user_data.get("team")
            print(f"[DEBUG] Team name: {team_name}")
            if team_name:
                team_role = user_data.get("team_role", "Member")
                team = get_team(team_name)
                print(f"[DEBUG] Team object: {team}")
                team_points = team.get("points", 0) if team else 0
                # Calculate team rank by points
                all_teams = get_all_users()
                print(f"[DEBUG] All teams: {all_teams}")
                team_points_list = [u.get("team_points", 0) for u in all_teams if u.get("team") == team_name]
                team_points_list.sort(reverse=True)
                team_rank = team_points_list.index(user_data.get("team_points", 0)) + 1 if user_data.get("team_points", 0) in team_points_list else "N/A"
                embed.add_field(name="Team", value=team_name, inline=True)
                embed.add_field(name="Team Role", value=team_role, inline=True)
                embed.add_field(name="Team Points", value=team_points, inline=True)
                embed.add_field(name="Team Rank", value=team_rank, inline=True)
            # Add muted status and silly message if muted
            if muted:
                embed.add_field(name="Status", value="🔇 Muted", inline=False)
                embed.add_field(name="Note", value=silly_message, inline=False)
            # Title
            title = user_data.get("title")
            if title:
                embed.title = f"🎮 Profile: {user.display_name} | {title}"
            # Badges
            badges = user_data.get("badges", [])
            print(f"[DEBUG] Badges: {badges}")
            badge_emojis = {
                "VIP": "🌟",
                # Add more badge types and emojis here as you add more cosmetics
            }
            if badges:
                badge_display = " ".join(badge_emojis.get(b, b) for b in badges)
                embed.add_field(name="Badges", value=badge_display, inline=False)
            print(f"[DEBUG] Finished building embed for {user.display_name}")
            await interaction.response.send_message(embed=embed, delete_after=300)
            return
        except Exception as e:
            print(f"[ERROR] Profile command error: {e}")
            traceback.print_exc()
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        f"❌ An error occurred while loading the profile. Please try again.\nError: {e}",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        f"❌ An error occurred while loading the profile. Please try again.\nError: {e}",
                        ephemeral=True
                    )
            except Exception as inner_e:
                print(f"[ERROR] Failed to send error message: {inner_e}")

    @app_commands.command(name="pro", description="Shortcut for /profile - Show a user's profile")
    @app_commands.describe(user="The user to view (leave blank for yourself)")
    async def pro(self, interaction: discord.Interaction, user: discord.Member = None):
        """Alias for profile command"""
        await self.profile(interaction, user)

    @app_commands.command(name="mission", description="Complete a mission for XP")
    async def mission(self, interaction: discord.Interaction):
        print(f"[DEBUG] /mission called by {interaction.user}")
        user_data = get_user(interaction.user.id)
        user_data["xp"] = user_data.get("xp", 0) + 10
        update_user(interaction.user.id, xp=user_data["xp"])
        embed = discord.Embed(
            description=f"{interaction.user.mention}, you gained 10 XP! (Total: {user_data['xp']})",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        # Level up check
        levelup_embed = check_level_up(interaction, user_data)
        if levelup_embed:
            try:
                await interaction.followup.send(embed=levelup_embed)
            except discord.errors.NotFound as e:
                print(f"[ERROR] Tried to send followup but webhook was gone: {e}")
            except Exception as e:
                print(f"[ERROR] Unexpected error sending followup: {e}")
        try:
            # Delete the ephemeral message after 5 minutes (300 seconds)
            await asyncio.sleep(300)
            await interaction.delete_original_response()
        except Exception:
            pass

        # --- Random Event Logic ---
        # 5% chance for an event (1 in 20)
        if random.randint(1, 20) == 1:
            event_type = random.choice(["vault", "008"])
            if event_type == "vault":
                # Vault Air Drop: Give a random user a keycard
                all_users = get_all_users()
                lucky_user = random.choice(all_users)
                keycard = random.choice(["Keycard Level 2", "Keycard Level 3"])
                inventory = lucky_user.get("inventory", [])
                inventory.append(keycard)
                update_user(lucky_user["id"], inventory=inventory)
                member = interaction.guild.get_member(lucky_user["id"])
                name = member.display_name if member else f"User {lucky_user['id']}"
                event_embed = discord.Embed(
                    title="🚁 Vault Air Drop!",
                    description=f"A supply drop has landed! {name} found a **{keycard}**!",
                    color=discord.Color.gold()
                )
                await interaction.followup.send(embed=event_embed)
            else:
                # SCP-008 Breach Event
                has_suit = "Containment Suit" in user_data.get("inventory", [])
                if has_suit:
                    event_embed = discord.Embed(
                        title="☣️ SCP-008 Breach!",
                        description=f"SCP-008 has breached containment, but your Containment Suit protected you!",
                        color=discord.Color.green()
                    )
                else:
                    # Apply a penalty or just a message
                    penalty = 50
                    user_data["credits"] = max(0, user_data.get("credits", 0) - penalty)
                    update_user(interaction.user.id, credits=user_data["credits"])
                    event_embed = discord.Embed(
                        title="☣️ SCP-008 Breach!",
                        description=f"SCP-008 has breached containment! You were exposed and lost {penalty} credits. (Get a Containment Suit to protect yourself.)",
                        color=discord.Color.red()
                    )
                await interaction.followup.send(embed=event_embed)

    @app_commands.command(name="daily", description="Claim your daily reward")
    async def daily(self, interaction: discord.Interaction):
        print(f"[DEBUG] /daily called by {interaction.user}")
        try:
            user_data = get_user(interaction.user.id)
            now = datetime.utcnow()
            last_daily = user_data.get("last_daily")
            daily_streak = user_data.get("daily_streak", 0)
            cooldown_active = False
            
            if last_daily:
                try:
                    last_dt = datetime.fromisoformat(str(last_daily))
                    time_diff = now - last_dt
                    
                    if time_diff.total_seconds() < 86400:
                        cooldown_active = True
                        left = timedelta(seconds=86400 - time_diff.total_seconds())
                        embed = discord.Embed(
                            description=f"⏳ You have already claimed your daily. Please wait **{str(left).split('.')[0]}** before claiming again.",
                            color=discord.Color.red()
                        )
                        embed.add_field(name="Current Streak", value=f"🔥 {daily_streak} days", inline=True)
                        await interaction.response.send_message(embed=embed)
                        try:
                            await asyncio.sleep(300)
                            await interaction.delete_original_response()
                        except Exception as e:
                            print(f"[ERROR] /daily delete_original_response: {e}")
                        return
                    elif time_diff.total_seconds() > 172800:  # More than 48 hours - streak broken
                        daily_streak = 0
                        
                except Exception as e:
                    print(f"[ERROR] /daily cooldown check failed: {e}")
                    # Send error message and return to prevent further execution
                    embed = discord.Embed(
                        description="❌ An error occurred while checking your daily cooldown. Please try again.",
                        color=discord.Color.red()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
            
            if not cooldown_active:
                # Increment streak
                daily_streak += 1
                
                # Calculate base reward and streak multiplier
                base_reward = 100
                streak_multiplier = min(1 + (daily_streak - 1) * 0.1, 2.0)  # Max 2x multiplier at 11+ days
                total_reward = int(base_reward * streak_multiplier)
                
                # Bonus rewards for milestone streaks
                bonus_reward = 0
                bonus_message = ""
                
                if daily_streak == 7:
                    bonus_reward = 200
                    bonus_message = "🎉 **7-Day Streak Bonus:** +200 credits!"
                elif daily_streak == 14:
                    bonus_reward = 500
                    bonus_message = "🎉 **14-Day Streak Bonus:** +500 credits!"
                elif daily_streak == 30:
                    bonus_reward = 1000
                    bonus_message = "🎉 **30-Day Streak Bonus:** +1000 credits!"
                elif daily_streak == 100:
                    bonus_reward = 5000
                    bonus_message = "🎉 **100-Day Streak Bonus:** +5000 credits!"
                
                total_reward += bonus_reward
                
                # Update user data
                user_data["credits"] = user_data.get("credits", 0) + total_reward
                user_data["last_daily"] = now.isoformat()
                user_data["daily_streak"] = daily_streak
                update_user(interaction.user.id, credits=user_data["credits"], last_daily=user_data["last_daily"], daily_streak=daily_streak)
                
                # Create embed
                embed = discord.Embed(
                    title="✅ Daily Reward Claimed!",
                    description=f"{interaction.user.mention}, you claimed your daily reward!",
                    color=discord.Color.green()
                )
                
                embed.add_field(name="Base Reward", value=f"💰 {base_reward} credits", inline=True)
                embed.add_field(name="Streak Multiplier", value=f"🔥 {streak_multiplier:.1f}x", inline=True)
                embed.add_field(name="Total Reward", value=f"💰 {total_reward} credits", inline=True)
                embed.add_field(name="Current Streak", value=f"🔥 {daily_streak} days", inline=True)
                
                if bonus_message:
                    embed.add_field(name="🎉 Streak Bonus", value=bonus_message, inline=False)
                
                # Streak milestone messages
                if daily_streak in [7, 14, 30, 50, 100]:
                    embed.add_field(name="🏆 Streak Milestone", value=f"Congratulations on reaching {daily_streak} days!", inline=False)
                
                embed.set_footer(text="Come back tomorrow to maintain your streak!")
                
                await interaction.response.send_message(embed=embed)
                
        except Exception as e:
            print(f"[ERROR] /daily failed: {e}")
            # Only try to respond if we haven't already responded
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ An error occurred while claiming your daily reward.", ephemeral=True)
            except Exception:
                pass

    @app_commands.command(name="weekly", description="Claim your weekly reward")
    async def weekly(self, interaction: discord.Interaction):
        print(f"[DEBUG] /weekly called by {interaction.user}")
        try:
            user_data = get_user(interaction.user.id)
            now = datetime.utcnow()
            last_weekly = user_data.get("last_weekly")
            weekly_streak = user_data.get("weekly_streak", 0)
            cooldown_active = False
            
            if last_weekly:
                try:
                    last_dt = datetime.fromisoformat(str(last_weekly))
                    time_diff = now - last_dt
                    
                    if time_diff.total_seconds() < 604800:
                        cooldown_active = True
                        left = timedelta(seconds=604800 - time_diff.total_seconds())
                        embed = discord.Embed(
                            description=f"⏳ You have already claimed your weekly. Please wait **{str(left).split('.')[0]}** before claiming again.",
                            color=discord.Color.red()
                        )
                        embed.add_field(name="Current Streak", value=f"🔥 {weekly_streak} weeks", inline=True)
                        await interaction.response.send_message(embed=embed)
                        try:
                            await asyncio.sleep(300)
                            await interaction.delete_original_response()
                        except Exception as e:
                            print(f"[ERROR] /weekly delete_original_response: {e}")
                        return
                    elif time_diff.total_seconds() > 1209600:  # More than 14 days - streak broken
                        weekly_streak = 0
                        
                except Exception as e:
                    print(f"[ERROR] /weekly cooldown check failed: {e}")
                    # Send error message and return to prevent further execution
                    embed = discord.Embed(
                        description="❌ An error occurred while checking your weekly cooldown. Please try again.",
                        color=discord.Color.red()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
            
            if not cooldown_active:
                # Increment streak
                weekly_streak += 1
                
                # Calculate base reward and streak multiplier
                base_reward = 500
                streak_multiplier = min(1 + (weekly_streak - 1) * 0.2, 3.0)  # Max 3x multiplier at 11+ weeks
                total_reward = int(base_reward * streak_multiplier)
                
                # Bonus rewards for milestone streaks
                bonus_reward = 0
                bonus_message = ""
                
                if weekly_streak == 4:
                    bonus_reward = 1000
                    bonus_message = "🎉 **4-Week Streak Bonus:** +1000 credits!"
                elif weekly_streak == 8:
                    bonus_reward = 2500
                    bonus_message = "🎉 **8-Week Streak Bonus:** +2500 credits!"
                elif weekly_streak == 12:
                    bonus_reward = 5000
                    bonus_message = "🎉 **12-Week Streak Bonus:** +5000 credits!"
                elif weekly_streak == 52:
                    bonus_reward = 25000
                    bonus_message = "🎉 **1-Year Streak Bonus:** +25000 credits!"
                
                total_reward += bonus_reward
                
                # Update user data
                user_data["credits"] = user_data.get("credits", 0) + total_reward
                user_data["last_weekly"] = now.isoformat()
                user_data["weekly_streak"] = weekly_streak
                update_user(interaction.user.id, credits=user_data["credits"], last_weekly=user_data["last_weekly"], weekly_streak=weekly_streak)
                
                # Create embed
                embed = discord.Embed(
                    title="✅ Weekly Reward Claimed!",
                    description=f"{interaction.user.mention}, you claimed your weekly reward!",
                    color=discord.Color.green()
                )
                
                embed.add_field(name="Base Reward", value=f"💰 {base_reward} credits", inline=True)
                embed.add_field(name="Streak Multiplier", value=f"🔥 {streak_multiplier:.1f}x", inline=True)
                embed.add_field(name="Total Reward", value=f"💰 {total_reward} credits", inline=True)
                embed.add_field(name="Current Streak", value=f"🔥 {weekly_streak} weeks", inline=True)
                
                if bonus_message:
                    embed.add_field(name="🎉 Streak Bonus", value=bonus_message, inline=False)
                
                # Streak milestone messages
                if weekly_streak in [4, 8, 12, 26, 52]:
                    embed.add_field(name="🏆 Streak Milestone", value=f"Congratulations on reaching {weekly_streak} weeks!", inline=False)
                
                embed.set_footer(text="Come back next week to maintain your streak!")
                
                await interaction.response.send_message(embed=embed)
                
        except Exception as e:
            print(f"[ERROR] /weekly failed: {e}")
            # Only try to respond if we haven't already responded
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ An error occurred while claiming your weekly reward.", ephemeral=True)
            except Exception:
                pass

    @app_commands.command(name="leaderboard", description="Show the top 10 users by level")
    async def leaderboard(self, interaction: discord.Interaction):
        print(f"[DEBUG] /leaderboard called by {interaction.user}")
        users = get_all_users()
        # Sort by level (primary), then XP (secondary), then credits (tertiary)
        users.sort(key=lambda u: (u.get("level", 1), u.get("xp", 0), u.get("credits", 0)), reverse=True)
        embed = discord.Embed(
            title="🏆 Leaderboard (Top 10 by Level)",
            color=config.EMBED_COLORS["info"]
        )
        for i, user in enumerate(users[:10], 1):
            member = interaction.guild.get_member(user["id"]) if interaction.guild else None
            if member:
                name = f"**{member.display_name}**"
            else:
                name = f"**Unknown User ({user['id']})**"
            embed.add_field(
                name=f"#{i}",
                value=f"{name}\nLevel: {user.get('level', 1)} | XP: {user.get('xp', 0)} | Credits: {user.get('credits', 0)}",
                inline=False
            )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="recontainscp", description="Battle an SCP in a containment event!")
    async def recontainscp(self, interaction: discord.Interaction):
        try:
            print(f"[DEBUG] /recontainscp called by {interaction.user}")
            # Defer the interaction to avoid timeout issues
            await interaction.response.defer()
            # Daily quest progress update
            quests = load_quests()
            user_id = str(interaction.user.id)
            today = datetime.utcnow().strftime("%Y-%m-%d")
            user_quests = quests.get(user_id, {"daily": {"date": today, "recontain": 0, "claimed": False}})
            # Reset if new day
            if user_quests["daily"].get("date") != today:
                user_quests["daily"] = {"date": today, "recontain": 0, "claimed": False}
            user_quests["daily"]["recontain"] += 1
            quests[user_id] = user_quests
            save_quests(quests)
            user_data = get_user(interaction.user.id)
            inventory = user_data.get("inventory", [])
            damaged_items = user_data.get("damaged_items")
            if not isinstance(damaged_items, list):
                damaged_items = []
            # Determine if rare dangerous battle (10% chance)
            is_dangerous = random.random() < 0.10
            if is_dangerous:
                scp = {
                    "name": "SCP-682 (Hard-to-Destroy Reptile)",
                    "hp": 500 + random.randint(0, 200),
                    "atk": 40 + random.randint(0, 20),
                    "desc": "Extremely dangerous and nearly impossible to destroy."
                }
            else:
                scp = random.choice(SCP_LIST)
            scp_hp = scp["hp"]
            scp_atk = scp["atk"]
            # User base stats
            user_hp = 100
            user_atk = 10
            # Find equipped weapon (first weapon in inventory not damaged or unrepairable)
            equipped_weapon = None
            for item in inventory:
                cond = get_gun_condition(user_data, item)
                if item in WEAPON_BONUS and cond != "Unrepairable":
                    equipped_weapon = item
                    break
            # If equipped weapon is Unrepairable, remove it
            weapon_removed_message = None
            if equipped_weapon:
                cond = get_gun_condition(user_data, equipped_weapon)
                if cond == "Unrepairable":
                    inventory.remove(equipped_weapon)
                    if user_data.get("equipped_gun") == equipped_weapon:
                        user_data["equipped_gun"] = None
                    update_user(interaction.user.id, inventory=inventory, equipped_gun=user_data.get("equipped_gun"))
                    weapon_removed_message = f"❌ Your {equipped_weapon} became unrepairable and was removed from your inventory!"
                    equipped_weapon = None
            if equipped_weapon:
                cond = get_gun_condition(user_data, equipped_weapon)
                if cond == "Damaged":
                    user_atk += int(WEAPON_BONUS[equipped_weapon] * 0.5)  # 50% damage if damaged
                else:
                    user_atk += WEAPON_BONUS[equipped_weapon]
            # Equipped pets logic
            equipped_pets = user_data.get("equipped_pets", [])
            pet_objs = []
            total_pet_atk = 0
            pet_names = []
            
            for pet_name in equipped_pets:
                if pet_name in user_data.get("pets", []):
                    pet_obj = get_pet_by_name(pet_name)
                    if pet_obj:
                        pet_objs.append(pet_obj)
                        total_pet_atk += pet_obj["atk"]
                        pet_names.append(pet_obj["name"])
            
            # Battle log
            pet_info = f" | Pets: {', '.join(pet_names)} (Total ATK: {total_pet_atk})" if pet_objs else ""
            log = [f"You encounter **{scp['name']}**! {scp['desc']}",
                   f"Your HP: {user_hp} | ATK: {user_atk}{pet_info}",
                   f"SCP HP: {scp_hp} | ATK: {scp_atk}"]
            turn = 1
            u_hp, s_hp = user_hp, scp_hp
            weapon_damaged = False
            while u_hp > 0 and s_hp > 0 and turn <= 20:
                # User attacks
                if equipped_weapon:
                    dmg = random.randint(int(user_atk*0.8), int(user_atk*1.2))
                    s_hp -= dmg
                    log.append(f"Turn {turn}: You attack {scp['name']} for {dmg} damage! SCP HP: {max(s_hp,0)}")
                else:
                    log.append(f"Turn {turn}:DANGER! You have no usable weapon!")
                # Pet attacks (if present)
                if pet_objs and s_hp > 0:
                    for pet_obj in pet_objs:
                        if s_hp <= 0:
                            break
                        pet_dmg = random.randint(int(pet_obj["atk"]*0.8), int(pet_obj["atk"]*1.2))
                        s_hp -= pet_dmg
                        log.append(f"Turn {turn}: Your pet {pet_obj['name']} attacks {scp['name']} for {pet_dmg} damage! SCP HP: {max(s_hp,0)}")
                if s_hp <= 0:
                    break
                # SCP attacks
                dmg = random.randint(int(scp_atk*0.8), int(scp_atk*1.2))
                u_hp -= dmg
                log.append(f"Turn {turn}: {scp['name']} attacks you for {dmg} damage! Your HP: {max(u_hp,0)}")
                turn += 1
            # Result and rewards
            reward_xp = 0
            reward_credits = 0
            gun_condition_changed = False
            levelup_embed = None
            if u_hp > 0 and s_hp <= 0:
                if is_dangerous:
                    reward_xp = 50
                    reward_credits = 200
                else:
                    reward_xp = 20
                    reward_credits = 75
                reward_xp = apply_xp_boost(user_data, reward_xp)
                reward_credits = apply_credit_boost(user_data, reward_credits)
                user_data["xp"] = user_data.get("xp", 0) + reward_xp
                user_data["credits"] = user_data.get("credits", 0) + reward_credits
                update_user(interaction.user.id, xp=user_data["xp"], credits=user_data["credits"])
                result = f"✅ You successfully recontained {scp['name']}!\nYou earned {reward_xp} XP and {reward_credits} credits."
                color = discord.Color.green()
                # Level up check
                levelup_embed = check_level_up(interaction, user_data)
                print(f"[DEBUG] levelup_embed: {levelup_embed} (type: {type(levelup_embed)})")
            elif s_hp > 0 and u_hp <= 0:
                # Gun break logic: 30% chance to degrade equipped gun
                gun_status_msg = ""
                if equipped_weapon:
                    gun_conditions = user_data.get("gun_conditions", {})
                    current_percentage = get_gun_percentage(user_data, equipped_weapon)
                    current_condition = get_gun_condition(user_data, equipped_weapon)
                    
                    if current_condition != "Unrepairable" and random.random() < 0.30:  # 30% chance
                        # Reduce percentage by 5%
                        new_percentage = max(80, current_percentage - 5)  # Minimum 80% (Unrepairable)
                        gun_conditions[equipped_weapon] = new_percentage
                        new_condition = get_gun_condition(user_data, equipped_weapon)
                        gun_condition_changed = True
                        log.append(f"❗ Your {equipped_weapon} condition degraded to {new_condition} ({new_percentage}%)!")
                        current_condition = new_condition
                        
                        # Remove gun if it becomes unrepairable
                        if new_condition == "Unrepairable":
                            inventory.remove(equipped_weapon)
                            if user_data.get("equipped_gun") == equipped_weapon:
                                user_data["equipped_gun"] = None
                            log.append(f"❌ Your {equipped_weapon} became unrepairable and was removed from your inventory!")
                            update_user(interaction.user.id, gun_conditions=gun_conditions, inventory=inventory, equipped_gun=user_data.get("equipped_gun"))
                        else:
                            update_user(interaction.user.id, gun_conditions=gun_conditions)
                    
                    gun_status_msg = f"\nYour {equipped_weapon} status is **{current_condition}** ({current_percentage}%)."
                # Deduct credits based on SCP difficulty
                if is_dangerous:
                    loss_credits = 100
                else:
                    loss_credits = 30
                user_data["credits"] = max(0, user_data.get("credits", 0) - loss_credits)
                update_user(interaction.user.id, credits=user_data["credits"])
                result = f"❌ You were defeated by {scp['name']}! You lost {loss_credits} credits.{gun_status_msg}"
                color = discord.Color.red()
            else:
                result = f"⚠️ The battle ended in a draw!"
                color = discord.Color.orange()
            # Save damaged items if changed
            if weapon_damaged:
                update_user(interaction.user.id, damaged_items=damaged_items)
            embed = discord.Embed(title=f"Containment Battle: {scp['name']}", description="\n".join(log), color=color)
            embed.add_field(name="Result", value=result, inline=False)
            
            # Send the main response
            await interaction.followup.send(embed=embed)
            
            # Send weapon removed message if applicable
            if weapon_removed_message:
                try:
                    await interaction.followup.send(weapon_removed_message)
                except discord.errors.NotFound as e:
                    print(f"[ERROR] Tried to send weapon removed message but webhook was gone: {e}")
                except Exception as e:
                    print(f"[ERROR] Unexpected error sending weapon removed message: {e}")
            
            # Send levelup embed if applicable
            if levelup_embed:
                try:
                    await interaction.followup.send(embed=levelup_embed)
                except discord.errors.NotFound as e:
                    print(f"[ERROR] Tried to send followup but webhook was gone: {e}")
                except Exception as e:
                    print(f"[ERROR] Unexpected error sending followup: {e}")
        except Exception as e:
            print(f"[ERROR] recontainscp command error: {e}")
            import traceback; traceback.print_exc()
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        f"❌ An error occurred. Please try again.\nError: {e}",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        f"❌ An error occurred. Please try again.\nError: {e}",
                        ephemeral=True
                    )
            except Exception as inner_e:
                print(f"[ERROR] Failed to send error message: {inner_e}")

    @app_commands.command(name="gunsmith", description="Repair a damaged weapon for 10% of its shop price.")
    @app_commands.describe(item="The name of the weapon to repair")
    async def gunsmith(self, interaction: discord.Interaction, item: str):
        print(f"[DEBUG] /gunsmith called by {interaction.user} for {item}")
        user_data = get_user(interaction.user.id)
        inventory = user_data.get("inventory", [])
        damaged_items = user_data.get("damaged_items")
        if not isinstance(damaged_items, list):
            damaged_items = []
        gun_conditions = user_data.get("gun_conditions", {})
        cond = gun_conditions.get(item, "Excellent")
        if cond == "Unrepairable":
            if item in inventory:
                inventory.remove(item)
                if user_data.get("equipped_gun") == item:
                    user_data["equipped_gun"] = None
                update_user(interaction.user.id, inventory=inventory, equipped_gun=user_data.get("equipped_gun"))
            await interaction.response.send_message(f"❌ {item} is unrepairable and has been removed from your inventory.", ephemeral=True)
            return
        # Find item in shop
        from cogs.shop import SHOP_ITEMS
        weapon = next((i for i in SHOP_ITEMS if i["name"].lower() == item.lower()), None)
        if not weapon or item not in inventory:
            await interaction.response.send_message(f"❌ You do not own '{item}'.", ephemeral=True)
            return
        if item not in damaged_items:
            await interaction.response.send_message(f"'{item}' is not damaged.", ephemeral=True)
            return
        cost = int(weapon["price"] * 0.1)
        if user_data.get("credits", 0) < cost:
            await interaction.response.send_message(f"❌ You need {cost} credits to repair '{item}'.", ephemeral=True)
            return
        user_data["credits"] -= cost
        damaged_items.remove(item)
        update_user(interaction.user.id, credits=user_data["credits"], damaged_items=damaged_items)
        cond = gun_conditions.get(item, "Excellent")
        embed = discord.Embed(description=f"🛠️ You repaired **{item} [{cond}]** for {cost} credits!", color=discord.Color.green())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="checkgun", description="Check the condition of a gun you own")
    @app_commands.describe(gun="The name of the gun to check")
    async def checkgun(self, interaction: discord.Interaction, gun: str):
        user_data = get_user(interaction.user.id)
        if gun not in user_data.get("inventory", []):
            await interaction.response.send_message(f"❌ You do not own '{gun}'.", ephemeral=True)
            return
        condition = get_gun_condition(user_data, gun)
        color_map = {
            "Excellent": discord.Color.green(),
            "Great": discord.Color.blue(),
            "Good": discord.Color.orange(),
            "Damaged": discord.Color.red(),
            "Unrepairable": discord.Color.dark_red()
        }
        embed = discord.Embed(
            title=f"🔫 {gun} Condition",
            description=f"Condition: **{condition}**",
            color=color_map.get(condition, discord.Color.light_grey())
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="checkcredits", description="Check your or another user's credits")
    @app_commands.describe(user="The user to check (leave blank for yourself)", public="Show the result publicly (default: private)")
    async def checkcredits(self, interaction: discord.Interaction, user: discord.Member = None, public: bool = False):
        if user is None:
            user = interaction.user
        user_data = get_user(user.id)
        credits = user_data.get("credits", 0)
        embed = discord.Embed(
            title=f"💰 Credits for {user.display_name}",
            description=f"{user.mention} has **{credits}** credits.",
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed, ephemeral=not public)

    @app_commands.command(name="quest", description="View and claim your daily, weekly, and monthly quest rewards")
    async def quest(self, interaction: discord.Interaction):
        quests = load_quests()
        user_id = str(interaction.user.id)
        today = datetime.utcnow().strftime("%Y-%m-%d")
        week = datetime.utcnow().strftime("%Y-W%U")
        month = datetime.utcnow().strftime("%Y-%m")
        user_quests = quests.get(user_id, {})
        # Daily
        if "daily" not in user_quests or user_quests["daily"].get("date") != today:
            user_quests["daily"] = {"date": today, "recontain": 0, "claimed": False}
        # Weekly
        if "weekly" not in user_quests or user_quests["weekly"].get("week") != week:
            user_quests["weekly"] = {"week": week, "petbattle": 0, "claimed": False}
        # Monthly
        if "monthly" not in user_quests or user_quests["monthly"].get("month") != month:
            user_quests["monthly"] = {"month": month, "adopt": 0, "claimed": False}
        # Daily quest
        daily_progress = user_quests["daily"]["recontain"]
        daily_claimed = user_quests["daily"]["claimed"]
        # Weekly quest
        weekly_progress = user_quests["weekly"]["petbattle"]
        weekly_claimed = user_quests["weekly"]["claimed"]
        # Monthly quest
        monthly_progress = user_quests["monthly"]["adopt"]
        monthly_claimed = user_quests["monthly"]["claimed"]
        embed = discord.Embed(title="📅 Quests", color=discord.Color.green())
        # Daily
        embed.add_field(name="Daily Quest", value=f"Complete 5 recontainment battles (/recontainscp)\nProgress: {daily_progress}/5\nStatus: {'✅ Claimed' if daily_claimed else ('🎉 Ready to claim!' if daily_progress >= 5 else '❌ Not completed')}", inline=False)
        # Weekly
        embed.add_field(name="Weekly Quest", value=f"Win 10 pet battles (/petbattle)\nProgress: {weekly_progress}/10\nStatus: {'✅ Claimed' if weekly_claimed else ('🎉 Ready to claim!' if weekly_progress >= 10 else '❌ Not completed')}", inline=False)
        # Monthly
        embed.add_field(name="Monthly Quest", value=f"Adopt 10 pets (/adoptpet or /premiumpets)\nProgress: {monthly_progress}/10\nStatus: {'✅ Claimed' if monthly_claimed else ('🎉 Ready to claim!' if monthly_progress >= 10 else '❌ Not completed')}", inline=False)
        # Claim rewards if ready
        reward_msgs = []
        user_data = get_user(interaction.user.id)
        # Daily
        if not daily_claimed and daily_progress >= 5:
            user_data["credits"] = user_data.get("credits", 0) + 100
            user_quests["daily"]["claimed"] = True
            reward_msgs.append("Daily: 100 credits")
        # Weekly
        if not weekly_claimed and weekly_progress >= 10:
            user_data["credits"] = user_data.get("credits", 0) + 500
            user_quests["weekly"]["claimed"] = True
            reward_msgs.append("Weekly: 500 credits")
        # Monthly
        if not monthly_claimed and monthly_progress >= 10:
            user_data["credits"] = user_data.get("credits", 0) + 2000
            user_quests["monthly"]["claimed"] = True
            reward_msgs.append("Monthly: 2000 credits")
        if reward_msgs:
            update_user(interaction.user.id, credits=user_data["credits"])
            embed.add_field(name="Rewards Claimed!", value="\n".join(reward_msgs), inline=False)
        quests[user_id] = user_quests
        save_quests(quests)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="scp914", description="Gamble your credits in SCP-914! Choose a setting for different odds.")
    @app_commands.describe(bet="Amount of credits to gamble (or 'all')", setting="SCP-914 setting: rough, coarse, 1:1, fine, very fine")
    async def scp914(self, interaction: discord.Interaction, bet: str, setting: str):
        user_data = get_user(interaction.user.id)
        if bet.lower() == "all":
            bet = user_data.get("credits", 0)
        else:
            try:
                bet = int(bet)
            except Exception:
                await interaction.response.send_message("Bet must be a positive number or 'all'.", ephemeral=True)
                return
        if bet <= 0:
            await interaction.response.send_message("You have no more credits to bet!", ephemeral=True)
            return
        if user_data.get("credits", 0) < bet:
            await interaction.response.send_message("You don't have enough credits to bet that amount!", ephemeral=True)
            return
        settings = {
            "rough": {"win_chance": 0.10, "multiplier": 10, "desc": "You risk it all for a huge reward!"},
            "coarse": {"win_chance": 0.25, "multiplier": 4, "desc": "A dangerous gamble for a big payout."},
            "1:1": {"win_chance": 0.5, "multiplier": 2, "desc": "A fair 50/50 shot."},
            "fine": {"win_chance": 0.7, "multiplier": 1.5, "desc": "Safer, but smaller reward."},
            "very fine": {"win_chance": 0.9, "multiplier": 1.2, "desc": "Almost safe, but not much gain."}
        }
        setting = setting.lower()
        if setting not in settings:
            await interaction.response.send_message("Invalid setting. Choose from: rough, coarse, 1:1, fine, very fine.", ephemeral=True)
            return
        if user_data.get("credits", 0) < bet:
            await interaction.response.send_message("You don't have enough credits to bet that amount!", ephemeral=True)
            return
        odds = settings[setting]
        import random
        win = random.random() < odds["win_chance"]
        if win:
            winnings = int(bet * odds["multiplier"])
            user_data["credits"] = user_data.get("credits", 0) - bet + winnings
            update_user(interaction.user.id, credits=user_data["credits"])
            msg = f"🛠️ You placed {bet} credits into SCP-914 on **{setting.title()}**. {odds['desc']}\n\n**Success!** You received {winnings} credits!"
            color = discord.Color.green()
        else:
            user_data["credits"] = user_data.get("credits", 0) - bet
            update_user(interaction.user.id, credits=user_data["credits"])
            msg = f"🛠️ You placed {bet} credits into SCP-914 on **{setting.title()}**. {odds['desc']}\n\n**Failure!** You lost your bet."
            color = discord.Color.red()
        embed = discord.Embed(title="SCP-914: The Clockworks", description=msg, color=color)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="scp294", description="Order a mystery drink from SCP-294 for a random outcome!")
    @app_commands.describe(bet="Amount of credits to gamble (or 'all')")
    async def scp294(self, interaction: discord.Interaction, bet: str):
        user_data = get_user(interaction.user.id)
        if bet.lower() == "all":
            bet = user_data.get("credits", 0)
        else:
            try:
                bet = int(bet)
            except Exception:
                await interaction.response.send_message("Bet must be a positive number or 'all'.", ephemeral=True)
                return
        if bet <= 0:
            await interaction.response.send_message("You have no more credits to bet!", ephemeral=True)
            return
        if user_data.get("credits", 0) < bet:
            await interaction.response.send_message("You don't have enough credits to bet that amount!", ephemeral=True)
            return
        outcomes = [
            ("win", 0.25),  # 25% win double
            ("lose", 0.5),  # 50% lose all
            ("item", 0.15), # 15% get a random item
            ("funny", 0.1)  # 10% funny message
        ]
        roll = random.random()
        acc = 0
        for outcome, chance in outcomes:
            acc += chance
            if roll < acc:
                result = outcome
                break
        if result == "win":
            winnings = bet * 2
            user_data["credits"] = user_data.get("credits", 0) - bet + winnings
            update_user(interaction.user.id, credits=user_data["credits"])
            msg = f"☕ SCP-294 dispenses a mysterious drink... It's lucky! You win {winnings} credits!"
            color = discord.Color.green()
        elif result == "lose":
            user_data["credits"] = user_data.get("credits", 0) - bet
            update_user(interaction.user.id, credits=user_data["credits"])
            msg = f"☕ SCP-294 dispenses a foul-tasting drink. You lose your bet."
            color = discord.Color.red()
        elif result == "item":
            # Give a random item (for demo, just a message)
            user_data["credits"] = user_data.get("credits", 0) - bet
            update_user(interaction.user.id, credits=user_data["credits"])
            msg = f"☕ SCP-294 dispenses a strange item! (But it's just a collectible cup for now.)"
            color = discord.Color.blurple()
        else:
            user_data["credits"] = user_data.get("credits", 0) - bet
            update_user(interaction.user.id, credits=user_data["credits"])
            msg = f"☕ SCP-294 dispenses... nothing? The machine beeps and displays: 'OUT OF ORDER'."
            color = discord.Color.orange()
        embed = discord.Embed(title="SCP-294: The Coffee Machine", description=msg, color=color)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="scp963", description="Flip Dr. Bright's Coin of Fate!")
    @app_commands.describe(bet="Amount of credits to gamble (or 'all')", side="Choose heads or tails")
    async def scp963(self, interaction: discord.Interaction, bet: str, side: str):
        user_data = get_user(interaction.user.id)
        if bet.lower() == "all":
            bet = user_data.get("credits", 0)
        else:
            try:
                bet = int(bet)
            except Exception:
                await interaction.response.send_message("Bet must be a positive number or 'all'.", ephemeral=True)
                return
        if bet <= 0:
            await interaction.response.send_message("You have no more credits to bet!", ephemeral=True)
            return
        if user_data.get("credits", 0) < bet:
            await interaction.response.send_message("You don't have enough credits to bet that amount!", ephemeral=True)
            return
        side = side.lower()
        if side not in ["heads", "tails"]:
            await interaction.response.send_message("You must choose 'heads' or 'tails'!", ephemeral=True)
            return
        roll = random.random()
        if roll < 0.48:
            result = "heads"
        elif roll < 0.96:
            result = "tails"
        else:
            result = "edge"
        if result == side:
            winnings = bet * 2
            user_data["credits"] = user_data.get("credits", 0) - bet + winnings
            update_user(interaction.user.id, credits=user_data["credits"])
            msg = f"🪙 The coin lands on **{result}**! You guessed right and win {winnings} credits!"
            color = discord.Color.green()
        elif result == "edge":
            winnings = bet * 10
            user_data["credits"] = user_data.get("credits", 0) - bet + winnings
            update_user(interaction.user.id, credits=user_data["credits"])
            msg = f"🪙 The coin lands on its edge! Dr. Bright laughs and gives you {winnings} credits!"
            color = discord.Color.gold()
        else:
            user_data["credits"] = user_data.get("credits", 0) - bet
            update_user(interaction.user.id, credits=user_data["credits"])
            msg = f"🪙 The coin lands on **{result}**. You guessed wrong and lose your bet."
            color = discord.Color.red()
        embed = discord.Embed(title="SCP-963: Coin of Fate", description=msg, color=color)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="scp999", description="Hug SCP-999 for a chance at a lucky reward!")
    @app_commands.describe(bet="Amount of credits to gamble (or 'all')")
    async def scp999(self, interaction: discord.Interaction, bet: str):
        user_data = get_user(interaction.user.id)
        if bet.lower() == "all":
            bet = user_data.get("credits", 0)
        else:
            try:
                bet = int(bet)
            except Exception:
                await interaction.response.send_message("Bet must be a positive number or 'all'.", ephemeral=True)
                return
        if bet <= 0:
            await interaction.response.send_message("You have no more credits to bet!", ephemeral=True)
            return
        if user_data.get("credits", 0) < bet:
            await interaction.response.send_message("You don't have enough credits to bet that amount!", ephemeral=True)
            return
        roll = random.random()
        if roll < 0.7:
            winnings = int(bet * 1.2)
            user_data["credits"] = user_data.get("credits", 0) - bet + winnings
            update_user(interaction.user.id, credits=user_data["credits"])
            msg = f"🧡 SCP-999 gives you a big, ticklish hug! You feel lucky and win {winnings} credits!"
            color = discord.Color.green()
        elif roll < 0.9:
            user_data["credits"] = user_data.get("credits", 0) - bet
            update_user(interaction.user.id, credits=user_data["credits"])
            msg = f"🧡 SCP-999 hugs you, but nothing special happens. You lose your bet."
            color = discord.Color.orange()
        else:
            winnings = bet * 5
            user_data["credits"] = user_data.get("credits", 0) - bet + winnings
            update_user(interaction.user.id, credits=user_data["credits"])
            msg = f"🧡 SCP-999 is extra bouncy today! You win {winnings} credits!"
            color = discord.Color.gold()
        embed = discord.Embed(title="SCP-999: The Tickle Monster", description=msg, color=color)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="easyrecontain", description="Complete 5 easy SCP containment tasks (no weapon required)")
    async def easyrecontain(self, interaction: discord.Interaction):
        easy_tasks = [
            "Sweep the containment cell floor.",
            "Check the door lock for malfunctions.",
            "Refill the SCP's food dispenser.",
            "Log the SCP's behavior in the report.",
            "Test the intercom system.",
            "Inspect the security camera feed.",
            "Replace a burnt-out lightbulb.",
            "Wipe down the observation window.",
            "Deliver a memo to the security office.",
            "Check the backup generator status."
        ]
        selected_tasks = random.sample(easy_tasks, 5)
        task_list = "\n".join([f"{i+1}. {task}" for i, task in enumerate(selected_tasks)])
        reward_xp = 5
        reward_credits = 10
        user_data = get_user(interaction.user.id)
        user_data["xp"] = user_data.get("xp", 0) + reward_xp
        user_data["credits"] = user_data.get("credits", 0) + reward_credits
        update_user(interaction.user.id, xp=user_data["xp"], credits=user_data["credits"])
        embed = discord.Embed(
            title="🧹 Easy SCP Containment Tasks",
            description=f"Complete these 5 tasks to help the Foundation!\n\n{task_list}\n\n✅ All tasks completed! You earned {reward_xp} XP and {reward_credits} credits.",
            color=discord.Color.green()
        )
        # Level up check
        levelup_embed = check_level_up(interaction, user_data)
        await interaction.response.send_message(embed=embed)
        if levelup_embed:
            try:
                await interaction.followup.send(embed=levelup_embed)
            except discord.errors.NotFound as e:
                print(f"[ERROR] Tried to send followup but webhook was gone: {e}")
            except Exception as e:
                print(f"[ERROR] Unexpected error sending followup: {e}")

    @app_commands.command(name="inventoryvalue", description="Check the total value of your inventory")
    async def inventoryvalue(self, interaction: discord.Interaction):
        try:
            user_data = get_user(interaction.user.id)
            inventory = user_data.get("inventory", [])
            
            # Calculate current inventory value
            current_value = calculate_inventory_value(inventory)
            
            # Update the database with the calculated value
            update_user(interaction.user.id, inventory_value=current_value)
            
            embed = discord.Embed(
                title="💰 Inventory Value",
                description=f"Your inventory is worth **{current_value:,} credits**",
                color=discord.Color.gold()
            )
            
            if inventory:
                # Show breakdown of valuable items
                item_prices = {
                    "Pistol": 1000, "SMG": 2500, "Rifle": 5000, "Sniper": 10000, "Shotgun": 3000, "LMG": 8000,
                    "Keycard Level 1": 500, "Keycard Level 2": 1000, "Keycard Level 3": 2000, 
                    "Keycard Level 4": 5000, "Keycard Level 5": 10000,
                    "Containment Suit": 1500, "SCP Plushie": 100, "SCP-999 Plushie": 200, "SCP-682 Plushie": 500,
                    "Medkit": 300, "Flashlight": 50, "Radio": 200, "Gas Mask": 400, "Bulletproof Vest": 800
                }
                
                valuable_items = []
                for item in inventory:
                    if item in item_prices and item_prices[item] > 100:
                        valuable_items.append(f"• {item}: {item_prices[item]:,} credits")
                
                if valuable_items:
                    embed.add_field(
                        name="Valuable Items", 
                        value="\n".join(valuable_items[:10]),  # Show top 10 most valuable
                        inline=False
                    )
            else:
                embed.add_field(name="Items", value="No items in inventory", inline=False)
            
            embed.set_footer(text="💡 Tip: Your inventory value helps you understand your total wealth!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            print(f"[ERROR] inventoryvalue command error: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while calculating inventory value. Please try again.",
                ephemeral=True
            )

    @app_commands.command(name="bal", description="Shortcut for /checkcredits - Check your credits")
    @app_commands.describe(user="The user to check (leave blank for yourself)", public="Show the result publicly (default: private)")
    async def bal(self, interaction: discord.Interaction, user: discord.Member = None, public: bool = False):
        """Alias for checkcredits command"""
        await self.checkcredits(interaction, user, public)

    @app_commands.command(name="lb", description="Shortcut for /leaderboard - Show the top 10 users")
    async def lb(self, interaction: discord.Interaction):
        """Alias for leaderboard command"""
        await self.leaderboard(interaction)

    @app_commands.command(name="equipgear", description="Equip a gear item from your inventory.")
    @app_commands.describe(gear="The name of the gear to equip")
    async def equipgear(self, interaction: discord.Interaction, gear: str):
        GEAR_NAMES = [
            "Containment Suit", "Tactical Vest", "Night Vision Goggles", "Radio", "Binoculars", "Lockpick Set"
        ]
        user_data = get_user(interaction.user.id)
        inventory = user_data.get("inventory", [])
        if gear not in inventory or gear not in GEAR_NAMES:
            await interaction.response.send_message(f"❌ You do not have '{gear}' in your inventory or it is not a valid gear item.", ephemeral=True)
            return
        user_data["equipped_gear"] = gear
        update_user(interaction.user.id, equipped_gear=gear)
        await interaction.response.send_message(f"✅ You have equipped '{gear}'.", ephemeral=True)

    @app_commands.command(name="gleaderboard", description="Show the global top 10 users across all servers")
    async def gleaderboard(self, interaction: discord.Interaction):
        print(f"[DEBUG] /gleaderboard called by {interaction.user}")
        try:
            # Get all users from the database
            all_users = get_all_users()
            print(f"[DEBUG] get_all_users() returned: {all_users}")
            if not all_users:
                await interaction.response.send_message("❌ No users found in the global database.", ephemeral=True)
                return
            # Filter out users missing required fields
            filtered_users = []
            for u in all_users:
                if not isinstance(u, dict):
                    print(f"[DEBUG] Skipping non-dict user: {u}")
                    continue
                if "id" not in u:
                    print(f"[DEBUG] Skipping user missing 'id': {u}")
                    continue
                filtered_users.append(u)
            print(f"[DEBUG] Filtered users: {filtered_users}")
            # Sort by level (primary), then XP (secondary), then credits (tertiary)
            sorted_users = sorted(filtered_users, key=lambda x: (
                x.get("level", 1), 
                x.get("xp", 0), 
                x.get("credits", 0)
            ), reverse=True)
            # Get top 10
            top_10 = sorted_users[:10]
            embed = discord.Embed(
                title="🌍 Global Leaderboard",
                description="Top 10 players across all servers",
                color=discord.Color.gold()
            )
            for i, user_data in enumerate(top_10, 1):
                user_id = user_data.get("id")
                if not user_id:
                    continue
                try:
                    user = await self.bot.fetch_user(int(user_id))
                    username = user.display_name
                except Exception as e:
                    print(f"[DEBUG] Could not fetch user {user_id}: {e}")
                    username = f"User {user_id}"
                credits = user_data.get("credits", 0)
                xp = user_data.get("xp", 0)
                level = user_data.get("level", 1)
                # Medal emojis for top 3
                medal = ""
                if i == 1:
                    medal = "🥇 1st"
                elif i == 2:
                    medal = "🥈 2nd"
                elif i == 3:
                    medal = "🥉 3rd"
                else:
                    medal = f"#{i}"
                embed.add_field(
                    name=f"{medal} {username}",
                    value=f"💰 {credits:,} credits | ⭐ {xp:,} XP | 📊 Level {level}",
                    inline=False
                )
            embed.set_footer(text="Global rankings across all servers")
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            print(f"[ERROR] gleaderboard command error: {e}")
            # Use followup.send() instead of response.send_message() to avoid "already acknowledged" error
            try:
                await interaction.followup.send(
                    "❌ An error occurred while loading the global leaderboard. Please try again.",
                    ephemeral=True
                )
            except discord.errors.NotFound:
                # If the interaction is already gone, we can't send a followup either
                print(f"[ERROR] Could not send followup for gleaderboard error: {e}")
            except Exception as followup_error:
                print(f"[ERROR] Followup send failed: {followup_error}")

async def setup(bot):
    await bot.add_cog(Game(bot))

async def sync_commands():
    await bot.wait_until_ready()
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands with Discord.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

if __name__ == "__main__":
    for ext in initial_extensions:
        bot.load_extension(ext)
    # Schedule the sync_commands coroutine to run after the bot is ready
    bot.loop.create_task(sync_commands())
    TOKEN = os.environ.get("DISCORD_BOT_TOKEN", config.BOT_TOKEN)
    bot.run(TOKEN) 