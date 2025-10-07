"""
Rank calculation and progression utilities with legacy support.
"""
from typing import Dict, Optional, Tuple, Any, List
from datetime import datetime
from config.constants import MGS_RANKS, MGS_RANKS_LEGACY, LEGACY_USER_CUTOFF
from config.settings import logger


def is_legacy_user(member_join_date: Optional[str]) -> bool:
    """
    Check if user should use legacy rank progression.

    Args:
        member_join_date: User's join date in YYYY-MM-DD format

    Returns:
        True if user joined before cutoff date
    """
    if not member_join_date:
        return False

    try:
        join_date = datetime.strptime(member_join_date, '%Y-%m-%d')
        cutoff_date = datetime.strptime(LEGACY_USER_CUTOFF, '%Y-%m-%d')
        return join_date < cutoff_date
    except (ValueError, AttributeError):
        return False


def get_rank_table(use_legacy: bool = False) -> List[Dict[str, Any]]:
    """
    Get appropriate rank table based on user type.

    Args:
        use_legacy: Whether to use legacy progression

    Returns:
        Appropriate rank table
    """
    return MGS_RANKS_LEGACY if use_legacy else MGS_RANKS


def get_rank_data_by_name(rank_name: str, use_legacy: bool = False) -> Dict[str, Any]:
    """
    Get rank data dictionary by rank name.

    Args:
        rank_name: Name of the rank to find
        use_legacy: Whether to use legacy rank table

    Returns:
        Rank data dictionary or the Rookie rank if not found
    """
    rank_table = get_rank_table(use_legacy)
    for rank in rank_table:
        if rank["name"] == rank_name:
            return rank
    return rank_table[0]


def calculate_rank_from_xp(xp: int, use_legacy: bool = False) -> Tuple[str, str]:
    """
    Calculate rank based on XP amount with legacy support.

    Args:
        xp: Experience points amount
        use_legacy: Whether to use legacy progression

    Returns:
        Tuple of (rank_name, rank_icon)
    """
    rank_table = get_rank_table(use_legacy)
    current_rank = rank_table[0]

    # Find the highest rank the user qualifies for based on XP only
    for rank_data in reversed(rank_table):
        if xp >= rank_data["required_xp"]:
            current_rank = rank_data
            break

    return current_rank["name"], current_rank["icon"]


def get_next_rank_info(current_xp: int, current_rank: str, use_legacy: bool = False) -> Optional[Dict[str, Any]]:
    """
    Get information about the next rank in progression.

    Args:
        current_xp: Current XP amount
        current_rank: Current rank name
        use_legacy: Whether to use legacy progression

    Returns:
        Dictionary with next rank information or None if at max rank
    """
    rank_table = get_rank_table(use_legacy)

    # Find current rank index
    current_index = 0
    for i, rank_data in enumerate(rank_table):
        if rank_data["name"] == current_rank:
            current_index = i
            break

    # Check if there's a next rank
    if current_index >= len(rank_table) - 1:
        return None

    next_rank = rank_table[current_index + 1]
    current_rank_data = rank_table[current_index]

    return {
        "name": next_rank["name"],
        "icon": next_rank["icon"],
        "next_xp": next_rank["required_xp"],
        "current_rank_xp": current_rank_data["required_xp"],
        "role_name": next_rank.get("role_name")
    }
