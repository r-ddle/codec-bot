"""
Discord Components v2 Builder Utility
Modern component-based message system to replace embeds.
Uses Discord's new Components v2 API for better UX.
"""
import discord
from discord import SeparatorSpacing
from typing import Optional, List, Dict, Any
from discord.ui import Container, Section, TextDisplay, Thumbnail, Separator


def create_status_container(
    title: str,
    fields: List[Dict[str, str]],
    thumbnail_url: Optional[str] = None,
    color: int = 0x599cff,
    footer: Optional[str] = None
) -> Container:
    """
    Create a status display container with fields.

    Args:
        title: Main title for the container
        fields: List of dicts with 'name' and 'value' keys
        thumbnail_url: Optional thumbnail image URL
        color: Color for the container accent (ignored to remove side colors)
        footer: Optional footer text

    Returns:
        Container with organized sections
    """
    container = Container()  # No accent_color

    # Title as TextDisplay
    container.add_item(TextDisplay(content=f"# {title}"))

    if thumbnail_url:
        container.add_item(Separator(spacing=SeparatorSpacing.small))
        # Add thumbnail using Section with accessory
        thumb_section = Section(
            TextDisplay(content=""),  # Empty content
            accessory=Thumbnail(url=thumbnail_url)
        )
        container.add_item(thumb_section)

    container.add_item(Separator(spacing=SeparatorSpacing.small))

    # Add fields as text displays
    for field in fields:
        container.add_item(TextDisplay(content=f"**{field['name']}**\n{field['value']}"))

    # Footer if provided
    if footer:
        container.add_item(Separator(spacing=SeparatorSpacing.small))
        container.add_item(TextDisplay(content=f"*{footer}*"))

    return container


def create_simple_message(
    title: str,
    *descriptions: str,
    emoji: Optional[str] = None,
    color_code: str = "blue"
) -> Container:
    """
    Create a simple message container.

    Args:
        title: Message title
        *descriptions: One or more description strings (each becomes a separate TextDisplay)
        emoji: Optional emoji (ignored)
        color_code: Color theme (ignored)

    Returns:
        Simple container with title and description
    """
    container = Container()  # No accent_color

    # Title without emoji
    container.add_item(TextDisplay(content=f"## {title}"))

    # Add each description as a separate TextDisplay
    for desc in descriptions:
        container.add_item(TextDisplay(content=desc))

    return container


def create_error_message(
    title: str,
    *descriptions: str
) -> Container:
    """
    Create an error message container.

    Args:
        title: Error title
        *descriptions: One or more description strings (each becomes a separate TextDisplay)

    Returns:
        Container with error information
    """
    container = Container()  # No accent_color

    # Error title without emoji
    container.add_item(TextDisplay(content=f"## {title}"))

    # Add each description as a separate TextDisplay
    for desc in descriptions:
        container.add_item(TextDisplay(content=desc))

    return container


def create_success_message(
    title: str,
    *descriptions: str
) -> Container:
    """
    Create a success message container.

    Args:
        title: Success title
        *descriptions: One or more description strings (each becomes a separate TextDisplay)

    Returns:
        Container with success information
    """
    container = Container()  # No accent_color

    # Title without checkmark
    container.add_item(TextDisplay(content=f"## {title}"))

    # Add each description as a separate TextDisplay
    for desc in descriptions:
        container.add_item(TextDisplay(content=desc))

    return container


def create_info_card(
    title: str,
    *descriptions: str,
    thumbnail_url: Optional[str] = None,
    color_code: str = "blue",
    footer: Optional[str] = None
) -> Container:
    """
    Create an information card container.

    Args:
        title: Card title
        *descriptions: One or more description strings (each becomes a separate TextDisplay)
        thumbnail_url: Optional thumbnail URL
        color_code: Color theme (ignored)
        footer: Optional footer text

    Returns:
        Container with information card
    """
    container = Container()  # No accent_color

    # Title
    container.add_item(TextDisplay(content=f"## {title}"))

    # Thumbnail if provided
    if thumbnail_url:
        thumb_section = Section(
            TextDisplay(content=""),
            accessory=Thumbnail(url=thumbnail_url)
        )
        container.add_item(thumb_section)

    # Add each description as a separate TextDisplay
    for desc in descriptions:
        container.add_item(TextDisplay(content=desc))

    # Footer if provided
    if footer:
        container.add_item(Separator(spacing=SeparatorSpacing.small))
        container.add_item(TextDisplay(content=f"*{footer}*"))

    return container


def create_list_container(
    title: str,
    items: List[str],
    color_code: str = "blue",
    footer: Optional[str] = None
) -> Container:
    """
    Create a list container.

    Args:
        title: List title
        items: List of items to display
        color_code: Color theme (ignored)
        footer: Optional footer text

    Returns:
        Container with list items
    """
    container = Container()  # No accent_color

    # Title
    container.add_item(TextDisplay(content=f"## {title}"))

    container.add_item(Separator(spacing=SeparatorSpacing.small))

    # List items
    for item in items:
        container.add_item(TextDisplay(content=f"• {item}"))

    # Footer if provided
    if footer:
        container.add_item(Separator(spacing=SeparatorSpacing.small))
        container.add_item(TextDisplay(content=f"*{footer}*"))

    return container
def create_stats_container(
    title: str,
    description: str,
    stats: Dict[str, str],
    color_code: str = "blue",
    footer: Optional[str] = None
) -> Container:
    """
    Create a statistics container.

    Args:
        title: Stats title
        description: Stats description
        stats: Dictionary of stat_name: stat_value pairs
        color_code: Color theme (ignored)
        footer: Optional footer text

    Returns:
        Container with statistics
    """
    container = Container()  # No accent_color

    # Title
    container.add_item(TextDisplay(content=f"## {title}"))

    # Description
    if description:
        container.add_item(TextDisplay(content=description))

    container.add_item(Separator(spacing=SeparatorSpacing.small))

    # Stats
    for stat_name, stat_value in stats.items():
        container.add_item(TextDisplay(content=f"**{stat_name}**\n{stat_value}"))

    # Footer if provided
    if footer:
        container.add_item(Separator(spacing=SeparatorSpacing.small))
        container.add_item(TextDisplay(content=f"*{footer}*"))

    return container


def create_progress_container(
    title: str,
    current: int,
    goal: int,
    percentage: float,
    additional_info: Optional[Dict[str, str]] = None,
    color_code: str = "blue"
) -> Container:
    """
    Create a progress display container.

    Args:
        title: Progress title
        current: Current progress value
        goal: Goal value
        percentage: Progress percentage (0-100)
        additional_info: Optional additional information dict
        color_code: Color theme (ignored)

    Returns:
        Container with progress information
    """
    container = Container()  # No accent_color

    # Title
    container.add_item(TextDisplay(content=f"## {title}"))

    container.add_item(Separator(spacing=SeparatorSpacing.small))

    # Progress bar (text-based)
    filled = int(percentage / 10)
    empty = 10 - filled
    bar = "█" * filled + "░" * empty
    container.add_item(TextDisplay(content=f"`[{bar}]` {percentage:.1f}%"))

    # Progress numbers
    container.add_item(TextDisplay(content=f"**Progress:** {current:,} / {goal:,}"))

    # Additional info if provided
    if additional_info:
        container.add_item(Separator(spacing=SeparatorSpacing.small))
        for key, value in additional_info.items():
            container.add_item(TextDisplay(content=f"**{key}:** {value}"))

    return container
