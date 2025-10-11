"""
Global Bot Settings & Configuration
All hardcoded values and tunable parameters in one place.
Edit values here instead of searching through the codebase.

Outer Heaven: Exiled Soldiers - Exclusive Bot
"""

# ═══════════════════════════════════════════════════════════════════
# DISCORD SERVER IDS (Update these for your server)
# ═══════════════════════════════════════════════════════════════════

# Event System
EVENT_ROLE_ID = 1426451950207242280
EVENT_CHANNEL_ID = 1423506534658474181

# Word-Up Game Channel
WORD_UP_CHANNEL_ID = 1423506535199281254

# Voice Tracking Channels
VOICE_TRACKED_CHANNELS = [
    1423506535199281258,
    1423506535199281260,
    1423506535199281261
]

# Add more channel/role IDs as needed
# WELCOME_CHANNEL_ID = None
# ADMIN_ROLE_ID = None
# MODERATOR_ROLE_ID = None

# ═══════════════════════════════════════════════════════════════════
# RATE LIMITING SETTINGS (seconds)
# ═══════════════════════════════════════════════════════════════════

RATE_LIMITS = {
    # Basic commands
    'status': 5,           # Status check
    'rank': 10,            # Rank card (image generation)
    'leaderboard': 15,     # Leaderboard (image generation)

    # Profile commands (image-heavy, higher cooldowns)
    'profile': 15,         # Profile cards
    'setbio': 10,          # Set bio
}

# Rate limit cleanup interval (seconds)
RATE_LIMIT_CLEANUP_INTERVAL = 3600  # 1 hour
RATE_LIMIT_MAX_AGE = 3600           # Remove entries older than 1 hour

# ═══════════════════════════════════════════════════════════════════
# REWARD AMOUNTS (XP ONLY)
# ═══════════════════════════════════════════════════════════════════

# Activity rewards
REWARDS = {
    "message": {"xp": 3},
    "voice_minute": {"xp": 2},
    "reaction": {"xp": 1},
    "reaction_received": {"xp": 2},
    "daily_bonus": {"xp": 50}
}

# Starting XP for new members
STARTING_XP = 0

# ═══════════════════════════════════════════════════════════════════
# GAMEPLAY SETTINGS
# ═══════════════════════════════════════════════════════════════════

# Message cooldown (seconds between message XP rewards)
MESSAGE_COOLDOWN = 30

# Daily streak multiplier
DAILY_STREAK_BONUS_PER_DAY = 10  # Extra XP per streak day

# Bio character limit
BIO_MAX_LENGTH = 150

# ═══════════════════════════════════════════════════════════════════
# TASK INTERVALS (minutes)
# ═══════════════════════════════════════════════════════════════════

VOICE_TRACK_INTERVAL = 1        # Voice activity tracking
BACKUP_INTERVAL = 360           # Data backup (6 hours)
AUTO_SAVE_INTERVAL = 5          # Auto-save pending changes

# ═══════════════════════════════════════════════════════════════════
# EVENT SYSTEM SETTINGS
# ═══════════════════════════════════════════════════════════════════

# Default event settings
DEFAULT_EVENT_GOAL = 500      # Default message goal (15-1000 range)
EVENT_DURATION_DAYS = 7         # Week-long events
EVENT_PROGRESS_UPDATE_INTERVAL = 48  # Hours between progress updates

# Event rewards (XP only)
EVENT_PARTICIPATION_REWARD = {
    "xp": 50
}

EVENT_TOP_3_BONUS = {
    "xp": 500
}

# ═══════════════════════════════════════════════════════════════════
# IMAGE GENERATION SETTINGS
# ═══════════════════════════════════════════════════════════════════

# Maximum concurrent image generation tasks (prevents CPU overload)
MAX_CONCURRENT_IMAGE_GENERATION = 3

# Image caching (future feature)
ENABLE_IMAGE_CACHING = False
IMAGE_CACHE_SIZE = 100
IMAGE_CACHE_TTL = 300  # seconds

# ═══════════════════════════════════════════════════════════════════
# FEATURE FLAGS
# ═══════════════════════════════════════════════════════════════════

FEATURES = {
    'daily_streaks': True,
    'voice_activity_tracking': True,
    'server_events': True,
    'automatic_backups': True,
    'neon_database': True,
    'word_up_game': True,  # Word-Up game moderation
}

# ═══════════════════════════════════════════════════════════════════
# LOGGING & DEBUG
# ═══════════════════════════════════════════════════════════════════

# Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL = "INFO"

# Enable verbose logging for specific systems
DEBUG_RATE_LIMITER = False
DEBUG_IMAGE_GENERATION = False
DEBUG_DATABASE = False

# ═══════════════════════════════════════════════════════════════════
# LEGACY USER SUPPORT
# ═══════════════════════════════════════════════════════════════════

# Users who joined before this date use old XP thresholds
LEGACY_USER_CUTOFF_DATE = "2025-10-08"

# ═══════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def get_rate_limit(command_name: str) -> int:
    """Get rate limit for a command (with fallback)."""
    return RATE_LIMITS.get(command_name, 10)  # Default 10 seconds


def get_reward(activity_type: str, resource: str = 'xp') -> int:
    """Get reward amount for an activity."""
    return REWARDS.get(activity_type, {}).get(resource, 0)


def is_feature_enabled(feature_name: str) -> bool:
    """Check if a feature is enabled."""
    return FEATURES.get(feature_name, True)
