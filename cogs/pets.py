from discord.ext import commands, tasks
import discord
from discord import app_commands, ui

# Try to import config, fall back to config_fallback if not available
try:
    import config
except ImportError:
    import config_fallback as config

import random
import json
import os
import time
from datetime import datetime, timedelta
from db import get_user, update_user
import asyncio

PETS = [
    {"name": "SCP-999", "rarity": "Legendary", "hp": 120, "atk": 30},
    {"name": "SCP-131-A", "rarity": "Common", "hp": 60, "atk": 10},
    {"name": "SCP-131-B", "rarity": "Common", "hp": 60, "atk": 10},
    {"name": "SCP-2295", "rarity": "Rare", "hp": 90, "atk": 18},
    {"name": "SCP-053", "rarity": "Epic", "hp": 100, "atk": 22},
    {"name": "SCP-040", "rarity": "Legendary", "hp": 110, "atk": 28},
    {"name": "SCP-105", "rarity": "Epic", "hp": 95, "atk": 24},
    {"name": "SCP-529", "rarity": "Uncommon", "hp": 70, "atk": 12},
    {"name": "SCP-1762 Dragon", "rarity": "Epic", "hp": 105, "atk": 26},
    {"name": "SCP-250 Tiny T-Rex", "rarity": "Rare", "hp": 85, "atk": 20},
    {"name": "SCP-054 Water Nymph", "rarity": "Rare", "hp": 80, "atk": 19},
    {"name": "SCP-1230 Dream Dragon", "rarity": "Legendary", "hp": 115, "atk": 29},
    {"name": "SCP-811 Swamp Woman", "rarity": "Epic", "hp": 100, "atk": 23},
    {"name": "SCP-040-2 Cat", "rarity": "Uncommon", "hp": 65, "atk": 13},
    {"name": "SCP-040-3 Dog", "rarity": "Uncommon", "hp": 68, "atk": 14},
    {"name": "SCP-040-4 Rabbit", "rarity": "Common", "hp": 55, "atk": 9},
    {"name": "SCP-040-5 Bird", "rarity": "Common", "hp": 50, "atk": 8},
    {"name": "SCP-682 Mini Reptile", "rarity": "Epic", "hp": 110, "atk": 27},
    {"name": "SCP-963 Hamster", "rarity": "Rare", "hp": 75, "atk": 17},
    {"name": "SCP-1048 Bear", "rarity": "Rare", "hp": 80, "atk": 18},
    {"name": "SCP-181 Lucky Cat", "rarity": "Legendary", "hp": 120, "atk": 32},
    {"name": "SCP-529-2 Kitten", "rarity": "Uncommon", "hp": 66, "atk": 13},
    {"name": "SCP-999-2 Smiling Blob", "rarity": "Rare", "hp": 90, "atk": 19},
    {"name": "Golden Retriever", "rarity": "Uncommon", "hp": 72, "atk": 15},
    {"name": "Black Cat", "rarity": "Uncommon", "hp": 68, "atk": 14},
    {"name": "Albino Ferret", "rarity": "Rare", "hp": 78, "atk": 16},
    {"name": "Miniature Pig", "rarity": "Uncommon", "hp": 70, "atk": 13},
    {"name": "Axolotl", "rarity": "Rare", "hp": 80, "atk": 17},
    {"name": "Red Panda", "rarity": "Epic", "hp": 100, "atk": 22},
    {"name": "Snowy Owl", "rarity": "Epic", "hp": 98, "atk": 21},
    {"name": "Fennec Fox", "rarity": "Rare", "hp": 82, "atk": 18},
    {"name": "Capybara", "rarity": "Uncommon", "hp": 74, "atk": 14},
    {"name": "Chinchilla", "rarity": "Uncommon", "hp": 69, "atk": 13},
    {"name": "SCP-3812 Reality Wanderer", "rarity": "Mythic", "hp": 150, "atk": 40},
    {"name": "SCP-343 The Friendly God", "rarity": "Mythic", "hp": 145, "atk": 38},
    {"name": "SCP-001 The Gate Guardian", "rarity": "Classified", "hp": 200, "atk": 50}
]

# Example rarity weights for regular and premium gacha
RARITY_WEIGHTS = {
    "Common": 60,
    "Uncommon": 25,
    "Rare": 10,
    "Epic": 4,
    "Legendary": 1,
    "Mythic": 5,
    "Classified": 1
}
PREMIUM_WEIGHTS = {
    "Common": 20,
    "Uncommon": 20,
    "Rare": 15,
    "Epic": 10,
    "Legendary": 6,
    "Mythic": 5,
    "Classified": 1
}

PET_RARITIES = {
    # Map pet names to rarities (add more as needed)
    "SCP-999": "Legendary",
    "SCP-131-A": "Common",
    "SCP-131-B": "Common",
    "SCP-2295": "Rare",
    "SCP-053": "Epic",
    "SCP-040": "Legendary",
    "SCP-105": "Epic",
    "SCP-529": "Uncommon",
    "SCP-1762 Dragon": "Epic",
    "SCP-250 Tiny T-Rex": "Rare",
    "SCP-054 Water Nymph": "Rare",
    "SCP-1230 Dream Dragon": "Legendary",
    "SCP-811 Swamp Woman": "Epic",
    "SCP-040-2 Cat": "Uncommon",
    "SCP-040-3 Dog": "Uncommon",
    "SCP-040-4 Rabbit": "Common",
    "SCP-040-5 Bird": "Common",
    "SCP-682 Mini Reptile": "Epic",
    "SCP-963 Hamster": "Rare",
    "SCP-1048 Bear": "Rare",
    "SCP-181 Lucky Cat": "Legendary",
    "SCP-529-2 Kitten": "Uncommon",
    "SCP-999-2 Smiling Blob": "Rare",
    "Golden Retriever": "Uncommon",
    "Black Cat": "Uncommon",
    "Albino Ferret": "Rare",
    "Miniature Pig": "Uncommon",
    "Axolotl": "Rare",
    "Red Panda": "Epic",
    "Snowy Owl": "Epic",
    "Fennec Fox": "Rare",
    "Capybara": "Uncommon",
    "Chinchilla": "Uncommon",
    # New Mythic pets
    "SCP-3812 Reality Wanderer": "Mythic",
    "SCP-343 The Friendly God": "Mythic",
    # New Classified pet
    "SCP-001 The Gate Guardian": "Classified"
}

PET_ADOPT_COST = 250
PREMIUM_PET_COST = 1000

PET_RARITY_COLORS = {
    "Common": 0x2ecc40,      # green
    "Uncommon": 0x3498db,    # blue
    "Rare": 0xe67e22,        # orange
    "Epic": 0x9b59b6,        # purple
    "Legendary": 0xffd700,   # gold
    "Mythic": 0xff69b4,      # pink
    "Classified": 0x800000   # maroon
}

def get_pet_by_name(name):
    return next((p for p in PETS if p['name'] == name), None)

def get_pet_rarity_color(rarity):
    return PET_RARITY_COLORS.get(rarity, 0x95a5a6)

class PetSelect(ui.View):
    def __init__(self, user_id, owned_pets):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.owned_pets = owned_pets
        # Build select options
        options = [discord.SelectOption(label=pet, value=pet) for pet in owned_pets]
        # Add the select menu
        select = ui.Select(placeholder="Choose a pet to equip", min_values=1, max_values=1, options=options)
        select.callback = self.select_callback
        self.add_item(select)
    
    async def select_callback(self, interaction2):
        pet = interaction2.data["values"][0]
        pet_obj = get_pet_by_name(pet)
        if not pet_obj:
            try:
                await interaction2.response.send_message(f"❌ Pet '{pet}' not found in the global pet list. Please contact a mod.", ephemeral=True)
            except discord.NotFound:
                await interaction2.followup.send(f"❌ Pet '{pet}' not found in the global pet list. Please contact a mod.", ephemeral=True)
            return
        
        update_user(self.user_id, equipped_pet=pet)
        color = get_pet_rarity_color(pet_obj['rarity']) if pet_obj else 0x95a5a6
        embed = discord.Embed(
            description=f"🐾 Equipped **{pet}** ({pet_obj['rarity']})!",
            color=color
        )
        
        try:
            await interaction2.response.send_message(embed=embed, ephemeral=True)
        except discord.NotFound:
            await interaction2.followup.send(embed=embed, ephemeral=True)
        
        self.stop()

class Pets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="adoptpet", description="Adopt a random pet (gacha)")
    async def adoptpet(self, interaction: discord.Interaction):
        print(f"[DEBUG] /adoptpet called by {interaction.user}")
        user_data = get_user(interaction.user.id)
        if user_data.get("credits", 0) < PET_ADOPT_COST:
            await interaction.response.send_message(f"❌ You need {PET_ADOPT_COST} credits to adopt a pet.", ephemeral=True)
            return
        available = PETS
        weights = [RARITY_WEIGHTS[PET_RARITIES.get(p['name'], "Common")] for p in available]
        pet = random.choices(available, weights=weights, k=1)[0]
        if pet['name'] in user_data.get("pets", []):
            # Dupe reward
            user_data["credits"] += 50
            update_user(interaction.user.id, credits=user_data["credits"])
            await interaction.response.send_message(f"You got a duplicate **{pet['name']}**! You received 50 credits instead.")
            return
        user_data.setdefault("pets", []).append(pet['name'])
        user_data["credits"] -= PET_ADOPT_COST
        update_user(interaction.user.id, credits=user_data["credits"], pets=user_data["pets"])
        embed = discord.Embed(
            title="🐾 New Pet Adopted!",
            description=f"You adopted **{pet['name']}**!",
            color=discord.Color.green()
        )
        embed.set_footer(text="Try to collect them all!")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="premiumpets", description="Adopt a premium pet (gacha) with higher rare chance for 1000 credits")
    async def premiumpets(self, interaction: discord.Interaction):
        print(f"[DEBUG] /premiumpets called by {interaction.user}")
        user_data = get_user(interaction.user.id)
        if user_data.get("credits", 0) < PREMIUM_PET_COST:
            await interaction.response.send_message(f"❌ You need {PREMIUM_PET_COST} credits to adopt a premium pet.", ephemeral=True)
            return
        available = [p for p in PETS if p['rarity'] in ("Mythic", "Legendary", "Classified")]
        weights = [PREMIUM_WEIGHTS[p['rarity']] for p in available]
        pet = random.choices(available, weights=weights, k=1)[0]
        if pet['name'] in user_data.get("pets", []):
            # Dupe reward
            user_data["credits"] += 200
            update_user(interaction.user.id, credits=user_data["credits"])
            await interaction.response.send_message(f"You got a duplicate **{pet['name']}**! You received 200 credits instead.")
            return
        user_data.setdefault("pets", []).append(pet['name'])
        user_data["credits"] -= PREMIUM_PET_COST
        update_user(interaction.user.id, credits=user_data["credits"], pets=user_data["pets"])
        embed = discord.Embed(
            title="🌟 Premium Pet Adopted!",
            description=f"You adopted **{pet['name']}**! (Premium Gacha)",
            color=get_pet_rarity_color(pet['rarity'])
        )
        embed.set_footer(text="Try to collect all the rarest pets!")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="pets", description="View your adopted pets")
    async def pets(self, interaction: discord.Interaction):
        print(f"[DEBUG] /pets called by {interaction.user}")
        user_data = get_user(interaction.user.id)
        if not user_data["pets"]:
            await interaction.response.send_message("You have no pets yet. Use /adoptpet!", ephemeral=True)
            return
        embed = discord.Embed(
            title=f"🐾 {interaction.user.display_name}'s Pets",
            color=config.EMBED_COLORS["info"]
        )
        for pet_name in user_data["pets"]:
            pet = get_pet_by_name(pet_name)
            if not pet:
                embed.add_field(
                    name=f"{pet_name} (Unknown)",
                    value="Legacy pet or missing data.",
                    inline=False
                )
            else:
                embed.add_field(
                    name=f"{pet['name']} ({pet['rarity']})",
                    value=f"HP: {pet['hp']}, ATK: {pet['atk']}",
                    inline=False
                )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="trainpet", description="Train one of your pets (1h cooldown)")
    @app_commands.describe(pet_name="The name of the pet to train")
    async def trainpet(self, interaction: discord.Interaction, pet_name: str):
        print(f"[DEBUG] /trainpet called by {interaction.user} for pet: {pet_name}")
        user_data = get_user(interaction.user.id)
        if pet_name not in user_data["pets"]:
            await interaction.response.send_message(f"❌ You do not own a pet named '{pet_name}'.", ephemeral=True)
            return
        now = datetime.utcnow()
        last_train = user_data.get("pet_last_train", {}).get(pet_name)
        if last_train:
            last_dt = datetime.fromisoformat(last_train)
            if (now - last_dt).total_seconds() < 3600:
                left = timedelta(seconds=3600 - (now - last_dt).total_seconds())
                await interaction.response.send_message(f"⏳ You must wait {str(left).split('.')[0]} before training this pet again.", ephemeral=True)
                return
        # Example: increase power stat
        stats = user_data.get("pet_stats", {}).get(pet_name, {"power": 0, "speed": 0, "cuteness": 0})
        stats["power"] += 1
        user_data.setdefault("pet_stats", {})[pet_name] = stats
        user_data.setdefault("pet_last_train", {})[pet_name] = now.isoformat()
        update_user(interaction.user.id, pet_stats=user_data["pet_stats"], pet_last_train=user_data["pet_last_train"])
        await interaction.response.send_message(f"🐾 {pet_name} trained! Power is now {stats['power']}.")

    @app_commands.command(name="petbattle", description="Battle your pet against another user's pet")
    @app_commands.describe(your_pet="Your pet's name", opponent="The user to battle", their_pet="Their pet's name")
    async def petbattle(self, interaction: discord.Interaction, your_pet: str, opponent: discord.Member, their_pet: str):
        print(f"[DEBUG] /petbattle called by {interaction.user} with {your_pet} vs {opponent.display_name}'s {their_pet}")
        user_data = get_user(interaction.user.id)
        opp_data = get_user(opponent.id)
        if your_pet not in user_data["pets"]:
            await interaction.response.send_message(f"❌ You do not own a pet named '{your_pet}'.", ephemeral=True)
            return
        if their_pet not in opp_data["pets"]:
            await interaction.response.send_message(f"❌ {opponent.display_name} does not own a pet named '{their_pet}'.", ephemeral=True)
            return
        your_stats = user_data.get("pet_stats", {}).get(your_pet, {"power": 0, "speed": 0, "cuteness": 0})
        their_stats = opp_data.get("pet_stats", {}).get(their_pet, {"power": 0, "speed": 0, "cuteness": 0})
        your_score = your_stats["power"] + your_stats["speed"] + your_stats["cuteness"] + random.randint(0, 5)
        their_score = their_stats["power"] + their_stats["speed"] + their_stats["cuteness"] + random.randint(0, 5)
        if your_score > their_score:
            await interaction.response.send_message(f"🎉 {interaction.user.display_name}'s {your_pet} wins the battle!")
        elif their_score > your_score:
            await interaction.response.send_message(f"🎉 {opponent.display_name}'s {their_pet} wins the battle!")
        else:
            await interaction.response.send_message("It's a tie!")

    async def equippet_autocomplete(self, interaction: discord.Interaction, current: str):
        user_data = get_user(interaction.user.id)
        owned_pets = user_data.get("pets", [])
        return [
            app_commands.Choice(name=pet, value=pet)
            for pet in owned_pets if current.lower() in pet.lower()
        ][:25]  # Discord max autocomplete options

    @app_commands.command(name="equippet", description="Equip a pet to show on your profile")
    @app_commands.describe(pet="The name of the pet to equip")
    @app_commands.autocomplete(pet=equippet_autocomplete)
    async def equippet(self, interaction: discord.Interaction, pet: str):
        print(f"[DEBUG] /equippet called by {interaction.user} for pet: {pet}")
        user_data = get_user(interaction.user.id)
        owned_pets = user_data.get("pets", [])
        if pet not in owned_pets:
            await interaction.response.send_message(f"❌ You do not own '{pet}'.", ephemeral=True)
            return
        pet_obj = get_pet_by_name(pet)
        if not pet_obj:
            await interaction.response.send_message(f"❌ Pet '{pet}' not found in the global pet list. Please contact a mod.", ephemeral=True)
            return
        update_user(interaction.user.id, equipped_pet=pet)
        color = get_pet_rarity_color(pet_obj['rarity']) if pet_obj else 0x95a5a6
        embed = discord.Embed(
            description=f"🐾 Equipped **{pet}** ({pet_obj['rarity']})!",
            color=color
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="unequippet", description="Unequip your current pet")
    async def unequippet(self, interaction: discord.Interaction):
        print(f"[DEBUG] /unequippet called by {interaction.user}")
        user_data = get_user(interaction.user.id)
        # Relaxed: treat any non-empty equipped_pet as equipped
        if not user_data.get("equipped_pet"):
            await interaction.response.send_message("You have no pet equipped.", ephemeral=True)
            return
        update_user(interaction.user.id, equipped_pet=None)
        embed = discord.Embed(description="You have unequipped your pet.", color=0x95a5a6)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        try:
            await asyncio.sleep(300)  # 5 minutes
            await interaction.delete_original_response()
        except Exception:
            pass

    @app_commands.command(name="releasepet", description="Release a pet you own (even if equipped). This will remove it from your pets.")
    @app_commands.describe(pet="The name of the pet to release")
    async def releasepet(self, interaction: discord.Interaction, pet: str):
        print(f"[DEBUG] /releasepet called by {interaction.user} for pet: {pet}")
        try:
            user_data = get_user(interaction.user.id)
            if pet not in user_data.get("pets", []):
                await interaction.response.send_message(f"❌ You do not own '{pet}'.", ephemeral=True)
                return
            # Remove from pets
            user_data["pets"].remove(pet)
            # If equipped, unequip
            if user_data.get("equipped_pet") == pet:
                user_data["equipped_pet"] = None
            update_user(interaction.user.id, pets=user_data["pets"], equipped_pet=user_data.get("equipped_pet"))
            embed = discord.Embed(
                description=f"🕊️ You have released **{pet}**. Farewell!",
                color=discord.Color.light_grey()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            try:
                await asyncio.sleep(300)  # 5 minutes
                await interaction.delete_original_response()
            except Exception:
                pass
        except Exception as e:
            print(f"[ERROR] /releasepet failed: {e}")
            try:
                await interaction.response.send_message("❌ An error occurred while releasing your pet.", ephemeral=True)
            except Exception:
                pass

    async def comparepet_autocomplete(self, interaction: discord.Interaction, current: str):
        user_data = get_user(interaction.user.id)
        owned_pets = user_data.get("pets", [])
        return [
            app_commands.Choice(name=pet, value=pet)
            for pet in owned_pets if current.lower() in pet.lower()
        ][:25]

    @app_commands.command(name="comparepet", description="Compare the stats of two pets by name")
    @app_commands.describe(pet1="The name of the first pet", pet2="The name of the second pet")
    @app_commands.autocomplete(pet1=comparepet_autocomplete, pet2=comparepet_autocomplete)
    async def comparepet(self, interaction: discord.Interaction, pet1: str, pet2: str):
        pet_obj1 = get_pet_by_name(pet1)
        pet_obj2 = get_pet_by_name(pet2)
        if not pet_obj1 and not pet_obj2:
            await interaction.response.send_message(f"❌ Neither '{pet1}' nor '{pet2}' were found in the pet list.", ephemeral=True)
            return
        if not pet_obj1:
            await interaction.response.send_message(f"❌ Pet '{pet1}' not found in the pet list.", ephemeral=True)
            return
        if not pet_obj2:
            await interaction.response.send_message(f"❌ Pet '{pet2}' not found in the pet list.", ephemeral=True)
            return
        embed = discord.Embed(
            title=f"Pet Comparison: {pet1} vs {pet2}",
            color=0x3498db
        )
        embed.add_field(name=pet_obj1['name'], value=f"Rarity: {pet_obj1['rarity']}\nHP: {pet_obj1['hp']}\nATK: {pet_obj1['atk']}", inline=True)
        embed.add_field(name=pet_obj2['name'], value=f"Rarity: {pet_obj2['rarity']}\nHP: {pet_obj2['hp']}\nATK: {pet_obj2['atk']}", inline=True)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Pets(bot)) 