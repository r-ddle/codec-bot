"""
Server Event Image Generator - MGS Codec Style
Generates progress images for weekly server events
"""
from PIL import Image, ImageDraw
from datetime import datetime, timedelta
from typing import List, Tuple, Optional

from utils.image_gen import (
    load_font,
    safe_draw_text,
    add_heavy_scanlines,
    add_static_noise,
    add_phosphor_glow,
    draw_codec_frame,
    draw_codec_divider,
    sanitize_username,
    CODEC_GREEN_BRIGHT,
    CODEC_GREEN_TEXT,
    CODEC_GREEN_DIM,
    CODEC_BG_DARK,
    CODEC_BORDER_BRIGHT
)


def generate_event_start_banner(
    event_title: str,
    message_goal: int,
    start_date: str,
    end_date: str
) -> Image.Image:
    """
    Generate event start banner - announces new weekly event

    Args:
        event_title: Event name
        message_goal: Target message count
        start_date: Start date string
        end_date: End date string
    """
    width = 800
    height = 500  # Increased from 400

    base = Image.new("RGB", (width, height), CODEC_BG_DARK)
    draw = ImageDraw.Draw(base)

    # Fonts
    font_title = load_font(28, "title")
    font_subtitle = load_font(20, "text")
    font_body = load_font(16, "text")
    font_small = load_font(14, "text")

    # === HEADER ===
    header_y = 40
    safe_draw_text(draw, (40, header_y),
                  "◄◄ TACTICAL MISSION BRIEFING ►►",
                  primary_font=font_small, fill=CODEC_GREEN_DIM)

    # === EVENT TITLE ===
    title_y = header_y + 35
    safe_draw_text(draw, (40, title_y),
                  event_title.upper(),
                  primary_font=font_title, fill=CODEC_BORDER_BRIGHT)

    # === DIVIDER ===
    divider1_y = title_y + 45
    draw_codec_divider(draw, 40, divider1_y, width - 80)

    # === MISSION DETAILS ===
    details_y = divider1_y + 30
    safe_draw_text(draw, (40, details_y),
                  "MISSION OBJECTIVE",
                  primary_font=font_subtitle, fill=CODEC_GREEN_BRIGHT)

    objective_y = details_y + 40
    safe_draw_text(draw, (50, objective_y),
                  f"► REACH {message_goal:,} MESSAGES",
                  primary_font=font_body, fill=CODEC_GREEN_TEXT)

    safe_draw_text(draw, (50, objective_y + 35),
                  "► ALL PARTICIPANTS EARN REWARDS",
                  primary_font=font_body, fill=CODEC_GREEN_TEXT)

    safe_draw_text(draw, (50, objective_y + 70),
                  "► TOP 3 CONTRIBUTORS GET BONUS",
                  primary_font=font_body, fill=CODEC_GREEN_TEXT)

    # === DIVIDER ===
    divider2_y = objective_y + 115
    draw_codec_divider(draw, 40, divider2_y, width - 80)

    # === TIMELINE ===
    timeline_y = divider2_y + 30
    safe_draw_text(draw, (40, timeline_y),
                  "OPERATION TIMELINE",
                  primary_font=font_subtitle, fill=CODEC_GREEN_BRIGHT)

    dates_y = timeline_y + 40
    safe_draw_text(draw, (50, dates_y),
                  f"START: {start_date}",
                  primary_font=font_body, fill=CODEC_GREEN_TEXT)

    safe_draw_text(draw, (50, dates_y + 35),
                  f"END: {end_date}",
                  primary_font=font_body, fill=CODEC_GREEN_TEXT)

    # === FOOTER ===
    footer_y = height - 40
    safe_draw_text(draw, (40, footer_y),
                  "◄◄ GOOD LUCK, SOLDIER. DISMISSED. ►►",
                  primary_font=font_small, fill=CODEC_GREEN_DIM)

    # === APPLY EFFECTS ===
    draw_codec_frame(draw, width, height)
    base = add_heavy_scanlines(base, spacing=3)
    base = add_static_noise(base, intensity=12)
    base = add_phosphor_glow(base)

    return base


def generate_event_progress(
    event_title: str,
    current_messages: int,
    goal_messages: int,
    time_remaining: str,
    participant_count: int,
    top_contributors: Optional[List[Tuple[str, int]]] = None
) -> Image.Image:
    """
    Generate event progress update image

    Args:
        event_title: Event name
        current_messages: Current message count
        goal_messages: Goal message count
        time_remaining: Time left string (e.g., "3 days, 5 hours")
        participant_count: Number of participants
        top_contributors: List of (username, message_count) tuples
    """
    width = 750
    height = 300

    base = Image.new("RGB", (width, height), CODEC_BG_DARK)
    draw = ImageDraw.Draw(base)

    # Fonts
    font_title = load_font(24, "title")
    font_subtitle = load_font(18, "text")
    font_body = load_font(16, "text")
    font_stats = load_font(15, "text")
    font_small = load_font(13, "text")

    # === HEADER ===
    header_y = 30
    safe_draw_text(draw, (40, header_y),
                  "◄◄ MISSION STATUS REPORT ►►",
                  primary_font=font_small, fill=CODEC_GREEN_DIM)

    # === EVENT TITLE ===
    title_y = header_y + 30
    safe_draw_text(draw, (40, title_y),
                  event_title.upper(),
                  primary_font=font_title, fill=CODEC_BORDER_BRIGHT)

    # === DIVIDER ===
    divider1_y = title_y + 40
    draw_codec_divider(draw, 40, divider1_y, width - 80)

    # === PROGRESS BAR ===
    progress_y = divider1_y + 25
    safe_draw_text(draw, (40, progress_y),
                  "OBJECTIVE PROGRESS",
                  primary_font=font_subtitle, fill=CODEC_GREEN_BRIGHT)

    # Progress percentage
    percentage = min(100, (current_messages / goal_messages * 100)) if goal_messages > 0 else 0

    progress_text_y = progress_y + 35
    safe_draw_text(draw, (40, progress_text_y),
                  f"{current_messages:,} / {goal_messages:,} MESSAGES",
                  primary_font=font_body, fill=CODEC_GREEN_TEXT)

    safe_draw_text(draw, (40, progress_text_y + 28),
                  f"{percentage:.1f}% COMPLETE",
                  primary_font=font_body, fill=CODEC_GREEN_BRIGHT if percentage >= 100 else CODEC_GREEN_TEXT)

    # Visual progress bar
    bar_y = progress_text_y + 65
    bar_width = width - 120
    bar_height = 25
    bar_x = 40

    # Background bar
    draw.rectangle([bar_x, bar_y, bar_x + bar_width, bar_y + bar_height],
                  outline=CODEC_GREEN_TEXT, width=2)

    # Filled portion
    filled_width = int(bar_width * min(percentage / 100, 1.0))
    if filled_width > 4:  # Need at least 4 pixels to draw with 2px border offset
        draw.rectangle([bar_x + 2, bar_y + 2, bar_x + filled_width - 2, bar_y + bar_height - 2],
                      fill=CODEC_GREEN_TEXT)

    # === FOOTER ===
    footer_y = height - 35
    safe_draw_text(draw, (40, footer_y),
                  "◄◄ KEEP UP THE GOOD WORK, SOLDIER ►►",
                  primary_font=font_small, fill=CODEC_GREEN_DIM)

    # === APPLY EFFECTS ===
    draw_codec_frame(draw, width, height)
    base = add_heavy_scanlines(base, spacing=3)
    base = add_static_noise(base, intensity=12)
    base = add_phosphor_glow(base)

    return base


def generate_event_results(
    event_title: str,
    total_messages: int,
    goal_messages: int,
    goal_reached: bool,
    leaderboard: List[Tuple[str, int]],
    participant_count: int
) -> Image.Image:
    """
    Generate event end results/leaderboard

    Args:
        event_title: Event name
        total_messages: Final message count
        goal_messages: Goal that was set
        goal_reached: Whether goal was achieved
        leaderboard: List of (username, message_count) sorted by count
        participant_count: Total participants
    """
    width = 800
    height = 450  # Adjusted height for status line

    base = Image.new("RGB", (width, height), CODEC_BG_DARK)
    draw = ImageDraw.Draw(base)

    # Fonts
    font_title = load_font(26, "title")
    font_subtitle = load_font(18, "text")
    font_body = load_font(16, "text")
    font_stats = load_font(15, "text")
    font_small = load_font(13, "text")

    # === HEADER ===
    header_y = 35
    safe_draw_text(draw, (40, header_y),
                  "◄◄ MISSION DEBRIEF ►►",
                  primary_font=font_small, fill=CODEC_GREEN_DIM)

    # === EVENT TITLE ===
    title_y = header_y + 30
    title_status = "COMPLETE" if goal_reached else "FAILED"
    safe_draw_text(draw, (40, title_y),
                  f"{event_title.upper()}",
                  primary_font=font_title, fill=CODEC_BORDER_BRIGHT)

    # Status on separate line
    status_y = title_y + 35
    safe_draw_text(draw, (40, status_y),
                  title_status,
                  primary_font=font_subtitle, fill=CODEC_GREEN_BRIGHT if goal_reached else CODEC_GREEN_DIM)

    # === DIVIDER ===
    divider1_y = status_y + 42
    draw_codec_divider(draw, 40, divider1_y, width - 80)

    # === RESULTS SUMMARY ===
    results_y = divider1_y + 30
    safe_draw_text(draw, (40, results_y),
                  "MISSION RESULTS",
                  primary_font=font_subtitle, fill=CODEC_GREEN_BRIGHT)

    summary_y = results_y + 40

    # Goal status
    status_text = "✓ OBJECTIVE COMPLETE" if goal_reached else "✗ OBJECTIVE FAILED"
    status_color = CODEC_GREEN_BRIGHT if goal_reached else CODEC_GREEN_DIM
    safe_draw_text(draw, (50, summary_y),
                  status_text,
                  primary_font=font_body, fill=status_color)

    # Message count
    safe_draw_text(draw, (50, summary_y + 35),
                  f"TOTAL MESSAGES: {total_messages:,} / {goal_messages:,}",
                  primary_font=font_body, fill=CODEC_GREEN_TEXT)

    # === DIVIDER ===
    divider2_y = summary_y + 80
    draw_codec_divider(draw, 40, divider2_y, width - 80)

    # === REWARDS ===
    rewards_y = divider2_y + 25
    safe_draw_text(draw, (40, rewards_y),
                  "REWARDS DISTRIBUTED",
                  primary_font=font_subtitle, fill=CODEC_GREEN_BRIGHT)

    reward_info_y = rewards_y + 35
    safe_draw_text(draw, (50, reward_info_y),
                  "ALL PARTICIPANTS: +100 XP",
                  primary_font=font_body, fill=CODEC_GREEN_TEXT)

    safe_draw_text(draw, (50, reward_info_y + 32),
                  "TOP 3 CONTRIBUTORS: +500 XP BONUS",
                  primary_font=font_body, fill=CODEC_GREEN_TEXT)

    # === FOOTER ===
    footer_y = height - 35
    footer_text = "◄◄ EXCELLENT WORK. MISSION COMPLETE. ►►" if goal_reached else "◄◄ MISSION FAILED. BETTER LUCK NEXT TIME. ►►"
    safe_draw_text(draw, (40, footer_y),
                  footer_text,
                  primary_font=font_small, fill=CODEC_GREEN_DIM)

    # === APPLY EFFECTS ===
    draw_codec_frame(draw, width, height)
    base = add_heavy_scanlines(base, spacing=3)
    base = add_static_noise(base, intensity=12)
    base = add_phosphor_glow(base)

    return base


# === TEST ===
if __name__ == "__main__":
    # Test start banner
    start_img = generate_event_start_banner(
        event_title="Weekly Community Challenge",
        message_goal=15000,
        start_date="MONDAY, OCT 9",
        end_date="SUNDAY, OCT 15"
    )
    start_img.save("event_start_test.png")
    print("✅ Start banner saved!")

    # Test progress
    progress_img = generate_event_progress(
        event_title="Weekly Community Challenge",
        current_messages=8542,
        goal_messages=15000,
        time_remaining="3 days, 12 hours",
        participant_count=45,
        top_contributors=[
            ("Solid Snake", 1250),
            ("Big Boss", 980),
            ("Revolver Ocelot", 765)
        ]
    )
    progress_img.save("event_progress_test.png")
    print("✅ Progress image saved!")

    # Test results
    results_img = generate_event_results(
        event_title="Weekly Community Challenge",
        total_messages=16234,
        goal_messages=15000,
        goal_reached=True,
        leaderboard=[
            ("Solid Snake", 1842),
            ("Big Boss", 1456),
            ("Revolver Ocelot", 1123),
            ("Otacon", 892),
            ("Meryl", 765),
            ("Gray Fox", 654),
            ("Naomi", 543),
            ("Mei Ling", 432),
            ("Campbell", 321),
            ("Miller", 287)
        ],
        participant_count=67
    )
    results_img.save("event_results_test.png")
    print("✅ Results image saved!")
