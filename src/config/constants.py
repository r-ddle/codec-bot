"""
Constants for the MGS Discord Bot including ranks, rewards, and themed messages.
"""
from typing import List, Dict, Any

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

MGS_CODEC_SOUNDS: List[str] = [
    "*codec ring*",
    "*codec beep*",
    "*codec static*",
]

# Codec conversation responses
CODEC_RESPONSES: List[str] = [
    "Snake, can you hear me?",
    "This is Colonel Campbell. What's your status?",
    "Stay alert, Snake. Enemy activity detected in your area.",
    "Remember, this is a stealth mission.",
    "Keep your guard up out there.",
    "Good work so far. Continue the mission.",
    "Be careful, Snake. We're counting on you.",
    "That's what I like to hear, soldier.",
    "Mission parameters remain unchanged.",
    "I can talk now well... Let's continue this operation.",
    "Solid copy, Snake. Campbell out."
]

# XP-BASED RANK PROGRESSION SYSTEM
# NEW BALANCED PROGRESSION (Oct 2025) - Existing users keep old thresholds
MGS_RANKS: List[Dict[str, Any]] = [
    {"name": "Rookie", "required_xp": 0, "icon": "🎖️", "role_name": None},
    {"name": "Private", "required_xp": 200, "icon": "🪖", "role_name": "Private"},
    {"name": "Specialist", "required_xp": 500, "icon": "🎯", "role_name": "Specialist"},
    {"name": "Corporal", "required_xp": 1000, "icon": "⭐", "role_name": "Corporal"},
    {"name": "Sergeant", "required_xp": 1800, "icon": "🏅", "role_name": "Sergeant"},
    {"name": "Lieutenant", "required_xp": 3000, "icon": "🎖️", "role_name": "Lieutenant"},
    {"name": "Captain", "required_xp": 5000, "icon": "💫", "role_name": "Captain"},
    {"name": "Major", "required_xp": 8000, "icon": "⚡", "role_name": "Major"},
    {"name": "Colonel", "required_xp": 12000, "icon": "🌟", "role_name": "Colonel"},
    {"name": "FOXHOUND", "required_xp": 18000, "icon": "🦊", "role_name": "FOXHOUND"}
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

# Activity rewards
ACTIVITY_REWARDS: Dict[str, Dict[str, int]] = {
    "message": {"gmp": 15, "xp": 3},
    "voice_minute": {"gmp": 8, "xp": 2},
    "reaction": {"gmp": 3, "xp": 1},
    "reaction_received": {"gmp": 8, "xp": 2},
    "daily_bonus": {"gmp": 200, "xp": 50},
    "tactical_word": {"gmp": 25, "xp": 8}
}

# Tactical vocabulary for bonus detection
TACTICAL_WORDS: List[str] = [
    "tactical", "stealth", "operation", "infiltrate", "extract", "intel",
    "recon", "mission", "target", "objective", "deploy", "enemy", "patrol",
    "metal gear", "foxhound", "shadow moses", "outer heaven", "snake",
    "ocelot", "motherbase", "phantom pain", "peace walker", "mg", "mgs",
    "nanomachines", "revolver", "diamond dogs", "boss", "tactic",
    "espionage", "alert", "caution", "silencer", "weapon", "gear", "military",
    "soldier", "warfare", "combat", "strategy", "sniper", "assault", "defense",
    "artillery", "ammunition", "camouflage", "surveillance", "reconnaissance",
    "elimination", "extraction", "insertion", "breach", "secure", "hostile",
    "friendly", "neutral", "contact", "engage", "disengage", "retreat",
    "advance", "flank", "cover", "suppression", "overwatch", "backup",
    "reinforcement", "casualty", "wounded", "medic", "evac", "rendezvous",
    "cipher", "patriot", "codec", "operative", "commander",
    "colonel", "major", "captain", "lieutenant", "sergeant", "private"
]

# Contact administrators for moderation appeals
CONTACT_ADMINS: List[str] = [
    "solid.ninja",
    "rip_carti",
    "ahab_in_rehab",
    "*outer.heaven*"
]
