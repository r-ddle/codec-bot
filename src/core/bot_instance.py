"""
Core bot instance and task loops for the MGS Discord Bot.
"""
import discord
from discord.ext import tasks, commands
import random
import re
from typing import Dict, Any
from config.settings import COMMAND_PREFIX, logger, ALERT_CHECK_INTERVAL, VOICE_TRACK_INTERVAL, BACKUP_INTERVAL, AUTO_SAVE_INTERVAL, TACTICAL_BONUS_MAX
from config.constants import MGS_CODEC_SOUNDS, MGS_QUOTES, TACTICAL_WORDS, ACTIVITY_REWARDS
from database.member_data import MemberData
from database.neon_db import NeonDatabase


class MGSBot(commands.Bot):
    """Main bot class with task loops and tactical word detection."""

    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix=COMMAND_PREFIX, intents=intents)

        # Initialize Neon database
        self.neon_db = NeonDatabase()

        # Initialize member data with Neon integration
        self.member_data = MemberData(neon_db=self.neon_db)

        self.remove_command('help')  # Remove default help to use custom one
        self.codec_conversations: Dict[int, Dict[str, Any]] = {}

    async def setup_hook(self):
        """Initialize bot tasks and sync slash commands."""
        # Connect to Neon database
        await self.neon_db.connect()

        # Start background tasks
        self.check_alerts.start()
        self.track_voice_activity.start()
        self.backup_data.start()
        self.auto_save_data.start()

        try:
            synced = await self.tree.sync()
            logger.info(f"✅ Synced {len(synced)} slash commands")
        except Exception as e:
            logger.error(f"❌ Error syncing slash commands: {e}")

    @tasks.loop(minutes=ALERT_CHECK_INTERVAL)
    async def check_alerts(self):
        """Random codec calls to general channel."""
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
                    if not member.voice.self_deaf and not member.voice.self_mute:
                        self.member_data.add_xp_and_gmp(
                            member.id, guild.id,
                            ACTIVITY_REWARDS["voice_minute"]["gmp"],
                            ACTIVITY_REWARDS["voice_minute"]["xp"],
                            "voice_minute"
                        )

    @tasks.loop(hours=BACKUP_INTERVAL // 60)
    async def backup_data(self):
        """Periodic data backup."""
        await self.member_data.save_data_async()

    @tasks.loop(minutes=AUTO_SAVE_INTERVAL)
    async def auto_save_data(self):
        """Auto-save data if there are pending changes."""
        if self.member_data._pending_saves:
            await self.member_data.save_data_async()

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
