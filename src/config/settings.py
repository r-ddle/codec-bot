"""
Configuration and environment settings for the MGS Discord Bot.
Loads environment variables and provides configuration constants.
"""
import os
import logging
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()

# Simple logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('mgs_bot')

# Bot Configuration
TOKEN: Optional[str] = os.getenv('DISCORD_TOKEN')
NEWS_API_KEY: Optional[str] = os.getenv('NEWS_API_KEY')
WELCOME_CHANNEL_ID: Optional[int] = int(os.getenv('WELCOME_CHANNEL_ID')) if os.getenv('WELCOME_CHANNEL_ID') else None
DATABASE_FILE: str = 'member_data.json'

# Bot Settings
COMMAND_PREFIX: str = '!'
MESSAGE_COOLDOWN: int = 30  # seconds between message XP rewards
TACTICAL_BONUS_MAX: int = 10  # max tactical words counted per message
CODEC_CONVERSATION_TIMEOUT: int = 300  # 5 minutes

# Task Loop Intervals (in minutes)
ALERT_CHECK_INTERVAL: int = 60
VOICE_TRACK_INTERVAL: int = 10
BACKUP_INTERVAL: int = 720  # 12 hours
AUTO_SAVE_INTERVAL: int = 5

# Neon/Postgres sync interval (minutes) - controls how often we push the JSON -> Neon
# Setting this to a larger value (e.g., 60) will reduce Neon API/database requests
NEON_SYNC_INTERVAL_MINUTES: int = 60

# Bot Version Tracking
BOT_VERSION: str = "2.0.0-alpha"
MIGRATION_VERSION: int = 1

# Feature Flags - Enable/disable features without code changes
# IMPORTANT: Keep these False until features are fully tested
FEATURE_FLAGS = {
    'ENABLE_SHOP': True,  # GMP shop system - Phase 3/4
    'ENABLE_MISSIONS': True,  # Daily/weekly missions - Phase 5
    'ENABLE_SLASH_COMMANDS': True,  # Slash commands (already partially implemented)
    'ENABLE_ACHIEVEMENTS': True,  # Achievement system - Phase 6
    'ENABLE_XP_BOOSTERS': True,  # XP multiplier boosters from shop - Phase 3/4
}
