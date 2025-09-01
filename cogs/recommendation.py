@app_commands.command(
    name="recommend",
    description="Recommend a song in a text channel"
)
@app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.guild_id, i.user.id))
@app_commands.describe(
    url="The YouTube/Spotify/etc. link you want to recommend",
    channel="The channel where the recommendation will appear"
)
async def recommend(
    self,
    interaction: discord.Interaction,
    url: str,
    channel: discord.TextChannel
):
    """Send the recommendation as an embed."""
    me = interaction.guild.me if interaction.guild else None
    if not me:
        await interaction.response.send_message(
            "❌ This command must be used in a server.", ephemeral=True
        )
        return

    perms = channel.permissions_for(me)
    missing = []
    if not perms.view_channel:
        missing.append("View Channel")
    if not perms.send_messages:
        missing.append("Send Messages")

    if missing:
        await interaction.response.send_message(
            f"❌ I can't post in {channel.mention}. Missing: {', '.join(missing)}.",
            ephemeral=True,
        )
        return

    if not perms.embed_links:
        await interaction.response.send_message(
            f"⚠️ I can't send embeds in {channel.mention}. Please grant **Embed Links** permission.",
            ephemeral=True,
        )
        return

    # Create embed instead of sending raw link
    embed = discord.Embed(
        title="🎵 New Recommendation!",
        description=f"[Click to listen]({url})",
        color=discord.Color.blue()
    )
    embed.set_footer(text=f"Recommended by {interaction.user.display_name}")

    try:
        await channel.send(embed=embed)
    except discord.Forbidden:
        await interaction.response.send_message(
            f"❌ Missing access to post in {channel.mention}. Please grant 'View Channel' and 'Send Messages' to my role.",
            ephemeral=True,
        )
        return

    await interaction.response.send_message(
        f"✅ Your recommendation has been sent to {channel.mention}!", ephemeral=True
    )
