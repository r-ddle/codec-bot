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

    @app_commands.command(name="rank", description="View your or another member's rank card")
    @app_commands.describe(user="The member to check (optional)")
    async def rank_slash(self, interaction: discord.Interaction, user: discord.Member = None):
        """Slash command version of !rank - shows detailed rank information."""
        try:
            target = user or interaction.user
            member_data = self.bot.member_data.get_member_data(target.id, interaction.guild.id)

            # Get current rank safely
            current_rank_name = member_data.get('rank', 'Rookie')

            # Calculate XP to next rank
            current_rank_index = 0
            for i, rank_info in enumerate(MGS_RANKS):
                if rank_info.get("name") == current_rank_name:
                    current_rank_index = i
                    break

            next_rank = MGS_RANKS[current_rank_index + 1] if current_rank_index < len(MGS_RANKS) - 1 else None

            xp_progress = ""
            if next_rank:
                current_xp = member_data.get('xp', 0)
                required_xp = next_rank.get("required_xp", 0)
                current_rank_xp = MGS_RANKS[current_rank_index].get("required_xp", 0)
                progress_xp = current_xp - current_rank_xp
                needed_xp = required_xp - current_rank_xp
                percentage = int((progress_xp / needed_xp) * 100) if needed_xp > 0 else 100
                xp_progress = f"{progress_xp}/{needed_xp} XP ({percentage}%)"
            else:
                xp_progress = "MAX RANK"

            embed = discord.Embed(
                title=f"🎖️ {target.display_name}",
                description=f"**Rank:** {current_rank_name}\n**GMP:** {format_number(member_data.get('gmp', 0))}\n**XP:** {format_number(member_data.get('xp', 0))}",
                color=0x599cff
            )

            if next_rank:
                embed.add_field(
                    name=f"Progress to {next_rank.get('name', 'Unknown')}",
                    value=xp_progress,
                    inline=False
                )

            embed.add_field(name="Messages Sent", value=format_number(member_data.get('messages_sent', 0)), inline=True)
            embed.add_field(name="Tactical Words", value=format_number(member_data.get('total_tactical_words', 0)), inline=True)

            if target.avatar:
                embed.set_thumbnail(url=target.avatar.url)

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            # Log the full error for debugging
            import traceback
            error_details = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            print(f"Error in rank_slash: {error_details}")

            # Send user-friendly error message
            await interaction.response.send_message(
                f"❌ An error occurred while fetching rank data: {str(e)}\nPlease contact an administrator.",
                ephemeral=True
            )

    @app_commands.command(name="daily", description="Claim your daily bonus of GMP and XP")
    async def daily_slash(self, interaction: discord.Interaction):
        """Slash command version of !daily - claim daily rewards."""
        success, gmp, xp, rank_changed, new_rank = self.bot.member_data.award_daily_bonus(
            interaction.user.id,
            interaction.guild.id
        )

        if success:
            embed = discord.Embed(
                title="📅 DAILY BONUS CLAIMED",
                description=f"You received **{gmp} GMP** and **{xp} XP**!",
                color=0x00ff00
            )

            if rank_changed:
                embed.add_field(
                    name="🎉 RANK UP!",
                    value=f"You've been promoted to **{new_rank}**!",
                    inline=False
                )

            embed.set_footer(text="Come back tomorrow for another bonus!")
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                title="⏰ ALREADY CLAIMED",
                description="You've already claimed your daily bonus. Come back tomorrow!",
                color=0xff9900
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="leaderboard", description="View the server leaderboard")
    @app_commands.describe(
        board_type="Type of leaderboard to view",
    )
    @app_commands.choices(board_type=[
        app_commands.Choice(name="XP (Experience)", value="xp"),
        app_commands.Choice(name="GMP (Currency)", value="gmp"),
        app_commands.Choice(name="Messages Sent", value="messages"),
    ])
    async def leaderboard_slash(self, interaction: discord.Interaction, board_type: str = "xp"):
        """Show leaderboard via slash command."""
        await interaction.response.defer()  # This might take a moment

        guild_data = self.bot.member_data.data.get(str(interaction.guild.id), {})

        # Sort based on type
        sort_key = board_type if board_type != "messages" else "messages_sent"
        sorted_members = sorted(
            guild_data.items(),
            key=lambda x: x[1].get(sort_key, 0),
            reverse=True
        )[:10]  # Top 10

        # Build leaderboard
        leaderboard_text = ""
        for idx, (member_id, data) in enumerate(sorted_members, 1):
            member = interaction.guild.get_member(int(member_id))
            if not member:
                continue

            value = data.get(sort_key, 0)
            emoji = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"{idx}."
            leaderboard_text += f"{emoji} **{member.display_name}** - {format_number(value)}\n"

        board_names = {
            "xp": "Experience Points",
            "gmp": "GMP Currency",
            "messages": "Messages Sent"
        }

        embed = discord.Embed(
            title=f"📊 {board_names[board_type]} Leaderboard",
            description=leaderboard_text or "No data available",
            color=0xffd700
        )
        embed.set_footer(text=f"Server: {interaction.guild.name}")

        await interaction.followup.send(embed=embed)


async def setup(bot):
    """Load the SlashCommands cog."""
    await bot.add_cog(SlashCommands(bot))
