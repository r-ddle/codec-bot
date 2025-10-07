"""
Discord role management utilities for rank-based role assignment.
"""
import discord
from typing import Optional
from config.constants import MGS_RANKS
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
        
        # Get the role name for the new rank
        new_role_name: Optional[str] = None
        for rank_data in MGS_RANKS:
            if rank_data["name"] == new_rank:
                new_role_name = rank_data["role_name"]
                break
        
        # Get all rank role names for removal
        rank_role_names = [rank["role_name"] for rank in MGS_RANKS if rank["role_name"]]
        roles_to_remove = []
        
        # Find current rank roles to remove
        for role in member.roles:
            if role.name in rank_role_names:
                roles_to_remove.append(role)
        
        # Remove old rank roles
        if roles_to_remove:
            await member.remove_roles(*roles_to_remove, reason="Rank role update")
            logger.info(f"Removed old rank roles from {member.name}")
        
        # Add new role if not Rookie
        if new_role_name:
            new_role = discord.utils.get(guild.roles, name=new_role_name)
            
            if new_role:
                await member.add_roles(new_role, reason=f"Promoted to {new_rank}")
                logger.info(f"Added {new_role_name} role to {member.name}")
                return True
            else:
                logger.error(f"Role '{new_role_name}' not found in server!")
                return False
        else:
            logger.info(f"{member.name} is Rookie - no role assigned")
            return True
            
    except discord.Forbidden:
        logger.error(f"No permission to manage roles for {member.name}")
        return False
    except Exception as e:
        logger.error(f"Error updating roles for {member.name}: {e}")
        return False
