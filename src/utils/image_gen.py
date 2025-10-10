# image_gen.py
# Author: Tom & GitHub Copilot + Claude
# MGS Codec-style tactical rank card generator - Full Rebuild

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import io
import requests
import random
import unicodedata

# === UNICODE SANITIZATION ===
def sanitize_username(username):
    """
    Sanitizes username to handle Unicode characters properly.
    Keeps Unicode characters intact since we're now using robust system fonts.
    Only removes control characters and excessive whitespace.
    """
    if not username:
        return "UNKNOWN"

    # Remove control characters but keep printable Unicode
    cleaned = ''.join(char for char in username if unicodedata.category(char)[0] != 'C')

    # Normalize whitespace
    cleaned = ' '.join(cleaned.split())

    # If nothing left after cleaning, use fallback
    if not cleaned or cleaned.isspace():
        return "AGENT"

    # Limit length and trim
    cleaned = cleaned.strip()[:30]

    return cleaned if cleaned else "AGENT"

# === AUTHENTIC MGS CODEC COLOR PALETTE ===
CODEC_BG_DARK = (5, 25, 15)           # Deep dark green background
CODEC_BG_MEDIUM = (10, 35, 20)        # Medium background
CODEC_GREEN_PRIMARY = (50, 200, 100)  # Primary codec green
CODEC_GREEN_BRIGHT = (100, 255, 150)  # Bright highlights
CODEC_GREEN_DIM = (30, 120, 60)       # Dimmed elements
CODEC_GREEN_TEXT = (80, 220, 120)     # Standard text
CODEC_BORDER_BRIGHT = (120, 255, 180) # Bright borders
CODEC_STATIC_OVERLAY = (40, 160, 80)  # Static effect color

# === FONT LOADING WITH FALLBACKS ===
def load_font(size, font_type="text"):
    """
    Load custom fonts from public/fonts directory with robust fallback
    font_type: 'title', 'text', or 'numbers'

    For 'text' type, uses system fonts (Helvetica/Arial) to avoid character support issues
    """
    import os

    # For 'text' type, use reliable system fonts instead of custom fonts
    # This prevents unsupported character issues
    if font_type == "text":
        fallback_fonts = [
            "arial.ttf",
            "Arial.ttf",
            "arialbd.ttf",  # Arial Bold
            "helvetica.ttf",
            "Helvetica.ttf",
            "segoeui.ttf",
            "calibri.ttf",
            "C:\\Windows\\Fonts\\arial.ttf",  # Windows direct path
            "C:\\Windows\\Fonts\\Arial.ttf"
        ]

        for font_name in fallback_fonts:
            try:
                font = ImageFont.truetype(font_name, size)
                return font
            except Exception:
                continue

        # Last resort: default font
        return ImageFont.load_default()

    # For 'title' and 'numbers', try custom fonts first
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    fonts_dir = os.path.join(base_dir, "public", "fonts")

    # Map font types to files
    font_files = {
        "title": "title.TTF",
        "numbers": "numbers.ttf"
    }

    # Try custom font
    if font_type in font_files:
        custom_font_path = os.path.join(fonts_dir, font_files[font_type])
        try:
            font = ImageFont.truetype(custom_font_path, size)
            return font
        except Exception as e:
            print(f"⚠️ Could not load custom font {font_type}: {e}")

    # Fallback to system fonts
    fallback_fonts = [
        "arial.ttf",
        "Arial.ttf",
        "helvetica.ttf",
        "Helvetica.ttf",
        "segoeui.ttf",
        "calibri.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\Arial.ttf"
    ]

    for font_name in fallback_fonts:
        try:
            font = ImageFont.truetype(font_name, size)
            return font
        except Exception:
            continue

    return ImageFont.load_default()


# === SAFE TEXT RENDERER WITH FALLBACK ===
def safe_draw_text(draw, xy, text, primary_font, fallback_font=None, fill=(255,255,255)):
    """
    Draw text character-by-character using primary_font when possible,
    otherwise draw individual characters with fallback_font.

    This avoids large blocks or missing-glyph boxes when the primary
    (custom) font lacks certain Unicode glyphs.
    """
    if not text:
        return

    if fallback_font is None:
        # fall back to robust system text font
        fallback_font = load_font(getattr(primary_font, 'size', 18), 'text')

    x, y = xy
    for ch in text:
        # try primary font first; if it cannot render the glyph, fall back
        try:
            # Many FreeTypeFont implementations raise when glyph missing via getmask
            mask = primary_font.getmask(ch)
            # If mask is empty or getmask succeeded, use primary
            draw.text((x, y), ch, font=primary_font, fill=fill)
            # measure width
            bbox = draw.textbbox((0,0), ch, font=primary_font)
            w = bbox[2] - bbox[0]
        except Exception:
            # fallback font draw
            draw.text((x, y), ch, font=fallback_font, fill=fill)
            bbox = draw.textbbox((0,0), ch, font=fallback_font)
            w = bbox[2] - bbox[0]

        # advance x by measured width (at least 1 to avoid infinite loops)
        x += max(1, w)


# === AVATAR PROCESSING ===
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
    # Convert to greyscale first
    grey = avatar.convert('L')

    # Apply slight blur for CRT softness
    blurred = grey.filter(ImageFilter.GaussianBlur(radius=0.8))

    # Increase contrast for that punchy look
    enhancer = ImageEnhance.Contrast(blurred)
    contrasted = enhancer.enhance(1.4)

    # Convert to RGB and apply green tint
    rgb = Image.new('RGB', avatar.size, CODEC_BG_DARK)
    rgb_draw = ImageDraw.Draw(rgb)

    # Apply green colorization
    pixels = contrasted.load()
    new_pixels = rgb.load()

    for y in range(avatar.height):
        for x in range(avatar.width):
            brightness = pixels[x, y]
            # Map brightness to green scale
            green_intensity = int(brightness * 0.85)
            new_pixels[x, y] = (0, green_intensity, int(green_intensity * 0.5))

    return rgb

def create_codec_avatar(avatar_url):
    """Creates MGS Codec-styled avatar with frame"""
    avatar = download_avatar(avatar_url, size=(240, 240))

    if not avatar:
        # Create placeholder
        placeholder = Image.new('RGB', (240, 240), CODEC_BG_MEDIUM)
        draw = ImageDraw.Draw(placeholder)
        font = load_font(20)
        draw.text((60, 110), "NO SIGNAL", fill=CODEC_GREEN_DIM, font=font)
        return placeholder

    # Apply MGS filter
    filtered = apply_mgs_filter(avatar)

    # Add heavy scanlines
    filtered = add_heavy_scanlines(filtered, spacing=2)

    # Add subtle static
    filtered = add_static_noise(filtered, intensity=15)

    return filtered

# === CRT EFFECTS ===
def add_heavy_scanlines(img, spacing=2):
    """Adds prominent horizontal scanlines for authentic CRT look"""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for y in range(0, img.height, spacing):
        # Alternate scanline intensity - INCREASED for better visibility
        alpha = 80 if y % (spacing * 2) == 0 else 45
        draw.line([(0, y), (img.width, y)], fill=(0, 0, 0, alpha))

    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    result = Image.alpha_composite(img, overlay)
    return result.convert('RGB')

def add_static_noise(img, intensity=20):
    """Adds subtle interference/static noise"""
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
    """Adds subtle phosphor glow effect"""
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    blurred = img.filter(ImageFilter.GaussianBlur(radius=1))
    enhancer = ImageEnhance.Brightness(blurred)
    glow = enhancer.enhance(1.2)

    return Image.blend(img, glow, alpha=0.3).convert('RGB')

# === CODEC FRAME ELEMENTS ===
def draw_codec_frame(draw, width, height):
    """Draws authentic MGS Codec frame with corner brackets"""
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
    """Draws horizontal divider line"""
    draw.line([(x, y), (x + width, y)], fill=CODEC_GREEN_PRIMARY, width=2)
    # Add small accent lines
    draw.line([(x, y - 2), (x + 30, y - 2)], fill=CODEC_BORDER_BRIGHT, width=1)
    draw.line([(x + width - 30, y - 2), (x + width, y - 2)],
              fill=CODEC_BORDER_BRIGHT, width=1)

def draw_mgs_progress_bar(draw, x, y, width, height, progress, label=""):
    """Draws authentic MGS-style segmented progress bar"""
    segments = 20
    segment_width = (width - (segments + 1) * 2) // segments

    # Background frame
    draw.rectangle([x, y, x + width, y + height],
                   fill=CODEC_BG_DARK, outline=CODEC_GREEN_DIM, width=2)

    # Draw segments
    filled_segments = int(segments * progress)
    for i in range(segments):
        seg_x = x + 4 + i * (segment_width + 2)
        seg_y = y + 4

        if i < filled_segments:
            color = CODEC_BORDER_BRIGHT if i >= segments - 2 else CODEC_GREEN_PRIMARY
            draw.rectangle([seg_x, seg_y, seg_x + segment_width, seg_y + height - 8],
                          fill=color)
        else:
            draw.rectangle([seg_x, seg_y, seg_x + segment_width, seg_y + height - 8],
                          outline=CODEC_GREEN_DIM, width=1)

    # Label text
    if label:
        font = load_font(14)
        percentage = f"{int(progress * 100)}%"
        draw.text((x + width + 10, y + 4), percentage,
                 fill=CODEC_GREEN_BRIGHT, font=font)

def draw_stat_box(draw, x, y, label, value, font_label, font_value):
    """Draws a labeled stat box"""
    # Label
    draw.text((x, y), label, fill=CODEC_GREEN_DIM, font=font_label)
    # Value: use safe renderer to fall back to system font for unsupported glyphs
    try:
        safe_draw_text(draw, (x, y + 22), str(value), primary_font=font_value,
                       fallback_font=load_font(getattr(font_value, 'size', 18), 'text'),
                       fill=CODEC_GREEN_BRIGHT)
    except Exception:
        # Last-resort: direct draw
        draw.text((x, y + 22), str(value), fill=CODEC_GREEN_BRIGHT, font=font_value)

    # Underline: measure using primary font when possible, otherwise fallback
    try:
        bbox = draw.textbbox((x, y + 22), str(value), font=font_value)
    except Exception:
        fb = load_font(getattr(font_value, 'size', 18), 'text')
        bbox = draw.textbbox((x, y + 22), str(value), font=fb)

    draw.line([(x, bbox[3] + 2), (bbox[2], bbox[3] + 2)],
              fill=CODEC_GREEN_PRIMARY, width=1)

# === MAIN GENERATOR ===
def generate_rank_card(username, rank_badge, rank_name, xp, xp_max,
                       avatar_url=None, message_count=0, voice_time=0,
                       leaderboard_pos=None):
    """
    Generates authentic MGS Codec-style rank card

    Args:
        username: Display name
        rank_badge: Emoji or badge (e.g., "🎖️")
        rank_name: Military rank name (e.g., "Captain", "FOXHOUND")
        xp: Current XP
        xp_max: XP needed for next level
        avatar_url: URL to avatar image
        message_count: Total messages sent
        voice_time: Voice chat minutes
        leaderboard_pos: Position on leaderboard (optional)

    Returns:
        PIL Image object
    """
    width, height = 1200, 450

    # Sanitize username to handle unsupported Unicode characters
    username = sanitize_username(username)

    # Create base with dark codec background
    base = Image.new("RGB", (width, height), CODEC_BG_DARK)
    draw = ImageDraw.Draw(base)

    # Load fonts with custom font types
    font_title = load_font(48, "title")      # Username - title font
    font_large = load_font(36, "numbers")    # Stats values - numbers font
    font_medium = load_font(24, "text")      # Labels - text font
    font_small = load_font(20, "text")       # Secondary info - text font
    font_tiny = load_font(16, "text")        # Footer - text font

    # === LEFT SIDE: AVATAR PANEL ===
    avatar_x = 30
    avatar_y = 80

    if avatar_url:
        codec_avatar = create_codec_avatar(avatar_url)
        base.paste(codec_avatar, (avatar_x, avatar_y))
    else:
        # Draw placeholder frame
        draw.rectangle([avatar_x, avatar_y, avatar_x + 240, avatar_y + 240],
                      outline=CODEC_GREEN_DIM, width=2)
        draw.text((avatar_x + 70, avatar_y + 110), "NO SIGNAL",
                 fill=CODEC_GREEN_DIM, font=font_medium)

    # Avatar border frame
    draw.rectangle([avatar_x - 3, avatar_y - 3,
                   avatar_x + 243, avatar_y + 243],
                  outline=CODEC_GREEN_PRIMARY, width=2)

    # === RIGHT SIDE: INFORMATION PANEL ===
    info_x = 320
    info_y = 30  # Slightly higher for better balance

    # Header: Badge + Username
    header_text = f"{username.upper()}"
    safe_draw_text(draw, (info_x, info_y), header_text,
                   primary_font=font_title, fallback_font=load_font(font_title.size, 'text'),
                   fill=CODEC_BORDER_BRIGHT)

    # Divider - increased spacing for larger font
    draw_codec_divider(draw, info_x, info_y + 55, 820)

    # Mission Briefing Style Header
    current_y = info_y + 75  # Increased from 65 for better spacing
    draw.text((info_x, current_y), "► TACTICAL STATUS REPORT",
             fill=CODEC_GREEN_TEXT, font=font_small)
    current_y += 30  # Increased from 25 for better spacing

    # === STAT DISPLAYS ===
    # Row 1: Rank Name and XP
    stat_spacing = 240  # Increased from 200 to accommodate larger text
    draw_stat_box(draw, info_x, current_y, "RANK", rank_name.upper(),
                 font_small, font_large)
    draw_stat_box(draw, info_x + stat_spacing, current_y, "EXPERIENCE",
                 f"{xp:,} XP", font_small, font_large)

    # Row 2: Messages and Voice Time
    current_y += 85  # Increased from 80 for better spacing
    draw_stat_box(draw, info_x, current_y, "MESSAGES", f"{message_count:,}",
                 font_small, font_large)
    draw_stat_box(draw, info_x + stat_spacing, current_y, "VOICE TIME",
                 f"{voice_time} min", font_small, font_large)

    # Leaderboard position (if provided)
    if leaderboard_pos:
        draw_stat_box(draw, info_x + stat_spacing * 2, current_y, "RANKING",
                     f"#{leaderboard_pos}", font_small, font_large)

    # === XP PROGRESS BAR ===
    current_y += 65  # Increased from 80 for better spacing
    draw.text((info_x, current_y), "EXPERIENCE POINTS",
             fill=CODEC_GREEN_DIM, font=font_small)

    progress_y = current_y + 26  # Increased from 22 for larger fonts
    progress_width = 600
    progress = min(max(xp / xp_max, 0), 1) if xp_max > 0 else 1.0

    draw_mgs_progress_bar(draw, info_x, progress_y, progress_width, 28,  # Height increased from 24 to 28
                         progress, f"{xp:,} / {xp_max:,}")

    # XP text below bar - INCREASED font size
    draw.text((info_x, progress_y + 35),  # Adjusted position
             f"[ {xp:,} XP / {xp_max:,} XP ]",
             fill=CODEC_GREEN_TEXT, font=font_small)  # Changed from font_tiny to font_small

    # === FOOTER ===
    footer_y = height - 35  # Adjusted position
    safe_draw_text(draw, (info_x, footer_y),
             "◄◄ TACTICAL ESPIONAGE ACTION // CODEC NETWORK ►►",
             primary_font=font_tiny, fallback_font=load_font(font_tiny.size, 'text'),
             fill=CODEC_GREEN_DIM)

    # Copyright
    safe_draw_text(draw, (width - 300, footer_y),  # Adjusted position
             "Outer Heaven: Exciled Units",
             primary_font=font_tiny, fallback_font=load_font(font_tiny.size, 'text'),
             fill=CODEC_GREEN_DIM)

    # === APPLY CODEC FRAME ===
    draw_codec_frame(draw, width, height)

    # === FINAL CRT EFFECTS ===
    base = add_heavy_scanlines(base, spacing=3)
    base = add_static_noise(base, intensity=10)
    base = add_phosphor_glow(base)

    return base

# === TEST/PREVIEW ===
if __name__ == "__main__":
    img = generate_rank_card(
        username="Solid Snake",
        rank_badge="🎖️",
        level=42,
        xp=5320,
        xp_max=6000,
        avatar_url="https://cdn.discordapp.com/embed/avatars/1.png",
        message_count=1547,
        voice_time=342,
        leaderboard_pos=7
    )
    img.save("mgs_codec_rank_card.png")
    print("✅ MGS Codec Rank Card saved as 'mgs_codec_rank_card.png'")
