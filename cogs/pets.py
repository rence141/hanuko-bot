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
    {"name": "SCP-001 The Gate Guardian", "rarity": "Classified", "hp": 200, "atk": 50},
    # New Epic SCPs (2 more)
    {"name": "SCP-1471 MalO", "rarity": "Epic", "hp": 108, "atk": 25},
    {"name": "SCP-173 The Sculpture", "rarity": "Epic", "hp": 112, "atk": 28},
    # New Legendary SCPs (4 more)
    {"name": "SCP-096 The Shy Guy", "rarity": "Legendary", "hp": 125, "atk": 35},
    {"name": "SCP-049 The Plague Doctor", "rarity": "Legendary", "hp": 118, "atk": 0},
    {"name": "SCP-106 The Old Man", "rarity": "Legendary", "hp": 122, "atk": 33},
    {"name": "SCP-035 The Possessive Mask", "rarity": "Legendary", "hp": 116, "atk": 29},
    # New Mythic SCPs (3 more)
    {"name": "SCP-239 The Witch Child", "rarity": "Mythic", "hp": 155, "atk": 42},
    {"name": "SCP-682 The Hard-to-Destroy Reptile", "rarity": "Mythic", "hp": 160, "atk": 45},
    {"name": "SCP-001 The Scarlet King", "rarity": "Mythic", "hp": 165, "atk": 48},
    # New Classified SCP (1 more)
    {"name": "SCP-001 The Factory", "rarity": "Classified", "hp": 220, "atk": 55}
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
    "SCP-001 The Gate Guardian": "Classified",
    # New Epic SCPs
    "SCP-1471 MalO": "Epic",
    "SCP-173 The Sculpture": "Epic",
    # New Legendary SCPs
    "SCP-096 The Shy Guy": "Legendary",
    "SCP-049 The Plague Doctor": "Legendary",
    "SCP-106 The Old Man": "Legendary",
    "SCP-035 The Possessive Mask": "Legendary",
    # New Mythic SCPs
    "SCP-239 The Witch Child": "Mythic",
    "SCP-682 The Hard-to-Destroy Reptile": "Mythic",
    "SCP-001 The Scarlet King": "Mythic",
    # New Classified SCP
    "SCP-001 The Factory": "Classified"
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
        # Build select options for up to 2 pets
        options = [discord.SelectOption(label=pet, value=pet) for pet in owned_pets]
        # Add the select menu - allow up to 2 selections
        select = ui.Select(placeholder="Choose up to 2 pets to equip", min_values=1, max_values=2, options=options)
        select.callback = self.select_callback
        self.add_item(select)
    
    async def select_callback(self, interaction2):
        selected_pets = interaction2.data["values"]
        
        # Validate pets
        for pet in selected_pets:
            pet_obj = get_pet_by_name(pet)
            if not pet_obj:
                try:
                    await interaction2.response.send_message(f"❌ Pet '{pet}' not found in the global pet list. Please contact a mod.", ephemeral=True)
                except discord.NotFound:
                    await interaction2.followup.send(f"❌ Pet '{pet}' not found in the global pet list. Please contact a mod.", ephemeral=True)
                return
        
        # Update equipped pets
        update_user(self.user_id, equipped_pets=selected_pets)
        
        # Create embed showing equipped pets
        embed = discord.Embed(title="🐾 Pets Equipped!", description="", color=0x00ff00)
        
        for i, pet in enumerate(selected_pets, 1):
            pet_obj = get_pet_by_name(pet)
            color = get_pet_rarity_color(pet_obj['rarity']) if pet_obj else 0x95a5a6
            embed.add_field(
                name=f"Slot {i}: {pet}",
                value=f"Rarity: {pet_obj['rarity']} | HP: {pet_obj['hp']} | ATK: {pet_obj['atk']}",
                inline=False
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

    async def petbattle_mode_autocomplete(self, interaction: discord.Interaction, current: str):
        modes = ["auto", "manual"]
        return [
            app_commands.Choice(name=mode, value=mode)
            for mode in modes if current.lower() in mode.lower()
        ]

    @app_commands.command(name="petbattle", description="Battle your pets against another user's pets (3v3)")
    @app_commands.describe(
        opponent="The user to battle", 
        mode="Battle mode: auto (use battle team/equipped pets) or manual (specify pets)"
    )
    @app_commands.autocomplete(mode=petbattle_mode_autocomplete)
    async def petbattle(self, interaction: discord.Interaction, opponent: discord.Member, mode: str = "auto"):
        print(f"[DEBUG] /petbattle called by {interaction.user} vs {opponent.display_name} in {mode} mode")
        
        user_data = get_user(interaction.user.id)
        opp_data = get_user(opponent.id)
        
        # Check if both users have at least 1 pet
        user_pets = user_data.get("pets", [])
        opp_pets = opp_data.get("pets", [])
        
        if len(user_pets) < 1:
            await interaction.response.send_message(f"❌ You need at least 1 pet to participate in pet battles. You have {len(user_pets)} pets.", ephemeral=True)
            return
            
        if len(opp_pets) < 1:
            await interaction.response.send_message(f"❌ {opponent.display_name} needs at least 1 pet to participate in pet battles. They have {len(opp_pets)} pets.", ephemeral=True)
            return
        
        # Get battle pets based on mode
        if mode.lower() == "auto":
            # Use battle team for auto mode
            user_battle_pets = user_data.get("battle_team", [])
            opp_battle_pets = opp_data.get("battle_team", [])
            
            # If no battle team set, use equipped pets as fallback
            if len(user_battle_pets) < 1:
                user_battle_pets = user_data.get("equipped_pets", [])
                if len(user_battle_pets) < 1:
                    user_battle_pets = user_pets[:1]  # Use at least 1 pet
                    
            if len(opp_battle_pets) < 1:
                opp_battle_pets = opp_data.get("equipped_pets", [])
                if len(opp_battle_pets) < 1:
                    opp_battle_pets = opp_pets[:1]  # Use at least 1 pet
                    
        else:
            # Manual mode - would need to be implemented with pet selection
            await interaction.response.send_message("❌ Manual mode not implemented yet. Use 'auto' mode.", ephemeral=True)
            return
        
        # Validate battle pets
        for pet in user_battle_pets:
            if pet not in user_pets:
                await interaction.response.send_message(f"❌ You do not own '{pet}'.", ephemeral=True)
                return
                
        for pet in opp_battle_pets:
            if pet not in opp_pets:
                await interaction.response.send_message(f"❌ {opponent.display_name} does not own '{pet}'.", ephemeral=True)
                return
        
        # Start the battle
        embed = discord.Embed(
            title="🐾 Pet Battle",
            description=f"{interaction.user.display_name} vs {opponent.display_name}",
            color=0xff6b6b
        )
        
        # Show teams
        user_team = "\n".join([f"• {pet}" for pet in user_battle_pets])
        opp_team = "\n".join([f"• {pet}" for pet in opp_battle_pets])
        
        embed.add_field(name=f"{interaction.user.display_name}'s Team ({len(user_battle_pets)} pets)", value=user_team, inline=True)
        embed.add_field(name=f"{opponent.display_name}'s Team ({len(opp_battle_pets)} pets)", value=opp_team, inline=True)
        
        # Add warnings for smaller teams
        warnings = []
        if len(user_battle_pets) < 3:
            warnings.append(f"⚠️ {interaction.user.display_name} has fewer than 3 pets - this is a disadvantage!")
        if len(opp_battle_pets) < 3:
            warnings.append(f"⚠️ {opponent.display_name} has fewer than 3 pets - this is a disadvantage!")
        
        if warnings:
            embed.add_field(name="Battle Warnings", value="\n".join(warnings), inline=False)
        
        await interaction.response.send_message(embed=embed)
        
        # Simulate battle
        battle_log = []
        user_pets_hp = {}
        opp_pets_hp = {}
        
        # Initialize HP for all pets
        for pet in user_battle_pets:
            pet_obj = get_pet_by_name(pet)
            user_pets_hp[pet] = pet_obj["hp"] if pet_obj else 100
            
        for pet in opp_battle_pets:
            pet_obj = get_pet_by_name(pet)
            opp_pets_hp[pet] = pet_obj["hp"] if pet_obj else 100
        
        battle_log.append("🎯 Battle begins!")
        
        # Battle rounds
        round_num = 1
        while round_num <= 10:  # Max 10 rounds
            battle_log.append(f"\n**Round {round_num}**")
            
            # User pets attack
            for pet in user_battle_pets:
                if user_pets_hp[pet] > 0:
                    # Find alive opponent pet to attack
                    alive_opp_pets = [p for p in opp_battle_pets if opp_pets_hp[p] > 0]
                    if alive_opp_pets:
                        target = random.choice(alive_opp_pets)
                        pet_obj = get_pet_by_name(pet)
                        damage = random.randint(int(pet_obj["atk"] * 0.8), int(pet_obj["atk"] * 1.2)) if pet_obj else 10
                        opp_pets_hp[target] = max(0, opp_pets_hp[target] - damage)
                        battle_log.append(f"⚔️ {pet} attacks {target} for {damage} damage!")
            
            # Check if opponent is defeated
            if all(hp <= 0 for hp in opp_pets_hp.values()):
                battle_log.append(f"🏆 **{interaction.user.display_name} wins!**")
                break
                
            # Opponent pets attack
            for pet in opp_battle_pets:
                if opp_pets_hp[pet] > 0:
                    # Find alive user pet to attack
                    alive_user_pets = [p for p in user_battle_pets if user_pets_hp[p] > 0]
                    if alive_user_pets:
                        target = random.choice(alive_user_pets)
                        pet_obj = get_pet_by_name(pet)
                        damage = random.randint(int(pet_obj["atk"] * 0.8), int(pet_obj["atk"] * 1.2)) if pet_obj else 10
                        user_pets_hp[target] = max(0, user_pets_hp[target] - damage)
                        battle_log.append(f"⚔️ {pet} attacks {target} for {damage} damage!")
            
            # Check if user is defeated
            if all(hp <= 0 for hp in user_pets_hp.values()):
                battle_log.append(f"🏆 **{opponent.display_name} wins!**")
                break
                
            round_num += 1
        
        if round_num > 10:
            battle_log.append("⏰ **Battle ended in a draw!** (Max rounds reached)")
        
        # Create battle result embed
        result_embed = discord.Embed(
            title="🐾 Battle Results",
            description="\n".join(battle_log),
            color=0x00ff00 if all(hp <= 0 for hp in opp_pets_hp.values()) else 0xff0000
        )
        
        await interaction.followup.send(embed=result_embed)

    async def equippet_autocomplete(self, interaction: discord.Interaction, current: str):
        user_data = get_user(interaction.user.id)
        owned_pets = user_data.get("pets", [])
        return [
            app_commands.Choice(name=pet, value=pet)
            for pet in owned_pets if current.lower() in pet.lower()
        ][:25]  # Discord max autocomplete options

    @app_commands.command(name="equippet", description="Equip up to 2 pets to show on your profile")
    @app_commands.describe(pet="The name of the pet to equip")
    @app_commands.autocomplete(pet=equippet_autocomplete)
    async def equippet(self, interaction: discord.Interaction, pet: str):
        print(f"[DEBUG] /equippet called by {interaction.user} for pet: {pet}")
        user_data = get_user(interaction.user.id)
        owned_pets = user_data.get("pets", [])
        equipped_pets = user_data.get("equipped_pets", [])
        
        if pet not in owned_pets:
            await interaction.response.send_message(f"❌ You do not own '{pet}'.", ephemeral=True)
            return
        
        pet_obj = get_pet_by_name(pet)
        if not pet_obj:
            await interaction.response.send_message(f"❌ Pet '{pet}' not found in the global pet list. Please contact a mod.", ephemeral=True)
            return
        
        # Check if pet is already equipped
        if pet in equipped_pets:
            await interaction.response.send_message(f"❌ {pet} is already equipped!", ephemeral=True)
            return
        
        # Check if we have room for another pet
        if len(equipped_pets) >= 2:
            await interaction.response.send_message(f"❌ You already have 2 pets equipped. Use /unequippet to remove one first.", ephemeral=True)
            return
        
        # Add pet to equipped pets
        equipped_pets.append(pet)
        update_user(interaction.user.id, equipped_pets=equipped_pets)
        
        # Create embed showing all equipped pets
        embed = discord.Embed(title="🐾 Pet Equipped!", description="", color=0x00ff00)
        
        for i, equipped_pet in enumerate(equipped_pets, 1):
            equipped_pet_obj = get_pet_by_name(equipped_pet)
            embed.add_field(
                name=f"Slot {i}: {equipped_pet}",
                value=f"Rarity: {equipped_pet_obj['rarity']} | HP: {equipped_pet_obj['hp']} | ATK: {equipped_pet_obj['atk']}",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="unequippet", description="Unequip a pet from your equipped slots")
    @app_commands.describe(pet="The name of the pet to unequip (leave blank to see current pets)")
    async def unequippet(self, interaction: discord.Interaction, pet: str = None):
        print(f"[DEBUG] /unequippet called by {interaction.user} for pet: {pet}")
        user_data = get_user(interaction.user.id)
        equipped_pets = user_data.get("equipped_pets", [])
        
        if not equipped_pets:
            await interaction.response.send_message("You have no pets equipped.", ephemeral=True)
            return
        
        # If no pet specified, show current equipped pets
        if not pet:
            embed = discord.Embed(title="🐾 Currently Equipped Pets", description="", color=0x3498db)
            for i, equipped_pet in enumerate(equipped_pets, 1):
                pet_obj = get_pet_by_name(equipped_pet)
                embed.add_field(
                    name=f"Slot {i}: {equipped_pet}",
                    value=f"Rarity: {pet_obj['rarity']} | HP: {pet_obj['hp']} | ATK: {pet_obj['atk']}",
                    inline=False
                )
            embed.set_footer(text="Use /unequippet <pet_name> to unequip a specific pet")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Check if pet is equipped
        if pet not in equipped_pets:
            await interaction.response.send_message(f"❌ {pet} is not equipped.", ephemeral=True)
            return
        
        # Remove pet from equipped pets
        equipped_pets.remove(pet)
        update_user(interaction.user.id, equipped_pets=equipped_pets)
        
        embed = discord.Embed(description=f"🐾 Unequipped **{pet}**.", color=0x95a5a6)
        await interaction.response.send_message(embed=embed, ephemeral=True)

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
            
            # If equipped, remove from equipped pets
            equipped_pets = user_data.get("equipped_pets", [])
            if pet in equipped_pets:
                equipped_pets.remove(pet)
            
            update_user(interaction.user.id, pets=user_data["pets"], equipped_pets=equipped_pets)
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

    @app_commands.command(name="equippedpets", description="View and manage your equipped pets (up to 2 slots)")
    async def equippedpets(self, interaction: discord.Interaction):
        print(f"[DEBUG] /equippedpets called by {interaction.user}")
        user_data = get_user(interaction.user.id)
        owned_pets = user_data.get("pets", [])
        equipped_pets = user_data.get("equipped_pets", [])
        
        if not owned_pets:
            await interaction.response.send_message("You have no pets yet. Use /adoptpet to get your first pet!", ephemeral=True)
            return
        
        # Show current equipped pets
        embed = discord.Embed(title="🐾 Equipped Pets", description="", color=0x3498db)
        
        if equipped_pets:
            for i, pet_name in enumerate(equipped_pets, 1):
                pet_obj = get_pet_by_name(pet_name)
                if pet_obj:
                    embed.add_field(
                        name=f"Slot {i}: {pet_name}",
                        value=f"Rarity: {pet_obj['rarity']} | HP: {pet_obj['hp']} | ATK: {pet_obj['atk']}",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name=f"Slot {i}: {pet_name}",
                        value="Unknown pet data",
                        inline=False
                    )
        else:
            embed.add_field(name="No Pets Equipped", value="Use /equippet to equip pets!", inline=False)
        
        embed.add_field(
            name="Available Slots", 
            value=f"{len(equipped_pets)}/2 slots used", 
            inline=False
        )
        
        # Add dropdown to manage pets
        view = PetSelect(interaction.user.id, owned_pets)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="petbattleteam", description="Set up your pet battle team (1-3 pets for battles)")
    async def petbattleteam(self, interaction: discord.Interaction):
        print(f"[DEBUG] /petbattleteam called by {interaction.user}")
        user_data = get_user(interaction.user.id)
        owned_pets = user_data.get("pets", [])
        
        if len(owned_pets) < 1:
            await interaction.response.send_message(f"❌ You need at least 1 pet to create a battle team. You have {len(owned_pets)} pets.", ephemeral=True)
            return
        
        # Create a view with a select menu for 1-3 pets
        class BattleTeamSelect(ui.View):
            def __init__(self, user_id, owned_pets):
                super().__init__(timeout=60)
                self.user_id = user_id
                self.owned_pets = owned_pets
                # Build select options for 1-3 pets
                options = [discord.SelectOption(label=pet, value=pet) for pet in owned_pets]
                # Add the select menu - allow 1-3 selections
                max_selections = min(3, len(owned_pets))
                select = ui.Select(placeholder=f"Choose 1-{max_selections} pets for your battle team", min_values=1, max_values=max_selections, options=options)
                select.callback = self.select_callback
                self.add_item(select)
            
            async def select_callback(self, interaction2):
                selected_pets = interaction2.data["values"]
                
                # Validate pets
                for pet in selected_pets:
                    pet_obj = get_pet_by_name(pet)
                    if not pet_obj:
                        try:
                            await interaction2.response.send_message(f"❌ Pet '{pet}' not found in the global pet list. Please contact a mod.", ephemeral=True)
                        except discord.NotFound:
                            await interaction2.followup.send(f"❌ Pet '{pet}' not found in the global pet list. Please contact a mod.", ephemeral=True)
                        return
                
                # Save battle team
                update_user(self.user_id, battle_team=selected_pets)
                
                # Create embed showing battle team
                embed = discord.Embed(title="⚔️ Battle Team Set!", description="Your pet battle team:", color=0xff6b6b)
                
                for i, pet in enumerate(selected_pets, 1):
                    pet_obj = get_pet_by_name(pet)
                    embed.add_field(
                        name=f"Slot {i}: {pet}",
                        value=f"Rarity: {pet_obj['rarity']} | HP: {pet_obj['hp']} | ATK: {pet_obj['atk']}",
                        inline=False
                    )
                
                # Warning message for fewer pets
                if len(selected_pets) < 3:
                    embed.add_field(
                        name="⚠️ Warning",
                        value=f"You have set {len(selected_pets)} pet(s) in your battle team. Having fewer than 3 pets puts you at a disadvantage in 3v3 battles!",
                        inline=False
                    )
                    embed.color = 0xffa500  # Orange for warning
                
                embed.set_footer(text="Use /petbattle to challenge other players!")
                
                try:
                    await interaction2.response.send_message(embed=embed, ephemeral=True)
                except discord.NotFound:
                    await interaction2.followup.send(embed=embed, ephemeral=True)
                
                self.stop()
        
        # Show current battle team if exists
        current_team = user_data.get("battle_team", [])
        embed = discord.Embed(title="⚔️ Pet Battle Team", description="", color=0x3498db)
        
        if current_team:
            embed.add_field(name="Current Battle Team", value="", inline=False)
            for i, pet in enumerate(current_team, 1):
                pet_obj = get_pet_by_name(pet)
                if pet_obj:
                    embed.add_field(
                        name=f"Slot {i}: {pet}",
                        value=f"Rarity: {pet_obj['rarity']} | HP: {pet_obj['hp']} | ATK: {pet_obj['atk']}",
                        inline=False
                    )
            
            # Show warning if current team has fewer than 3 pets
            if len(current_team) < 3:
                embed.add_field(
                    name="⚠️ Current Team Status",
                    value=f"Your current team has {len(current_team)} pet(s). Consider adding more pets for better battle performance!",
                    inline=False
                )
        else:
            embed.add_field(name="No Battle Team Set", value=f"Select 1-{min(3, len(owned_pets))} pets below to create your battle team!", inline=False)
        
        # Add dropdown to select battle team
        view = BattleTeamSelect(interaction.user.id, owned_pets)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="adoptpet10x", description="Adopt 10 random pets at once (5% discount)")
    async def adoptpet10x(self, interaction: discord.Interaction):
        print(f"[DEBUG] /adoptpet10x called by {interaction.user}")
        user_data = get_user(interaction.user.id)
        
        # Calculate cost with 5% discount
        base_cost = PET_ADOPT_COST * 10  # 10 pets at 250 each = 2,500
        discounted_cost = int(base_cost * 0.95)  # 5% discount = 2,375
        
        if user_data.get("credits", 0) < discounted_cost:
            await interaction.response.send_message(f"❌ You need {discounted_cost} credits for 10x pet adoption. You have {user_data.get('credits', 0)} credits.", ephemeral=True)
            return
        
        # Deduct credits
        update_user(interaction.user.id, credits=user_data.get("credits", 0) - discounted_cost)
        
        # Get 10 random pets
        adopted_pets = []
        for _ in range(10):
            pet = random.choice(PETS)
            adopted_pets.append(pet["name"])
        
        # Add pets to user's collection
        user_pets = user_data.get("pets", [])
        user_pets.extend(adopted_pets)
        update_user(interaction.user.id, pets=user_pets)
        
        # Create embed
        embed = discord.Embed(
            title="🐾 10x Pet Adoption Complete!",
            description=f"You adopted 10 pets for {discounted_cost} credits (5% discount applied)",
            color=0x2ecc71
        )
        
        # Group pets by rarity for display
        rarity_counts = {}
        for pet_name in adopted_pets:
            pet = get_pet_by_name(pet_name)
            if pet:
                rarity = pet["rarity"]
                rarity_counts[rarity] = rarity_counts.get(rarity, 0) + 1
        
        # Display pets by rarity
        for rarity in ["Common", "Uncommon", "Rare", "Epic", "Legendary", "Mythic"]:
            if rarity in rarity_counts:
                embed.add_field(
                    name=f"{rarity} ({rarity_counts[rarity]})",
                    value=", ".join([pet for pet in adopted_pets if get_pet_by_name(pet) and get_pet_by_name(pet).get("rarity") == rarity]),
                    inline=False
                )
        
        embed.set_footer(text=f"Total pets owned: {len(user_pets)}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="premiumpets10x", description="Adopt 10 premium pets at once (5% discount)")
    async def premiumpets10x(self, interaction: discord.Interaction):
        print(f"[DEBUG] /premiumpets10x called by {interaction.user}")
        user_data = get_user(interaction.user.id)
        
        # Calculate cost with 5% discount
        base_cost = PREMIUM_PET_COST * 10  # 10 premium pets at 1000 each = 10,000
        discounted_cost = int(base_cost * 0.95)  # 5% discount = 9,500
        
        if user_data.get("credits", 0) < discounted_cost:
            await interaction.response.send_message(f"❌ You need {discounted_cost} credits for 10x premium pet adoption. You have {user_data.get('credits', 0)} credits.", ephemeral=True)
            return
        
        # Deduct credits
        update_user(interaction.user.id, credits=user_data.get("credits", 0) - discounted_cost)
        
        # Get 10 random premium pets
        adopted_pets = []
        for _ in range(10):
            pet = random.choice(PETS)
            adopted_pets.append(pet["name"])
        
        # Add pets to user's collection
        user_pets = user_data.get("pets", [])
        user_pets.extend(adopted_pets)
        update_user(interaction.user.id, pets=user_pets)
        
        # Create embed
        embed = discord.Embed(
            title="🌟 10x Premium Pet Adoption Complete!",
            description=f"You adopted 10 premium pets for {discounted_cost} credits (5% discount applied)",
            color=0xf39c12
        )
        
        # Group pets by rarity for display
        rarity_counts = {}
        for pet_name in adopted_pets:
            pet = get_pet_by_name(pet_name)
            if pet:
                rarity = pet["rarity"]
                rarity_counts[rarity] = rarity_counts.get(rarity, 0) + 1
        
        # Display pets by rarity
        for rarity in ["Common", "Uncommon", "Rare", "Epic", "Legendary", "Mythic", "Classified"]:
            if rarity in rarity_counts:
                embed.add_field(
                    name=f"{rarity} ({rarity_counts[rarity]})",
                    value=", ".join([pet for pet in adopted_pets if get_pet_by_name(pet) and get_pet_by_name(pet).get("rarity") == rarity]),
                    inline=False
                )
        
        embed.set_footer(text=f"Total pets owned: {len(user_pets)}")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Pets(bot)) 