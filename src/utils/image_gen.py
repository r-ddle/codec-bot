# image_gen.py
# Author: Tom & GitHub Copilot + Claude
# MGS Codec-style tactical rank card generator - Full Rebuild

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import io
import requests
import random

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
def load_font(size):
    """Load MGS-style monospace font with multiple fallbacks"""
    fonts_to_try = [
        "consola.ttf",
        "cour.ttf",
        "DejaVuSansMono.ttf",
        "LiberationMono-Regular.ttf",
        "FreeMono.ttf"
    ]

    for font_name in fonts_to_try:
        try:
            return ImageFont.truetype(font_name, size)
        except:
            continue

    return ImageFont.load_default()

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
        # Alternate scanline intensity
        alpha = 60 if y % (spacing * 2) == 0 else 30
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
    # Value
    draw.text((x, y + 22), str(value), fill=CODEC_GREEN_BRIGHT, font=font_value)
    # Underline
    bbox = draw.textbbox((x, y + 22), str(value), font=font_value)
    draw.line([(x, bbox[3] + 2), (bbox[2], bbox[3] + 2)],
              fill=CODEC_GREEN_PRIMARY, width=1)

# === MAIN GENERATOR ===
def generate_rank_card(username, rank_badge, level, xp, xp_max, gmp,
                       avatar_url=None, message_count=0, voice_time=0,
                       leaderboard_pos=None):
    """
    Generates authentic MGS Codec-style rank card

    Args:
        username: Display name
        rank_badge: Emoji or badge (e.g., "🎖️")
        level: Rank level number
        xp: Current XP
        xp_max: XP needed for next level
        gmp: GMP (currency/points)
        avatar_url: URL to avatar image
        message_count: Total messages sent
        voice_time: Voice chat minutes
        leaderboard_pos: Position on leaderboard (optional)

    Returns:
        PIL Image object
    """
    width, height = 1200, 400

    # Create base with dark codec background
    base = Image.new("RGB", (width, height), CODEC_BG_DARK)
    draw = ImageDraw.Draw(base)

    # Load fonts
    font_title = load_font(32)      # Username
    font_large = load_font(24)      # Stats values
    font_medium = load_font(18)     # Labels
    font_small = load_font(14)      # Secondary info
    font_tiny = load_font(12)       # Footer

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
    info_y = 40

    # Header: Badge + Username
    header_text = f"{rank_badge} {username.upper()}"
    draw.text((info_x, info_y), header_text,
             fill=CODEC_BORDER_BRIGHT, font=font_title)

    # Divider
    draw_codec_divider(draw, info_x, info_y + 45, 820)

    # Mission Briefing Style Header
    current_y = info_y + 65
    draw.text((info_x, current_y), "► TACTICAL STATUS REPORT",
             fill=CODEC_GREEN_TEXT, font=font_small)
    current_y += 25

    # === STAT DISPLAYS ===
    # Row 1: Level and GMP
    stat_spacing = 200
    draw_stat_box(draw, info_x, current_y, "RANK LEVEL", f"Lv. {level}",
                 font_small, font_large)
    draw_stat_box(draw, info_x + stat_spacing, current_y, "GMP BALANCE",
                 f"{gmp:,}", font_small, font_large)

    # Row 2: Messages and Voice Time
    current_y += 80
    draw_stat_box(draw, info_x, current_y, "MESSAGES", f"{message_count:,}",
                 font_small, font_large)
    draw_stat_box(draw, info_x + stat_spacing, current_y, "VOICE TIME",
                 f"{voice_time} min", font_small, font_large)

    # Leaderboard position (if provided)
    if leaderboard_pos:
        draw_stat_box(draw, info_x + stat_spacing * 2, current_y, "RANKING",
                     f"#{leaderboard_pos}", font_small, font_large)

    # === XP PROGRESS BAR ===
    current_y += 80
    draw.text((info_x, current_y), "EXPERIENCE POINTS",
             fill=CODEC_GREEN_DIM, font=font_small)

    progress_y = current_y + 22
    progress_width = 600
    progress = min(max(xp / xp_max, 0), 1) if xp_max > 0 else 1.0

    draw_mgs_progress_bar(draw, info_x, progress_y, progress_width, 24,
                         progress, f"{xp:,} / {xp_max:,}")

    # XP text below bar
    draw.text((info_x, progress_y + 30),
             f"[ {xp:,} XP / {xp_max:,} XP ]",
             fill=CODEC_GREEN_TEXT, font=font_tiny)

    # === FOOTER ===
    footer_y = height - 30
    draw.text((info_x, footer_y),
             "◄◄ TACTICAL ESPIONAGE ACTION // CODEC NETWORK ►►",
             fill=CODEC_GREEN_DIM, font=font_tiny)

    # Copyright
    draw.text((width - 400, footer_y),
             "©1987 2001 Konami Computer Entertainment",
             fill=CODEC_GREEN_DIM, font=font_tiny)

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
        gmp=125000,
        avatar_url="https://cdn.discordapp.com/embed/avatars/1.png",
        message_count=1547,
        voice_time=342,
        leaderboard_pos=7
    )
    img.save("mgs_codec_rank_card.png")
    print("✅ MGS Codec Rank Card saved as 'mgs_codec_rank_card.png'")
