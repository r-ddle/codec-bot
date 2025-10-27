"""
Core bot instance and task loops for the MGS Discord Bot.
"""
import discord
from discord.ext import tasks, commands
from discord.ui import LayoutView
import random
import re
import time
from datetime import datetime, date
from typing import Dict, Any
from config.settings import COMMAND_PREFIX, logger, VOICE_TRACK_INTERVAL, BACKUP_INTERVAL, AUTO_SAVE_INTERVAL, FEATURE_FLAGS
from config.constants import MGS_QUOTES, ACTIVITY_REWARDS
from database.member_data import MemberData
from database.neon_db import NeonDatabase
from database.extensions import DatabaseExtensions
from utils.components_builder import create_info_card


class MGSBot(commands.Bot):
    """Main bot class with task loops and tactical word detection."""

    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix=COMMAND_PREFIX, intents=intents)

        # Initialize Neon database
        self.neon_db = NeonDatabase()

        # Initialize database extensions (Phase 1)
        self.db_extensions = DatabaseExtensions(self.neon_db)

        # Initialize member data with Neon integration
        self.member_data = MemberData(neon_db=self.neon_db)

        self.remove_command('help')  # Remove default help to use custom one
        self.bot_metadata_file = 'bot_metadata.json'
        self.last_monthly_reset = None  # Track last monthly reset date
        self.load_bot_metadata()

    def load_bot_metadata(self):
        """Load bot metadata from JSON file."""
        try:
            import json
            import os
            if os.path.exists(self.bot_metadata_file):
                with open(self.bot_metadata_file, 'r') as f:
                    data = json.load(f)
                    if 'last_monthly_reset' in data:
                        # Parse the date string back to date object
                        reset_date_str = data['last_monthly_reset']
                        self.last_monthly_reset = datetime.strptime(reset_date_str, '%Y-%m-%d').date()
                        logger.info(f"Loaded last monthly reset date: {self.last_monthly_reset}")
        except Exception as e:
            logger.error(f"Error loading bot metadata: {e}")
            self.last_monthly_reset = None

    def save_bot_metadata(self):
        """Save bot metadata to JSON file."""
        try:
            import json
            data = {}
            if self.last_monthly_reset:
                data['last_monthly_reset'] = self.last_monthly_reset.isoformat()

            with open(self.bot_metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving bot metadata: {e}")

    async def setup_hook(self):
        """Initialize bot tasks and sync slash commands."""
        # Connect to Neon database
        success, error = await self.neon_db.connect()
        if not success:
            logger.error(f"Failed to connect to Neon database: {error}")

        # Force load from database if:
        # 1. Local JSON is empty/missing, OR
        # 2. Database is available (prioritize database as source of truth)
        if self.neon_db.pool:
            # Always check database first if it's available
            logger.info("🔄 Loading member data from Neon database (database is source of truth)...")
            await self.member_data.load_from_database()
        elif not self.member_data.data:
            # Fallback to local JSON if database isn't available
            logger.warning("⚠️ Database not available, using local JSON data")

        # Clean up database to only contain our guild's data
        if self.neon_db.pool:
            logger.info("🧹 Cleaning up database to only contain our guild's data...")
            await self.neon_db.cleanup_other_guilds(1423506532745875560)

        # Initialize extended database schema (Phase 1) - safe, won't affect existing data
        if self.neon_db.pool:
            await self.db_extensions.init_extended_schema()
            logger.info("✅ Database extensions initialized")

        # Start background tasks
        self.track_voice_activity.start()
        self.backup_data.start()
        self.auto_save_data.start()
        self.cleanup_rate_limits.start()
        self.monthly_xp_reset.start()

        # Add slash command groups to the tree
        slash_cog = self.get_cog('SlashCommands')
        if slash_cog and hasattr(slash_cog, 'event_group'):
            # Check if group is already added
            existing_commands = [cmd.name for cmd in self.tree.get_commands()]
            if 'event' not in existing_commands:
                self.tree.add_command(slash_cog.event_group)
                logger.info("✅ Added event command group to tree")

        try:
            synced = await self.tree.sync()
            logger.info(f"✅ Synced {len(synced)} slash commands")
        except Exception as e:
            logger.error(f"❌ Error syncing slash commands: {e}")


    @tasks.loop(minutes=VOICE_TRACK_INTERVAL)
    async def track_voice_activity(self):
        """Track voice activity and award XP."""
        for guild in self.guilds:
            for voice_channel in guild.voice_channels:
                for member in voice_channel.members:
                    if member.bot:
                        continue
                    # Award XP only if NOT deafened or muted (active participation)
                    if not member.voice.self_deaf and not member.voice.self_mute and not member.voice.deaf and not member.voice.mute:
                        self.member_data.add_xp(
                            member.id, guild.id,
                            ACTIVITY_REWARDS["voice_minute"]["xp"],
                            "voice_minute"
                        )

    @tasks.loop(hours=BACKUP_INTERVAL // 60)
    async def backup_data(self):
        """Periodic data backup."""
        # Force Neon sync during periodic backups
        await self.member_data.save_data_async(force=True)

    @tasks.loop(minutes=AUTO_SAVE_INTERVAL)
    async def auto_save_data(self):
        """Auto-save data if there are pending changes."""
        if self.member_data._pending_saves:
            await self.member_data.save_data_async()

    @tasks.loop(hours=1)
    async def cleanup_rate_limits(self):
        """Cleanup old rate limit entries to prevent memory leaks."""
        from utils.rate_limiter import rate_limiter
        rate_limiter.cleanup_old_entries()

    @tasks.loop(hours=6)
    async def monthly_xp_reset(self):
        """Reset XP for all members on the 1st of each month."""
        current_date = date.today()

        # Only reset on the 1st of the month
        if current_date.day != 1:
            return

        # Don't reset if we already reset this month
        if self.last_monthly_reset and self.last_monthly_reset.month == current_date.month and self.last_monthly_reset.year == current_date.year:
            return

        logger.info(f"🌙 Starting monthly XP reset for {current_date.strftime('%B %Y')}")

        reset_count = 0
        total_guilds = 0

        # Reset XP for all members in all guilds
        for guild_id, guild_data in self.member_data.data.items():
            total_guilds += 1
            for member_id, member_data_entry in guild_data.items():
                if member_data_entry.get('xp', 0) > 0:
                    # Keep rank, GMP, and all other stats - only reset XP
                    old_xp = member_data_entry['xp']
                    member_data_entry['xp'] = 0
                    reset_count += 1

                    logger.debug(f"Reset XP for member {member_id} in guild {guild_id}: {old_xp} -> 0")

                # Also reset Word-Up points monthly
                if member_data_entry.get('word_up_points', 0) > 0:
                    old_points = member_data_entry['word_up_points']
                    member_data_entry['word_up_points'] = 0
                    logger.debug(f"Reset Word-Up points for member {member_id} in guild {guild_id}: {old_points} -> 0")

        # Mark reset as completed
        self.last_monthly_reset = current_date
        self.save_bot_metadata()

        # Force save the changes
        await self.member_data.save_data_async(force=True)

        logger.info(f"✅ Monthly XP reset completed: {reset_count} members across {total_guilds} guilds had their XP reset")

        # Announce the reset in all guilds
        for guild in self.guilds:
            try:
                # Try to find a general channel to announce
                general = discord.utils.get(guild.text_channels, name='general')
                if general:
                    container = create_info_card(
                        title="🌙 MONTHLY XP RESET",
                        description=f"**{current_date.strftime('%B %Y')}** XP reset completed!\n\n"
                                  f"• All XP has been reset to 0\n"
                                  f"• Word-Up points reset to 0\n"
                                  f"• Ranks and multipliers are preserved\n"
                                  f"• New monthly competition begins now!",
                        footer="Higher ranks = better multipliers for the new month!",
                        color_code="blue"
                    )
                    view = LayoutView()
                    view.add_item(container)
                    await general.send(view=view)
            except Exception as e:
                logger.error(f"Failed to announce monthly reset in guild {guild.id}: {e}")
