"""
Rank migration utility to convert old MGS-themed ranks to new Cozy ranks.
"""
from typing import Dict, Tuple, Optional
from config.constants import COZY_RANKS, ACTIVITY_REWARDS
from config.settings import logger


# Mapping of old MGS-themed ranks to approximate activity levels
OLD_RANK_HIERARCHY = [
    "Rookie",
    "Private",
    "Corporal",
    "Sergeant",
    "Lieutenant",
    "Captain",
    "Major",
    "Colonel",
    "Commander",
    "FOXHOUND",
    "Big Boss"
]


def is_old_rank(rank_name: str) -> bool:
    """
    Check if a rank name belongs to the old MGS system.

    Args:
        rank_name: Rank name to check

    Returns:
        True if it's an old rank, False otherwise
    """
    if not rank_name:
        return False

    # Check if rank is in old hierarchy
    if rank_name in OLD_RANK_HIERARCHY:
        return True

    # Check if rank is NOT in new COZY_RANKS
    cozy_rank_names = [rank["name"] for rank in COZY_RANKS]
    if rank_name not in cozy_rank_names:
        # If it's not in cozy ranks and looks like it could be an old rank, treat it as old
        return True

    return False


def estimate_xp_from_activity(messages_sent: int, voice_minutes: int, reactions_given: int, reactions_received: int) -> int:
    """
    Estimate XP based on activity statistics.
    This helps migrate users who have stats but no XP.

    Args:
        messages_sent: Number of messages sent
        voice_minutes: Minutes in voice chat
        reactions_given: Reactions given to others
        reactions_received: Reactions received

    Returns:
        Estimated XP amount
    """
    # Use the same XP rewards from constants
    message_xp = messages_sent * ACTIVITY_REWARDS["message"]["xp"]
    voice_xp = voice_minutes * ACTIVITY_REWARDS["voice_minute"]["xp"]
    reaction_xp = reactions_given * ACTIVITY_REWARDS["reaction"]["xp"]
    reaction_received_xp = reactions_received * ACTIVITY_REWARDS["reaction_received"]["xp"]

    total_xp = message_xp + voice_xp + reaction_xp + reaction_received_xp

    return total_xp


def map_old_rank_to_new_rank(old_rank: str, estimated_xp: int) -> Tuple[str, str]:
    """
    Map an old MGS rank to a new Cozy rank based on position in hierarchy and XP.

    Args:
        old_rank: Old rank name
        estimated_xp: Estimated or actual XP

    Returns:
        Tuple of (new_rank_name, new_rank_icon)
    """
    # If it's already a cozy rank, return it as-is
    for rank in COZY_RANKS:
        if rank["name"] == old_rank:
            return old_rank, rank["icon"]

    # Find position in old hierarchy (0-indexed)
    try:
        old_position = OLD_RANK_HIERARCHY.index(old_rank)
    except ValueError:
        # Unknown old rank - default to first cozy rank
        logger.warning(f"Unknown old rank: {old_rank}, defaulting to first rank")
        return COZY_RANKS[0]["name"], COZY_RANKS[0]["icon"]

    # Map old position to new rank index
    # We have 11 old ranks (0-10) and 10 new ranks (0-9)
    # Map proportionally
    old_max = len(OLD_RANK_HIERARCHY) - 1  # 10
    new_max = len(COZY_RANKS) - 1  # 9

    # Proportional mapping
    if old_max > 0:
        new_position = int((old_position / old_max) * new_max)
    else:
        new_position = 0

    # Clamp to valid range
    new_position = max(0, min(new_position, new_max))

    # Also respect XP requirements - user should be at least at the rank their XP qualifies them for
    xp_qualified_rank_index = 0
    for i, rank_data in enumerate(COZY_RANKS):
        if estimated_xp >= rank_data["required_xp"]:
            xp_qualified_rank_index = i

    # Take the higher of the two (position mapping or XP qualification)
    final_position = max(new_position, xp_qualified_rank_index)

    new_rank = COZY_RANKS[final_position]
    return new_rank["name"], new_rank["icon"]


def migrate_member_rank(member_data: Dict) -> Tuple[bool, str, str, int]:
    """
    Migrate a single member's rank data from old to new system.

    Args:
        member_data: Member data dictionary to migrate

    Returns:
        Tuple of (was_migrated, new_rank, new_icon, calculated_xp)
    """
    current_rank = member_data.get("rank", "")
    current_xp = member_data.get("xp", 0)

    # Check if migration is needed
    if not is_old_rank(current_rank):
        # Already using new rank system
        return False, current_rank, member_data.get("rank_icon", ""), current_xp

    # This user needs migration
    logger.info(f"Migrating user with old rank: {current_rank}, current XP: {current_xp}")

    # Estimate XP if it's 0 or very low but user has activity
    estimated_xp = current_xp
    if current_xp < 50:  # Arbitrary threshold - likely needs recalculation
        estimated_xp = estimate_xp_from_activity(
            member_data.get("messages_sent", 0),
            member_data.get("voice_minutes", 0),
            member_data.get("reactions_given", 0),
            member_data.get("reactions_received", 0)
        )
        logger.info(f"Estimated XP from activity: {estimated_xp} (was {current_xp})")

    # Map to new rank
    new_rank, new_icon = map_old_rank_to_new_rank(current_rank, estimated_xp)

    logger.info(f"Migration: {current_rank} -> {new_rank} (XP: {current_xp} -> {estimated_xp})")

    return True, new_rank, new_icon, estimated_xp


def get_all_cozy_rank_names() -> list:
    """Get list of all valid cozy rank names."""
    return [rank["name"] for rank in COZY_RANKS]


def is_valid_cozy_rank(rank_name: str) -> bool:
    """Check if a rank name is a valid cozy rank."""
    return rank_name in get_all_cozy_rank_names()
