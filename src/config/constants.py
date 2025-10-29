"""
Constants for Kira - r.ddle's Exile Server Bot
"""
from typing import List, Dict, Any

# ═══════════════════════════════════════════════════════════════════
# SERVER IDENTITY
# ═══════════════════════════════════════════════════════════════════
SERVER_NAME = "Exile"
SERVER_OWNER = "r.ddle"
SERVER_FOOTER = "© 2025 EXILE - r.ddle's Hangout"

# ═══════════════════════════════════════════════════════════════════
# COMMAND NAMES (Customize command names here)
# ═══════════════════════════════════════════════════════════════════
COMMAND_NAMES = {
    # Progression commands
    "status": "status",          # Check your rank and XP
    "rank": "rank",              # View rank card
    "leaderboard": "leaderboard", # View leaderboards
    "daily": "daily",            # Daily supply drop

    # Info commands

    # Profile commands
    "profile": "profile",        # View profile card
    "setbio": "setbio",         # Set profile bio

    # Admin commands (keep these hidden from help)
    "sync": "sync",
    "backup": "backup",
    "event": "event",
}

# MGS-themed messages
MGS_QUOTES: List[str] = [
    "Kept you waiting, huh?",
    "Snake? Snake?! SNAAAAKE!",
    "I'm no hero. Never was, never will be.",
    "Metal Gear?!",
    "War has changed...",
    "Nanomachines, son!",
    "This is good... isn't it?",
    "A weapon to surpass Metal Gear!",
    "Brother!",
    "You're pretty good.",
    "The future is not some place we are going, but one we are creating."
]



# XP-BASED RANK PROGRESSION SYSTEM (Unified) - Cozy Ranks with Role IDs
COZY_RANKS: List[Dict[str, Any]] = [
    {"name": "New Lifeform", "required_xp": 0, "icon": "🥚", "role_id": 1423506533148266568},
    {"name": "Grass Kisser", "required_xp": 50, "icon": "🌱", "role_id": 1423506533148266569},
    {"name": "Busy Bee", "required_xp": 100, "icon": "🐝", "role_id": 1423506533148266570},
    {"name": "Active Af", "required_xp": 500, "icon": "⚡", "role_id": 1423506533148266571},
    {"name": "Computer Cuddler", "required_xp": 1500, "icon": "💻", "role_id": 1423506533148266572},
    {"name": "Discord Dweller", "required_xp": 2500, "icon": "📡", "role_id": 1423506533148266573},
    {"name": "Keyboard Philosopher", "required_xp": 5000, "icon": "⌨️", "role_id": 1423506533148266574},
    {"name": "Server Resident", "required_xp": 8000, "icon": "🏠", "role_id": 1423506533148266575},
    {"name": "Discord Degenerate", "required_xp": 12000, "icon": "🔥", "role_id": 1423506533148266577},
    {"name": "Anti-Grass Toucher", "required_xp": 20000, "icon": "🧠", "role_id": 1423506533224022067}
]


# Default member data structure (single source of truth)
DEFAULT_MEMBER_DATA: Dict[str, Any] = {
    "xp": 0,
    "rank": "Rookie",
    "rank_icon": "",
    "messages_sent": 0,
    "voice_minutes": 0,
    "reactions_given": 0,
    "reactions_received": 0,
    "last_daily_claim": None,
    "daily_streak": 0,
    "last_activity_date": None,  # Track last day user was active
    "current_streak": 0,  # Current consecutive days active
    "longest_streak": 0,  # Best streak ever achieved
    "last_message_time": 0,
    "join_date": None,
    "bio": "",
    "verified": False,
    "word_up_points": 0
}

# XP Multipliers based on Cozy Rank
RANK_XP_MULTIPLIERS = {
    "New Lifeform": 1.0,
    "Grass Kisser": 1.0,
    "Busy Bee": 1.1,
    "Active Af": 1.2,
    "Computer Cuddler": 1.3,
    "Discord Dweller": 1.4,
    "Keyboard Philosopher": 1.5,
    "Server Resident": 1.6,
    "Discord Degenerate": 1.7,
    "Anti-Grass Toucher": 2.0
}

# Streak XP bonuses (bonus XP per message based on streak days)
STREAK_XP_BONUSES = {
    3: 2,   # 3 day streak: +2 XP per message
    7: 5,   # 7 day streak: +5 XP per message
    14: 8,  # 14 day streak: +8 XP per message
    30: 15, # 30 day streak: +15 XP per message
    60: 25, # 60 day streak: +25 XP per message
    90: 40  # 90+ day streak: +40 XP per message
}

# Activity rewards
ACTIVITY_REWARDS: Dict[str, Dict[str, int]] = {
    "message": {"xp": 5},
    "voice_minute": {"xp": 2},
    "reaction": {"xp": 2},
    "reaction_received": {"xp": 3},
    "daily_bonus": {"xp": 150}
}

# Contact administrators for support
CONTACT_ADMINS: List[str] = [
    "r.ddle",  # Server Owner
    "MysteriousBoyz1"
]
