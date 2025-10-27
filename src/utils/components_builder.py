"""
Discord Components v2 Builder Utility
Modern component-based message system to replace embeds.
Uses Discord's new Components v2 API for better UX.
"""
import discord
from discord import SeparatorSpacing, ButtonStyle
from discord.ui import View, Button
from typing import Optional, List, Dict, Any, Callable
from discord.ui import Container, Section, TextDisplay, Thumbnail, Separator
from io import BytesIO
import asyncio


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
            accessory=Thumbnail(thumbnail_url)
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
    description: str = "",
    *descriptions: str
) -> Container:
    """
    Create an error message container.

    Args:
        title: Error title
        description: Main description string
        *descriptions: Additional description strings (each becomes a separate TextDisplay)

    Returns:
        Container with error information
    """
    container = Container()  # No accent_color

    # Error title without emoji
    container.add_item(TextDisplay(content=f"## {title}"))

    # Add main description if provided
    if description:
        container.add_item(TextDisplay(content=description))

    # Add each additional description as a separate TextDisplay
    for desc in descriptions:
        container.add_item(TextDisplay(content=desc))

    return container


def create_success_message(
    title: str,
    description: str = "",
    *descriptions: str
) -> Container:
    """
    Create a success message container.

    Args:
        title: Success title
        description: Main description string
        *descriptions: Additional description strings (each becomes a separate TextDisplay)

    Returns:
        Container with success information
    """
    container = Container()  # No accent_color

    # Title without checkmark
    container.add_item(TextDisplay(content=f"## {title}"))

    # Add main description if provided
    if description:
        container.add_item(TextDisplay(content=description))

    # Add each additional description as a separate TextDisplay
    for desc in descriptions:
        container.add_item(TextDisplay(content=desc))

    return container


def create_info_card(
    title: str,
    description: str = "",
    *descriptions: str,
    thumbnail_url: Optional[str] = None,
    color_code: str = "blue",
    footer: Optional[str] = None
) -> Container:
    """
    Create an information card container.

    Args:
        title: Card title
        description: Main description string
        *descriptions: Additional description strings (each becomes a separate TextDisplay)
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
            accessory=Thumbnail(thumbnail_url)
        )
        container.add_item(thumb_section)

    # Add main description if provided
    if description:
        container.add_item(TextDisplay(content=description))

    # Add each additional description as a separate TextDisplay
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


class LeaderboardView(View):
    """Interactive view for leaderboard with category buttons."""

    def __init__(self, bot, ctx, current_category: str = "xp"):
        super().__init__(timeout=180)
        self.bot = bot
        self.ctx = ctx
        self.current_category = current_category
        self.message = None

        # Category mappings
        self.valid_categories = {
            "xp": ("EXPERIENCE POINTS", "XP"),
            "messages": ("MESSAGES SENT", "MSG"),
            "voice": ("VOICE TIME", "MIN")
        }

        self.category_mapping = {
            "xp": "xp",
            "messages": "messages_sent",
            "voice": "voice_minutes"
        }

        # Create buttons
        self.xp_button = Button(
            label="xp",
            style=ButtonStyle.gray,
            custom_id="lb_xp"
        )
        self.messages_button = Button(
            label="messages",
            style=ButtonStyle.gray,
            custom_id="lb_messages"
        )
        self.voice_button = Button(
            label="voice",
            style=ButtonStyle.gray,
            custom_id="lb_voice"
        )

        # Set callbacks
        self.xp_button.callback = self.xp_callback
        self.messages_button.callback = self.messages_callback
        self.voice_button.callback = self.voice_callback

        # Add buttons to view
        self.add_item(self.xp_button)
        self.add_item(self.messages_button)
        self.add_item(self.voice_button)

        # Update button styles based on current category
        self._update_button_styles()

    def _update_button_styles(self):
        """Update button styles to show active category."""
        # Reset all to gray
        self.xp_button.style = ButtonStyle.gray
        self.messages_button.style = ButtonStyle.gray
        self.voice_button.style = ButtonStyle.gray

        # Highlight current category (keep gray but will be visually distinct in Discord)
        if self.current_category == "xp":
            self.xp_button.disabled = True
        elif self.current_category == "messages":
            self.messages_button.disabled = True
        elif self.current_category == "voice":
            self.voice_button.disabled = True

    async def _generate_and_update(self, interaction: discord.Interaction, category: str):
        """Generate leaderboard image for category and update message."""
        await interaction.response.defer()

        self.current_category = category
        sort_field = self.category_mapping[category]
        category_name, unit_suffix = self.valid_categories[category]

        try:
            # Fetch leaderboard data
            from utils.leaderboard_gen import generate_leaderboard

            leaderboard_data = self.bot.member_data.get_leaderboard(
                self.ctx.guild.id, sort_by=sort_field, limit=10
            )

            if not leaderboard_data:
                await interaction.followup.send("no data available for this category", ephemeral=True)
                return

            # Format data for image generator
            formatted_data = []
            for i, (member_id, data) in enumerate(leaderboard_data, 1):
                try:
                    member = self.ctx.guild.get_member(int(member_id))
                    name = member.display_name if member else f"unknown"
                    value = data.get(sort_field, 0)
                    rank_icon = data.get("rank_icon", "")

                    formatted_data.append((i, name, value, rank_icon))
                except Exception:
                    continue

            # Generate image off the event loop
            img = await asyncio.to_thread(
                generate_leaderboard,
                leaderboard_data=formatted_data,
                category=category_name,
                unit_suffix=unit_suffix,
                guild_name=self.ctx.guild.name
            )

            # Convert to Discord-compatible format
            buffer = BytesIO()
            await asyncio.to_thread(img.save, buffer, 'PNG')
            buffer.seek(0)

            file = discord.File(buffer, filename='leaderboard.png')

            # Update button styles
            self._update_button_styles()

            # Re-enable all buttons first
            self.xp_button.disabled = False
            self.messages_button.disabled = False
            self.voice_button.disabled = False

            # Disable current category button
            if category == "xp":
                self.xp_button.disabled = True
            elif category == "messages":
                self.messages_button.disabled = True
            elif category == "voice":
                self.voice_button.disabled = True

            # Update message with new image and buttons
            await interaction.edit_original_response(attachments=[file], view=self)

        except Exception as e:
            await interaction.followup.send(f"error generating leaderboard: {str(e)}", ephemeral=True)

    async def xp_callback(self, interaction: discord.Interaction):
        """Handle XP button click."""
        await self._generate_and_update(interaction, "xp")

    async def messages_callback(self, interaction: discord.Interaction):
        """Handle messages button click."""
        await self._generate_and_update(interaction, "messages")

    async def voice_callback(self, interaction: discord.Interaction):
        """Handle voice button click."""
        await self._generate_and_update(interaction, "voice")

    async def on_timeout(self):
        """Disable buttons when view times out."""
        for item in self.children:
            item.disabled = True

        if self.message:
            try:
                await self.message.edit(view=self)
            except:
                pass


def create_rank_perks_info(faq_channel_id: Optional[int] = None) -> tuple[Container, Optional[View]]:
    """
    Create a reusable component showing rank system info and perks.

    Args:
        faq_channel_id: Optional FAQ channel ID for the button link

    Returns:
        Tuple of (Container, Optional View with button)
    """
    container = Container()

    # Title
    container.add_item(TextDisplay(content="# Rank System Overview"))

    container.add_item(Separator(spacing=SeparatorSpacing.small))

    # Rank progression info
    container.add_item(TextDisplay(
        content="**How It Works**\n"
                "Earn XP by chatting, being in voice channels, and reacting to messages.\n"
                "As you gain XP, you'll rank up through the military hierarchy."
    ))

    container.add_item(Separator(spacing=SeparatorSpacing.small))

    # Rank tiers and perks
    container.add_item(TextDisplay(
        content="**Rank Tiers**\n"
                "• **Rookie** - Starting rank, basic permissions\n"
                "• **Private - Corporal** - Access to more channels\n"
                "• **Sergeant - Captain** - Special channel access, XP multipliers\n"
                "• **Major - Colonel** - Exclusive perks, higher XP rates\n"
                "• **Foxhound** - Elite rank, maximum perks"
    ))

    container.add_item(Separator(spacing=SeparatorSpacing.small))

    # XP earning
    container.add_item(TextDisplay(
        content="**Earning XP**\n"
                "• Sending messages: 2 XP (with cooldown)\n"
                "• Voice activity: 2 XP per minute\n"
                "• Giving reactions: 1 XP\n"
                "• Receiving reactions: 3 XP\n"
                "• Daily streak bonus: Up to +40 XP per message"
    ))

    container.add_item(Separator(spacing=SeparatorSpacing.small))

    # Commands
    faq_mention = f"<#{faq_channel_id}>" if faq_channel_id else "the FAQ channel"
    container.add_item(TextDisplay(
        content="**Useful Commands**\n"
                "`!rank` - Check your rank and XP\n"
                "`!leaderboard` - View server rankings\n"
                "`!daily` - Claim daily XP bonus\n\n"
                f"**For more information**, check out {faq_mention}"
    ))

    return container, None
