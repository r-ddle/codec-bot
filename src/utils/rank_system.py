"""
Rank calculation and progression utilities.
"""
from typing import Dict, Optional, Tuple, Any, List
from config.constants import MGS_RANKS
from config.settings import logger


def calculate_rank_from_xp(xp: int) -> Tuple[str, str]:
    """
    Calculate rank based on XP amount.

    Args:
        xp: Experience points amount

    Returns:
        Tuple of (rank_name, rank_icon)
    """
    current_rank = MGS_RANKS[0]

    # Find the highest rank the user qualifies for based on XP only
    for rank_data in reversed(MGS_RANKS):
        if xp >= rank_data["required_xp"]:
            current_rank = rank_data
            break

    return current_rank["name"], current_rank["icon"]


def get_next_rank_info(current_xp: int, current_rank: str) -> Optional[Dict[str, Any]]:
    """
    Get information about the next rank in progression.

    Args:
        current_xp: Current XP amount
        current_rank: Current rank name

    Returns:
        Dictionary with next rank information or None if at max rank
    """
    # Find current rank index
    current_index = 0
    for i, rank_data in enumerate(MGS_RANKS):
        if rank_data["name"] == current_rank:
            current_index = i
            break

    # Check if there's a next rank
    if current_index >= len(MGS_RANKS) - 1:
        return None

    next_rank = MGS_RANKS[current_index + 1]
    current_rank_data = MGS_RANKS[current_index]

    return {
        "name": next_rank["name"],
        "icon": next_rank["icon"],
        "next_xp": next_rank["required_xp"],
        "current_rank_xp": current_rank_data["required_xp"],
        "role_name": next_rank.get("role_name")
    }

def get_rank_data_by_name(rank_name: str) -> Dict[str, Any]:
    """
    Get rank data dictionary by rank name.

    Args:
        rank_name: Name of the rank to find

    Returns:
        Rank data dictionary or the Rookie rank if not found
    """
    for rank in MGS_RANKS:
        if rank["name"] == rank_name:
            return rank
    return MGS_RANKS[0]
