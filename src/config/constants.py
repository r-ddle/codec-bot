"""
Constants for the MGS Discord Bot including ranks, rewards, and themed messages.
Outer Heaven: Exiled Soldiers
"""
from typing import List, Dict, Any

# ═══════════════════════════════════════════════════════════════════
# SERVER IDENTITY
# ═══════════════════════════════════════════════════════════════════
SERVER_NAME = "Outer Heaven: Exiled Soldiers"
SERVER_OWNER = "r.ddle"
SERVER_FOOTER = "© 2025 OUTER HEAVEN: EXILED SOLDIERS"

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



# XP-BASED RANK PROGRESSION SYSTEM
# NEW BALANCED PROGRESSION (Oct 2025) - Existing users keep old thresholds
MGS_RANKS: List[Dict[str, Any]] = [
    {"name": "Rookie", "required_xp": 0, "icon": "🎖️", "role_name": None},
    {"name": "Private", "required_xp": 100, "icon": "🪖", "role_name": "Private"},
    {"name": "Specialist", "required_xp": 500, "icon": "🎯", "role_name": "Specialist"},
    {"name": "Corporal", "required_xp": 1000, "icon": "⭐", "role_name": "Corporal"},
    {"name": "Sergeant", "required_xp": 1800, "icon": "🏅", "role_name": "Sergeant"},
    {"name": "Lieutenant", "required_xp": 3000, "icon": "🎖️", "role_name": "Lieutenant"},
    {"name": "Captain", "required_xp": 5000, "icon": "💫", "role_name": "Captain"},
    {"name": "Major", "required_xp": 8000, "icon": "⚡", "role_name": "Major"},
    {"name": "Colonel", "required_xp": 12000, "icon": "🌟", "role_name": "Colonel"},
    {"name": "FOXHOUND", "required_xp": 18000, "icon": "🦊", "role_name": "Foxhound"}
]

# LEGACY RANKS (Pre-Oct 2025 users) - Used for backward compatibility
MGS_RANKS_LEGACY: List[Dict[str, Any]] = [
    {"name": "Rookie", "required_xp": 0, "icon": "🎖️", "role_name": None},
    {"name": "Private", "required_xp": 100, "icon": "🪖", "role_name": "Private"},
    {"name": "Specialist", "required_xp": 200, "icon": "🎯", "role_name": "Specialist"},
    {"name": "Corporal", "required_xp": 350, "icon": "⭐", "role_name": "Corporal"},
    {"name": "Sergeant", "required_xp": 500, "icon": "🏅", "role_name": "Sergeant"},
    {"name": "Lieutenant", "required_xp": 750, "icon": "🎖️", "role_name": "Lieutenant"},
    {"name": "Captain", "required_xp": 1000, "icon": "💫", "role_name": "Captain"},
    {"name": "Major", "required_xp": 1500, "icon": "⚡", "role_name": "Major"},
    {"name": "Colonel", "required_xp": 2500, "icon": "🌟", "role_name": "Colonel"},
    {"name": "FOXHOUND", "required_xp": 4000, "icon": "🦊", "role_name": "FOXHOUND"}
]

# Cutoff date for legacy progression (October 8, 2025)
LEGACY_USER_CUTOFF = "2025-10-08"

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
    "last_message_time": 0,
    "join_date": None,
    "bio": "",
    "verified": False,
    "legacy_progression": False
}

# XP Multipliers based on rank
RANK_XP_MULTIPLIERS = {
    "Rookie": 1.0,
    "Private": 1.0,
    "Specialist": 1.1,
    "Corporal": 1.2,
    "Sergeant": 1.3,
    "Lieutenant": 1.4,
    "Captain": 1.5,
    "Major": 1.6,
    "Colonel": 1.7,
    "FOXHOUND": 2.0
}

# Activity rewards
ACTIVITY_REWARDS: Dict[str, Dict[str, int]] = {
    "message": {"xp": 2},
    "voice_minute": {"xp": 2},
    "reaction": {"xp": 1},
    "reaction_received": {"xp": 3},
    "daily_bonus": {"xp": 100}
}

# Contact administrators for support
CONTACT_ADMINS: List[str] = [
    "r.ddle",  # Server Owner
    "MysteriousBoyz1"
]
