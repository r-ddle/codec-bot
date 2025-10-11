"""
Voice events - Handlers for voice channel activity tracking.
"""
import discord
from discord.ext import commands
from datetime import datetime, timezone
from config.bot_settings import VOICE_TRACKED_CHANNELS, REWARDS
from config.settings import logger


class VoiceEvents(commands.Cog):
    """Event handlers for voice channel activity tracking."""

    def __init__(self, bot):
        self.bot = bot
        # Track when users join voice channels
        self.voice_join_times = {}  # {(user_id, guild_id): datetime}

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Track voice channel activity."""
        # Ignore bots
        if member.bot:
            return

        guild_id = member.guild.id
        user_id = member.id
        key = (user_id, guild_id)

        # Check if user joined a tracked voice channel
        if after.channel and after.channel.id in VOICE_TRACKED_CHANNELS:
            # User joined a tracked voice channel
            if key not in self.voice_join_times:
                self.voice_join_times[key] = datetime.now(timezone.utc)
                logger.info(f"Voice tracking started: {member.name} in channel {after.channel.name}")

        # Check if user left a tracked voice channel
        elif before.channel and before.channel.id in VOICE_TRACKED_CHANNELS:
            # User left a tracked voice channel
            if key in self.voice_join_times:
                # Calculate time spent
                join_time = self.voice_join_times[key]
                leave_time = datetime.now(timezone.utc)
                duration = (leave_time - join_time).total_seconds()
                minutes = int(duration // 60)

                if minutes > 0:
                    # Award XP for voice time
                    member_data = self.bot.member_data.get_member_data(user_id, guild_id)
                    xp_per_minute = REWARDS["voice_minute"]["xp"]
                    xp_earned = minutes * xp_per_minute

                    member_data['voice_minutes'] = member_data.get('voice_minutes', 0) + minutes
                    member_data['xp'] = member_data.get('xp', 0) + xp_earned

                    logger.info(f"Voice activity: {member.name} spent {minutes} min, earned {xp_earned} XP")

                    # Schedule save
                    self.bot.member_data.schedule_save()

                # Remove tracking
                del self.voice_join_times[key]

        # Handle case where user switches between channels
        elif before.channel and after.channel:
            # Check if switching from tracked to untracked or vice versa
            before_tracked = before.channel.id in VOICE_TRACKED_CHANNELS
            after_tracked = after.channel.id in VOICE_TRACKED_CHANNELS

            if before_tracked and not after_tracked:
                # Leaving tracked channel
                if key in self.voice_join_times:
                    join_time = self.voice_join_times[key]
                    leave_time = datetime.now(timezone.utc)
                    duration = (leave_time - join_time).total_seconds()
                    minutes = int(duration // 60)

                    if minutes > 0:
                        member_data = self.bot.member_data.get_member_data(user_id, guild_id)
                        xp_per_minute = REWARDS["voice_minute"]["xp"]
                        xp_earned = minutes * xp_per_minute

                        member_data['voice_minutes'] = member_data.get('voice_minutes', 0) + minutes
                        member_data['xp'] = member_data.get('xp', 0) + xp_earned

                        logger.info(f"Voice activity: {member.name} spent {minutes} min, earned {xp_earned} XP")
                        self.bot.member_data.schedule_save()

                    del self.voice_join_times[key]

            elif not before_tracked and after_tracked:
                # Joining tracked channel
                self.voice_join_times[key] = datetime.now(timezone.utc)
                logger.info(f"Voice tracking started: {member.name} in channel {after.channel.name}")


async def setup(bot):
    """Load the VoiceEvents cog."""
    await bot.add_cog(VoiceEvents(bot))
