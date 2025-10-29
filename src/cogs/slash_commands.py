"""
Slash Commands cog - Application command implementations.
"""
import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import LayoutView
from io import BytesIO
import asyncio

from utils.formatters import format_number
from config.constants import COZY_RANKS
from utils.daily_supply_gen import generate_daily_supply_card, generate_promotion_card
from utils.server_event_gen import generate_event_progress
from utils.rank_system import get_rank_data_by_name
from utils.role_manager import update_member_roles
from utils.rate_limiter import enforce_rate_limit
from utils.components_builder import (
    create_status_container,
    create_error_message,
    create_simple_message,
    create_success_message
)
from config.settings import logger
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
        container = create_status_container(
            title="📡 CODEC CONNECTION TEST",
            fields=[
                {
                    "name": "CONNECTION STATUS",
                    "value": f"```\nLatency: {round(self.bot.latency * 1000)}ms\nStatus: ✓ OPERATIONAL\nXP System: ✓ ACTIVE\n```"
                }
            ]
        )

        view = LayoutView()
        view.add_item(container)
        await interaction.response.send_message(view=view)

    @app_commands.command(name="status", description="Check your MGS rank and XP status")
    async def status_slash(self, interaction: discord.Interaction):
        """Quick status check via slash command."""
        # rate limit enforced via decorator wrapper
        member_id = interaction.user.id
        guild_id = interaction.guild.id
        member_data = self.bot.member_data.get_member_data(member_id, guild_id)

        # Show current Discord role if any
        rank_role_ids = [rank["role_id"] for rank in COZY_RANKS if rank.get("role_id")]
        current_role = None
        for role in interaction.user.roles:
            if role.id in rank_role_ids:
                current_role = role.name
                break

        container = create_status_container(
            title=f"{member_data.get('rank_icon', '🎖️')} OPERATIVE STATUS",
            fields=[
                {
                    "name": "OPERATIVE",
                    "value": f"**{interaction.user.display_name}**"
                },
                {
                    "name": "CURRENT STATS",
                    "value": f"```\nRank: {member_data['rank']}\nXP: {format_number(member_data['xp'])}\n```"
                },
                {
                    "name": "ACTIVITY",
                    "value": f"```\nMessages: {format_number(member_data['messages_sent'])}\n```"
                },
                {
                    "name": "DISCORD ROLE",
                    "value": f"```\n{current_role if current_role else 'None (Rookie)'}\n```"
                }
            ],
            thumbnail_url=interaction.user.avatar.url if interaction.user.avatar else None
        )

        view = LayoutView()
        view.add_item(container)
        await interaction.response.send_message(view=view, ephemeral=True)

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
            for i, rank_info in enumerate(COZY_RANKS):
                if rank_info.get("name") == current_rank_name:
                    current_rank_index = i
                    break

            next_rank = COZY_RANKS[current_rank_index + 1] if current_rank_index < len(COZY_RANKS) - 1 else None

            xp_progress = ""
            if next_rank:
                current_xp = member_data.get('xp', 0)
                required_xp = next_rank.get("required_xp", 0)
                current_rank_xp = COZY_RANKS[current_rank_index].get("required_xp", 0)
                progress_xp = current_xp - current_rank_xp
                needed_xp = required_xp - current_rank_xp
                percentage = int((progress_xp / needed_xp) * 100) if needed_xp > 0 else 100
                xp_progress = f"{progress_xp}/{needed_xp} XP ({percentage}%)"
            else:
                xp_progress = "MAX RANK"

            fields = [
                {
                    "name": "RANK INFO",
                    "value": f"**Rank:** {current_rank_name}\n**XP:** {format_number(member_data.get('xp', 0))}"
                },
                {
                    "name": "MESSAGES SENT",
                    "value": format_number(member_data.get('messages_sent', 0))
                }
            ]

            if next_rank:
                fields.insert(1, {
                    "name": f"Progress to {next_rank.get('name', 'Unknown')}",
                    "value": xp_progress
                })

            container = create_status_container(
                title=f"🎖️ {target.display_name}",
                fields=fields,
                thumbnail_url=target.avatar.url if target.avatar else None
            )

            view = LayoutView()
            view.add_item(container)
            await interaction.response.send_message(view=view)

        except Exception as e:
            # Log the full error for debugging
            import traceback
            error_details = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            print(f"Error in rank_slash: {error_details}")

            # Send user-friendly error message
            container = create_error_message(
                "Error fetching rank data",
                f"{str(e)}\nPlease contact an administrator."
            )
            view = LayoutView()
            view.add_item(container)
            await interaction.response.send_message(view=view, ephemeral=True)

    @app_commands.command(name="daily", description="Claim your daily bonus of XP")
    async def daily_slash(self, interaction: discord.Interaction):
        """Slash command version of !daily - claim daily rewards."""
        await interaction.response.defer()  # Image generation might take a moment

        success, xp, rank_changed, new_rank = self.bot.member_data.award_daily_bonus(
            interaction.user.id,
            interaction.guild.id
        )

        if not success:
            # Already claimed today - show time remaining
            member_data = self.bot.member_data.get_member_data(interaction.user.id, interaction.guild.id)
            last_daily = member_data.get("last_daily")

            if last_daily:
                from datetime import datetime, timezone, timedelta
                last_claim_date = datetime.strptime(last_daily, '%Y-%m-%d').replace(tzinfo=timezone.utc)
                next_claim_time = last_claim_date + timedelta(days=1)
                now = datetime.now(timezone.utc)
                time_remaining = next_claim_time - now

                if time_remaining.total_seconds() > 0:
                    hours, remainder = divmod(int(time_remaining.total_seconds()), 3600)
                    minutes, seconds = divmod(remainder, 60)

                    if hours > 0:
                        time_str = f"{hours}h {minutes}m {seconds}s"
                    elif minutes > 0:
                        time_str = f"{minutes}m {seconds}s"
                    else:
                        time_str = f"{seconds}s"
                else:
                    time_str = "a few seconds"
            else:
                time_str = "unknown"

            container = create_status_container(
                title="⏰ DAILY ALREADY CLAIMED",
                fields=[
                    {
                        "name": "NEXT CLAIM",
                        "value": f"Available in **{time_str}**"
                    },
                    {
                        "name": "CURRENT STATS",
                        "value": f"```\nXP: {member_data.get('xp', 0):,}\nRank: {member_data.get('rank', 'Rookie')}\nStreak: {member_data.get('daily_streak', 0)} days\n```"
                    }
                ],
                footer="Outer Heaven: Exiled Units"
            )

            view = LayoutView()
            view.add_item(container)
            await interaction.followup.send(view=view)
            return

        # Success - proceed with normal daily claim logic
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

                # Send promotion announcement to specific channel if promoted
                if rank_changed and new_rank:
                    try:
                        promo_channel = interaction.client.get_channel(1423506534872387584)
                        if promo_channel:
                            # Get old rank for promotion card
                            old_rank = member_data.get('rank', 'Unknown')

                            # Generate promotion card
                            promo_img = generate_promotion_card(
                                username=interaction.user.display_name,
                                old_rank=old_rank,
                                new_rank=new_rank,
                                current_xp=member_data['xp'],
                                role_granted=role_granted
                            )

                            # Convert to Discord file
                            promo_bytes = BytesIO()
                            promo_img.save(promo_bytes, format='PNG')
                            promo_bytes.seek(0)
                            promo_file = discord.File(promo_bytes, filename="promotion.png")

                            # Send promotion message
                            await promo_channel.send(
                                f"{interaction.user.mention} has been promoted to {new_rank}!",
                                file=promo_file
                            )
                    except Exception as e:
                        logger.error(f"Error sending promotion announcement: {e}")

            except Exception as e:
                # Fallback to component display if image fails
                fields = [
                    {
                        "name": "REWARD",
                        "value": f"**+{xp} XP** received!"
                    },
                    {
                        "name": "UPDATED STATS",
                        "value": f"```\nXP: {member_data['xp']:,}\nRank: {member_data['rank']}\nStreak: {streak_days} days\n```"
                    }
                ]

                if rank_changed:
                    fields.append({
                        "name": "🎖️ PROMOTION!",
                        "value": f"New rank: **{new_rank}**"
                    })
                    if role_granted:
                        fields.append({
                            "name": "✓ ROLE ASSIGNED",
                            "value": f"Discord role **{role_granted}** granted!"
                        })

                container = create_status_container(
                    title="💰 DAILY SUPPLY DROP",
                    fields=fields,
                    footer=f"⚠️ Image generation failed: {e}"
                )

                view = LayoutView()
                view.add_item(container)
                await interaction.followup.send(view=view)

    @app_commands.command(name="leaderboard", description="View the server leaderboard")
    @app_commands.describe(
        board_type="Type of leaderboard to view",
    )
    @app_commands.choices(board_type=[
        app_commands.Choice(name="XP (Experience)", value="xp"),
        app_commands.Choice(name="Messages Sent", value="messages"),
        app_commands.Choice(name="Word-Up Points", value="wordup"),
    ])
    @enforce_rate_limit('leaderboard')
    async def leaderboard_slash(self, interaction: discord.Interaction, board_type: str = "xp"):
        """Show leaderboard via slash command."""
        await interaction.response.defer()  # This might take a moment

        guild_data = self.bot.member_data.data.get(str(interaction.guild.id), {})

        # Special handling for Word-Up leaderboard (with image)
        if board_type == "wordup":
            try:
                # Collect Word-Up scores
                scores = []
                for member_id, data in guild_data.items():
                    word_up_points = data.get('word_up_points', 0)
                    if word_up_points > 0:
                        member = interaction.guild.get_member(int(member_id))
                        if member:
                            scores.append((member.display_name, word_up_points))

                if not scores:
                    container = create_simple_message(
                        "No Word-Up Scores",
                        "No Word-Up scores yet. Start playing to see your name on the leaderboard!",
                        "🎮"
                    )
                    view = LayoutView()
                    view.add_item(container)
                    await interaction.followup.send(view=view)
                    return

                # Sort by points
                scores.sort(key=lambda x: x[1], reverse=True)
                top_10 = scores[:10]

                # Format leaderboard data for image generation
                leaderboard_data = [
                    (idx + 1, name, points, "WORD-UP")
                    for idx, (name, points) in enumerate(top_10)
                ]

                # Generate leaderboard image
                from utils.leaderboard_gen import generate_leaderboard
                import os

                img = generate_leaderboard(
                    leaderboard_data=leaderboard_data,
                    category="WORD-UP POINTS",
                    unit_suffix="PTS",
                    guild_name=interaction.guild.name.upper()
                )

                # Save and send
                filename = f"wordup_leaderboard_{interaction.guild.id}.png"
                img.save(filename)

                file = discord.File(filename, filename="wordup_leaderboard.png")
                await interaction.followup.send(file=file)

                # Clean up
                os.remove(filename)
                return

            except Exception as e:
                logger.error(f"Error generating Word-Up leaderboard: {e}")
                container = create_error_message(
                    "Error generating leaderboard",
                    f"Failed to create Word-Up leaderboard: {str(e)}"
                )
                view = LayoutView()
                view.add_item(container)
                await interaction.followup.send(view=view)
                return

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

        container = create_status_container(
            title=f"📊 {board_names[board_type]} Leaderboard",
            fields=[
                {
                    "name": "TOP 10",
                    "value": leaderboard_text or "No data available"
                }
            ],
            footer=f"Server: {interaction.guild.name}"
        )

        view = LayoutView()
        view.add_item(container)
        await interaction.followup.send(view=view)
        @self.event_group.command(name="status", description="Check current event status")
        async def event_status(self, interaction: discord.Interaction):
            from utils.components_builder import create_error_message, create_info_card
            from discord.ui import LayoutView

            if not self.bot.get_cog('ServerEvent'):
                container = create_error_message(
                    "Event System Unavailable",
                    "The event system is not currently loaded. Please contact an administrator if this persists."
                )
                view = LayoutView()
                view.add_item(container)
                await interaction.response.send_message(view=view, ephemeral=True)
                return

            event_cog = self.bot.get_cog('ServerEvent')
            info = event_cog.event_manager.get_event_info()

            if not info.get("active"):
                container = create_info_card(
                    "No Active Event",
                    "There is currently no active server event. Check back later or contact admins to start an event!"
                )
                view = LayoutView()
                view.add_item(container)
                await interaction.response.send_message(view=view, ephemeral=True)
                return

            percentage = (info.get("current", 0) / info.get("goal", 1) * 100) if info.get("goal", 0) > 0 else 0
            container = create_info_card(
                "Event Status",
                f"**{info.get('title')}**\n\nProgress: {info.get('current',0):,}/{info.get('goal',0):,} ({percentage:.1f}%)"
            )
            view = LayoutView()
            view.add_item(container)
            await interaction.response.send_message(view=view)

        @self.event_group.command(name="info", description="Show event banner and leaderboard")
        @enforce_rate_limit('leaderboard')
        async def event_info(self, interaction: discord.Interaction):
            from utils.components_builder import create_error_message
            from discord.ui import LayoutView

            if not self.bot.get_cog('ServerEvent'):
                container = create_error_message(
                    "Event System Unavailable",
                    "The event system is not currently loaded. Please contact an administrator if this persists."
                )
                view = LayoutView()
                view.add_item(container)
                await interaction.response.send_message(view=view, ephemeral=True)
                return

            event_cog = self.bot.get_cog('ServerEvent')
            if not event_cog.event_manager.is_event_active():
                container = create_error_message(
                    "No Active Event",
                    "There is no active event at this time."
                )
                view = LayoutView()
                view.add_item(container)
                await interaction.response.send_message(view=view, ephemeral=True)
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
        async def event_start(self, interaction: discord.Interaction, goal: Optional[int] = None, title: Optional[str] = None):
            await interaction.response.defer(ephemeral=True)

            # Validate goal range if provided
            if goal is not None and (goal < 15 or goal > 50000):
                await interaction.followup.send("❌ Event goal must be between 15 and 50,000 messages.", ephemeral=True)
                return

            event_cog = self.bot.get_cog('ServerEvent')
            if not event_cog:
                await interaction.followup.send("Event system not loaded.", ephemeral=True)
                return

            try:
                event_info = await event_cog.event_manager.start_event(
                    title=title or "Weekly Community Challenge",
                    message_goal=goal,
                    guild_id=interaction.guild_id
                )
                # Announce to event channel
                await event_cog._announce_event_start(event_info)

                goal_note = " (dynamically calculated)" if goal is None else ""
                await interaction.followup.send(
                    f"✅ Event started: {title or 'Weekly Community Challenge'} with goal {event_info['goal']:,}{goal_note}"
                )
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

        fields = [
            {
                "name": "Current Date",
                "value": current_date.strftime("%B %d, %Y")
            }
        ]

        if self.bot.last_monthly_reset:
            fields.append({
                "name": "Last Reset",
                "value": self.bot.last_monthly_reset.strftime("%B %d, %Y")
            })

            # Calculate days since last reset
            days_since = (current_date - self.bot.last_monthly_reset).days
            fields.append({
                "name": "Days Since Reset",
                "value": f"{days_since} days"
            })
        else:
            fields.append({
                "name": "Last Reset",
                "value": "Never"
            })

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

        fields.append({
            "name": "Next Reset",
            "value": next_reset.strftime("%B %d, %Y")
        })

        fields.append({
            "name": "Days Until Reset",
            "value": f"{days_until_reset} days"
        })

        container = create_status_container(
            title="Monthly XP Reset Status",
            fields=fields,
            footer="XP resets monthly while ranks and multipliers are preserved"
        )

        view = LayoutView()
        view.add_item(container)
        await interaction.response.send_message(view=view)

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

            container = create_status_container(
                title="Server Event Progress",
                fields=[
                    {
                        "name": "EVENT",
                        "value": f"**{event_cog.event_manager.get_event_info().get('title')}**"
                    },
                    {
                        "name": "PROGRESS",
                        "value": f"{progress_data.get('current',0):,} / {progress_data.get('goal',0):,} messages"
                    }
                ]
            )

            view = LayoutView()
            view.add_item(container)
            await interaction.followup.send(view=view, file=file)

        except Exception as e:
            container = create_error_message(
                "Error generating event info",
                str(e)
            )
            view = LayoutView()
            view.add_item(container)
            await interaction.followup.send(view=view)

    @event_group.command(name="start", description="Start an event with dynamic goal (Admin only)")
    @app_commands.checks.has_permissions(administrator=True)
    async def event_start_slash(self, interaction: discord.Interaction, goal: Optional[int] = None, title: Optional[str] = None):
        await interaction.response.defer(ephemeral=True)

        # Validate goal range if provided
        if goal is not None and (goal < 15 or goal > 50000):
            await interaction.followup.send("❌ Event goal must be between 15 and 50,000 messages.", ephemeral=True)
            return

        event_cog = self.bot.get_cog('ServerEvent')
        if not event_cog:
            await interaction.followup.send("Event system not loaded.", ephemeral=True)
            return

        try:
            event_info = await event_cog.event_manager.start_event(
                title=title or "Weekly Community Challenge",
                message_goal=goal,
                guild_id=interaction.guild_id
            )
            # Announce to event channel
            await event_cog._announce_event_start(event_info)

            goal_note = " (dynamically calculated)" if goal is None else ""
            await interaction.followup.send(
                f"✅ Event started: {title or 'Weekly Community Challenge'} with goal {event_info['goal']:,}{goal_note}"
            )
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
