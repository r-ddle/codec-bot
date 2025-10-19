"""
Voice events - Handlers for voice channel activity tracking.
Uses periodic checks to award XP while users are in calls (bot restart safe).
"""
import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone
from config.bot_settings import VOICE_TRACKED_CHANNELS, REWARDS
from config.settings import logger


class VoiceEvents(commands.Cog):
    """Event handlers for voice channel activity tracking."""

    def __init__(self, bot):
        self.bot = bot
        # Track when users were last rewarded (for minute-by-minute XP)
        self.last_reward_time = {}  # {(user_id, guild_id): datetime}
        # Start the periodic voice XP task
        self.voice_xp_task.start()

    def cog_unload(self):
        """Clean up when cog is unloaded."""
        self.voice_xp_task.cancel()

    @tasks.loop(seconds=60)  # Check every minute
    async def voice_xp_task(self):
        """Award XP to users currently in tracked voice channels."""
        try:
            for guild in self.bot.guilds:
                for channel_id in VOICE_TRACKED_CHANNELS:
                    channel = guild.get_channel(channel_id)

                    if not channel or not isinstance(channel, discord.VoiceChannel):
                        continue

                    # Check each member in the voice channel
                    for member in channel.members:
                        # Skip bots
                        if member.bot:
                            continue

                        user_id = member.id
                        guild_id = guild.id
                        key = (user_id, guild_id)
                        current_time = datetime.now(timezone.utc)

                        # Check if we've already rewarded in the last minute
                        last_reward = self.last_reward_time.get(key)
                        if last_reward and (current_time - last_reward).total_seconds() < 55:
                            # Skip if rewarded less than 55 seconds ago (buffer for timing)
                            continue

                        # Store old rank before XP change
                        member_data = self.bot.member_data.get_member_data(user_id, guild_id)
                        old_rank = member_data.get('rank', 'Rookie')

                        # Award XP for this minute
                        xp_per_minute = REWARDS["voice_minute"]["xp"]
                        rank_changed, new_rank = self.bot.member_data.add_xp(
                            user_id, guild_id,
                            xp_per_minute,
                            "voice_minute"
                        )

                        # Update last reward time
                        self.last_reward_time[key] = current_time

                        # Send promotion notification if rank changed
                        if rank_changed:
                            await self._send_voice_promotion(member, channel, old_rank, new_rank, 1)

                        logger.debug(f"Voice XP: {member.name} earned {xp_per_minute} XP (1 min in {channel.name})")

        except Exception as e:
            logger.error(f"Error in voice_xp_task: {e}")

    @voice_xp_task.before_loop
    async def before_voice_xp_task(self):
        """Wait until the bot is ready before starting the task."""
        await self.bot.wait_until_ready()

    async def _send_voice_promotion(self, member, channel, old_rank, new_rank, minutes):
        """Helper to send voice promotion notifications with image."""
        try:
            import asyncio
            from io import BytesIO
            from utils.role_manager import update_member_roles
            from utils.rank_system import get_rank_data_by_name
            from utils.daily_supply_gen import generate_promotion_card

            # Update Discord role
            role_updated = await update_member_roles(member, new_rank)

            # Get member data
            member_data = self.bot.member_data.get_member_data(member.id, member.guild.id)

            # Get old rank (we need to track this better, for now use a fallback)
            old_rank = "Previous Rank"  # This is a limitation we can improve later

            # Get role name if granted
            rank_data = get_rank_data_by_name(new_rank)
            role_name = rank_data.get("role_name") if role_updated else None

            # Generate promotion card image (off the main thread)
            img = await asyncio.to_thread(
                generate_promotion_card,
                username=member.display_name,
                old_rank=old_rank,
                new_rank=new_rank,
                current_xp=member_data['xp'],
                role_granted=role_name
            )

            # Convert to Discord file
            image_bytes = BytesIO()
            await asyncio.to_thread(img.save, image_bytes, format='PNG')
            image_bytes.seek(0)

            file = discord.File(fp=image_bytes, filename="promotion.png")

            # Add context message
            context_msg = "**RANK PROMOTION** - Earned through voice activity!"

            await channel.send(content=context_msg, file=file)
            logger.info(f"PROMOTION: {member.name} promoted to {new_rank} via voice activity")

        except Exception as e:
            logger.error(f"Error sending voice promotion notification: {e}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Clean up tracking when users leave voice channels."""
        # Ignore bots
        if member.bot:
            return

        user_id = member.id
        guild_id = member.guild.id
        key = (user_id, guild_id)

        # Clean up last reward time when user leaves tracked channels
        if before.channel and before.channel.id in VOICE_TRACKED_CHANNELS:
            if not (after.channel and after.channel.id in VOICE_TRACKED_CHANNELS):
                # User left all tracked channels
                if key in self.last_reward_time:
                    del self.last_reward_time[key]
                    logger.info(f"Voice tracking ended: {member.name}")

        # Log when user joins tracked channel
        if after.channel and after.channel.id in VOICE_TRACKED_CHANNELS:
            if not (before.channel and before.channel.id in VOICE_TRACKED_CHANNELS):
                logger.info(f"Voice tracking started: {member.name} in channel {after.channel.name}")


async def setup(bot):
    """Load the VoiceEvents cog."""
    await bot.add_cog(VoiceEvents(bot))
