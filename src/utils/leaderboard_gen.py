# leaderboard_gen.py
# Author: Tom & Claude
# MGS Codec-style tactical leaderboard generator

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import unicodedata
import random

# === IMPORT SHARED FUNCTIONS FROM image_gen.py ===
# NOTE: In production, import these from image_gen.py:
# from image_gen import (sanitize_username, load_font, safe_draw_text,
#                        add_heavy_scanlines, add_static_noise, add_phosphor_glow)

# For this artifact, we'll include minimal versions:

# === AUTHENTIC MGS CODEC COLOR PALETTE ===
CODEC_BG_DARK = (5, 25, 15)
CODEC_BG_MEDIUM = (10, 35, 20)
CODEC_GREEN_PRIMARY = (50, 200, 100)
CODEC_GREEN_BRIGHT = (100, 255, 150)
CODEC_GREEN_DIM = (30, 120, 60)
CODEC_GREEN_TEXT = (80, 220, 120)
CODEC_BORDER_BRIGHT = (120, 255, 180)
CODEC_STATIC_OVERLAY = (40, 160, 80)

# Top 3 special highlights
CODEC_GOLD = (255, 215, 0)
CODEC_SILVER = (192, 192, 192)
CODEC_BRONZE = (205, 127, 50)

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

# === LEADERBOARD-SPECIFIC FRAME ELEMENTS ===
def draw_codec_frame(draw, width, height):
    """Draws authentic MGS Codec frame with corner brackets."""
    bracket_size = 40
    thickness = 3

    # Main border
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

def draw_leaderboard_entry(draw, x, y, position, name, value,
                          font_text, font_numbers, entry_width, is_top3=False):
    """
    Draws a single leaderboard entry with rank, name, and value.

    Args:
        draw: ImageDraw object
        x, y: Position coordinates
        position: Ranking position (1-10)
        name: Member display name
        value: Stat value to display
        font_text: Font for text (name)
        font_numbers: Font for numbers (value)
        entry_width: Total width of entry
        is_top3: Whether this is a top 3 entry (special styling)
    """
    entry_height = 45
    padding = 15

    # Determine colors based on position
    if position == 1:
        bg_color = CODEC_BG_MEDIUM
        border_color = CODEC_BORDER_BRIGHT
        text_color = CODEC_BORDER_BRIGHT
        number_color = CODEC_BORDER_BRIGHT
        border_width = 3
        rank_prefix = "1ST"
    elif position == 2:
        bg_color = CODEC_BG_MEDIUM
        border_color = CODEC_GREEN_BRIGHT
        text_color = CODEC_GREEN_BRIGHT
        number_color = CODEC_GREEN_BRIGHT
        border_width = 2
        rank_prefix = "2ND"
    elif position == 3:
        bg_color = CODEC_BG_MEDIUM
        border_color = CODEC_GREEN_PRIMARY
        text_color = CODEC_GREEN_PRIMARY
        number_color = CODEC_GREEN_PRIMARY
        border_width = 2
        rank_prefix = "3RD"
    else:
        bg_color = CODEC_BG_DARK
        border_color = CODEC_GREEN_DIM
        text_color = CODEC_GREEN_TEXT
        number_color = CODEC_GREEN_PRIMARY
        border_width = 1
        rank_prefix = f"{position}."

    # Draw background box
    if is_top3:
        # Top 3: Full background
        draw.rectangle([x, y, x + entry_width, y + entry_height],
                      fill=bg_color, outline=border_color, width=border_width)
    else:
        # Others: Just border line
        draw.line([(x, y + entry_height), (x + entry_width, y + entry_height)],
                 fill=border_color, width=1)

    # Position number/prefix (left-aligned)
    pos_x = x + padding
    pos_y = y + (entry_height - 24) // 2  # Vertically centered

    safe_draw_text(draw, (pos_x, pos_y), rank_prefix,
                  primary_font=font_text, fill=text_color)

    # Measure position text width for proper spacing
    try:
        pos_bbox = draw.textbbox((0, 0), rank_prefix, font=font_text)
        pos_width = pos_bbox[2] - pos_bbox[0]
    except:
        pos_width = len(rank_prefix) * 12

    # Member name (after position)
    name_x = pos_x + pos_width + 20
    name_y = pos_y

    # Truncate name if too long
    max_name_length = 25
    display_name = name[:max_name_length] + "..." if len(name) > max_name_length else name

    safe_draw_text(draw, (name_x, name_y), display_name.upper(),
                  primary_font=font_text, fill=text_color)

    # Value (right-aligned)
    # Format value with commas
    value_str = f"{value:,}"

    try:
        val_bbox = draw.textbbox((0, 0), value_str, font=font_numbers)
        val_width = val_bbox[2] - val_bbox[0]
    except:
        val_width = len(value_str) * 12

    # Calculate value position (right-aligned)
    value_x = x + entry_width - padding - val_width
    value_y = pos_y

    safe_draw_text(draw, (value_x, value_y), value_str,
                  primary_font=font_numbers, fill=number_color)

# === MAIN LEADERBOARD GENERATOR ===
def generate_leaderboard(leaderboard_data, category="EXPERIENCE POINTS",
                        unit_suffix="XP", guild_name="OUTER HEAVEN"):
    """
    Generates authentic MGS Codec-style leaderboard image.

    Args:
        leaderboard_data: List of tuples (position, name, value, rank_icon)
                         Example: [(1, "Solid Snake", 15420, "FOXHOUND"),
                                  (2, "Big Boss", 12350, "SNAKE"), ...]
        category: Category name (e.g., "EXPERIENCE POINTS", "GMP RANKING")
        unit_suffix: Unit to display after value (e.g., "XP", "GMP", "MSG")
        guild_name: Server/guild name for header

    Returns:
        PIL Image object
    """
    width = 900

    # Calculate height based on number of entries
    num_entries = len(leaderboard_data)
    header_height = 180
    entry_height = 50  # Space per entry
    footer_height = 60
    height = header_height + (num_entries * entry_height) + footer_height + 40

    # Create base with dark codec background
    base = Image.new("RGB", (width, height), CODEC_BG_DARK)
    draw = ImageDraw.Draw(base)

    # Load fonts
    font_title = load_font(38, "text")      # Headers
    font_subtitle = load_font(24, "text")   # Subheaders
    font_text = load_font(20, "text")       # Entry names
    font_numbers = load_font(22, "numbers") # Entry values
    font_footer = load_font(16, "text")     # Footer

    # === HEADER SECTION ===
    header_x = 40
    header_y = 35

    # Main title
    safe_draw_text(draw, (header_x, header_y),
                  "► TACTICAL ESPIONAGE LEADERBOARD",
                  primary_font=font_title, fill=CODEC_BORDER_BRIGHT)

    # Category subtitle
    subtitle_y = header_y + 45
    safe_draw_text(draw, (header_x, subtitle_y),
                  f"CATEGORY: {category.upper()}",
                  primary_font=font_subtitle, fill=CODEC_GREEN_TEXT)

    # Guild name
    guild_y = subtitle_y + 30
    safe_draw_text(draw, (header_x, guild_y),
                  f"Outer Heaven: Exciled Units",
                  primary_font=font_footer, fill=CODEC_GREEN_DIM)

    # Divider line
    divider_y = guild_y + 35
    draw_codec_divider(draw, header_x, divider_y, width - 80)

    # === LEADERBOARD ENTRIES ===
    entries_start_y = divider_y + 25
    entry_width = width - 80

    for idx, (position, name, value, rank_icon) in enumerate(leaderboard_data):
        entry_y = entries_start_y + (idx * entry_height)

        # Sanitize name
        clean_name = sanitize_username(name)

        # Check if top 3
        is_top3 = position <= 3

        draw_leaderboard_entry(
            draw, header_x, entry_y,
            position, clean_name, value,
            font_text, font_numbers, entry_width, is_top3
        )

    # === FOOTER ===
    footer_y = height - 45
    safe_draw_text(draw, ((header_x - -20), footer_y),
                  "Chat more to climb the ranks!",
                  primary_font=font_footer, fill=CODEC_GREEN_DIM)

    # Copyright
    safe_draw_text(draw, (width - 280, footer_y),
                  "Outer Heaven: Exciled Units",
                  primary_font=font_footer, fill=CODEC_GREEN_DIM)

    # === APPLY CODEC FRAME ===
    draw_codec_frame(draw, width, height)

    # === FINAL CRT EFFECTS ===
    base = add_heavy_scanlines(base, spacing=3)
    base = add_static_noise(base, intensity=12)
    base = add_phosphor_glow(base)

    return base

# === TEST/PREVIEW ===
if __name__ == "__main__":
    # Sample leaderboard data
    test_data = [
        (1, "Solid Snake", 15420, "FOXHOUND"),
        (2, "Big Boss", 12350, "SNAKE"),
        (3, "The Boss", 11120, "COBRA"),
        (4, "Revolver Ocelot", 9840, "OCELOT"),
        (5, "Otacon", 8750, "GENIUS"),
        (6, "Raiden", 7650, "CYBORG"),
        (7, "Meryl Silverburgh", 6540, "ROOKIE"),
        (8, "Liquid Snake", 5430, "SNAKE"),
        (9, "Psycho Mantis", 4320, "MANTIS"),
        (10, "Vulcan Raven", 3210, "RAVEN")
    ]

    img = generate_leaderboard(
        leaderboard_data=test_data,
        category="EXPERIENCE POINTS",
        unit_suffix="XP",
        guild_name="OUTER HEAVEN"
    )

    img.save("mgs_codec_leaderboard.png")
    print("✅ MGS Codec Leaderboard saved as 'mgs_codec_leaderboard.png'")
