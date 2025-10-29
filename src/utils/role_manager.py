"""
Discord role management utilities for rank-based role assignment.
"""
import discord
from typing import Optional
from config.constants import COZY_RANKS
from config.settings import logger


async def update_member_roles(member: discord.Member, new_rank: str) -> bool:
    """
    Update member Discord roles based on their rank.

    Args:
        member: Discord member to update
        new_rank: New rank name to assign

    Returns:
        True if successful, False otherwise
    """
    try:
        guild = member.guild

        # Get the role ID for the new rank
        new_role_id: Optional[int] = None
        for rank_data in COZY_RANKS:
            if rank_data["name"] == new_rank:
                new_role_id = rank_data.get("role_id")
                break

        # Add new role if role_id exists
        if new_role_id:
            new_role = guild.get_role(new_role_id)

            if new_role:
                await member.add_roles(new_role, reason=f"Promoted to {new_rank}")
                logger.info(f"Added {new_rank} role to {member.name}")
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
