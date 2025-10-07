"""
Utility functions for formatting numbers and creating visual progress bars.
"""
from typing import Tuple


def format_number(number: int) -> str:
    """
    Format numbers with commas for better readability.
    
    Args:
        number: The number to format
        
    Returns:
        Formatted string with comma separators
    """
    return f"{number:,}"


def make_progress_bar(current: int, maximum: int, length: int = 10) -> str:
    """
    Create a visual progress bar for rank progression.
    
    Args:
        current: Current progress value
        maximum: Maximum progress value
        length: Length of the progress bar (default: 10)
        
    Returns:
        Formatted progress bar string with percentage
    """
    current = min(current, maximum)
    percentage = int((current / maximum) * 100) if maximum > 0 else 100
    filled = int((current / maximum) * length) if maximum > 0 else length
    empty = length - filled
    bar = ''.join(['' for _ in range(filled)] + ['' for _ in range(empty)])
    return f"[{bar}] {percentage}%"
