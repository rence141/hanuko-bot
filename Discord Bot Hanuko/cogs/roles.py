import discord
from discord.ext import commands
from discord import app_commands, Colour
import json
import os

ROLES_FILE = "custom_roles.json"

# Common color names mapping
COLOR_NAMES = {
    "red": 0xFF0000,
    "green": 0x00FF00,
    "blue": 0x0000FF,
    "yellow": 0xFFFF00,
    "purple": 0x800080,
    "orange": 0xFFA500,
    "pink": 0xFFC0CB,
    "cyan": 0x00FFFF,
    "teal": 0x008080,
    "magenta": 0xFF00FF,
    "black": 0x000000,
    "white": 0xFFFFFF,
    "grey": 0x808080,
    "gray": 0x808080,
    "brown": 0xA52A2A,
}

def load_roles():
    if not os.path.exists(ROLES_FILE):
        return {}
    with open(ROLES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_roles(data):
    with open(ROLES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("[DEBUG] Roles cog loaded.")

    async def cog_load(self):
        print("[DEBUG] Roles cog commands registered:", [cmd.name for cmd in self.bot.tree.get_commands()])

    @app_commands.command(name="addcustomrole", description="Add a custom role to the assignable list (admin only)")
    @app_commands.describe(role_name="The name of the role to add", color="Optional color for the role (hex or name)")
    @app_commands.checks.has_permissions(administrator=True)
    async def addcustomrole(self, interaction: discord.Interaction, role_name: str, color: str = None):
        data = load_roles()
        guild_id = str(interaction.guild.id)
        allowed = data.get(guild_id, [])
        if role_name in allowed:
            await interaction.response.send_message(f"Role '{role_name}' is already assignable.", ephemeral=True)
            return
        # Parse color
        role_color = None
        if color:
            color = color.strip().lower()
            if color.startswith('#'):
                try:
                    role_color = Colour(int(color[1:], 16))
                except Exception:
                    await interaction.response.send_message(f"Invalid hex color code.", ephemeral=True)
                    return
            elif color in COLOR_NAMES:
                role_color = Colour(COLOR_NAMES[color])
            else:
                await interaction.response.send_message(f"Unknown color name. Use a hex code like #ff0000 or a common name like red, blue, green.", ephemeral=True)
                return
        # Create the role if it doesn't exist
        guild = interaction.guild
        role = discord.utils.get(guild.roles, name=role_name)
        if not role:
            try:
                role = await guild.create_role(name=role_name, reason="Custom role via bot", color=role_color or discord.Color.default())
            except Exception as e:
                await interaction.response.send_message(f"Failed to create role: {e}", ephemeral=True)
                return
        allowed.append(role_name)
        data[guild_id] = allowed
        save_roles(data)
        await interaction.response.send_message(f"Role '{role_name}' added to assignable roles{f' with color {color}' if color else ''}.", ephemeral=True)

    @app_commands.command(name="removecustomrole", description="Remove a custom role from the assignable list (admin only)")
    @app_commands.describe(role_name="The name of the role to remove")
    @app_commands.checks.has_permissions(administrator=True)
    async def removecustomrole(self, interaction: discord.Interaction, role_name: str):
        data = load_roles()
        guild_id = str(interaction.guild.id)
        allowed = data.get(guild_id, [])
        if role_name not in allowed:
            await interaction.response.send_message(f"Role '{role_name}' is not in the assignable list.", ephemeral=True)
            return
        allowed.remove(role_name)
        data[guild_id] = allowed
        save_roles(data)
        await interaction.response.send_message(f"Role '{role_name}' removed from assignable roles.", ephemeral=True)

    @app_commands.command(name="setrole", description="Assign yourself a custom role from the allowed list")
    @app_commands.describe(role_name="The name of the role to assign to yourself")
    async def setrole(self, interaction: discord.Interaction, role_name: str):
        data = load_roles()
        guild_id = str(interaction.guild.id)
        allowed = data.get(guild_id, [])
        if role_name not in allowed:
            await interaction.response.send_message(f"Role '{role_name}' is not assignable. Ask an admin to add it.", ephemeral=True)
            return
        # Find the role
        guild = interaction.guild
        role = discord.utils.get(guild.roles, name=role_name)
        if not role:
            await interaction.response.send_message(f"Role '{role_name}' does not exist. Ask an admin to add it.", ephemeral=True)
            return
        # Remove other allowed roles from the user
        member = interaction.user
        roles_to_remove = [r for r in member.roles if r.name in allowed and r != role]
        try:
            await member.remove_roles(*roles_to_remove, reason="Bot role customization")
        except Exception:
            pass
        # Add the new role
        try:
            await member.add_roles(role, reason="Bot role customization")
            await interaction.response.send_message(f"You have been given the role '{role_name}'.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Failed to assign role: {e}", ephemeral=True)

    @app_commands.command(name="listcustomroles", description="List all assignable custom roles for this server")
    async def listcustomroles(self, interaction: discord.Interaction):
        data = load_roles()
        guild_id = str(interaction.guild.id)
        allowed = data.get(guild_id, [])
        if not allowed:
            await interaction.response.send_message("No custom roles are currently assignable in this server.", ephemeral=True)
            return
        lines = []
        for role_name in allowed:
            role = discord.utils.get(interaction.guild.roles, name=role_name)
            if role:
                hex_color = f"#{role.color.value:06x}" if role.color.value else "#000000"
                lines.append(f"• <@&{role.id}> ({hex_color})")
            else:
                lines.append(f"• {role_name} (not found)")
        roles_list = '\n'.join(lines)
        embed = discord.Embed(
            title="Assignable Custom Roles",
            description=roles_list,
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Roles(bot)) 