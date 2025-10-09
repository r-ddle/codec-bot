"""
Global Bot Settings & Configuration
All hardcoded values and tunable parameters in one place.
Edit values here instead of searching through the codebase.
"""

# ═══════════════════════════════════════════════════════════════════
# DISCORD SERVER IDS (Update these for your server)
# ═══════════════════════════════════════════════════════════════════

# Event System
EVENT_ROLE_ID = 1425552378798805132
EVENT_CHANNEL_ID = 1322065560707530854

# Add more channel/role IDs as needed
# WELCOME_CHANNEL_ID = None
# ADMIN_ROLE_ID = None
# MODERATOR_ROLE_ID = None

# ═══════════════════════════════════════════════════════════════════
# RATE LIMITING SETTINGS (seconds)
# ═══════════════════════════════════════════════════════════════════

RATE_LIMITS = {
    # Basic commands
    'gmp': 5,              # Status/balance check
    'rank': 10,            # Rank card (image generation)
    'leaderboard': 15,     # Leaderboard (image generation)
    'daily': 60,           # Daily bonus claim check

    # Shop commands
    'shop': 5,             # View shop (image generation)
    'buy': 3,              # Purchase items
    'inventory': 5,        # View inventory
    'use': 10,             # Use items / setbio

    # Info & Intel
    'intel': 30,           # Intel commands, codec

    # Image-heavy profile commands (higher cooldowns recommended)
    'profile': 15,         # Profile cards (all variants)
}

# Rate limit cleanup interval (seconds)
RATE_LIMIT_CLEANUP_INTERVAL = 3600  # 1 hour
RATE_LIMIT_MAX_AGE = 3600           # Remove entries older than 1 hour

# ═══════════════════════════════════════════════════════════════════
# REWARD AMOUNTS (GMP & XP)
# ═══════════════════════════════════════════════════════════════════

# Activity rewards
REWARDS = {
    "message": {"gmp": 15, "xp": 3},
    "voice_minute": {"gmp": 8, "xp": 2},
    "reaction": {"gmp": 3, "xp": 1},
    "reaction_received": {"gmp": 8, "xp": 2},
    "daily_bonus": {"gmp": 200, "xp": 50},
    "tactical_word": {"gmp": 25, "xp": 8}
}

# Starting balance for new members
STARTING_GMP = 1000
STARTING_XP = 0

# ═══════════════════════════════════════════════════════════════════
# GAMEPLAY SETTINGS
# ═══════════════════════════════════════════════════════════════════

# Message cooldown (seconds between message XP rewards)
MESSAGE_COOLDOWN = 30

# Tactical word bonus cap per message
TACTICAL_BONUS_MAX = 5

# Daily streak multiplier
DAILY_STREAK_BONUS_PER_DAY = 10  # Extra GMP per streak day

# Bio character limit
BIO_MAX_LENGTH = 150

# ═══════════════════════════════════════════════════════════════════
# TASK INTERVALS (minutes)
# ═══════════════════════════════════════════════════════════════════

ALERT_CHECK_INTERVAL = 60       # Random codec alerts
VOICE_TRACK_INTERVAL = 1        # Voice activity tracking
BACKUP_INTERVAL = 360           # Data backup (6 hours)
AUTO_SAVE_INTERVAL = 5          # Auto-save pending changes

# ═══════════════════════════════════════════════════════════════════
# EVENT SYSTEM SETTINGS
# ═══════════════════════════════════════════════════════════════════

# Default event settings
DEFAULT_EVENT_GOAL = 15000      # Default message goal
EVENT_DURATION_DAYS = 7         # Week-long events
EVENT_PROGRESS_UPDATE_INTERVAL = 48  # Hours between progress updates

# Event rewards
EVENT_PARTICIPATION_REWARD = {
    "gmp": 500,
    "xp": 700
}

EVENT_TOP_3_BONUS = {
    "gmp": 1500,
    "xp": 1500
}

# ═══════════════════════════════════════════════════════════════════
# SHOP ITEMS & PRICES
# ═══════════════════════════════════════════════════════════════════

SHOP_ITEMS_CONFIG = [
    {
        'name': 'CUSTOM ROLE',
        'description': 'Create your own custom role with any name & color',
        'price': 15000,
        'item_type': 'custom_role',
        'icon': '🎨'
    },
    {
        'name': 'EXTRA DAILY',
        'description': 'Claim an additional daily supply drop today',
        'price': 500,
        'item_type': 'extra_daily',
        'icon': '📦'
    },
    {
        'name': '2HR BOOSTER',
        'description': 'Extra XP/GMP + reduced cooldown (30s->10s)',
        'price': 1000,
        'item_type': 'xp_boost_2h',
        'duration_hours': 2,
        'icon': '⚡'
    }
]

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
    'codec_conversations': True,
    'tactical_word_detection': True,
    'daily_streaks': True,
    'voice_activity_tracking': True,
    'shop_system': True,
    'server_events': True,
    'automatic_backups': True,
    'neon_database': True,
}

# ═══════════════════════════════════════════════════════════════════
# CODEC SYSTEM
# ═══════════════════════════════════════════════════════════════════

CODEC_CONVERSATION_TIMEOUT = 300  # 5 minutes
CODEC_ALERT_CHANCE = 0.2          # 20% chance per check interval

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


def get_reward(activity_type: str, resource: str = 'gmp') -> int:
    """Get reward amount for an activity."""
    return REWARDS.get(activity_type, {}).get(resource, 0)


def is_feature_enabled(feature_name: str) -> bool:
    """Check if a feature is enabled."""
    return FEATURES.get(feature_name, True)
