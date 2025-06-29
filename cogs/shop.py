from discord.ext import commands, tasks
import discord
from discord import app_commands

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

# Expanded shop items: utility, guns, and more
SHOP_ITEMS = [
    {"name": "Stun Baton", "price": 100, "desc": "Basic containment tool. Deals light damage and can stun."},
    {"name": "Containment Suit", "price": 200, "desc": "Protection from SCPs. Reduces damage taken."},
    {"name": "Keycard Level 1", "price": 50, "desc": "Basic access card. Required for some vault events."},
    {"name": "Keycard Level 2", "price": 150, "desc": "Access to restricted areas. Required for some missions and vaults."},
    {"name": "Keycard Level 3", "price": 300, "desc": "Advanced access card. Reserved for future content/events."},
    {"name": "Keycard Level 05", "price": 5000, "desc": "Grants access to the most classified Foundation personnel files."},
    {"name": "SCP Plushie", "price": 75, "desc": "A cute collectible!"},
    {"name": "Medkit", "price": 120, "desc": "Heals you or a teammate during missions."},
    {"name": "Flashbang", "price": 90, "desc": "Temporarily blinds enemies in missions or battles."},
    {"name": "Radio", "price": 60, "desc": "Communicate with your team during missions."},
    {"name": "Night Vision Goggles", "price": 180, "desc": "See in the dark during certain missions."},
    {"name": "Pistol", "price": 250, "desc": "Basic firearm. Increases your attack in battles."},
    {"name": "SMG", "price": 400, "desc": "Faster firing gun. Higher attack bonus in battles."},
    {"name": "Shotgun", "price": 500, "desc": "High damage at close range. Useful in some missions."},
    {"name": "Rifle", "price": 700, "desc": "Long-range firearm. High attack bonus in battles."},
    {"name": "Tactical Vest", "price": 220, "desc": "Extra protection. Reduces damage in battles."},
    {"name": "Adrenaline Shot", "price": 130, "desc": "Boosts your speed for one mission or battle."},
    {"name": "EMP Grenade", "price": 300, "desc": "Disables electronics and robotic enemies."},
    {"name": "SCP-500 Pill", "price": 1000, "desc": "Legendary healing item. Cures any status effect."},
    {"name": "SCP-914 Token", "price": 350, "desc": "Use at SCP-914 for a random upgrade or effect."},
    {"name": "Binoculars", "price": 80, "desc": "Scout ahead during missions."},
    {"name": "Lockpick Set", "price": 110, "desc": "Open locked doors in missions."},
    {"name": "Double XP (1h)", "price": 500, "desc": "Doubles your XP gain for 1 hour."},
    {"name": "Double Credits (1h)", "price": 500, "desc": "Doubles your credit gain for 1 hour."},
    {"name": "VIP Badge", "price": 35000, "desc": "A special badge for your profile."},
    {"name": "Containment Specialist Title", "price": 50000, "desc": "A prestigious title for your profile."},
]

SHOP_CATEGORIES = {
    "Weapons": [
        "Stun Baton", "Pistol", "SMG", "Shotgun", "Rifle"
    ],
    "Gear": [
        "Containment Suit", "Tactical Vest", "Night Vision Goggles", "Radio", "Binoculars", "Lockpick Set"
    ],
    "Consumables": [
        "Medkit", "Flashbang", "Adrenaline Shot", "EMP Grenade", "SCP-500 Pill"
    ],
    "Special": [
        "SCP Plushie", "Keycard Level 2", "Keycard Level 3", "SCP-914 Token"
    ]
}

MARKETPLACE_FILE = "marketplace.json"
TRADE_FILE = "trades.json"

def load_marketplace():
    if not os.path.exists(MARKETPLACE_FILE):
        return []
    with open(MARKETPLACE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_marketplace(data):
    with open(MARKETPLACE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def load_trades():
    if not os.path.exists(TRADE_FILE):
        return []
    with open(TRADE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_trades(data):
    with open(TRADE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="shop", description="View the SCP shop")
    async def shop(self, interaction: discord.Interaction):
        print(f"[DEBUG] /shop called by {interaction.user}")
        embed = discord.Embed(
            title="🛒 SCP Foundation Shop",
            description="Welcome to the Foundation Shop! Browse our selection of weapons, gear, consumables, and special items.",
            color=config.EMBED_COLORS["info"]
        )
        for category, names in SHOP_CATEGORIES.items():
            items = [item for item in SHOP_ITEMS if item["name"] in names]
            value = "\n".join([
                f"**{i['name']}** - {i['price']} credits\n{i['desc']}" for i in items
            ])
            embed.add_field(name=f"__{category}__", value=value or "No items", inline=False)
        embed.set_footer(text="Use /buy <item name> to purchase. | All sales are final.")
        await interaction.response.send_message(embed=embed)

    async def buy_autocomplete(self, interaction: discord.Interaction, current: str):
        return [app_commands.Choice(name=item["name"], value=item["name"]) for item in SHOP_ITEMS if current.lower() in item["name"].lower()][:25]

    @app_commands.command(name="buy", description="Buy an item from the shop by number or name")
    @app_commands.describe(item="The item number or name to buy")
    @app_commands.autocomplete(item=buy_autocomplete)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def buy(self, interaction: discord.Interaction, item: str):
        print(f"[DEBUG] /buy called by {interaction.user} for item: {item}")
        user_data = get_user(interaction.user.id)
        # Try to buy by number first
        item_obj = None
        if item.isdigit():
            idx = int(item) - 1
            if 0 <= idx < len(SHOP_ITEMS):
                item_obj = SHOP_ITEMS[idx]
        else:
            item_obj = next((i for i in SHOP_ITEMS if i["name"].lower() == item.lower()), None)
        if not item_obj:
            embed = discord.Embed(description=f"❌ Item '{item}' not found in the shop.\nUsage: /buy item:<item name>", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        if user_data.get("credits", 0) < item_obj["price"]:
            embed = discord.Embed(description=f"❌ You don't have enough credits to buy {item_obj['name']}.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        user_data["credits"] -= item_obj["price"]
        # Handle boosts and cosmetics
        if item_obj["name"] == "Double XP (1h)":
            user_data["xp_boost"] = time.time() + 3600
            msg = "✅ Double XP boost activated for 1 hour!"
        elif item_obj["name"] == "Double Credits (1h)":
            user_data["credit_boost"] = time.time() + 3600
            msg = "✅ Double Credits boost activated for 1 hour!"
        elif item_obj["name"] == "VIP Badge":
            badges = user_data.get("badges", [])
            if "VIP" not in badges:
                badges.append("VIP")
            user_data["badges"] = badges
            msg = "✅ VIP Badge added to your profile!"
        elif item_obj["name"] == "Containment Specialist Title":
            user_data["title"] = "Containment Specialist"
            msg = "✅ Title 'Containment Specialist' added to your profile!"
        else:
            user_data["inventory"].append(item_obj["name"])
            msg = f"✅ You bought **{item_obj['name']}** for {item_obj['price']} credits!"
        update_user(interaction.user.id, **user_data)
        embed = discord.Embed(description=msg, color=discord.Color.green())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="inventory", description="View your inventory")
    async def inventory(self, interaction: discord.Interaction):
        print(f"[DEBUG] /inventory called by {interaction.user}")
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

    @app_commands.command(name="upgrade", description="Upgrade an item in your inventory")
    @app_commands.describe(item="The item to upgrade")
    async def upgrade(self, interaction: discord.Interaction, item: str):
        print(f"[DEBUG] /upgrade called by {interaction.user} for item: {item}")
        user_data = get_user(interaction.user.id)
        upgrades = {"Stun Baton": ("Enhanced Stun Baton", 100)}
        item_name = next((i for i in upgrades if i.lower() == item.lower()), None)
        if not item_name:
            embed = discord.Embed(description=f"❌ '{item}' cannot be upgraded.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        if item_name not in user_data["inventory"]:
            embed = discord.Embed(description=f"❌ You do not own a '{item_name}' in your inventory.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        new_name, cost = upgrades[item_name]
        if user_data["credits"] < cost:
            embed = discord.Embed(description=f"❌ You need {cost} credits to upgrade '{item_name}'.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        user_data["credits"] -= cost
        user_data["inventory"].remove(item_name)
        user_data["inventory"].append(new_name)
        update_user(interaction.user.id, credits=user_data["credits"], inventory=user_data["inventory"])
        embed = discord.Embed(description=f"✅ Upgraded **{item_name}** to **{new_name}** for {cost} credits!", color=discord.Color.green())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="removeitem", description="Remove an item from your inventory by name")
    @app_commands.describe(item="The name of the item to remove")
    async def removeitem(self, interaction: discord.Interaction, item: str):
        print(f"[DEBUG] /removeitem called by {interaction.user} for item: {item}")
        user_data = get_user(interaction.user.id)
        if item not in user_data["inventory"]:
            embed = discord.Embed(description=f"❌ You do not have '{item}' in your inventory.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        user_data["inventory"].remove(item)
        update_user(interaction.user.id, inventory=user_data["inventory"])
        embed = discord.Embed(description=f"✅ Removed **{item}** from your inventory.", color=discord.Color.green())
        await interaction.response.send_message(embed=embed)

    async def market_item_autocomplete(self, interaction: discord.Interaction, current: str):
        user_data = get_user(interaction.user.id)
        return [app_commands.Choice(name=i, value=i) for i in user_data["inventory"] if current.lower() in i.lower()][:25]

    @app_commands.command(name="marketplace_list", description="List an item from your inventory for sale on the marketplace.")
    @app_commands.describe(item="The name of the item to list", price="Sale price in credits")
    @app_commands.autocomplete(item=market_item_autocomplete)
    async def marketplace_list(self, interaction: discord.Interaction, item: str, price: int):
        user_data = get_user(interaction.user.id)
        if item not in user_data["inventory"]:
            await interaction.response.send_message(f"❌ You do not have '{item}' in your inventory.", ephemeral=True)
            return
        if price <= 0:
            await interaction.response.send_message("❌ Price must be positive.", ephemeral=True)
            return
        # Remove item from inventory and add to marketplace
        user_data["inventory"].remove(item)
        update_user(interaction.user.id, inventory=user_data["inventory"])
        listings = load_marketplace()
        listing_id = int(time.time() * 1000)
        listings.append({
            "id": listing_id,
            "seller_id": interaction.user.id,
            "item": item,
            "price": price,
            "timestamp": time.time()
        })
        save_marketplace(listings)
        await interaction.response.send_message(f"✅ Listed '{item}' for {price} credits on the marketplace! (Listing ID: {listing_id})", ephemeral=True)

    @app_commands.command(name="marketplace_browse", description="Browse all items for sale on the marketplace.")
    async def marketplace_browse(self, interaction: discord.Interaction):
        listings = load_marketplace()
        if not listings:
            await interaction.response.send_message("No items are currently listed on the marketplace.", ephemeral=True)
            return
        embed = discord.Embed(title="🛒 Marketplace Listings", color=discord.Color.blurple())
        for l in listings:
            seller = interaction.guild.get_member(l["seller_id"]) if interaction.guild else None
            seller_name = seller.display_name if seller else f"User {l['seller_id']}"
            embed.add_field(
                name=f"ID: {l['id']} | {l['item']}",
                value=f"Price: {l['price']} credits\nSeller: {seller_name}",
                inline=False
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="marketplace_buy", description="Buy an item from the marketplace by listing ID.")
    @app_commands.describe(listing_id="The ID of the listing to buy")
    async def marketplace_buy(self, interaction: discord.Interaction, listing_id: int):
        listings = load_marketplace()
        listing = next((l for l in listings if l["id"] == listing_id), None)
        if not listing:
            await interaction.response.send_message(f"❌ Listing ID {listing_id} not found.", ephemeral=True)
            return
        if listing["seller_id"] == interaction.user.id:
            await interaction.response.send_message("❌ You cannot buy your own listing.", ephemeral=True)
            return
        buyer_data = get_user(interaction.user.id)
        if buyer_data.get("credits", 0) < listing["price"]:
            await interaction.response.send_message("❌ You do not have enough credits to buy this item.", ephemeral=True)
            return
        # Transfer credits and item
        seller_data = get_user(listing["seller_id"])
        buyer_data["credits"] -= listing["price"]
        buyer_data["inventory"].append(listing["item"])
        seller_data["credits"] = seller_data.get("credits", 0) + listing["price"]
        update_user(interaction.user.id, credits=buyer_data["credits"], inventory=buyer_data["inventory"])
        update_user(listing["seller_id"], credits=seller_data["credits"])
        # Remove listing
        listings = [l for l in listings if l["id"] != listing_id]
        save_marketplace(listings)
        await interaction.response.send_message(f"✅ You bought '{listing['item']}' from <@{listing['seller_id']}> for {listing['price']} credits!", ephemeral=True)

    @app_commands.command(name="marketplace_retrieve", description="Retrieve your item from the marketplace by listing ID.")
    @app_commands.describe(listing_id="The ID of the listing to retrieve")
    async def marketplace_retrieve(self, interaction: discord.Interaction, listing_id: int):
        listings = load_marketplace()
        listing = next((l for l in listings if l["id"] == listing_id), None)
        if not listing:
            await interaction.response.send_message(f"❌ Listing ID {listing_id} not found.", ephemeral=True)
            return
        if listing["seller_id"] != interaction.user.id:
            await interaction.response.send_message("❌ Only the seller can retrieve this item.", ephemeral=True)
            return
        # Return item to seller
        user_data = get_user(interaction.user.id)
        user_data["inventory"].append(listing["item"])
        update_user(interaction.user.id, inventory=user_data["inventory"])
        # Remove listing
        listings = [l for l in listings if l["id"] != listing_id]
        save_marketplace(listings)
        await interaction.response.send_message(f"✅ Retrieved '{listing['item']}' from the marketplace and returned it to your inventory.", ephemeral=True)

    async def trade_item_autocomplete(self, interaction: discord.Interaction, current: str):
        user_data = get_user(interaction.user.id)
        return [app_commands.Choice(name=i, value=i) for i in user_data["inventory"] if current.lower() in i.lower()][:25]

    async def trade_pet_autocomplete(self, interaction: discord.Interaction, current: str):
        user_data = get_user(interaction.user.id)
        return [app_commands.Choice(name=p, value=p) for p in user_data.get("pets", []) if current.lower() in p.lower()][:25]

    @app_commands.command(name="trade", description="Propose a trade to another user (items, pets, or credits)")
    @app_commands.describe(user="The user to trade with", offer_item="Item from your inventory to offer", offer_pet="Pet from your collection to offer", request_item="Item you want in return", request_pet="Pet you want in return", request_credits="Credits you want in return")
    @app_commands.autocomplete(offer_item=trade_item_autocomplete, offer_pet=trade_pet_autocomplete, request_item=trade_item_autocomplete, request_pet=trade_pet_autocomplete)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def trade(self, interaction: discord.Interaction, user: discord.Member, offer_item: str = None, offer_pet: str = None, request_item: str = None, request_pet: str = None, request_credits: int = 0):
        if user.id == interaction.user.id:
            await interaction.response.send_message("❌ You cannot trade with yourself.", ephemeral=True)
            return
        user_data = get_user(interaction.user.id)
        target_data = get_user(user.id)
        # Check offer item
        if offer_item and offer_item not in user_data["inventory"]:
            await interaction.response.send_message(f"❌ You do not have '{offer_item}' in your inventory.", ephemeral=True)
            return
        # Check offer pet
        if offer_pet and offer_pet not in user_data.get("pets", []):
            await interaction.response.send_message(f"❌ You do not own the pet '{offer_pet}'.", ephemeral=True)
            return
        # Check request item
        if request_item and request_item not in target_data["inventory"]:
            await interaction.response.send_message(f"❌ {user.display_name} does not have '{request_item}' in their inventory.", ephemeral=True)
            return
        # Check request pet
        if request_pet and request_pet not in target_data.get("pets", []):
            await interaction.response.send_message(f"❌ {user.display_name} does not own the pet '{request_pet}'.", ephemeral=True)
            return
        # Check request credits
        if request_credits and target_data.get("credits", 0) < request_credits:
            await interaction.response.send_message(f"❌ {user.display_name} does not have enough credits.", ephemeral=True)
            return
        # Store pending trade
        trades = load_trades()
        trade_id = int(time.time() * 1000)
        trade = {
            "id": trade_id,
            "from_id": interaction.user.id,
            "to_id": user.id,
            "offer_item": offer_item,
            "offer_pet": offer_pet,
            "request_item": request_item,
            "request_pet": request_pet,
            "request_credits": request_credits,
            "status": "pending"
        }
        trades.append(trade)
        save_trades(trades)
        # Notify initiator only (ephemeral)
        await interaction.response.send_message(f"✅ Trade proposed to {user.display_name}! (Trade ID: {trade_id})\nThey must confirm with `/confirmtrade trade_id:{trade_id}`.", ephemeral=True)
        # DM the recipient
        try:
            trade_details = f"{interaction.user.display_name} has proposed a trade with you!\n"
            if offer_item:
                trade_details += f"• They offer item: {offer_item}\n"
            if offer_pet:
                trade_details += f"• They offer pet: {offer_pet}\n"
            if request_item:
                trade_details += f"• They want item: {request_item}\n"
            if request_pet:
                trade_details += f"• They want pet: {request_pet}\n"
            if request_credits:
                trade_details += f"• They want credits: {request_credits}\n"
            trade_details += f"\nTo accept, use `/confirmtrade trade_id:{trade_id}` in the server."
            await user.send(trade_details)
        except Exception:
            await interaction.followup.send(f"Could not DM {user.display_name}. They may have DMs disabled.", ephemeral=True)

    @app_commands.command(name="confirmtrade", description="Confirm and execute a pending trade by trade ID.")
    @app_commands.describe(trade_id="The ID of the trade to confirm")
    async def confirmtrade(self, interaction: discord.Interaction, trade_id: int):
        trades = load_trades()
        trade = next((t for t in trades if t["id"] == trade_id), None)
        if not trade:
            await interaction.response.send_message(f"❌ Trade ID {trade_id} not found.", ephemeral=True)
            return
        if trade["to_id"] != interaction.user.id:
            await interaction.response.send_message("❌ Only the recipient can confirm this trade.", ephemeral=True)
            return
        # Check both users still have the required items/pets/credits
        from_data = get_user(trade["from_id"])
        to_data = get_user(trade["to_id"])
        # Offer checks
        if trade["offer_item"] and trade["offer_item"] not in from_data["inventory"]:
            await interaction.response.send_message(f"❌ The offerer no longer has '{trade['offer_item']}'.", ephemeral=True)
            return
        if trade["offer_pet"] and trade["offer_pet"] not in from_data.get("pets", []):
            await interaction.response.send_message(f"❌ The offerer no longer owns the pet '{trade['offer_pet']}'.", ephemeral=True)
            return
        # Request checks
        if trade["request_item"] and trade["request_item"] not in to_data["inventory"]:
            await interaction.response.send_message(f"❌ You no longer have '{trade['request_item']}'.", ephemeral=True)
            return
        if trade["request_pet"] and trade["request_pet"] not in to_data.get("pets", []):
            await interaction.response.send_message(f"❌ You no longer own the pet '{trade['request_pet']}'.", ephemeral=True)
            return
        if trade["request_credits"] and to_data.get("credits", 0) < trade["request_credits"]:
            await interaction.response.send_message(f"❌ You do not have enough credits.", ephemeral=True)
            return
        # Execute trade
        # Transfer offer item
        if trade["offer_item"]:
            from_data["inventory"].remove(trade["offer_item"])
            to_data["inventory"].append(trade["offer_item"])
        # Transfer offer pet
        if trade["offer_pet"]:
            from_data["pets"].remove(trade["offer_pet"])
            to_data.setdefault("pets", []).append(trade["offer_pet"])
        # Transfer request item
        if trade["request_item"]:
            to_data["inventory"].remove(trade["request_item"])
            from_data["inventory"].append(trade["request_item"])
        # Transfer request pet
        if trade["request_pet"]:
            to_data["pets"].remove(trade["request_pet"])
            from_data.setdefault("pets", []).append(trade["request_pet"])
        # Transfer credits
        if trade["request_credits"]:
            to_data["credits"] -= trade["request_credits"]
            from_data["credits"] = from_data.get("credits", 0) + trade["request_credits"]
        update_user(trade["from_id"], **from_data)
        update_user(trade["to_id"], **to_data)
        # Remove trade
        trades = [t for t in trades if t["id"] != trade_id]
        save_trades(trades)
        await interaction.response.send_message(f"✅ Trade completed between <@{trade['from_id']}> and <@{trade['to_id']}>! Items, pets, and credits have been exchanged.", ephemeral=False)
        # Optionally notify the offerer
        try:
            offerer = interaction.guild.get_member(trade["from_id"])
            if offerer:
                await offerer.send(f"Your trade with {interaction.user.display_name} has been completed!")
        except Exception:
            pass

    @app_commands.command(name="canceltrade", description="Cancel a pending trade you initiated by trade ID.")
    @app_commands.describe(trade_id="The ID of the trade to cancel")
    async def canceltrade(self, interaction: discord.Interaction, trade_id: int):
        trades = load_trades()
        trade = next((t for t in trades if t["id"] == trade_id), None)
        if not trade:
            await interaction.response.send_message(f"❌ Trade ID {trade_id} not found.", ephemeral=True)
            return
        if trade["from_id"] != interaction.user.id:
            await interaction.response.send_message("❌ Only the trade initiator can cancel this trade.", ephemeral=True)
            return
        # Return offered item/pet to initiator if not already traded
        from_data = get_user(trade["from_id"])
        if trade["offer_item"]:
            from_data["inventory"].append(trade["offer_item"])
        if trade["offer_pet"]:
            from_data.setdefault("pets", []).append(trade["offer_pet"])
        update_user(trade["from_id"], **from_data)
        # Remove trade
        trades = [t for t in trades if t["id"] != trade_id]
        save_trades(trades)
        await interaction.response.send_message(f"✅ Trade cancelled and your offered items/pets have been returned.", ephemeral=True)

    @app_commands.command(name="equipgun", description="Equip a gun from your inventory.")
    @app_commands.describe(gun="The name of the gun to equip")
    async def equipgun(self, interaction: discord.Interaction, gun: str):
        user_data = get_user(interaction.user.id)
        # List of guns (should match your shop's gun names)
        gun_names = ["Pistol", "SMG", "Shotgun", "Rifle"]
        if gun not in user_data["inventory"] or gun not in gun_names:
            await interaction.response.send_message(f"❌ You do not have '{gun}' in your inventory or it is not a valid gun.", ephemeral=True)
            return
        user_data["equipped_gun"] = gun
        update_user(interaction.user.id, equipped_gun=gun)
        await interaction.response.send_message(f"✅ You have equipped '{gun}'.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Shop(bot))
