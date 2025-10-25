# profile_card_gen.py
# Author: Tom & Claude
# MGS Codec-style tactical profile/bio card generator

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import io
import requests
import random
import unicodedata
from datetime import datetime
from typing import Optional, List

# === IMPORT SHARED FUNCTIONS FROM image_gen.py ===
# In production, import these from image_gen.py:
# from image_gen import (
#     sanitize_username, load_font, safe_draw_text,
#     download_avatar, apply_mgs_filter, create_codec_avatar,
#     add_heavy_scanlines, add_static_noise, add_phosphor_glow,
#     draw_codec_frame, draw_codec_divider,
#     CODEC_BG_DARK, CODEC_BG_MEDIUM, CODEC_GREEN_PRIMARY,
#     CODEC_GREEN_BRIGHT, CODEC_GREEN_DIM, CODEC_GREEN_TEXT,
#     CODEC_BORDER_BRIGHT
# )

# For this artifact, we'll include minimal versions:

# === AUTHENTIC MGS CODEC COLOR PALETTE ===
CODEC_BG_DARK = (5, 25, 15)
CODEC_BG_MEDIUM = (10, 35, 20)
CODEC_GREEN_PRIMARY = (50, 200, 100)
CODEC_GREEN_BRIGHT = (100, 255, 150)
CODEC_GREEN_DIM = (30, 120, 60)
CODEC_GREEN_TEXT = (80, 220, 120)
CODEC_BORDER_BRIGHT = (120, 255, 180)

def sanitize_username(username):
    """Sanitizes username to handle Unicode characters properly."""
    if not username:
        return "UNKNOWN"
    cleaned = ''.join(char for char in username if unicodedata.category(char)[0] != 'C')
    cleaned = ' '.join(cleaned.split())
    if not cleaned or cleaned.isspace():
        return "AGENT"
    cleaned = cleaned.strip()[:30]
    return cleaned if cleaned else "AGENT"

def load_font(size, font_type="text"):
    """Load fonts with fallback system."""
    import os

    if font_type == "text":
        # First, try to load from public/fonts
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        fonts_dir = os.path.join(base_dir, "public", "fonts")
        custom_fonts = [
            os.path.join(fonts_dir, "Helvetica.ttf"),
            os.path.join(fonts_dir, "helvetica.ttf"),
            os.path.join(fonts_dir, "Arial.ttf"),
            os.path.join(fonts_dir, "arial.ttf")
        ]

        for font_path in custom_fonts:
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                continue

        # Fall back to system fonts
        fallback_fonts = [
            "arial.ttf", "Arial.ttf", "arialbd.ttf",
            "helvetica.ttf", "Helvetica.ttf",
            "C:\\Windows\\Fonts\\arial.ttf",
            "C:\\Windows\\Fonts\\Arial.ttf"
        ]
        for font_name in fallback_fonts:
            try:
                return ImageFont.truetype(font_name, size)
            except Exception:
                continue
        return ImageFont.load_default()

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    fonts_dir = os.path.join(base_dir, "public", "fonts")

    font_files = {
        "title": "title.TTF",
        "numbers": "numbers.ttf"
    }

    if font_type in font_files:
        custom_font_path = os.path.join(fonts_dir, font_files[font_type])
        try:
            return ImageFont.truetype(custom_font_path, size)
        except Exception:
            pass

    fallback_fonts = ["arial.ttf", "Arial.ttf", "C:\\Windows\\Fonts\\arial.ttf"]
    for font_name in fallback_fonts:
        try:
            return ImageFont.truetype(font_name, size)
        except Exception:
            continue

    return ImageFont.load_default()

def safe_draw_text(draw, xy, text, primary_font, fallback_font=None, fill=(255,255,255)):
    """Draw text with fallback support for missing glyphs."""
    if not text:
        return

    if fallback_font is None:
        fallback_font = load_font(getattr(primary_font, 'size', 18), 'text')

    x, y = xy
    for ch in text:
        try:
            mask = primary_font.getmask(ch)
            draw.text((x, y), ch, font=primary_font, fill=fill)
            bbox = draw.textbbox((0,0), ch, font=primary_font)
            w = bbox[2] - bbox[0]
        except Exception:
            draw.text((x, y), ch, font=fallback_font, fill=fill)
            bbox = draw.textbbox((0,0), ch, font=fallback_font)
            w = bbox[2] - bbox[0]

        x += max(1, w)

def download_avatar(url, size=(280, 280)):
    """Downloads and resizes Discord avatar"""
    try:
        r = requests.get(url, timeout=5)
        avatar = Image.open(io.BytesIO(r.content)).convert("RGBA")
        avatar = avatar.resize(size, Image.Resampling.LANCZOS)
        return avatar
    except Exception as e:
        print(f"⚠️ Avatar download failed: {e}")
        return None

def apply_mgs_filter(avatar):
    """Applies authentic MGS Codec aesthetic to avatar"""
    grey = avatar.convert('L')
    blurred = grey.filter(ImageFilter.GaussianBlur(radius=0.8))
    enhancer = ImageEnhance.Contrast(blurred)
    contrasted = enhancer.enhance(1.4)

    rgb = Image.new('RGB', avatar.size, CODEC_BG_DARK)
    pixels = contrasted.load()
    new_pixels = rgb.load()

    for y in range(avatar.height):
        for x in range(avatar.width):
            brightness = pixels[x, y]
            green_intensity = int(brightness * 0.85)
            new_pixels[x, y] = (0, green_intensity, int(green_intensity * 0.5))

    return rgb

def add_heavy_scanlines(img, spacing=2):
    """Adds prominent horizontal scanlines for authentic CRT look."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for y in range(0, img.height, spacing):
        alpha = 80 if y % (spacing * 2) == 0 else 45
        draw.line([(0, y), (img.width, y)], fill=(0, 0, 0, alpha))

    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    result = Image.alpha_composite(img, overlay)
    return result.convert('RGB')

def add_static_noise(img, intensity=20):
    """Adds subtle interference/static noise."""
    if img.mode != 'RGB':
        img = img.convert('RGB')

    pixels = img.load()
    for _ in range(intensity * 100):
        x = random.randint(0, img.width - 1)
        y = random.randint(0, img.height - 1)

        noise = random.randint(-30, 30)
        r, g, b = pixels[x, y]
        pixels[x, y] = (
            max(0, min(255, r + noise)),
            max(0, min(255, g + noise)),
            max(0, min(255, b + noise))
        )

    return img

def add_phosphor_glow(img):
    """Adds subtle phosphor glow effect."""
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    blurred = img.filter(ImageFilter.GaussianBlur(radius=1))
    enhancer = ImageEnhance.Brightness(blurred)
    glow = enhancer.enhance(1.2)

    return Image.blend(img, glow, alpha=0.3).convert('RGB')

def draw_codec_frame(draw, width, height):
    """Draws authentic MGS Codec frame with corner brackets."""
    bracket_size = 40
    thickness = 3

    draw.rectangle([5, 5, width - 5, height - 5],
                   outline=CODEC_GREEN_PRIMARY, width=2)

    # Corner brackets - Top Left
    draw.line([(15, 15), (15 + bracket_size, 15)],
              fill=CODEC_BORDER_BRIGHT, width=thickness)
    draw.line([(15, 15), (15, 15 + bracket_size)],
              fill=CODEC_BORDER_BRIGHT, width=thickness)

    # Top Right
    draw.line([(width - 15 - bracket_size, 15), (width - 15, 15)],
              fill=CODEC_BORDER_BRIGHT, width=thickness)
    draw.line([(width - 15, 15), (width - 15, 15 + bracket_size)],
              fill=CODEC_BORDER_BRIGHT, width=thickness)

    # Bottom Left
    draw.line([(15, height - 15), (15 + bracket_size, height - 15)],
              fill=CODEC_BORDER_BRIGHT, width=thickness)
    draw.line([(15, height - 15 - bracket_size), (15, height - 15)],
              fill=CODEC_BORDER_BRIGHT, width=thickness)

    # Bottom Right
    draw.line([(width - 15 - bracket_size, height - 15), (width - 15, height - 15)],
              fill=CODEC_BORDER_BRIGHT, width=thickness)
    draw.line([(width - 15, height - 15 - bracket_size), (width - 15, height - 15)],
              fill=CODEC_BORDER_BRIGHT, width=thickness)

def draw_codec_divider(draw, x, y, width):
    """Draws horizontal divider line."""
    draw.line([(x, y), (x + width, y)], fill=CODEC_GREEN_PRIMARY, width=2)
    draw.line([(x, y - 2), (x + 30, y - 2)], fill=CODEC_BORDER_BRIGHT, width=1)
    draw.line([(x + width - 30, y - 2), (x + width, y - 2)],
              fill=CODEC_BORDER_BRIGHT, width=1)

# === PROFILE CARD SPECIFIC FUNCTIONS ===

def create_profile_avatar(avatar_url, size=(200, 200)):
    """Creates codec-styled avatar for profile card."""
    avatar = download_avatar(avatar_url, size=size)

    if not avatar:
        # Create placeholder
        placeholder = Image.new('RGB', size, CODEC_BG_MEDIUM)
        draw = ImageDraw.Draw(placeholder)
        font = load_font(16, "text")
        text = "NO SIGNAL"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        draw.text(((size[0] - text_width) // 2, size[1] // 2 - 10),
                 text, fill=CODEC_GREEN_DIM, font=font)
        return placeholder

    # Apply MGS filter
    filtered = apply_mgs_filter(avatar)

    # Add scanlines
    filtered = add_heavy_scanlines(filtered, spacing=2)

    # Add static
    filtered = add_static_noise(filtered, intensity=10)

    return filtered

def draw_section_header(draw, x, y, text, font_title, width):
    """Draws a section header with underline."""
    # Header text
    safe_draw_text(draw, (x, y), text, primary_font=font_title,
                  fill=CODEC_BORDER_BRIGHT)

    # Measure text width for underline
    try:
        bbox = draw.textbbox((0, 0), text, font=font_title)
        text_width = bbox[2] - bbox[0]
    except:
        text_width = len(text) * 12

    # Underline
    underline_y = y + 28
    draw.line([(x, underline_y), (x + text_width, underline_y)],
             fill=CODEC_GREEN_PRIMARY, width=2)

    return underline_y + 10  # Return next Y position

def draw_stat_line(draw, x, y, label, value, font_label, font_value, max_width):
    """Draws a single stat line with dotted leader."""
    # Draw label
    safe_draw_text(draw, (x, y), label, primary_font=font_label,
                  fill=CODEC_GREEN_TEXT)

    # Measure label width
    try:
        label_bbox = draw.textbbox((0, 0), label, font=font_label)
        label_width = label_bbox[2] - label_bbox[0]
    except:
        label_width = len(label) * 10

    # Draw value (right-aligned)
    value_str = str(value)
    try:
        value_bbox = draw.textbbox((0, 0), value_str, font=font_value)
        value_width = value_bbox[2] - value_bbox[0]
    except:
        value_width = len(value_str) * 12

    value_x = x + max_width - value_width
    safe_draw_text(draw, (value_x, y), value_str, primary_font=font_value,
                  fill=CODEC_GREEN_BRIGHT)

    # Draw dotted leader between label and value
    dots_start_x = x + label_width + 8
    dots_end_x = value_x - 8
    dot_spacing = 8

    for dot_x in range(dots_start_x, dots_end_x, dot_spacing):
        draw.rectangle([dot_x, y + 10, dot_x + 2, y + 12],
                      fill=CODEC_GREEN_DIM)

def wrap_text(text, font, max_width, draw):
    """Wraps text to fit within max_width."""
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = ' '.join(current_line + [word])
        try:
            bbox = draw.textbbox((0, 0), test_line, font=font)
            line_width = bbox[2] - bbox[0]
        except:
            line_width = len(test_line) * 8

        if line_width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]

    if current_line:
        lines.append(' '.join(current_line))

    return lines

# === MAIN PROFILE CARD GENERATOR ===

def generate_profile_card(
    username,
    role_name="OPERATIVE",
    avatar_url=None,
    member_since="SEPT 2025",
    bio_text="No bio set.",
    # Stats
    xp=0,
    messages=0,
    voice_hours=0
):
    """
    Generates authentic MGS Codec-style profile/bio card.

    Args:
        username: Display name
        role_name: User's primary role/rank
        avatar_url: URL to avatar image
        member_since: Join date string (e.g., "SEPT 2025")
        bio_text: User's custom bio (empty string if not set)
        xp: Experience points
        messages: Total messages sent
        voice_hours: Voice chat hours (not minutes)

    Returns:
        PIL Image object
    """
    # Card dimensions
    width = 700

    # Calculate dynamic height based on content
    base_height = 750

    # Add extra height for bio wrapping (estimate)
    bio_lines = len(bio_text) // 40 + 1  # Rough estimate
    bio_height = max(80, bio_lines * 25 + 50)

    height = base_height + bio_height - 100  # Adjust base

    # Create base with dark codec background
    base = Image.new("RGB", (width, height), CODEC_BG_DARK)
    draw = ImageDraw.Draw(base)

    # Load fonts
    font_title = load_font(24, "title")      # Section headers (sparingly)
    font_username = load_font(28, "text")    # Username
    font_role = load_font(20, "text")        # Role name
    font_label = load_font(18, "text")       # Stat labels
    font_value = load_font(22, "numbers")    # Stat values
    font_body = load_font(16, "text")        # Bio text, achievements
    font_small = load_font(14, "text")       # Member since

    # === HEADER SECTION: AVATAR + USERNAME + ROLE ===
    current_y = 40

    # Avatar (centered)
    avatar_size = 180
    avatar = create_profile_avatar(avatar_url, size=(avatar_size, avatar_size))
    avatar_x = (width - avatar_size) // 2
    base.paste(avatar, (avatar_x, current_y))

    # Avatar border
    draw.rectangle([avatar_x - 2, current_y - 2,
                   avatar_x + avatar_size + 2, current_y + avatar_size + 2],
                  outline=CODEC_GREEN_PRIMARY, width=2)

    current_y += avatar_size + 20

    # Username (centered)
    clean_username = sanitize_username(username).upper()
    try:
        username_bbox = draw.textbbox((0, 0), clean_username, font=font_username)
        username_width = username_bbox[2] - username_bbox[0]
    except:
        username_width = len(clean_username) * 14

    username_x = (width - username_width) // 2
    safe_draw_text(draw, (username_x, current_y), clean_username,
                  primary_font=font_username, fill=CODEC_BORDER_BRIGHT)

    current_y += 35

    # Role name (centered)
    role_display = f"[ {role_name.upper()} ]"
    try:
        role_bbox = draw.textbbox((0, 0), role_display, font=font_role)
        role_width = role_bbox[2] - role_bbox[0]
    except:
        role_width = len(role_display) * 10

    role_x = (width - role_width) // 2
    safe_draw_text(draw, (role_x, current_y), role_display,
                  primary_font=font_role, fill=CODEC_GREEN_TEXT)

    current_y += 28

    # Member since (centered)
    member_text = f"MEMBER SINCE: {member_since.upper()}"
    try:
        member_bbox = draw.textbbox((0, 0), member_text, font=font_small)
        member_width = member_bbox[2] - member_bbox[0]
    except:
        member_width = len(member_text) * 7

    member_x = (width - member_width) // 2
    safe_draw_text(draw, (member_x, current_y), member_text,
                  primary_font=font_small, fill=CODEC_GREEN_DIM)

    current_y += 35

    # === DIVIDER ===
    draw_codec_divider(draw, 40, current_y, width - 80)
    current_y += 25

    # === BIO SECTION ===
    section_x = 50
    section_width = width - 100

    current_y = draw_section_header(draw, section_x, current_y, "BIO",
                                    font_title, section_width)
    current_y += 10

    # Bio text (wrapped)
    bio_display = bio_text if bio_text else "No bio set."
    bio_lines = wrap_text(bio_display, font_body, section_width - 20, draw)

    for line in bio_lines[:5]:  # Limit to 5 lines
        safe_draw_text(draw, (section_x + 10, current_y), line,
                      primary_font=font_body, fill=CODEC_GREEN_TEXT)
        current_y += 22

    current_y += 15

    # === DIVIDER ===
    draw_codec_divider(draw, 40, current_y, width - 80)
    current_y += 25

    # === STATS SECTION ===
    current_y = draw_section_header(draw, section_x, current_y, "STATS",
                                    font_title, section_width)
    current_y += 15

    # Stat lines with dotted leaders
    stats = [
        ("XP", f"{xp:,}"),
        ("MESSAGES", f"{messages:,}"),
        ("VOICE TIME", f"{voice_hours} HOURS")
    ]

    for label, value in stats:
        draw_stat_line(draw, section_x + 10, current_y, label, value,
                      font_label, font_value, section_width - 20)
        current_y += 35

    current_y += 5

    # === DIVIDER ===
    draw_codec_divider(draw, 40, current_y, width - 80)
    current_y += 25

    # === FOOTER ===
    footer_y = height - 30
    footer_text = "<< TACTICAL ESPIONAGE ACTION >>"
    try:
        footer_bbox = draw.textbbox((0, 0), footer_text, font=font_small)
        footer_width = footer_bbox[2] - footer_bbox[0]
    except:
        footer_width = len(footer_text) * 7

    footer_x = (width - footer_width) // 2
    safe_draw_text(draw, (footer_x, footer_y), footer_text,
                  primary_font=font_small, fill=CODEC_GREEN_DIM)

    # === APPLY CODEC FRAME ===
    draw_codec_frame(draw, width, height)

    # === FINAL CRT EFFECTS ===
    base = add_heavy_scanlines(base, spacing=3)
    base = add_static_noise(base, intensity=10)
    base = add_phosphor_glow(base)

    return base

def generate_simple_profile_card(
    username: str,
    role_name: str,
    avatar_url: Optional[str],
    member_since: str,
    bio_text: Optional[str],
    xp: int,
    messages: int,
    voice_hours: int
):
    """
    Generates a simple MGS Codec-style profile card.

    Args:
        username: Discord username
        role_name: User's role name
        avatar_url: URL to user's avatar
        member_since: Member since date (e.g., "SEPT 2025")
        bio_text: User bio (optional)
        xp: XP amount
        messages: Message count
        voice_hours: Voice time in hours

    Returns:
        PIL Image object
    """
    width = 750
    height = 550

    # Create base
    base = Image.new("RGB", (width, height), CODEC_BG_DARK)
    draw = ImageDraw.Draw(base)

    # Load fonts
    font_title = load_font(32, "text")
    font_subtitle = load_font(18, "text")
    font_body = load_font(16, "text")
    font_stats = load_font(18, "text")

    # === AVATAR SECTION ===
    avatar_size = 150
    avatar = create_profile_avatar(avatar_url, size=(avatar_size, avatar_size)) if avatar_url else None

    if avatar:
        avatar_x = (width - avatar_size) // 2
        avatar_y = 30  # Moved up from 50
        base.paste(avatar, (avatar_x, avatar_y))

    # === USERNAME & ROLE ===
    username_clean = sanitize_username(username)
    username_y = 200 if avatar else 50  # Adjusted from 220

    # Center username
    try:
        username_bbox = draw.textbbox((0, 0), username_clean.upper(), font=font_title)
        username_width = username_bbox[2] - username_bbox[0]
    except:
        username_width = len(username_clean) * 18

    username_x = (width - username_width) // 2
    safe_draw_text(draw, (username_x, username_y),
                  username_clean.upper(),
                  primary_font=font_title, fill=CODEC_BORDER_BRIGHT)

    # Role name
    role_y = username_y + 35
    role_text = f"ROLE: {role_name.upper()}"
    try:
        role_bbox = draw.textbbox((0, 0), role_text, font=font_subtitle)
        role_width = role_bbox[2] - role_bbox[0]
    except:
        role_width = len(role_text) * 10

    role_x = (width - role_width) // 2
    safe_draw_text(draw, (role_x, role_y),
                  role_text,
                  primary_font=font_subtitle, fill=CODEC_GREEN_TEXT)

    # === DIVIDER ===
    divider_y = role_y + 35
    draw_codec_divider(draw, 40, divider_y, width - 80)

    # === BIO SECTION ===
    bio_y = divider_y + 20
    safe_draw_text(draw, (40, bio_y),
                  "BIO",
                  primary_font=font_subtitle, fill=CODEC_GREEN_BRIGHT)

    bio_text_y = bio_y + 25
    bio_display = bio_text[:300] if bio_text else "No bio set."
    safe_draw_text(draw, (40, bio_text_y),
                  f'"{bio_display}"',
                  primary_font=font_body, fill=CODEC_GREEN_TEXT)

    # === DIVIDER ===
    divider2_y = bio_text_y + 50
    draw_codec_divider(draw, 40, divider2_y, width - 80)

    # === STATS SECTION ===
    stats_y = divider2_y + 20
    safe_draw_text(draw, (40, stats_y),
                  "STATS",
                  primary_font=font_subtitle, fill=CODEC_GREEN_BRIGHT)

    stats_data = [
        ("XP", f"{xp:,}"),
        ("MESSAGES", f"{messages:,}"),
        ("VOICE TIME", f"{voice_hours} HOURS")
    ]

    stat_y = stats_y + 30
    stat_left_x = 50
    stat_right_x = width - 50  # Right edge with padding

    for label, value in stats_data:
        # Draw label on left
        safe_draw_text(draw, (stat_left_x, stat_y),
                      label,
                      primary_font=font_stats, fill=CODEC_GREEN_TEXT)

        # Draw value right-aligned
        try:
            val_bbox = draw.textbbox((0, 0), value, font=font_stats)
            val_width = val_bbox[2] - val_bbox[0]
        except:
            val_width = len(value) * 10

        safe_draw_text(draw, (stat_right_x - val_width, stat_y),
                      value,
                      primary_font=font_stats, fill=CODEC_GREEN_TEXT)
        stat_y += 28

    # === FOOTER ===
    footer_y = height - 35
    footer_text = "Outer Heaven: Exiled Units"
    try:
        footer_bbox = draw.textbbox((0, 0), footer_text, font=font_body)
        footer_width = footer_bbox[2] - footer_bbox[0]
    except:
        footer_width = len(footer_text) * 8

    footer_x = (width - footer_width) // 2  # Center the footer
    safe_draw_text(draw, (footer_x, footer_y),
                  footer_text,
                  primary_font=font_body, fill=CODEC_GREEN_DIM)

    # === APPLY EFFECTS ===
    draw_codec_frame(draw, width, height)
    base = add_heavy_scanlines(base, spacing=3)
    base = add_static_noise(base, intensity=12)
    base = add_phosphor_glow(base)

    return base


# === TEST/PREVIEW ===
if __name__ == "__main__":
    img = generate_simple_profile_card(
        username="Solid Snake",
        role_name="FOXHOUND Operative",
        avatar_url="https://cdn.discordapp.com/embed/avatars/1.png",
        member_since="SEPT 2025",
        bio_text="How to jump?",
        xp=3234,
        messages=556,
        voice_hours=58
    )

    img.save("mgs_codec_profile_simple.png")
    print("✅ MGS Codec Profile Card saved as 'mgs_codec_profile_simple.png'")
