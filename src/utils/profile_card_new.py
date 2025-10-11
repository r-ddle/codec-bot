"""
New MGS Codec Profile Card Designs
Three variants: Basic, Enhanced BG, Nitro Banner
"""
import asyncio
from PIL import Image, ImageDraw, ImageFilter
from io import BytesIO
import aiohttp
from typing import Optional, Tuple

# Import shared codec utilities
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
from utils.profile_card_gen import create_profile_avatar


def draw_stat_cell(draw, x, y, width, height, label, value, font_label, font_value):
    """Draw a stat cell with border, label on left, value on right"""
    # Draw cell border
    draw.rectangle([x, y, x + width, y + height], outline=CODEC_GREEN_TEXT, width=2)

    # Draw label on left
    label_x = x + 15
    label_y = y + (height - 20) // 2
    safe_draw_text(draw, (label_x, label_y), label, primary_font=font_label, fill=CODEC_GREEN_TEXT)

    # Draw value right-aligned
    try:
        val_bbox = draw.textbbox((0, 0), value, font=font_value)
        val_width = val_bbox[2] - val_bbox[0]
    except:
        val_width = len(value) * 10

    value_x = x + width - val_width - 15
    value_y = y + (height - 20) // 2
    safe_draw_text(draw, (value_x, value_y), value, primary_font=font_value, fill=CODEC_GREEN_BRIGHT)


async def download_banner(banner_url: str) -> Optional[Image.Image]:
    """Download and return user's banner image"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(banner_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.read()
                    return Image.open(BytesIO(data)).convert("RGB")
    except Exception as e:
        print(f"Error downloading banner: {e}")
    return None


def generate_profile_new(
    username: str,
    role_name: str,
    avatar_url: Optional[str],
    bio_text: str,
    xp: int,
    messages: int,
    voice_hours: int
) -> Image.Image:
    """
    New profile card design - Clean card layout

    Layout:
    [PFP]  Discord Username  |  XP                 xxx
    [PFP]  Profile bio                |  MESSAGES xxx
    [PFP]  Profile bio                |  VOICE          xxx
    """
    width = 800
    height = 340

    # Create base
    base = Image.new("RGB", (width, height), CODEC_BG_DARK)
    draw = ImageDraw.Draw(base)

    # Load fonts - Use Helvetica for username, numbers font for stats
    font_username = load_font(36, "text")  # Large Helvetica for Discord name
    font_body = load_font(15, "text")  # Helvetica for bio
    font_stat_label = load_font(14, "text")  # Helvetica for labels
    font_stat_numbers = load_font(24, "numbers")  # Numbers font for values
    font_footer = load_font(10, "text")

    # === PROFILE PICTURE (LEFT SIDE) ===
    avatar_size = 180
    avatar_x = 35
    avatar_y = 50

    if avatar_url:
        avatar = create_profile_avatar(avatar_url, size=(avatar_size, avatar_size))
        base.paste(avatar, (avatar_x, avatar_y))
    else:
        # Draw placeholder
        draw.rectangle([avatar_x, avatar_y, avatar_x + avatar_size, avatar_y + avatar_size],
                      outline=CODEC_GREEN_TEXT, width=2)

    # === CENTER: USERNAME & BIO ===
    center_x = avatar_x + avatar_size + 30
    center_y = avatar_y + 10
    center_width = 300

    # Discord Username (BIG TEXT)
    username_clean = sanitize_username(username)
    safe_draw_text(draw, (center_x, center_y),
                  username_clean,
                  primary_font=font_username, fill=CODEC_BORDER_BRIGHT)

    # Bio (2 rows for long bios)
    bio_y = center_y + 60
    bio_display = bio_text[:150] if bio_text else "No bio set."

    # Wrap bio text - max 2 lines
    words = bio_display.split()
    lines = []
    current_line = ""
    max_chars_per_line = 40

    for word in words:
        if len(current_line + word) <= max_chars_per_line:
            current_line += word + " "
        else:
            if current_line:
                lines.append(current_line.strip())
            current_line = word + " "
            if len(lines) >= 2:  # Max 2 lines for bio
                break

    if current_line and len(lines) < 2:
        lines.append(current_line.strip())

    for i, line in enumerate(lines):
        safe_draw_text(draw, (center_x, bio_y + i * 24),
                      line,
                      primary_font=font_body, fill=CODEC_GREEN_TEXT)

    # === RIGHT: STATS COLUMN ===
    # Draw vertical divider
    divider_x = center_x + center_width + 20
    draw.line([(divider_x, avatar_y), (divider_x, avatar_y + avatar_size)],
             fill=CODEC_GREEN_TEXT, width=2)

    stats_x = divider_x + 25
    stats_start_y = avatar_y + 15

    # XP Stat
    xp_y = stats_start_y
    safe_draw_text(draw, (stats_x, xp_y),
                  "XP",
                  primary_font=font_stat_label, fill=CODEC_GREEN_TEXT)
    safe_draw_text(draw, (stats_x + 130, xp_y - 5),
                  str(xp),
                  primary_font=font_stat_numbers, fill=CODEC_GREEN_BRIGHT)

    # MESSAGES Stat
    messages_y = xp_y + 60
    safe_draw_text(draw, (stats_x, messages_y),
                  "MESSAGES",
                  primary_font=font_stat_label, fill=CODEC_GREEN_TEXT)
    safe_draw_text(draw, (stats_x + 130, messages_y - 5),
                  str(messages),
                  primary_font=font_stat_numbers, fill=CODEC_GREEN_BRIGHT)

    # VOICE Stat
    voice_y = messages_y + 60
    safe_draw_text(draw, (stats_x, voice_y),
                  "VOICE",
                  primary_font=font_stat_label, fill=CODEC_GREEN_TEXT)
    voice_display = f"{voice_hours}H"
    safe_draw_text(draw, (stats_x + 130, voice_y - 5),
                  voice_display,
                  primary_font=font_stat_numbers, fill=CODEC_GREEN_BRIGHT)

    # === BORDER FRAME ===
    # Draw clean border around the card
    border_margin = 20
    draw.rectangle([border_margin, border_margin,
                   width - border_margin, height - border_margin],
                  outline=CODEC_GREEN_TEXT, width=3)

    # === FOOTER ===
    footer_y = height - 30
    footer_text = "Outer Heaven: Exciled Units"
    try:
        footer_bbox = draw.textbbox((0, 0), footer_text, font=font_footer)
        footer_width = footer_bbox[2] - footer_bbox[0]
    except:
        footer_width = len(footer_text) * 6

    footer_x = (width - footer_width) // 2
    safe_draw_text(draw, (footer_x, footer_y),
                  footer_text,
                  primary_font=font_footer, fill=CODEC_GREEN_DIM)

    # === APPLY CODEC EFFECTS ===
    base = add_heavy_scanlines(base, spacing=3)
    base = add_static_noise(base, intensity=12)
    base = add_phosphor_glow(base)

    return base


def generate_profile_new_bg(
    username: str,
    role_name: str,
    avatar_url: Optional[str],
    bio_text: str,
    xp: int,
    messages: int,
    voice_hours: int
) -> Image.Image:
    """
    New profile card design - Enhanced background version
    Same layout but with more interesting background patterns
    """
    width = 750
    height = 480

    # Create base with gradient pattern
    base = Image.new("RGB", (width, height), CODEC_BG_DARK)
    draw = ImageDraw.Draw(base)

    # Add background pattern (circuit-like lines)
    for i in range(0, width, 50):
        draw.line([(i, 0), (i + 100, height)], fill=(0, 50, 0), width=1)
    for i in range(0, height, 50):
        draw.line([(0, i), (width, i + 100)], fill=(0, 50, 0), width=1)

    # Add slight overlay to darken
    overlay = Image.new("RGB", (width, height), (0, 0, 0))
    base = Image.blend(base, overlay, 0.5)
    draw = ImageDraw.Draw(base)

    # Load fonts
    font_name = load_font(26, "title")
    font_subtitle = load_font(18, "text")
    font_body = load_font(16, "text")
    font_stat_label = load_font(15, "text")
    font_stat_value = load_font(18, "text")
    font_footer = load_font(11, "text")

    # === LEFT SIDE: AVATAR ===
    avatar_size = 140
    avatar_x = 40
    avatar_y = 40

    if avatar_url:
        avatar = create_profile_avatar(avatar_url, size=(avatar_size, avatar_size))
        base.paste(avatar, (avatar_x, avatar_y))
    else:
        draw.rectangle([avatar_x, avatar_y, avatar_x + avatar_size, avatar_y + avatar_size],
                      outline=CODEC_GREEN_TEXT, width=2)

    # === RIGHT SIDE: NAME, ROLE, BIO ===
    info_x = avatar_x + avatar_size + 30
    info_y = avatar_y

    username_clean = sanitize_username(username)
    safe_draw_text(draw, (info_x, info_y),
                  username_clean.upper(),
                  primary_font=font_name, fill=CODEC_BORDER_BRIGHT)

    role_y = info_y + 35
    role_text = f"► {role_name.upper()}"
    safe_draw_text(draw, (info_x, role_y),
                  role_text,
                  primary_font=font_subtitle, fill=CODEC_GREEN_BRIGHT)

    bio_y = role_y + 30
    bio_display = bio_text[:120] if bio_text else "No bio set."

    words = bio_display.split()
    lines = []
    current_line = ""
    max_chars_per_line = 45

    for word in words:
        if len(current_line + word) <= max_chars_per_line:
            current_line += word + " "
        else:
            if current_line:
                lines.append(current_line.strip())
            current_line = word + " "
            if len(lines) >= 3:
                break

    if current_line and len(lines) < 3:
        lines.append(current_line.strip())

    for i, line in enumerate(lines):
        safe_draw_text(draw, (info_x, bio_y + i * 22),
                      f'"{line}"' if i == 0 else line,
                      primary_font=font_body, fill=CODEC_GREEN_TEXT)

    # === DIVIDER ===
    divider_y = avatar_y + avatar_size + 25
    draw_codec_divider(draw, 40, divider_y, width - 80)

    # === STATS SECTION ===
    stats_header_y = divider_y + 20
    safe_draw_text(draw, (40, stats_header_y),
                  "STATS",
                  primary_font=font_subtitle, fill=CODEC_GREEN_BRIGHT)

    stats_y = stats_header_y + 35
    cell_width = (width - 120) // 2
    cell_height = 50
    cell_spacing = 10

    stats_data = [
        ("XP", f"{xp:,}"),
        ("MESSAGES", f"{messages:,}"),
        ("VOICE TIME", f"{voice_hours}H")
    ]

    for i, (label, value) in enumerate(stats_data):
        col = i % 2
        row = i // 2
        cell_x = 40 + col * (cell_width + cell_spacing)
        cell_y = stats_y + row * (cell_height + cell_spacing)

        draw_stat_cell(draw, cell_x, cell_y, cell_width, cell_height,
                      label, value, font_stat_label, font_stat_value)

    # === FOOTER ===
    footer_y = height - 25
    footer_text = "Outer Heaven: Exciled Units"
    try:
        footer_bbox = draw.textbbox((0, 0), footer_text, font=font_footer)
        footer_width = footer_bbox[2] - footer_bbox[0]
    except:
        footer_width = len(footer_text) * 6

    footer_x = (width - footer_width) // 2
    safe_draw_text(draw, (footer_x, footer_y),
                  footer_text,
                  primary_font=font_footer, fill=CODEC_GREEN_DIM)

    # === APPLY EFFECTS ===
    draw_codec_frame(draw, width, height)
    base = add_heavy_scanlines(base, spacing=3)
    base = add_static_noise(base, intensity=12)
    base = add_phosphor_glow(base)

    return base


async def generate_profile_new_nitro(
    username: str,
    role_name: str,
    avatar_url: Optional[str],
    banner_url: Optional[str],
    bio_text: str,
    xp: int,
    messages: int,
    voice_hours: int
) -> Image.Image:
    """
    New profile card design - Nitro banner version
    Uses user's banner as background for top section (blurred/dimmed)
    """
    width = 750
    height = 480

    # Create base
    base = Image.new("RGB", (width, height), CODEC_BG_DARK)

    # === BANNER SECTION (if available) ===
    banner_height = 210  # Top section height

    if banner_url:
        banner = await download_banner(banner_url)
        if banner:
            # Resize banner to fit width
            banner = banner.resize((width, banner_height), Image.Resampling.LANCZOS)

            # Apply blur
            banner = banner.filter(ImageFilter.GaussianBlur(radius=8))

            # Reduce opacity by blending with dark background
            dark_overlay = Image.new("RGB", (width, banner_height), (0, 10, 0))
            banner = Image.blend(banner, dark_overlay, 0.7)

            # Apply green tint
            pixels = banner.load()
            for y in range(banner_height):
                for x in range(width):
                    r, g, b = pixels[x, y]
                    # Shift to green tint
                    pixels[x, y] = (r // 4, g, b // 4)

            # Paste banner to top section
            base.paste(banner, (0, 0))

    draw = ImageDraw.Draw(base)

    # Load fonts
    font_name = load_font(26, "title")
    font_subtitle = load_font(18, "text")
    font_body = load_font(16, "text")
    font_stat_label = load_font(15, "text")
    font_stat_value = load_font(18, "text")
    font_footer = load_font(11, "text")

    # === LEFT SIDE: AVATAR ===
    avatar_size = 140
    avatar_x = 40
    avatar_y = 40

    if avatar_url:
        avatar = create_profile_avatar(avatar_url, size=(avatar_size, avatar_size))
        base.paste(avatar, (avatar_x, avatar_y))
    else:
        draw.rectangle([avatar_x, avatar_y, avatar_x + avatar_size, avatar_y + avatar_size],
                      outline=CODEC_GREEN_TEXT, width=2)

    # === RIGHT SIDE: NAME, ROLE, BIO ===
    info_x = avatar_x + avatar_size + 30
    info_y = avatar_y

    username_clean = sanitize_username(username)
    safe_draw_text(draw, (info_x, info_y),
                  username_clean.upper(),
                  primary_font=font_name, fill=CODEC_BORDER_BRIGHT)

    role_y = info_y + 35
    role_text = f"► {role_name.upper()}"
    safe_draw_text(draw, (info_x, role_y),
                  role_text,
                  primary_font=font_subtitle, fill=CODEC_GREEN_BRIGHT)

    bio_y = role_y + 30
    bio_display = bio_text[:120] if bio_text else "No bio set."

    words = bio_display.split()
    lines = []
    current_line = ""
    max_chars_per_line = 45

    for word in words:
        if len(current_line + word) <= max_chars_per_line:
            current_line += word + " "
        else:
            if current_line:
                lines.append(current_line.strip())
            current_line = word + " "
            if len(lines) >= 3:
                break

    if current_line and len(lines) < 3:
        lines.append(current_line.strip())

    for i, line in enumerate(lines):
        safe_draw_text(draw, (info_x, bio_y + i * 22),
                      f'"{line}"' if i == 0 else line,
                      primary_font=font_body, fill=CODEC_GREEN_TEXT)

    # === DIVIDER ===
    divider_y = banner_height + 15
    draw_codec_divider(draw, 40, divider_y, width - 80)

    # === STATS SECTION ===
    stats_header_y = divider_y + 20
    safe_draw_text(draw, (40, stats_header_y),
                  "STATS",
                  primary_font=font_subtitle, fill=CODEC_GREEN_BRIGHT)

    stats_y = stats_header_y + 35
    cell_width = (width - 120) // 2
    cell_height = 50
    cell_spacing = 10

    stats_data = [
        ("XP", f"{xp:,}"),
        ("MESSAGES", f"{messages:,}"),
        ("VOICE TIME", f"{voice_hours}H")
    ]

    for i, (label, value) in enumerate(stats_data):
        col = i % 2
        row = i // 2
        cell_x = 40 + col * (cell_width + cell_spacing)
        cell_y = stats_y + row * (cell_height + cell_spacing)

        draw_stat_cell(draw, cell_x, cell_y, cell_width, cell_height,
                      label, value, font_stat_label, font_stat_value)

    # === FOOTER ===
    footer_y = height - 25
    footer_text = "Outer Heaven: Exciled Units"
    try:
        footer_bbox = draw.textbbox((0, 0), footer_text, font=font_footer)
        footer_width = footer_bbox[2] - footer_bbox[0]
    except:
        footer_width = len(footer_text) * 6

    footer_x = (width - footer_width) // 2
    safe_draw_text(draw, (footer_x, footer_y),
                  footer_text,
                  primary_font=font_footer, fill=CODEC_GREEN_DIM)

    # === APPLY EFFECTS ===
    draw_codec_frame(draw, width, height)
    base = add_heavy_scanlines(base, spacing=3)
    base = add_static_noise(base, intensity=12)
    base = add_phosphor_glow(base)

    return base


# === TEST ===
if __name__ == "__main__":
    img = generate_profile_new(
        username="Solid Snake",
        role_name="FOXHOUND Operative",
        avatar_url="https://cdn.discordapp.com/embed/avatars/1.png",
        bio_text="A soldier who fights not for country, but for himself.",
        xp=12500,
        messages=850,
        voice_hours=42
    )
    img.save("profile_new_test.png")
    print("✅ New profile card saved!")
