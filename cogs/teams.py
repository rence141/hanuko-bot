from discord.ext import commands
import discord
from discord import app_commands
import config
from db import get_user, update_user, get_team, update_team, get_all_users

TEAM_ROLES = ["Owner", "Deputy", "Officer", "Member"]

class Teams(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="createteam", description="Create a new team")
    @app_commands.describe(name="The name of the team to create")
    async def createteam(self, interaction: discord.Interaction, name: str):
        print(f"[DEBUG] /createteam called by {interaction.user} for team: {name}")
        user_data = get_user(interaction.user.id)
        if user_data.get("team"):
            await interaction.response.send_message("❌ You are already in a team. Leave it first with /leaveteam.", ephemeral=True)
            return
        if get_team(name):
            await interaction.response.send_message("❌ A team with that name already exists.", ephemeral=True)
            return
        # Create team
        members = [interaction.user.id]
        now = discord.utils.utcnow().isoformat()
        update_team(name, owner=interaction.user.id, members=members, created=now, points=0)
        update_user(interaction.user.id, team=name, team_role="Owner")
        await interaction.response.send_message(f"✅ Team '{name}' created! You are the owner.")

    @app_commands.command(name="inviteteam", description="Invite a user to your team")
    @app_commands.describe(user="The user to invite")
    async def inviteteam(self, interaction: discord.Interaction, user: discord.Member):
        inviter_data = get_user(interaction.user.id)
        team_name = inviter_data.get("team")
        if not team_name:
            await interaction.response.send_message("You are not in a team.", ephemeral=True)
            return
        team = get_team(team_name)
        if not team:
            await interaction.response.send_message("Your team does not exist.", ephemeral=True)
            return
        if user.id in team["members"]:
            await interaction.response.send_message(f"{user.display_name} is already in your team.", ephemeral=True)
            return
        # Store invites in team data
        invites = team.get("invites", [])
        if user.id in invites:
            await interaction.response.send_message(f"{user.display_name} has already been invited.", ephemeral=True)
            return
        invites.append(user.id)
        update_team(team_name, invites=invites)
        try:
            await user.send(f"You have been invited to join the team '{team_name}' in {interaction.guild.name}! Use /jointeam {team_name} to accept.")
        except Exception:
            pass
        await interaction.response.send_message(f"Invite sent to {user.display_name} to join '{team_name}'.")

    @app_commands.command(name="jointeam", description="Join an existing team by name (if invited)")
    @app_commands.describe(name="The name of the team to join")
    async def jointeam(self, interaction: discord.Interaction, name: str):
        print(f"[DEBUG] /jointeam called by {interaction.user} for team: {name}")
        user_data = get_user(interaction.user.id)
        if user_data.get("team"):
            await interaction.response.send_message("❌ You are already in a team. Leave it first with /leaveteam.", ephemeral=True)
            return
        team = get_team(name)
        if not team:
            await interaction.response.send_message("❌ No team with that name exists.", ephemeral=True)
            return
        if interaction.user.id in team["members"]:
            await interaction.response.send_message("❌ You are already a member of this team.", ephemeral=True)
            return
        # Check invite
        if interaction.user.id not in team.get("invites", []):
            await interaction.response.send_message("❌ You have not been invited to this team.", ephemeral=True)
            return
        team["members"].append(interaction.user.id)
        team["invites"].remove(interaction.user.id)
        update_team(name, members=team["members"], invites=team["invites"])
        update_user(interaction.user.id, team=name, team_role="Member")
        await interaction.response.send_message(f"✅ You joined the team '{name}'!")

    @app_commands.command(name="promote", description="Promote a team member to Officer or Deputy")
    @app_commands.describe(user="The user to promote", role="The role to assign (Officer or Deputy)")
    async def promote(self, interaction: discord.Interaction, user: discord.Member, role: str):
        print(f"[DEBUG] /promote called by {interaction.user} for user: {user.display_name} to role: {role}")
        role = role.capitalize()
        if role not in ["Officer", "Deputy"]:
            await interaction.response.send_message("Role must be Officer or Deputy.", ephemeral=True)
            return
        user_data = get_user(interaction.user.id)
        if user_data.get("team_role") not in ["Owner", "Deputy"]:
            await interaction.response.send_message("Only the Owner or Deputy can promote members.", ephemeral=True)
            return
        team_name = user_data.get("team")
        if not team_name:
            await interaction.response.send_message("You are not in a team.", ephemeral=True)
            return
        team = get_team(team_name)
        if user.id not in team["members"]:
            await interaction.response.send_message("That user is not in your team.", ephemeral=True)
            return
        if role == "Deputy":
            # Only one Deputy per team
            all_users = get_all_users()
            for u in all_users:
                if u.get("team") == team_name and u.get("team_role") == "Deputy":
                    await interaction.response.send_message("There is already a Deputy in your team.", ephemeral=True)
                    return
        update_user(user.id, team_role=role)
        await interaction.response.send_message(f"✅ Promoted {user.display_name} to {role}.")

    @app_commands.command(name="demote", description="Demote a team member to Member")
    @app_commands.describe(user="The user to demote")
    async def demote(self, interaction: discord.Interaction, user: discord.Member):
        print(f"[DEBUG] /demote called by {interaction.user} for user: {user.display_name}")
        user_data = get_user(interaction.user.id)
        if user_data.get("team_role") not in ["Owner", "Deputy"]:
            await interaction.response.send_message("Only the Owner or Deputy can demote members.", ephemeral=True)
            return
        team_name = user_data.get("team")
        if not team_name:
            await interaction.response.send_message("You are not in a team.", ephemeral=True)
            return
        team = get_team(team_name)
        if user.id not in team["members"]:
            await interaction.response.send_message("That user is not in your team.", ephemeral=True)
            return
        update_user(user.id, team_role="Member")
        await interaction.response.send_message(f"✅ Demoted {user.display_name} to Member.")

    @app_commands.command(name="team", description="View your current team info")
    async def team(self, interaction: discord.Interaction):
        print(f"[DEBUG] /team called by {interaction.user}")
        user_data = get_user(interaction.user.id)
        team_name = user_data.get("team")
        if not team_name:
            await interaction.response.send_message("You are not in a team.", ephemeral=True)
            return
        team = get_team(team_name)
        if not team:
            await interaction.response.send_message(f"Team '{team_name}' does not exist.", ephemeral=True)
            return
        all_users = get_all_users()
        member_roles = {}
        for u in all_users:
            if u.get("team") == team_name:
                member_roles[u["id"]] = u.get("team_role", "Member")
        embed = discord.Embed(
            title=f"🏅 Team: {team_name}",
            color=config.EMBED_COLORS["info"]
        )
        owner_id = team.get("owner")
        owner = self.bot.get_user(owner_id)
        embed.add_field(name="Owner", value=owner.display_name if owner else owner_id, inline=True)
        embed.add_field(name="Members", value=str(len(team["members"])), inline=True)
        embed.add_field(name="Points", value=team.get("points", 0), inline=True)
        embed.add_field(name="Created", value=team.get("created", "N/A"), inline=False)
        # List members and their roles
        member_list = []
        for member_id in team["members"]:
            user_obj = self.bot.get_user(member_id)
            role = member_roles.get(member_id, "Member")
            name = user_obj.display_name if user_obj else str(member_id)
            member_list.append(f"{name} ({role})")
        embed.add_field(name="Team Members & Roles", value="\n".join(member_list), inline=False)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Teams(bot)) 