"""
Server Event Cog - Manages weekly community events
"""
import discord
from discord.ext import commands, tasks
from discord.ui import LayoutView
from discord import app_commands
from datetime import datetime, timedelta
import asyncio
from io import BytesIO
from typing import Optional

from database.server_event_manager import ServerEventManager
from utils.server_event_gen import (
    generate_event_start_banner,
    generate_event_progress,
    generate_event_results
)
from config.settings import logger
from utils.rate_limiter import enforce_rate_limit
from config.bot_settings import EVENT_ROLE_ID, EVENT_CHANNEL_ID
from utils.components_builder import create_stats_container, create_error_message, create_success_message, create_info_card
from utils.event_modals import CreateEventModal, EndEventModal, EventProgressModal
from utils.event_templates import list_templates, get_template


class ServerEvent(commands.Cog):
    """Weekly server event management"""

    def __init__(self, bot):
        self.bot = bot
        self.event_manager = ServerEventManager(bot=bot)
        self.check_event_tasks.start()

    def cog_unload(self):
        self.check_event_tasks.cancel()

    @tasks.loop(minutes=30)
    async def check_event_tasks(self):
        """Periodic task to check event status and send updates"""
        try:
            # Check if event should end
            if self.event_manager.should_end_event():
                await self._end_event_and_distribute_rewards()

            # Check if progress update needed
            elif self.event_manager.should_send_progress_update():
                await self._send_progress_update()

        except Exception as e:
            logger.error(f"error in event check task: {e}")

    @check_event_tasks.before_loop
    async def before_check_tasks(self):
        await self.bot.wait_until_ready()

    async def _auto_start_event(self):
        """Automatically start event on Monday with dynamic goal"""
        try:
            # Get the event channel to determine guild
            channel = self.bot.get_channel(EVENT_CHANNEL_ID)
            guild_id = channel.guild.id if channel else None

            # Start event with dynamic goal based on server activity
            event_info = await self.event_manager.start_event(guild_id=guild_id)
            await self._announce_event_start(event_info)
        except Exception as e:
            logger.error(f"Error auto-starting event: {e}")

    async def _announce_event_start(self, event_info: dict):
        """Announce event start with banner image"""
        try:
            channel = self.bot.get_channel(EVENT_CHANNEL_ID)
            if not channel:
                logger.error(f"Event channel {EVENT_CHANNEL_ID} not found")
                return

            # Generate start banner
            img = await asyncio.to_thread(
                generate_event_start_banner,
                event_title=event_info["title"],
                message_goal=event_info["goal"],
                start_date=event_info["start_date"],
                end_date=event_info["end_date"]
            )

            # Convert to Discord file
            buffer = BytesIO()
            await asyncio.to_thread(img.save, buffer, 'PNG')
            buffer.seek(0)

            await channel.send(
                f"**This Week's Server Event Has Started!**\n\n"
                f"**Goal:** {event_info['goal']:,} messages\n"
                f"**Rewards:** All participants get +100 XP\n"
                f"**Bonus:** Top 3 get +500 XP",
                file=discord.File(buffer, 'event_start.png')
            )

            # Send reminder message
            await channel.send("-# If you want to get notified of future server events, type !remindme")

            logger.info("Event start announced")

        except Exception as e:
            logger.error(f"Error announcing event start: {e}")

    async def _send_progress_update(self):
        """Send progress update image"""
        try:
            progress_data = self.event_manager.get_progress_data()
            if not progress_data:
                return

            channel = self.bot.get_channel(EVENT_CHANNEL_ID)
            if not channel:
                return

            # Generate progress image
            img = await asyncio.to_thread(
                generate_event_progress,
                event_title=progress_data["title"],
                current_messages=progress_data["current"],
                goal_messages=progress_data["goal"],
                time_remaining=progress_data["time_remaining"],
                participant_count=progress_data["participants"],
                top_contributors=progress_data["top_contributors"]
            )

            # Convert to Discord file
            buffer = BytesIO()
            await asyncio.to_thread(img.save, buffer, 'PNG')
            buffer.seek(0)

            # Build top contributors text
            top_contributors_text = ""
            if progress_data["top_contributors"]:
                top_contributors_text = "\n\n**Top Contributors:**\n"
                for i, (username, msg_count) in enumerate(progress_data["top_contributors"], 1):
                    top_contributors_text += f"{i}. {username} - {msg_count:,} messages\n"

            await channel.send(
                f"**Event Progress Update**{top_contributors_text}",
                file=discord.File(buffer, 'event_progress.png')
            )

            # Send reminder message
            await channel.send("-# If you want to get notified of future server events, type !remindme")

            await self.event_manager.mark_progress_update_sent()
            logger.info("Event progress update sent")

        except Exception as e:
            logger.error(f"Error sending progress update: {e}")

    async def _end_event_and_distribute_rewards(self):
        """End event, generate results, and distribute rewards"""
        try:
            results = await self.event_manager.end_event()
            if not results:
                return

            channel = self.bot.get_channel(EVENT_CHANNEL_ID)
            if not channel:
                logger.error(f"Event channel {EVENT_CHANNEL_ID} not found")
                return

            # Generate results image
            img = await asyncio.to_thread(
                generate_event_results,
                event_title=results["title"],
                total_messages=results["total_messages"],
                goal_messages=results["goal"],
                goal_reached=results["goal_reached"],
                leaderboard=results["leaderboard"],
                participant_count=results["participant_count"]
            )

            # Convert to Discord file
            buffer = BytesIO()
            await asyncio.to_thread(img.save, buffer, 'PNG')
            buffer.seek(0)

            # Send results image
            await channel.send(file=discord.File(buffer, 'event_results.png'))

            # Send leaderboard as text
            if results["leaderboard"]:
                leaderboard_text = "**Top Contributors:**\n"
                for i, (username, msg_count) in enumerate(results["leaderboard"][:10], 1):
                    leaderboard_text += f"{i}. {username} - {msg_count:,} messages\n"
                await channel.send(leaderboard_text)

            # Distribute rewards
            await self._distribute_rewards(results["rewards"], channel.guild)

            logger.info("Event ended and rewards distributed")

        except Exception as e:
            logger.error(f"Error ending event: {e}")

    async def _distribute_rewards(self, rewards: dict, guild: discord.Guild):
        """Distribute XP rewards to participants"""
        try:
            # Distribute to all eligible participants
            for participant in rewards["all_participants"]:
                member_data = self.bot.member_data.get_member_data(
                    participant["user_id"],
                    guild.id
                )

                member_data["xp"] = member_data.get("xp", 0) + participant["xp"]

            # Distribute bonus to top 3
            for top_user in rewards["top_3"]:
                member_data = self.bot.member_data.get_member_data(
                    top_user["user_id"],
                    guild.id
                )

                member_data["xp"] = member_data.get("xp", 0) + top_user["bonus_xp"]

            # Save all changes
            self.bot.member_data.schedule_save()
            await self.bot.member_data.save_data_async()

            logger.info(f"Distributed rewards to {len(rewards['all_participants'])} participants")

        except Exception as e:
            logger.error(f"Error distributing rewards: {e}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Track messages during active event"""
        # Ignore bots
        if message.author.bot:
            return

        # Ignore DMs
        if not message.guild:
            return

        # Track message if event is active
        if self.event_manager.is_event_active():
            await self.event_manager.track_message(
                message.author.id,
                message.author.display_name
            )

    @commands.command(name='eventstatus')
    async def event_status(self, ctx):
        """Check current event status"""
        info = self.event_manager.get_event_info()

        if not info["active"]:
            container = create_info_card(
                title="No Active Event",
                description="No active server event. Admins can start one with `!eventstart`",
                color_code="gray"
            )
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)
            return

        percentage = (info["current"] / info["goal"] * 100) if info["goal"] > 0 else 0

        # Calculate time remaining
        end_date = datetime.fromisoformat(info["end_date"])
        time_left = end_date - datetime.now()
        days = time_left.days
        hours = time_left.seconds // 3600

        # Prepare stats for the component
        stats = {
            "Progress": f"{info['current']:,} / {info['goal']:,} ({percentage:.1f}%)",
            "Time Left": f"{days}d {hours}h",
            "Participants": f"{info['participants']} soldiers"
        }

        # Show top 3 contributors
        leaderboard = self.event_manager.get_leaderboard(3)
        if leaderboard:
            lb_text = "\n".join([
                f"{['1st', '2nd', '3rd'][i]} {name}: {count:,}"
                for i, (name, count) in enumerate(leaderboard)
            ])
            stats["Top Contributors"] = lb_text

        container = create_stats_container(
            title=f"{info['title']}",
            description="Weekly Community Challenge",
            stats=stats,
            footer="Keep chatting to help reach the goal!",
            color_code="green"
        )

        view = LayoutView()
        view.add_item(container)
        await ctx.send(view=view)

    @commands.command(name='eventstart')
    @commands.has_permissions(administrator=True)
    async def start_event_command(self, ctx):
        """
        Start a new server event with customization modal (Admin only)

        Usage: !eventstart
            Opens a modal to customize the event with options for goal,
            duration, and description.

        Alternatively, use: /event_create (slash command)
        """
        if self.event_manager.is_event_active():
            container = create_error_message(
                title="Event Already Active",
                description="An event is already active! Use `!eventend` first."
            )
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)
            return

        try:
            # Create a view with event type selection
            from discord.ui import Button, View

            class EventTypeSelectView(View):
                def __init__(self, event_manager, bot):
                    super().__init__()
                    self.event_manager = event_manager
                    self.bot = bot

                @discord.ui.button(label="Message Marathon", style=discord.ButtonStyle.primary, emoji="💬")
                async def message_type(self, interaction: discord.Interaction, button: discord.ui.Button):
                    # Show the event creation modal with message type selected
                    modal = CreateEventModal(
                        self.event_manager,
                        EVENT_CHANNEL_ID,
                        EVENT_ROLE_ID,
                        event_type="message"
                    )
                    await interaction.response.send_modal(modal)

                @discord.ui.button(label="XP Race", style=discord.ButtonStyle.secondary, emoji="⚡")
                async def xp_type(self, interaction: discord.Interaction, button: discord.ui.Button):
                    # Show the event creation modal with xp type selected
                    modal = CreateEventModal(
                        self.event_manager,
                        EVENT_CHANNEL_ID,
                        EVENT_ROLE_ID,
                        event_type="xp"
                    )
                    await interaction.response.send_modal(modal)

                @discord.ui.button(label="Reaction Wave", style=discord.ButtonStyle.success, emoji="⭐")
                async def reaction_type(self, interaction: discord.Interaction, button: discord.ui.Button):
                    # Show the event creation modal with reaction type selected
                    modal = CreateEventModal(
                        self.event_manager,
                        EVENT_CHANNEL_ID,
                        EVENT_ROLE_ID,
                        event_type="reaction"
                    )
                    await interaction.response.send_modal(modal)

            info_container = create_info_card(
                title="Start Server Event",
                description="Select the type of event you want to create:"
            )
            view_layout = LayoutView()
            view_layout.add_item(info_container)

            # Create a regular View for the buttons (outside of LayoutView)
            button_view = EventTypeSelectView(self.event_manager, self.bot)

            # Send the layout view with container, then send the button view separately
            await ctx.send(view=view_layout)
            await ctx.send("", view=button_view)

        except Exception as e:
            logger.error(f"Error showing event creation: {e}")
            container = create_error_message(
                title="Error Starting Event",
                description=f"Error: {str(e)}"
            )
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)

    @commands.command(name='eventend')
    @commands.has_permissions(administrator=True)
    async def end_event_command(self, ctx):
        """End the current event and distribute rewards (Admin only)"""
        if not self.event_manager.is_event_active():
            container = create_error_message(
                title="No Active Event",
                description="No active event to end."
            )
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)
            return

        try:
            container = create_info_card(
                title="Ending Event",
                description="Ending event and distributing rewards...",
                color_code="blue"
            )
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)

            await self._end_event_and_distribute_rewards()

            success_container = create_success_message(
                title="Event Ended",
                description="Event ended successfully!"
            )
            success_view = LayoutView()
            success_view.add_item(success_container)
            await ctx.send(view=success_view)

        except Exception as e:
            container = create_error_message(
                title="Error Ending Event",
                description=f"Error ending event: {e}"
            )
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)

    @commands.command(name='eventrestart')
    @commands.has_permissions(administrator=True)
    async def restart_event_command(self, ctx):
        """Restart the current event with fresh data (Admin only)"""
        try:
            # Store current settings
            info = self.event_manager.get_event_info()
            was_active = info["active"]

            if was_active:
                # End current event without distributing rewards
                self.event_manager.data["active"] = False
                await self.event_manager.save_data()

            # Start new event with same settings
            event_info = await self.event_manager.start_event(
                title=info["title"],
                message_goal=info["goal"],
                guild_id=ctx.guild.id
            )

            await ctx.send(f"Event restarted! Progress reset to 0.")

            if was_active:
                await self._announce_event_start(event_info)

        except Exception as e:
            container = create_error_message(
                title="Error Restarting Event",
                description=f"Error restarting event: {e}"
            )
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)

    @commands.command(name='eventprogress')
    @commands.has_permissions(administrator=True)
    async def force_progress_update(self, ctx):
        """Force send a progress update image (Admin only)"""
        if not self.event_manager.is_event_active():
            container = create_error_message(
                title="No Active Event",
                description="No active event."
            )
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)
            return

        try:
            # await ctx.send("⏳ Generating progress update...")
            await self._send_progress_update()
            # await ctx.send("✅ Progress update sent!")

        except Exception as e:
            container = create_error_message(
                title="Error",
                description=f"Error: {e}"
            )
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)

    @commands.command(name='eventinfo')
    @enforce_rate_limit('leaderboard')
    async def event_info(self, ctx):
        """Public command: show current event progress image + leaderboard text + reminder"""
        if not self.event_manager.is_event_active():
            await ctx.send("No active event.")
            return

        try:
            progress_data = self.event_manager.get_progress_data()
            if not progress_data:
                await ctx.send("No event data available.")
                return

            # Generate the start banner (same banner used at event start)
            event_info = self.event_manager.get_event_info()

            # Parse and format start/end dates if possible
            start_str = event_info.get("start_date")
            end_str = event_info.get("end_date")
            try:
                start_dt = datetime.fromisoformat(start_str) if start_str else None
                end_dt = datetime.fromisoformat(end_str) if end_str else None
                start_fmt = start_dt.strftime("%A, %b %d") if start_dt else ""
                end_fmt = end_dt.strftime("%A, %b %d") if end_dt else ""
            except Exception:
                start_fmt = start_str or ""
                end_fmt = end_str or ""

            img = await asyncio.to_thread(
                generate_event_start_banner,
                event_title=event_info.get("title", "Weekly Community Challenge"),
                message_goal=event_info.get("goal", 15000),
                start_date=start_fmt,
                end_date=end_fmt
            )

            # Convert to Discord file and send in the invoking channel
            buffer = BytesIO()
            await asyncio.to_thread(img.save, buffer, 'PNG')
            buffer.seek(0)

            await ctx.send(file=discord.File(buffer, 'event_start.png'))

            # Send leaderboard (top 3) as plain text to avoid flooding
            leaderboard = self.event_manager.get_leaderboard(limit=3)
            if leaderboard:
                leaderboard_text = "**Top Contributors:**\n"
                for i, (username, msg_count) in enumerate(leaderboard, 1):
                    leaderboard_text += f"{i}. {username} - {msg_count:,} messages\n"
                await ctx.send(leaderboard_text)

            # Send reminder small text
            await ctx.send("-# If you want to get notified of future server events, type !remindme")

        except Exception as e:
            logger.error(f"Error in eventinfo command: {e}")
            await ctx.send(f"Error: {e}")

    # New modal-based slash commands
    @app_commands.command(name="event_create", description="create a new server event (admin only)")
    @app_commands.default_permissions(administrator=True)
    async def event_create_slash(self, interaction: discord.Interaction):
        """Create a new event using modal form."""
        modal = CreateEventModal(self.event_manager, EVENT_CHANNEL_ID, EVENT_ROLE_ID)
        await interaction.response.send_modal(modal)

    @app_commands.command(name="event_end", description="end the current server event (admin only)")
    @app_commands.default_permissions(administrator=True)
    async def event_end_slash(self, interaction: discord.Interaction):
        """End current event using modal confirmation."""
        if not self.event_manager.is_event_active():
            await interaction.response.send_message("no active event to end", ephemeral=True)
            return

        modal = EndEventModal(self.event_manager, self)
        await interaction.response.send_modal(modal)

    @app_commands.command(name="event_progress", description="send manual progress update (admin only)")
    @app_commands.default_permissions(administrator=True)
    async def event_progress_slash(self, interaction: discord.Interaction):
        """Send manual progress update."""
        modal = EventProgressModal(self)
        await interaction.response.send_modal(modal)

    @app_commands.command(name="event_template", description="create event from template (admin only)")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(template="choose an event template")
    @app_commands.choices(template=[
        app_commands.Choice(name="⚡ xp race", value="xp_race"),
        app_commands.Choice(name="💬 message marathon", value="message_war"),
        app_commands.Choice(name="⭐ reaction wave", value="reaction_wave"),
        app_commands.Choice(name="🔥 weekend blitz", value="weekend_blitz"),
        app_commands.Choice(name="🏆 monthly mega challenge", value="monthly_mega")
    ])
    async def event_template_slash(self, interaction: discord.Interaction, template: str):
        """Create event from a preset template."""
        if self.event_manager.is_event_active():
            await interaction.response.send_message(
                "an event is already active. end the current event first",
                ephemeral=True
            )
            return

        await interaction.response.defer()

        try:
            template_obj = get_template(template)
            if not template_obj:
                await interaction.followup.send("template not found", ephemeral=True)
                return

            # Get template configuration
            config = template_obj.get_config(interaction.guild.id, self.event_manager)

            # Start event with template config
            event_info = await self.event_manager.start_event(
                title=config['title'],
                event_type=config['event_type'],
                goal=config['goal'],
                duration_days=config['duration_days']
            )

            # Announce event
            event_channel = interaction.guild.get_channel(EVENT_CHANNEL_ID)
            if event_channel:
                img = await asyncio.to_thread(
                    generate_event_start_banner,
                    event_title=config['title'],
                    message_goal=config['goal'],
                    start_date=event_info['start_date'],
                    end_date=event_info['end_date']
                )

                buffer = BytesIO()
                await asyncio.to_thread(img.save, buffer, 'PNG')
                buffer.seek(0)

                file = discord.File(buffer, filename='event_start.png')

                role_mention = ""
                if EVENT_ROLE_ID:
                    role = interaction.guild.get_role(EVENT_ROLE_ID)
                    if role:
                        role_mention = f"{role.mention}\n\n"

                await event_channel.send(
                    f"{role_mention}**{config['icon']} new server event started**\n"
                    f"{config['description']}\n\n"
                    f"type: {config['event_type']}\n"
                    f"goal: {config['goal']:,}\n"
                    f"duration: {config['duration_days']} days",
                    file=file
                )

            await interaction.followup.send(
                f"event '{config['title']}' created from template",
                ephemeral=True
            )

        except Exception as e:
            await interaction.followup.send(
                f"error creating event from template: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(name="event_participants", description="view top event participants")
    async def event_participants_slash(self, interaction: discord.Interaction):
        """Show top event participants across all events."""
        await interaction.response.defer()

        try:
            top_participants = self.event_manager.get_top_participants(limit=10)

            if not top_participants:
                await interaction.followup.send("no participation data available")
                return

            # Build component display
            fields = []
            for i, (user_id, event_count) in enumerate(top_participants, 1):
                try:
                    member = interaction.guild.get_member(int(user_id))
                    name = member.display_name if member else f"user {user_id}"
                except:
                    name = f"user {user_id}"

                fields.append({
                    "name": f"#{i} {name}",
                    "value": f"participated in {event_count} events"
                })

            container = create_stats_container(
                title="top event participants",
                description="members who participated in the most events",
                stats={field['name']: field['value'] for field in fields}
            )

            view = LayoutView()
            view.add_item(container)
            await interaction.followup.send(view=view)

        except Exception as e:
            await interaction.followup.send(f"error fetching participants: {str(e)}")

    @app_commands.command(name="my_event_stats", description="view your event participation stats")
    async def my_event_stats_slash(self, interaction: discord.Interaction):
        """Show user's event participation statistics."""
        await interaction.response.defer(ephemeral=True)

        try:
            stats = self.event_manager.get_participation_stats(interaction.user.id)

            fields = [
                {
                    "name": "total events participated",
                    "value": str(stats['total_events'])
                }
            ]

            if stats['current_event_active']:
                fields.append({
                    "name": "current event contribution",
                    "value": f"{stats['current_event_contribution']:,} messages"
                })

            if stats['events']:
                recent_events = stats['events'][-5:]
                fields.append({
                    "name": "recent events",
                    "value": "\n".join(f"• {event}" for event in recent_events)
                })

            container = create_stats_container(
                title=f"{interaction.user.display_name}'s event stats",
                description="your participation history",
                stats={field['name']: field['value'] for field in fields}
            )

            view = LayoutView()
            view.add_item(container)
            await interaction.followup.send(view=view, ephemeral=True)

        except Exception as e:
            await interaction.followup.send(f"error fetching stats: {str(e)}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(ServerEvent(bot))
