"""
Slash Commands cog - Application command implementations.
"""
import discord
from discord.ext import commands
from discord import app_commands

from utils.formatters import format_number
from config.constants import MGS_RANKS


class SlashCommands(commands.Cog):
    """Slash command implementations."""
    
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Test connection")
    async def ping(self, interaction: discord.Interaction):
        """Test connection slash command."""
        embed = discord.Embed(
            title=" CODEC CONNECTION TEST",
            description=f"**Latency:** {round(self.bot.latency * 1000)}ms\n**Status:**  OPERATIONAL\n**XP System:**  ACTIVE",
            color=0x599cff
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="status", description="Check your MGS rank and XP status")
    async def status_slash(self, interaction: discord.Interaction):
        """Quick status check via slash command."""
        member_id = interaction.user.id
        guild_id = interaction.guild.id
        member_data = self.bot.member_data.get_member_data(member_id, guild_id)
        
        embed = discord.Embed(
            title=f"{member_data.get('rank_icon', '')} OPERATIVE STATUS",
            description=f"**{interaction.user.display_name}**",
            color=0x599cff
        )
        
        embed.add_field(
            name="CURRENT STATS",
            value=f"```\nRank: {member_data['rank']}\nGMP: {format_number(member_data['gmp'])}\nXP: {format_number(member_data['xp'])}\n```",
            inline=True
        )
        
        embed.add_field(
            name="ACTIVITY",
            value=f"```\nMessages: {format_number(member_data['messages_sent'])}\nTactical Words: {format_number(member_data.get('total_tactical_words', 0))}\n```",
            inline=True
        )
        
        # Show current Discord role if any
        rank_roles = [rank["role_name"] for rank in MGS_RANKS if rank["role_name"]]
        current_role = None
        for role in interaction.user.roles:
            if role.name in rank_roles:
                current_role = role.name
                break
        
        embed.add_field(
            name="DISCORD ROLE",
            value=f"```\n{current_role if current_role else 'None (Rookie)'}\n```",
            inline=False
        )
        
        if interaction.user.avatar:
            embed.set_thumbnail(url=interaction.user.avatar.url)
        
        embed.set_footer(text="Use !gmp for detailed rank progress")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    """Load the SlashCommands cog."""
    await bot.add_cog(SlashCommands(bot))
    bot.tree.add_command(bot.get_cog("SlashCommands").ping)
    bot.tree.add_command(bot.get_cog("SlashCommands").status_slash)
