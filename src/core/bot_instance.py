"""
Core bot instance and task loops for the MGS Discord Bot.
"""
import discord
from discord.ext import tasks, commands
import random
import re
import time
from typing import Dict, Any
from config.settings import COMMAND_PREFIX, logger, ALERT_CHECK_INTERVAL, VOICE_TRACK_INTERVAL, BACKUP_INTERVAL, AUTO_SAVE_INTERVAL, TACTICAL_BONUS_MAX, FEATURE_FLAGS, CODEC_CONVERSATION_TIMEOUT
from config.constants import MGS_CODEC_SOUNDS, MGS_QUOTES, TACTICAL_WORDS, ACTIVITY_REWARDS
from database.member_data import MemberData
from database.neon_db import NeonDatabase
from database.extensions import DatabaseExtensions
from utils.shop import ShopSystem


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

        # Initialize shop system (Phase 3)
        self.shop_system = ShopSystem(self)

        self.remove_command('help')  # Remove default help to use custom one
        self.codec_conversations: Dict[int, Dict[str, Any]] = {}

        # Track last cleanup time for codec conversations
        self._last_codec_cleanup = 0

    async def setup_hook(self):
        """Initialize bot tasks and sync slash commands."""
        # Connect to Neon database
        await self.neon_db.connect()

        # Initialize extended database schema (Phase 1) - safe, won't affect existing data
        if self.neon_db.pool:
            await self.db_extensions.init_extended_schema()
            logger.info("✅ Database extensions initialized")

        # Start background tasks
        self.check_alerts.start()
        self.track_voice_activity.start()
        self.backup_data.start()
        self.auto_save_data.start()
        self.cleanup_rate_limits.start()

        try:
            synced = await self.tree.sync()
            logger.info(f"✅ Synced {len(synced)} slash commands")
        except Exception as e:
            logger.error(f"❌ Error syncing slash commands: {e}")

    @tasks.loop(minutes=ALERT_CHECK_INTERVAL)
    async def check_alerts(self):
        """Random codec calls to general channel and cleanup old conversations."""
        # Cleanup old codec conversations (prevent memory leak)
        current_time = time.time()
        if current_time - self._last_codec_cleanup > 3600:  # Cleanup every hour
            expired_channels = [
                channel_id for channel_id, data in self.codec_conversations.items()
                if current_time - data.get('start_time', 0) > CODEC_CONVERSATION_TIMEOUT
            ]
            for channel_id in expired_channels:
                del self.codec_conversations[channel_id]
            if expired_channels:
                logger.info(f"Cleaned up {len(expired_channels)} expired codec conversations")
            self._last_codec_cleanup = current_time

        # Random codec alerts
        for guild in self.guilds:
            if random.random() < 0.2:
                general = discord.utils.get(guild.text_channels, name='general')
                if general:
                    sound = random.choice(MGS_CODEC_SOUNDS)
                    quote = random.choice(MGS_QUOTES)
                    await general.send(f"{sound}\nColonel: {quote}")

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
                        self.member_data.add_xp_and_gmp(
                            member.id, guild.id,
                            ACTIVITY_REWARDS["voice_minute"]["gmp"],
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

    def check_tactical_words(self, message_content: str) -> int:
        """
        Detect tactical words in message content.

        Args:
            message_content: Message text to analyze

        Returns:
            Number of tactical words found (capped at max)
        """
        count = 0
        words_found = set()
        lower_content = message_content.lower()

        for word in TACTICAL_WORDS:
            pattern = r'\b' + re.escape(word.lower()) + r'\b'
            matches = re.findall(pattern, lower_content)
            if matches:
                count += len(matches)
                words_found.add(word)

        if count > 0:
            logger.info(f"Tactical words found: {list(words_found)} (Total: {count})")

        return min(count, TACTICAL_BONUS_MAX)
