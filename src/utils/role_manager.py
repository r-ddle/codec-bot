"""
Discord role management utilities for rank-based role assignment.
"""
import discord
from typing import Optional, Tuple
from config.constants import COZY_RANKS
from config.settings import logger


async def update_member_roles(member: discord.Member, new_rank: str) -> bool:
    """
    Update member Discord roles based on their rank.
    Removes all other rank roles and adds only the current rank role.

    Args:
        member: Discord member to update
        new_rank: New rank name to assign

    Returns:
        True if successful, False otherwise
    """
    try:
        guild = member.guild

        # Get all rank role IDs (both new and potentially old ones)
        all_rank_role_ids = []
        new_role_id: Optional[int] = None

        for rank_data in COZY_RANKS:
            role_id = rank_data.get("role_id")
            if role_id:
                all_rank_role_ids.append(role_id)

            if rank_data["name"] == new_rank:
                new_role_id = role_id

        # Remove all existing rank roles from the member first
        roles_to_remove = []
        for role in member.roles:
            if role.id in all_rank_role_ids:
                roles_to_remove.append(role)

        if roles_to_remove:
            await member.remove_roles(*roles_to_remove, reason="Removing old rank roles")
            logger.info(f"Removed {len(roles_to_remove)} old rank role(s) from {member.name}")

        # Add new role if role_id exists
        if new_role_id:
            new_role = guild.get_role(new_role_id)

            if new_role:
                await member.add_roles(new_role, reason=f"Promoted to {new_rank}")
                logger.info(f"✅ Added {new_rank} role to {member.name}")
                return True
            else:
                logger.error(f"Role with ID {new_role_id} not found in server!")
                return False
        else:
            logger.info(f"{member.name} is at first rank - no role assigned")
            return True

    except discord.Forbidden:
        logger.error(f"No permission to manage roles for {member.name}")
        return False
    except Exception as e:
        logger.error(f"Error updating roles for {member.name}: {e}")
        return False


def detect_rank_from_roles(member: discord.Member) -> Optional[Tuple[str, str]]:
    """
    Detect a member's rank by checking their Discord roles.
    This is useful as a fallback when database data is inconsistent.

    Args:
        member: Discord member to check

    Returns:
        Tuple of (rank_name, rank_icon) if found, None otherwise
    """
    member_role_ids = [role.id for role in member.roles]

    # Find the highest rank role the member has
    # Check from highest rank to lowest
    for rank_data in reversed(COZY_RANKS):
        role_id = rank_data.get("role_id")
        if role_id and role_id in member_role_ids:
            return rank_data["name"], rank_data["icon"]

    # No rank role found
    return None
