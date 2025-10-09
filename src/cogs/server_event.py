"""
Server Event Cog - Manages weekly community events
"""
import discord
from discord.ext import commands, tasks
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


class ServerEvent(commands.Cog):
    """Weekly server event management"""

    def __init__(self, bot):
        self.bot = bot
        self.event_manager = ServerEventManager()
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

            # Check if we should start new event (Monday and no active event)
            elif not self.event_manager.is_event_active() and datetime.now().weekday() == 0:
                await self._auto_start_event()

            # Check if progress update needed
            elif self.event_manager.should_send_progress_update():
                await self._send_progress_update()

        except Exception as e:
            logger.error(f"Error in event check task: {e}")

    @check_event_tasks.before_loop
    async def before_check_tasks(self):
        await self.bot.wait_until_ready()

    async def _auto_start_event(self):
        """Automatically start event on Monday"""
        try:
            event_info = await self.event_manager.start_event()
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

            # Ping event role
            role = channel.guild.get_role(EVENT_ROLE_ID)
            ping_text = f"{role.mention}" if role else "@botevent"

            await channel.send(
                f"**THIS WEEK'S SERVER EVENT HAS STARTED!** {ping_text}\n\n"
                f"**Goal:** {event_info['goal']:,} messages\n"
                f"**Rewards:** All participants get +500 GMP & +700 XP\n"
                f"**Bonus:** Top 3 get +1500 GMP & +1500 XP",
                file=discord.File(buffer, 'event_start.png')
            )

            # Send reminder message
            await channel.send("-# If you want to get notified of future server events, type !remindme")

            logger.info("✅ Event start announced")

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
                f"📊 **EVENT PROGRESS UPDATE**{top_contributors_text}",
                file=discord.File(buffer, 'event_progress.png')
            )

            # Send reminder message
            await channel.send("-# If you want to get notified of future server events, type !remindme")

            await self.event_manager.mark_progress_update_sent()
            logger.info("✅ Event progress update sent")

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

            logger.info("✅ Event ended and rewards distributed")

        except Exception as e:
            logger.error(f"Error ending event: {e}")

    async def _distribute_rewards(self, rewards: dict, guild: discord.Guild):
        """Distribute GMP and XP rewards to participants"""
        try:
            # Distribute to all eligible participants
            for participant in rewards["all_participants"]:
                member_data = self.bot.member_data.get_member_data(
                    participant["user_id"],
                    guild.id
                )

                member_data["gmp"] = member_data.get("gmp", 0) + participant["gmp"]
                member_data["xp"] = member_data.get("xp", 0) + participant["xp"]

            # Distribute bonus to top 3
            for top_user in rewards["top_3"]:
                member_data = self.bot.member_data.get_member_data(
                    top_user["user_id"],
                    guild.id
                )

                member_data["gmp"] = member_data.get("gmp", 0) + top_user["bonus_gmp"]
                member_data["xp"] = member_data.get("xp", 0) + top_user["bonus_xp"]

            # Save all changes
            self.bot.member_data.schedule_save()
            await self.bot.member_data.save_data_async()

            logger.info(f"✅ Distributed rewards to {len(rewards['all_participants'])} participants")

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
    @enforce_rate_limit('gmp')
    async def event_status(self, ctx):
        """Check current event status"""
        info = self.event_manager.get_event_info()

        if not info["active"]:
            await ctx.send("❌ No active server event. Admins can start one with `!eventstart`")
            return

        percentage = (info["current"] / info["goal"] * 100) if info["goal"] > 0 else 0

        # Calculate time remaining
        end_date = datetime.fromisoformat(info["end_date"])
        time_left = end_date - datetime.now()
        days = time_left.days
        hours = time_left.seconds // 3600

        embed = discord.Embed(
            title=f"🎯 {info['title']}",
            description="Weekly Community Challenge",
            color=0x00ff00
        )

        embed.add_field(
            name="Progress",
            value=f"{info['current']:,} / {info['goal']:,} ({percentage:.1f}%)",
            inline=True
        )

        embed.add_field(
            name="Time Left",
            value=f"{days}d {hours}h",
            inline=True
        )

        embed.add_field(
            name="Participants",
            value=f"{info['participants']} soldiers",
            inline=True
        )

        # Show top 3
        leaderboard = self.event_manager.get_leaderboard(3)
        if leaderboard:
            lb_text = "\n".join([
                f"{'🥇🥈🥉'[i]} {name}: {count:,}"
                for i, (name, count) in enumerate(leaderboard)
            ])
            embed.add_field(name="Top Contributors", value=lb_text, inline=False)

        embed.set_footer(text="Keep chatting to help reach the goal!")

        await ctx.send(embed=embed)

    @commands.command(name='eventstart')
    @commands.has_permissions(administrator=True)
    async def start_event_command(
        self,
        ctx,
        goal: Optional[int] = 15000,
        *,
        title: Optional[str] = "Weekly Community Challenge"
    ):
        """
        Start a new server event (Admin only)

        Usage: !eventstart [goal] [title]
        Example: !eventstart 20000 "Holiday Special Event"
        """
        if self.event_manager.is_event_active():
            await ctx.send("⚠️ An event is already active! Use `!eventend` first.")
            return

        try:
            event_info = await self.event_manager.start_event(
                title=title,
                message_goal=goal
            )

            await ctx.send(f"✅ Event **{title}** started with goal: {goal:,} messages!")
            await self._announce_event_start(event_info)

        except Exception as e:
            await ctx.send(f"❌ Error starting event: {e}")

    @commands.command(name='eventend')
    @commands.has_permissions(administrator=True)
    async def end_event_command(self, ctx):
        """End the current event and distribute rewards (Admin only)"""
        if not self.event_manager.is_event_active():
            await ctx.send("❌ No active event to end.")
            return

        try:
            await ctx.send("⏳ Ending event and distributing rewards...")
            await self._end_event_and_distribute_rewards()
            await ctx.send("✅ Event ended successfully!")

        except Exception as e:
            await ctx.send(f"❌ Error ending event: {e}")

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
                message_goal=info["goal"]
            )

            await ctx.send(f"✅ Event restarted! Progress reset to 0.")

            if was_active:
                await self._announce_event_start(event_info)

        except Exception as e:
            await ctx.send(f"❌ Error restarting event: {e}")

    @commands.command(name='eventprogress')
    @commands.has_permissions(administrator=True)
    async def force_progress_update(self, ctx):
        """Force send a progress update image (Admin only)"""
        if not self.event_manager.is_event_active():
            await ctx.send("❌ No active event.")
            return

        try:
            # await ctx.send("⏳ Generating progress update...")
            await self._send_progress_update()
            # await ctx.send("✅ Progress update sent!")

        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    @commands.command(name='eventinfo')
    @enforce_rate_limit('leaderboard')
    async def event_info(self, ctx):
        """Public command: show current event progress image + leaderboard text + reminder"""
        if not self.event_manager.is_event_active():
            await ctx.send("❌ No active event.")
            return

        try:
            progress_data = self.event_manager.get_progress_data()
            if not progress_data:
                await ctx.send("❌ No event data available.")
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
            await ctx.send(f"❌ Error: {e}")


async def setup(bot):
    await bot.add_cog(ServerEvent(bot))
