"""
Slash Commands cog - Application command implementations.
"""
import discord
from discord.ext import commands
from discord import app_commands
from io import BytesIO
import asyncio

from utils.formatters import format_number
from config.constants import MGS_RANKS
from utils.daily_supply_gen import generate_daily_supply_card
from utils.server_event_gen import generate_event_progress
from utils.rank_system import get_rank_data_by_name
from utils.role_manager import update_member_roles
from utils.rate_limiter import enforce_rate_limit
from typing import Optional


class SlashCommands(commands.Cog):
    """Slash command implementations."""

    # Define event group at class level
    event_group = app_commands.Group(name="event", description="Server event commands")

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
        # rate limit enforced via decorator wrapper
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
            value=f"```\nRank: {member_data['rank']}\nXP: {format_number(member_data['xp'])}\n```",
            inline=True
        )

        embed.add_field(
            name="ACTIVITY",
            value=f"```\nMessages: {format_number(member_data['messages_sent'])}\n```",
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

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="rank", description="View your or another member's rank card")
    @app_commands.describe(user="The member to check (optional)")
    @enforce_rate_limit('rank')
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
                description=f"**Rank:** {current_rank_name}\n**XP:** {format_number(member_data.get('xp', 0))}",
                color=0x599cff
            )

            if next_rank:
                embed.add_field(
                    name=f"Progress to {next_rank.get('name', 'Unknown')}",
                    value=xp_progress,
                    inline=False
                )

            embed.add_field(name="Messages Sent", value=format_number(member_data.get('messages_sent', 0)), inline=True)

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

    @app_commands.command(name="daily", description="Claim your daily bonus of XP")
    @enforce_rate_limit('daily')
    async def daily_slash(self, interaction: discord.Interaction):
        """Slash command version of !daily - claim daily rewards."""
        await interaction.response.defer()  # Image generation might take a moment

        success, xp, rank_changed, new_rank = self.bot.member_data.award_daily_bonus(
            interaction.user.id,
            interaction.guild.id
        )

        if success:
            # Get updated member data
            member_data = self.bot.member_data.get_member_data(interaction.user.id, interaction.guild.id)

            # Get streak info
            streak_days = member_data.get('daily_streak', 1)

            # Determine role granted if promoted
            role_granted = None
            if rank_changed:
                role_updated = await update_member_roles(interaction.user, new_rank)
                if role_updated:
                    rank_data = get_rank_data_by_name(new_rank)
                    role_granted = rank_data.get("role_name", new_rank)

            # Generate MGS Codec-style supply drop image
            try:
                img = generate_daily_supply_card(
                    username=interaction.user.display_name,
                    xp_reward=xp,
                    current_xp=member_data['xp'],
                    current_rank=member_data['rank'],
                    streak_days=streak_days,
                    promoted=rank_changed,
                    new_rank=new_rank if rank_changed else None,
                    role_granted=role_granted
                )

                # Convert to Discord file
                image_bytes = BytesIO()
                img.save(image_bytes, format='PNG')
                image_bytes.seek(0)

                file = discord.File(fp=image_bytes, filename="daily_supply.png")
                await interaction.followup.send(file=file)

            except Exception as e:
                # Fallback to text embed if image fails
                embed = discord.Embed(
                    title="� DAILY SUPPLY DROP",
                    description=f"**+{xp} XP** received!",
                    color=0x00ff00
                )
                embed.add_field(
                    name="UPDATED STATS",
                    value=f"```\nXP: {member_data['xp']:,}\nRank: {member_data['rank']}\nStreak: {streak_days} days\n```",
                    inline=False
                )
                if rank_changed:
                    embed.add_field(name="🎖️ PROMOTION!", value=f"New rank: **{new_rank}**", inline=False)
                    if role_granted:
                        embed.add_field(name="✓ ROLE ASSIGNED", value=f"Discord role **{role_granted}** granted!", inline=False)

                embed.set_footer(text=f"Error generating image: {e}")
                await interaction.followup.send(embed=embed)
        else:
            embed = discord.Embed(
                title="⏰ ALREADY CLAIMED",
                description="You've already claimed your daily bonus. Come back tomorrow!",
                color=0xff9900
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="leaderboard", description="View the server leaderboard")
    @app_commands.describe(
        board_type="Type of leaderboard to view",
    )
    @app_commands.choices(board_type=[
        app_commands.Choice(name="XP (Experience)", value="xp"),
        app_commands.Choice(name="Messages Sent", value="messages"),
    ])
    @enforce_rate_limit('leaderboard')
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
            "messages": "Messages Sent"
        }

        embed = discord.Embed(
            title=f"📊 {board_names[board_type]} Leaderboard",
            description=leaderboard_text or "No data available",
            color=0xffd700
        )
        embed.set_footer(text=f"Server: {interaction.guild.name}")

        await interaction.followup.send(embed=embed)
        @self.event_group.command(name="status", description="Check current event status")
        async def event_status(self, interaction: discord.Interaction):
            if not self.bot.get_cog('ServerEvent'):
                await interaction.response.send_message("Event system not loaded.", ephemeral=True)
                return

            event_cog = self.bot.get_cog('ServerEvent')
            info = event_cog.event_manager.get_event_info()

            if not info.get("active"):
                await interaction.response.send_message("❌ No active server event.", ephemeral=True)
                return

            percentage = (info.get("current", 0) / info.get("goal", 1) * 100) if info.get("goal", 0) > 0 else 0
            await interaction.response.send_message(f"Event: {info.get('title')} - {info.get('current',0):,}/{info.get('goal',0):,} ({percentage:.1f}%)")

        @self.event_group.command(name="info", description="Show event banner and leaderboard")
        @enforce_rate_limit('leaderboard')
        async def event_info(self, interaction: discord.Interaction):
            if not self.bot.get_cog('ServerEvent'):
                await interaction.response.send_message("Event system not loaded.", ephemeral=True)
                return

            event_cog = self.bot.get_cog('ServerEvent')
            if not event_cog.event_manager.is_event_active():
                await interaction.response.send_message("❌ No active event.", ephemeral=True)
                return

            await interaction.response.defer()
            try:
                # Reuse existing generation code by calling the cog helper
                progress_data = event_cog.event_manager.get_progress_data()
                img = await self.bot.loop.run_in_executor(None, lambda: None)
                # For now, send a text summary and let the scheduled announcements handle images
                await interaction.followup.send(f"Event '{event_cog.event_manager.get_event_info().get('title')}' is active. Progress: {progress_data.get('current',0):,}/{progress_data.get('goal',0):,}")
            except Exception as e:
                await interaction.followup.send(f"❌ Error fetching event info: {e}", ephemeral=True)

        @self.event_group.command(name="start", description="Start an event (Admin only)")
        @app_commands.checks.has_permissions(administrator=True)
        async def event_start(self, interaction: discord.Interaction, goal: Optional[int] = 500, title: Optional[str] = None):
            await interaction.response.defer(ephemeral=True)

            # Validate goal range
            if goal is not None and (goal < 15 or goal > 1000):
                await interaction.followup.send("❌ Event goal must be between 15 and 1000 messages.", ephemeral=True)
                return

            event_cog = self.bot.get_cog('ServerEvent')
            if not event_cog:
                await interaction.followup.send("Event system not loaded.", ephemeral=True)
                return

            try:
                event_info = await event_cog.event_manager.start_event(title=title or "Weekly Community Challenge", message_goal=goal)
                # Announce to event channel
                await event_cog._announce_event_start(event_info)
                await interaction.followup.send(f"✅ Event started: {title or 'Weekly Community Challenge'} with goal {goal:,}")
            except Exception as e:
                await interaction.followup.send(f"❌ Error starting event: {e}")

        @self.event_group.command(name="end", description="End the event and distribute rewards (Admin only)")
        @app_commands.checks.has_permissions(administrator=True)
        async def event_end(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            event_cog = self.bot.get_cog('ServerEvent')
            if not event_cog:
                await interaction.followup.send("Event system not loaded.", ephemeral=True)
                return

            try:
                await event_cog._end_event_and_distribute_rewards()
                await interaction.followup.send("✅ Event ended and rewards distributed.")
            except Exception as e:
                await interaction.followup.send(f"❌ Error ending event: {e}")


    @app_commands.command(name="monthly_reset", description="Check monthly XP reset status")
    @commands.has_permissions(administrator=True)
    async def monthly_reset_status(self, interaction: discord.Interaction):
        """Check the status of monthly XP resets."""
        from datetime import date

        current_date = date.today()
        embed = discord.Embed(
            title="🌙 MONTHLY XP RESET STATUS",
            color=0x599cff
        )

        embed.add_field(
            name="Current Date",
            value=current_date.strftime("%B %d, %Y"),
            inline=True
        )

        if self.bot.last_monthly_reset:
            embed.add_field(
                name="Last Reset",
                value=self.bot.last_monthly_reset.strftime("%B %d, %Y"),
                inline=True
            )

            # Calculate days since last reset
            days_since = (current_date - self.bot.last_monthly_reset).days
            embed.add_field(
                name="Days Since Reset",
                value=f"{days_since} days",
                inline=True
            )
        else:
            embed.add_field(
                name="Last Reset",
                value="Never",
                inline=True
            )

        # Calculate next reset date
        if current_date.day == 1:
            next_reset = current_date
        else:
            # Next month
            if current_date.month == 12:
                next_reset = date(current_date.year + 1, 1, 1)
            else:
                next_reset = date(current_date.year, current_date.month + 1, 1)

        days_until_reset = (next_reset - current_date).days

        embed.add_field(
            name="Next Reset",
            value=next_reset.strftime("%B %d, %Y"),
            inline=True
        )

        embed.add_field(
            name="Days Until Reset",
            value=f"{days_until_reset} days",
            inline=True
        )

        embed.set_footer(text="XP resets monthly while ranks and multipliers are preserved")

        await interaction.response.send_message(embed=embed)

    # Event group commands
    @event_group.command(name="status", description="Check current event status")
    async def event_status(self, interaction: discord.Interaction):
        if not self.bot.get_cog('ServerEvent'):
            await interaction.response.send_message("Event system not loaded.", ephemeral=True)
            return

        event_cog = self.bot.get_cog('ServerEvent')
        info = event_cog.event_manager.get_event_info()

        if not info.get("active"):
            await interaction.response.send_message("❌ No active server event.", ephemeral=True)
            return

        percentage = (info.get("current", 0) / info.get("goal", 1) * 100) if info.get("goal", 0) > 0 else 0
        await interaction.response.send_message(f"Event: {info.get('title')} - {info.get('current',0):,}/{info.get('goal',0):,} ({percentage:.1f}%)")

    @event_group.command(name="info", description="Show event banner and leaderboard")
    @enforce_rate_limit('leaderboard')
    async def event_info(self, interaction: discord.Interaction):
        if not self.bot.get_cog('ServerEvent'):
            await interaction.response.send_message("Event system not loaded.", ephemeral=True)
            return

        event_cog = self.bot.get_cog('ServerEvent')
        if not event_cog.event_manager.is_event_active():
            await interaction.response.send_message("❌ No active server event.", ephemeral=True)
            return

        await interaction.response.defer()

        try:
            progress_data = event_cog.event_manager.get_progress_data()
            leaderboard_data = event_cog.event_manager.get_event_leaderboard()

            # Generate event progress image
            img = await asyncio.to_thread(
                generate_event_progress,
                event_title=event_cog.event_manager.get_event_info().get('title'),
                current_messages=progress_data.get('current', 0),
                goal_messages=progress_data.get('goal', 0),
                leaderboard=leaderboard_data,
                days_remaining=progress_data.get('days_remaining', 0)
            )

            # Convert to Discord file
            buffer = BytesIO()
            img.save(buffer, 'PNG')
            buffer.seek(0)
            file = discord.File(buffer, 'event_progress.png')

            embed = discord.Embed(
                title="🎯 SERVER EVENT PROGRESS",
                description=f"**{event_cog.event_manager.get_event_info().get('title')}**\n"
                           f"Progress: {progress_data.get('current',0):,}/{progress_data.get('goal',0):,} messages",
                color=0x599cff
            )
            embed.set_image(url="attachment://event_progress.png")

            await interaction.followup.send(embed=embed, file=file)

        except Exception as e:
            await interaction.followup.send(f"❌ Error generating event info: {e}")

    @event_group.command(name="start", description="Start an event (Admin only)")
    @app_commands.checks.has_permissions(administrator=True)
    async def event_start(self, interaction: discord.Interaction, goal: Optional[int] = 500, title: Optional[str] = None):
        await interaction.response.defer(ephemeral=True)

        # Validate goal range
        if goal is not None and (goal < 15 or goal > 1000):
            await interaction.followup.send("❌ Event goal must be between 15 and 1000 messages.", ephemeral=True)
            return

        event_cog = self.bot.get_cog('ServerEvent')
        if not event_cog:
            await interaction.followup.send("Event system not loaded.", ephemeral=True)
            return

        try:
            event_info = await event_cog.event_manager.start_event(title=title or "Weekly Community Challenge", message_goal=goal)
            # Announce to event channel
            await event_cog._announce_event_start(event_info)
            await interaction.followup.send(f"✅ Event started: {title or 'Weekly Community Challenge'} with goal {goal:,}")
        except Exception as e:
            await interaction.followup.send(f"❌ Error starting event: {e}")

    @event_group.command(name="end", description="End the event and distribute rewards (Admin only)")
    @app_commands.checks.has_permissions(administrator=True)
    async def event_end(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        event_cog = self.bot.get_cog('ServerEvent')
        if not event_cog:
            await interaction.followup.send("Event system not loaded.", ephemeral=True)
            return

        try:
            await event_cog._end_event_and_distribute_rewards()
            await interaction.followup.send("✅ Event ended and rewards distributed.")
        except Exception as e:
            await interaction.followup.send(f"❌ Error ending event: {e}")


async def setup(bot):
    """Load the SlashCommands cog."""
    await bot.add_cog(SlashCommands(bot))
