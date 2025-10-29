# profile_card_new.py
# Enhanced Cozy Hangout Bot profile card generator

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import io
import requests
import random
import unicodedata
from datetime import datetime
from typing import Optional, List
from config.constants import SERVER_FOOTER

# === IMPORT SHARED FUNCTIONS FROM image_gen.py ===
from .image_gen import (
    sanitize_username, load_font, safe_draw_text,
    add_heavy_scanlines, add_static_noise, add_phosphor_glow,
    draw_codec_frame, draw_codec_divider,
    CODEC_BG_DARK, CODEC_BG_MEDIUM, CODEC_GREEN_PRIMARY,
    CODEC_GREEN_DIM, CODEC_GREEN_TEXT, CODEC_GREEN_BRIGHT,
    CODEC_BORDER_BRIGHT
)
from .profile_card_gen import create_profile_avatar, wrap_text
from .rank_system import get_next_rank_info

def draw_progress_bar(draw, x, y, width, height, percentage, color_fill, color_bg):
    """Draws a progress bar with percentage fill."""
    # Background
    draw.rectangle([x, y, x + width, y + height], fill=color_bg, outline=CODEC_GREEN_PRIMARY)

    # Fill
    fill_width = int(width * (percentage / 100))
    if fill_width > 0:
        draw.rectangle([x, y, x + fill_width, y + height], fill=color_fill)

    # Segments (for that tech look)
    segment_width = width // 10
    for i in range(1, 10):
        seg_x = x + (i * segment_width)
        draw.line([(seg_x, y), (seg_x, y + height)], fill=CODEC_BG_DARK, width=1)

def draw_section_label(draw, x, y, text, font, with_arrow=True):
    """Draws a section label with optional arrow indicator."""
    text_x = x

    safe_draw_text(draw, (text_x, y), text, primary_font=font, fill=CODEC_GREEN_BRIGHT)
    return text_x

def calculate_stat_percentage(value, max_value):
    """Calculates percentage for progress bar, capped at 100%."""
    if max_value == 0:
        return 0
    return min(100, int((value / max_value) * 100))

def calculate_next_rank_progress(current_xp: int, current_rank: str, use_legacy: bool = False) -> int:
    """
    Calculate percentage progress towards the next rank.

    Args:
        current_xp: Current experience points
        current_rank: Current rank name
        use_legacy: Whether to use legacy rank progression

    Returns:
        Percentage (0-100) of progress to next rank
    """
    next_rank_info = get_next_rank_info(current_xp, current_rank, use_legacy)

    # If at max rank, return 100%
    if not next_rank_info:
        return 100

    current_rank_xp = next_rank_info['current_rank_xp']
    next_rank_xp = next_rank_info['next_xp']

    # Calculate XP needed in this tier
    xp_in_tier = current_xp - current_rank_xp
    xp_needed_for_tier = next_rank_xp - current_rank_xp

    if xp_needed_for_tier <= 0:
        return 100

    percentage = int((xp_in_tier / xp_needed_for_tier) * 100)
    return min(100, max(0, percentage))

def calculate_dynamic_message_goal(server_avg_messages: int = 0) -> int:
    """
    Calculate a dynamic monthly message goal based on server activity.

    If server average is available, sets goal at 75% of server average
    (encouraging but achievable). Otherwise uses sensible defaults.

    Args:
        server_avg_messages: Average messages per active member this month

    Returns:
        Dynamic message goal for the month
    """
    if server_avg_messages > 0:
        # Set goal at 75% of server average (encouraging but achievable)
        dynamic_goal = int(server_avg_messages * 0.75)
        # Clamp between reasonable bounds (100-2000)
        return max(100, min(2000, dynamic_goal))

    # Default fallback: ~17 messages per day for 30 days
    return 500

def calculate_dynamic_activity_tier(xp, messages, voice_hours, current_rank: str = "Rookie",
                                   use_legacy: bool = False, server_avg_messages: int = 0):
    """
    Calculates dynamic activity tier based on current month's stats.
    Returns percentages based on realistic monthly activity benchmarks.

    This system is designed to be encouraging and reset monthly:
    - XP: Shows progress towards NEXT RANK (not arbitrary benchmarks)
    - Messages: Dynamic goal based on server activity (~75% of server average)
    - Voice Hours: 10 = 50%, 20 = 100% (~40 min/day)

    Args:
        xp: Current XP (not used for percentage, see calculate_next_rank_progress)
        messages: Messages sent this month
        voice_hours: Voice hours this month
        current_rank: Current rank name
        use_legacy: Whether user uses legacy progression
        server_avg_messages: Server average messages for dynamic goal

    NOTE: These stats should reset monthly in sync with leaderboard resets!
    """
    # XP percentage is now based on NEXT RANK progress (calculated separately)
    xp_pct = calculate_next_rank_progress(xp, current_rank, use_legacy)

    # Messages: Dynamic goal based on server activity
    msg_goal = calculate_dynamic_message_goal(server_avg_messages)
    msg_pct = min(100, int((messages / msg_goal) * 100))

    # Voice: Keep existing system (20 hours = 100%)
    voice_pct = min(100, int((voice_hours / 20) * 100))

    return xp_pct, msg_pct, voice_pct

def get_activity_status(overall_pct):
    """Returns activity status label based on percentage."""
    if overall_pct >= 80:
        return "HIGHLY ACTIVE"
    elif overall_pct >= 60:
        return "ACTIVE"
    elif overall_pct >= 40:
        return "MODERATE"
    elif overall_pct >= 20:
        return "LOW ACTIVITY"
    else:
        return "MINIMAL"

def generate_profile_new(
    username: str,
    role_name: str,
    avatar_url: Optional[str],
    bio_text: Optional[str],
    xp: int,
    messages: int,
    voice_hours: int,
    current_rank: str = "Rookie",
    use_legacy: bool = False,
    server_avg_messages: int = 0
):
    """
    Generates an enhanced MGS Codec-style profile card with improved UI.

    Args:
        username: Discord username
        role_name: User's role name
        avatar_url: URL to user's avatar
        bio_text: User bio (optional)
        xp: XP amount
        messages: Message count
        voice_hours: Voice time in hours
        current_rank: Current rank name for next rank progress calculation
        use_legacy: Whether user uses legacy rank progression
        server_avg_messages: Server average messages for dynamic goal calculation

    Returns:
        PIL Image object
    """
    width = 750
    height = 650

    # Create base
    base = Image.new("RGB", (width, height), CODEC_BG_DARK)
    draw = ImageDraw.Draw(base)

    # Load fonts
    font_title = load_font(30, "text")
    font_subtitle = load_font(16, "text")
    font_body = load_font(14, "text")
    font_stats_label = load_font(12, "text")
    font_stats_value = load_font(20, "numbers")
    font_small = load_font(11, "text")
    font_tiny = load_font(10, "text")

    # === HEADER: FREQUENCY & TIMESTAMP ===
    header_y = 25
    freq_text = "FREQ: 140.85"
    safe_draw_text(draw, (25, header_y), freq_text,
                  primary_font=font_small, fill=CODEC_GREEN_DIM)

    timestamp = datetime.now().strftime("%H:%M:%S")
    date_text = f"{timestamp} | {datetime.now().strftime('%d.%m.%Y')}"
    try:
        date_bbox = draw.textbbox((0, 0), date_text, font=font_small)
        date_width = date_bbox[2] - date_bbox[0]
    except:
        date_width = len(date_text) * 6
    safe_draw_text(draw, (width - date_width - 25, header_y), date_text,
                  primary_font=font_small, fill=CODEC_GREEN_DIM)

    # === AVATAR SECTION ===
    avatar_size = 140
    avatar = create_profile_avatar(avatar_url, size=(avatar_size, avatar_size)) if avatar_url else None

    if avatar:
        avatar_x = (width - avatar_size) // 2
        avatar_y = 45
        base.paste(avatar, (avatar_x, avatar_y))

        # Enhanced border with corner accents
        border_pad = 3
        draw.rectangle([avatar_x - border_pad, avatar_y - border_pad,
                       avatar_x + avatar_size + border_pad, avatar_y + avatar_size + border_pad],
                      outline=CODEC_GREEN_PRIMARY, width=2)

    # === USERNAME & ROLE ===
    username_clean = sanitize_username(username)
    username_y = 200

    # Center username with underline effect
    try:
        username_bbox = draw.textbbox((0, 0), username_clean.upper(), font=font_title)
        username_width = username_bbox[2] - username_bbox[0]
    except:
        username_width = len(username_clean) * 16

    username_x = (width - username_width) // 2
    safe_draw_text(draw, (username_x, username_y),
                  username_clean.upper(),
                  primary_font=font_title, fill=CODEC_BORDER_BRIGHT)

    # Role badge
    role_y = username_y + 42
    role_text = role_name.upper()
    try:
        role_bbox = draw.textbbox((0, 0), role_text, font=font_subtitle)
        role_width = role_bbox[2] - role_bbox[0]
    except:
        role_width = len(role_text) * 9

    role_x = (width - role_width) // 2

    # Role background
    role_bg_pad = 8
    draw.rectangle([role_x - role_bg_pad, role_y - 3,
                   role_x + role_width + role_bg_pad, role_y + 18],
                  fill=CODEC_BG_MEDIUM, outline=CODEC_GREEN_PRIMARY)

    safe_draw_text(draw, (role_x, role_y),
                  role_text,
                  primary_font=font_subtitle, fill=CODEC_GREEN_TEXT)

    current_y = role_y + 40

    # === DIVIDER ===
    draw_codec_divider(draw, 40, current_y, width - 80)
    current_y += 20

    # === BIO SECTION (COMPACT) ===
    bio_x = 50
    draw_section_label(draw, bio_x, current_y, "OPERATIVE BIO", font_subtitle)
    current_y += 22

    bio_display = bio_text[:200] if bio_text else "No profile information available."
    bio_display_x = bio_x + 10
    bio_lines = wrap_text(bio_display, font_body, width - bio_display_x - 50, draw)

    for line in bio_lines[:2]:  # Max 2 lines
        safe_draw_text(draw, (bio_x + 20, current_y), line,
                      primary_font=font_body, fill=CODEC_GREEN_TEXT)
        current_y += 18

    current_y += 12

    # === DIVIDER ===
    draw_codec_divider(draw, 40, current_y, width - 80)
    current_y += 20

    # === STATS SECTION (HORIZONTAL GRID) ===
    draw_section_label(draw, 50, current_y, "TACTICAL STATISTICS", font_subtitle)
    current_y += 28

    # Calculate dynamic stat percentages based on monthly activity
    # XP shows progress to NEXT RANK, Messages use dynamic server-based goals
    xp_pct, msg_pct, voice_pct = calculate_dynamic_activity_tier(
        xp, messages, voice_hours, current_rank, use_legacy, server_avg_messages
    )

    # Stats grid layout
    stats_data = [
        ("EXPERIENCE", f"{xp:,}", "XP", xp_pct),
        ("MESSAGES", f"{messages:,}", "SENT", msg_pct),
        ("VOICE TIME", f"{voice_hours}", "HOURS", voice_pct)
    ]

    stat_box_width = 200
    stat_box_height = 75
    spacing = 15
    total_stats_width = (stat_box_width * 3) + (spacing * 2)
    start_x = (width - total_stats_width) // 2

    for idx, (label, value, unit, percentage) in enumerate(stats_data):
        box_x = start_x + (idx * (stat_box_width + spacing))
        box_y = current_y

        # Stat box background
        draw.rectangle([box_x, box_y, box_x + stat_box_width, box_y + stat_box_height],
                      fill=CODEC_BG_MEDIUM, outline=CODEC_GREEN_PRIMARY, width=1)

        # Label
        label_y = box_y + 8
        safe_draw_text(draw, (box_x + 10, label_y), label,
                      primary_font=font_stats_label, fill=CODEC_GREEN_DIM)

        # Value
        value_y = label_y + 16
        safe_draw_text(draw, (box_x + 10, value_y), value,
                      primary_font=font_stats_value, fill=CODEC_BORDER_BRIGHT)

        # Unit label
        unit_y = value_y + 24
        safe_draw_text(draw, (box_x + 10, unit_y), unit,
                      primary_font=font_tiny, fill=CODEC_GREEN_TEXT)

        # Progress bar
        bar_x = box_x + 10
        bar_y = box_y + stat_box_height - 12
        bar_width = stat_box_width - 20
        bar_height = 6

        draw_progress_bar(draw, bar_x, bar_y, bar_width, bar_height,
                         percentage, CODEC_GREEN_PRIMARY, CODEC_BG_DARK)

        # Percentage text
        pct_text = f"{percentage}%"
        try:
            pct_bbox = draw.textbbox((0, 0), pct_text, font=font_tiny)
            pct_width = pct_bbox[2] - pct_bbox[0]
        except:
            pct_width = len(pct_text) * 5

        safe_draw_text(draw, (box_x + stat_box_width - pct_width - 10, unit_y),
                      pct_text, primary_font=font_tiny, fill=CODEC_GREEN_DIM)

    current_y += stat_box_height + 20

    # === ACTIVITY STATUS BAR ===
    current_y += 5
    status_x = 50
    status_width = width - 100

    # Status label
    safe_draw_text(draw, (status_x, current_y), "MONTHLY ACTIVITY:",
                  primary_font=font_small, fill=CODEC_GREEN_TEXT)

    # Calculate overall activity (average of percentages)
    overall_activity = (xp_pct + msg_pct + voice_pct) // 3
    activity_label = get_activity_status(overall_activity)

    try:
        label_bbox = draw.textbbox((0, 0), "MONTHLY ACTIVITY:", font=font_small)
        label_width = label_bbox[2] - label_bbox[0]
    except:
        label_width = 110

    safe_draw_text(draw, (status_x + label_width + 10, current_y), activity_label,
                  primary_font=font_small, fill=CODEC_GREEN_BRIGHT)

    current_y += 18

    # Activity bar
    bar_height = 8
    draw_progress_bar(draw, status_x, current_y, status_width, bar_height,
                     overall_activity, CODEC_GREEN_BRIGHT, CODEC_BG_MEDIUM)

    current_y += bar_height + 15

    # === FOOTER ===
    footer_y = height - 45

    # Left: Status indicator
    status_circle_x = 30
    status_circle_y = footer_y + 6
    draw.ellipse([status_circle_x, status_circle_y, status_circle_x + 8, status_circle_y + 8],
                fill=CODEC_GREEN_BRIGHT)
    safe_draw_text(draw, (status_circle_x + 12, footer_y + 5), "SIGNAL: STRONG",
                  primary_font=font_small, fill=CODEC_GREEN_TEXT)

    # Center: Main footer
    footer_text = f"<< {SERVER_FOOTER.upper()}  >>"
    try:
        footer_bbox = draw.textbbox((0, 0), footer_text, font=font_small)
        footer_width = footer_bbox[2] - footer_bbox[0]
    except:
        footer_width = len(footer_text) * 6

    footer_x = (width - footer_width) // 2
    safe_draw_text(draw, (footer_x, footer_y + 5), footer_text,
                  primary_font=font_small, fill=CODEC_GREEN_DIM)

    # Right: Codec frequency
    codec_text = "CODEC: 140.85"
    try:
        codec_bbox = draw.textbbox((0, 0), codec_text, font=font_small)
        codec_width = codec_bbox[2] - codec_bbox[0]
    except:
        codec_width = len(codec_text) * 6

    safe_draw_text(draw, (width - codec_width - 30, footer_y + 5), codec_text,
                  primary_font=font_small, fill=CODEC_GREEN_TEXT)

    # === APPLY EFFECTS ===
    draw_codec_frame(draw, width, height)
    base = add_heavy_scanlines(base, spacing=3)
    base = add_static_noise(base, intensity=10)
    base = add_phosphor_glow(base)

    return base


def generate_profile_new_bg(
    username: str,
    role_name: str,
    avatar_url: Optional[str],
    bio_text: Optional[str],
    xp: int,
    messages: int,
    voice_hours: int,
    current_rank: str = "Rookie",
    use_legacy: bool = False,
    server_avg_messages: int = 0
):
    """
    Enhanced version of generate_profile_new with background effects.
    For now, just calls the basic version.
    """
    return generate_profile_new(username, role_name, avatar_url, bio_text, xp, messages, voice_hours,
                                current_rank, use_legacy, server_avg_messages)


async def generate_profile_new_nitro(
    username: str,
    role_name: str,
    avatar_url: Optional[str],
    bio_text: Optional[str],
    xp: int,
    messages: int,
    voice_hours: int,
    current_rank: str = "Rookie",
    use_legacy: bool = False,
    server_avg_messages: int = 0
):
    """
    Nitro version of generate_profile_new with enhanced effects.
    For now, just calls the basic version.
    """
    return generate_profile_new(username, role_name, avatar_url, bio_text, xp, messages, voice_hours,
                                current_rank, use_legacy, server_avg_messages)
