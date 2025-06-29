import discord
from discord.ext import commands
from discord import app_commands, Colour
from discord.ui import View, Button
import json
import os
import traceback

ROLES_FILE = "custom_roles.json"
ROLE_CHANNELS_FILE = "role_channels.json"

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

def load_role_channels():
    if not os.path.exists(ROLE_CHANNELS_FILE):
        return {}
    with open(ROLE_CHANNELS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_role_channels(data):
    with open(ROLE_CHANNELS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

class RoleButton(Button):
    def __init__(self, role_name: str, role_color: discord.Color, custom_id: str):
        # Determine button style based on role color
        if role_color.value == 0:  # Default color (no color)
            style = discord.ButtonStyle.secondary
        elif role_color.value <= 0xFFFFFF:  # Light colors
            style = discord.ButtonStyle.primary
        else:  # Dark colors
            style = discord.ButtonStyle.primary
            
        super().__init__(
            label=role_name,
            style=style,
            custom_id=custom_id
        )
        self.role_name = role_name
        self.role_color = role_color

class RoleAssignmentView(View):
    def __init__(self, roles_data: dict, guild_id: str, guild: discord.Guild):
        super().__init__(timeout=None)  # Persistent view
        self.roles_data = roles_data
        self.guild_id = guild_id
        
        # Add buttons for each role with proper colors, arranged in rows of 5
        allowed_roles = roles_data.get(guild_id, [])
        for idx, role_name in enumerate(allowed_roles):
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                button = RoleButton(role_name, role.color, f"role_{guild_id}_{role_name}")
                button.row = idx // 5  # Arrange 5 buttons per row
                self.add_item(button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        try:
            if not interaction.data.get("custom_id", "").startswith("role_"):
                return False
            
            # Extract role name from custom_id
            custom_id = interaction.data["custom_id"]
            parts = custom_id.split("_", 2)
            if len(parts) != 3:
                return False
            
            guild_id, role_name = parts[1], parts[2]
            
            # Get the role
            role = discord.utils.get(interaction.guild.roles, name=role_name)
            if not role:
                await interaction.response.send_message(f"Role '{role_name}' not found.", ephemeral=True)
                return False
            
            # Check if user already has this role
            member = interaction.user
            if role in member.roles:
                # Remove the role
                try:
                    await member.remove_roles(role, reason="Role button toggle")
                    await interaction.response.send_message(f"Removed role '{role_name}' from you.", ephemeral=True)
                except Exception as e:
                    print(f"[ERROR] Failed to remove role {role_name}: {e}")
                    await interaction.response.send_message(f"Failed to remove role: {e}", ephemeral=True)
            else:
                # Remove other assignable roles first
                allowed_roles = self.roles_data.get(guild_id, [])
                roles_to_remove = [r for r in member.roles if r.name in allowed_roles and r != role]
                try:
                    await member.remove_roles(*roles_to_remove, reason="Role button toggle")
                except Exception as e:
                    print(f"[WARNING] Failed to remove other roles: {e}")
                
                # Add the new role
                try:
                    await member.add_roles(role, reason="Role button toggle")
                    await interaction.response.send_message(f"Added role '{role_name}' to you.", ephemeral=True)
                except Exception as e:
                    print(f"[ERROR] Failed to add role {role_name}: {e}")
                    await interaction.response.send_message(f"Failed to add role: {e}", ephemeral=True)
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Role button interaction error: {e}")
            try:
                await interaction.response.send_message(
                    "❌ An error occurred while processing your role request. Please try again.",
                    ephemeral=True
                )
            except:
                # If interaction already expired, try followup
                try:
                    await interaction.followup.send(
                        "❌ An error occurred while processing your role request. Please try again.",
                        ephemeral=True
                    )
                except:
                    pass
            return False

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
        print(f"[DEBUG] /addcustomrole called by {interaction.user} for role: {role_name}")
        try:
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
            
            # Update role display if channel is configured
            await self.update_role_display_if_configured(interaction.guild)
        except Exception as e:
            print(f"[ERROR] /addcustomrole error: {e}")
            traceback.print_exc()
            await interaction.response.send_message("❌ An error occurred while adding the custom role. Please try again.", ephemeral=True)

    @app_commands.command(name="addexistingroles", description="Add existing server roles to the assignable list (admin only)")
    @app_commands.describe(role="The role to add to the assignable list")
    @app_commands.checks.has_permissions(administrator=True)
    async def addexistingroles(self, interaction: discord.Interaction, role: discord.Role):
        print(f"[DEBUG] /addexistingroles called by {interaction.user} for role: {role}")
        try:
            await interaction.response.defer(thinking=True, ephemeral=True)
            data = load_roles()
            guild_id = str(interaction.guild.id)
            allowed = data.get(guild_id, [])
            
            if role.name in allowed:
                await interaction.followup.send(f"Role '{role.name}' is already in the assignable list.", ephemeral=True)
                return
            
            # Check if the bot has permission to manage this role
            if role.position >= interaction.guild.me.top_role.position:
                await interaction.followup.send(f"Cannot add role '{role.name}' - it is higher than or equal to my highest role.", ephemeral=True)
                return
            
            # Add the role to the assignable list
            allowed.append(role.name)
            data[guild_id] = allowed
            save_roles(data)
            
            hex_color = f"#{role.color.value:06x}" if role.color.value else "#000000"
            embed = discord.Embed(
                title="Role Added Successfully",
                description=f"Role **{role.name}** has been added to the assignable list.",
                color=role.color or discord.Color.blue()
            )
            embed.add_field(name="Role ID", value=role.id, inline=True)
            embed.add_field(name="Color", value=hex_color, inline=True)
            embed.add_field(name="Position", value=role.position, inline=True)
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            # Update role display if channel is configured (do this after response to avoid timeout)
            try:
                await self.update_role_display_if_configured(interaction.guild)
            except Exception as e:
                print(f"[WARNING] Failed to update role display: {e}")
                
        except Exception as e:
            print(f"[ERROR] /addexistingroles error: {e}")
            traceback.print_exc()
            await interaction.followup.send("❌ An error occurred while adding the role. Please try again.", ephemeral=True)

    @app_commands.command(name="removecustomrole", description="Remove a custom role from the assignable list (admin only)")
    @app_commands.describe(role_name="The name of the role to remove")
    @app_commands.checks.has_permissions(administrator=True)
    async def removecustomrole(self, interaction: discord.Interaction, role_name: str):
        print(f"[DEBUG] /removecustomrole called by {interaction.user} for role: {role_name}")
        try:
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
            
            # Update role display if channel is configured
            await self.update_role_display_if_configured(interaction.guild)
        except Exception as e:
            print(f"[ERROR] /removecustomrole error: {e}")
            traceback.print_exc()
            await interaction.response.send_message("❌ An error occurred while removing the custom role. Please try again.", ephemeral=True)

    @app_commands.command(name="setrole", description="Assign yourself a custom role from the allowed list")
    @app_commands.describe(role_name="The name of the role to assign to yourself")
    async def setrole(self, interaction: discord.Interaction, role_name: str):
        print(f"[DEBUG] /setrole called by {interaction.user} for role: {role_name}")
        try:
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
        except Exception as e:
            print(f"[ERROR] /setrole error: {e}")
            traceback.print_exc()
            await interaction.response.send_message("❌ An error occurred while assigning the role. Please try again.", ephemeral=True)

    @app_commands.command(name="listcustomroles", description="List all assignable custom roles for this server")
    async def listcustomroles(self, interaction: discord.Interaction):
        print(f"[DEBUG] /listcustomroles called by {interaction.user}")
        try:
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
        except Exception as e:
            print(f"[ERROR] /listcustomroles error: {e}")
            traceback.print_exc()
            await interaction.response.send_message("❌ An error occurred while listing custom roles. Please try again.", ephemeral=True)

    @app_commands.command(name="setuprolechannel", description="Set up a channel to display role assignment buttons (admin only)")
    @app_commands.describe(channel="The channel where role buttons will be displayed")
    @app_commands.checks.has_permissions(administrator=True)
    async def setuprolechannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        print(f"[DEBUG] /setuprolechannel called by {interaction.user} for channel: {channel}")
        try:
            # Save the channel ID
            channels_data = load_role_channels()
            guild_id = str(interaction.guild.id)
            channels_data[guild_id] = channel.id
            save_role_channels(channels_data)
            
            # Create and send the role display message
            await self.create_role_display(channel)
            
            embed = discord.Embed(
                title="Role Channel Setup Complete",
                description=f"Role assignment buttons will be displayed in {channel.mention}",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"[ERROR] /setuprolechannel error: {e}")
            traceback.print_exc()
            await interaction.response.send_message("❌ An error occurred while setting up the role channel. Please try again.", ephemeral=True)

    @app_commands.command(name="updateroledisplay", description="Update the role display in the configured channel (admin only)")
    @app_commands.checks.has_permissions(administrator=True)
    async def updateroledisplay(self, interaction: discord.Interaction):
        print(f"[DEBUG] /updateroledisplay called by {interaction.user}")
        try:
            channels_data = load_role_channels()
            guild_id = str(interaction.guild.id)
            
            if guild_id not in channels_data:
                await interaction.response.send_message("No role channel has been set up. Use `/setuprolechannel` first.", ephemeral=True)
                return
            
            channel_id = channels_data[guild_id]
            channel = interaction.guild.get_channel(channel_id)
            
            if not channel:
                await interaction.response.send_message("The configured role channel no longer exists.", ephemeral=True)
                return
            
            # Clear existing messages in the channel
            try:
                async for message in channel.history(limit=100):
                    if message.author == self.bot.user:
                        await message.delete()
            except Exception as e:
                await interaction.response.send_message(f"Failed to clear channel: {e}", ephemeral=True)
                return
            
            # Create new role display
            await self.create_role_display(channel)
            
            embed = discord.Embed(
                title="Role Display Updated",
                description=f"Role assignment buttons have been updated in {channel.mention}",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"[ERROR] /updateroledisplay error: {e}")
            traceback.print_exc()
            await interaction.response.send_message("❌ An error occurred while updating the role display. Please try again.", ephemeral=True)

    async def create_role_display(self, channel: discord.TextChannel):
        """Create the role display message with colored buttons"""
        data = load_roles()
        guild_id = str(channel.guild.id)
        allowed_roles = data.get(guild_id, [])
        
        if not allowed_roles:
            embed = discord.Embed(
                title="🎭 Role Assignment",
                description="No assignable roles are currently available.\nAsk an administrator to add roles using `/addcustomrole` or `/addexistingroles`",
                color=discord.Color.blue()
            )
            await channel.send(embed=embed)
            return
        
        # Create embed with role information
        embed = discord.Embed(
            title="🎭 Role Assignment",
            description="Click the buttons below to assign yourself a role!\n\n**Available Roles:**",
            color=discord.Color.blue()
        )
        
        # Add role information to embed in the same format as listcustomroles
        lines = []
        for role_name in allowed_roles:
            role = discord.utils.get(channel.guild.roles, name=role_name)
            if role:
                hex_color = f"#{role.color.value:06x}" if role.color.value else "#000000"
                lines.append(f"• <@&{role.id}> ({hex_color}) - {len(role.members)} members")
            else:
                lines.append(f"• {role_name} (not found)")
        
        roles_list = '\n'.join(lines)
        embed.add_field(name="Roles", value=roles_list, inline=False)
        
        embed.set_footer(text="Click a button to toggle the role on/off")
        
        # Create view with colored buttons
        view = RoleAssignmentView(data, guild_id, channel.guild)
        
        await channel.send(embed=embed, view=view)

    async def update_role_display_if_configured(self, guild: discord.Guild):
        try:
            channels_data = load_role_channels()
            guild_id = str(guild.id)
            
            if guild_id not in channels_data:
                return
            
            channel_id = channels_data[guild_id]
            channel = guild.get_channel(channel_id)
            
            if not channel:
                return
            
            # Clear existing messages in the channel
            try:
                async for message in channel.history(limit=100):
                    if message.author == self.bot.user:
                        await message.delete()
            except Exception as e:
                print(f"Failed to clear channel: {e}")
                return
            
            # Create new role display
            await self.create_role_display(channel)
        except Exception as e:
            print(f"[ERROR] update_role_display_if_configured error: {e}")

async def setup(bot):
    await bot.add_cog(Roles(bot)) 