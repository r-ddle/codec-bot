# daily_supply_gen.py
# Author: Tom & GitHub Copilot + Claude
# MGS Codec-style Daily Supply Drop & Promotion card generator - REBUILT

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import random
import unicodedata

# === UNICODE SANITIZATION ===
def sanitize_username(username):
    """
    Sanitizes username to handle Unicode characters properly.
    Keeps Unicode characters intact since we're using robust system fonts.
    """
    if not username:
        return "UNKNOWN"

    # Remove control characters but keep printable Unicode
    cleaned = ''.join(char for char in username if unicodedata.category(char)[0] != 'C')

    # Normalize whitespace
    cleaned = ' '.join(cleaned.split())

    if not cleaned or cleaned.isspace():
        return "AGENT"

    return cleaned.strip()[:30] if cleaned else "AGENT"

# === AUTHENTIC MGS CODEC COLOR PALETTE ===
CODEC_BG_DARK = (5, 25, 15)
CODEC_BG_MEDIUM = (10, 35, 20)
CODEC_GREEN_PRIMARY = (50, 200, 100)
CODEC_GREEN_BRIGHT = (100, 255, 150)
CODEC_GREEN_DIM = (30, 120, 60)
CODEC_GREEN_TEXT = (80, 220, 120)
CODEC_BORDER_BRIGHT = (120, 255, 180)
CODEC_YELLOW = (255, 220, 0)
CODEC_ORANGE = (255, 150, 0)

# Streak milestone colors
STREAK_NORMAL = CODEC_GREEN_BRIGHT
STREAK_MILESTONE_7 = (255, 200, 50)
STREAK_MILESTONE_30 = (255, 140, 0)
STREAK_MILESTONE_100 = (255, 50, 50)

# === FONT LOADING WITH FALLBACKS ===
def load_font(size, font_type="text"):
    """
    Load fonts with robust fallback system.
    Uses system fonts for 'text' to ensure Unicode support.
    """
    import os

    # For text, use reliable system fonts to avoid character issues
    if font_type == "text":
        fallback_fonts = [
            "arial.ttf",
            "Arial.ttf",
            "helvetica.ttf",
            "Helvetica.ttf",
            "segoeui.ttf",
            "C:\\Windows\\Fonts\\arial.ttf",
            "C:\\Windows\\Fonts\\Arial.ttf"
        ]

        for font_name in fallback_fonts:
            try:
                return ImageFont.truetype(font_name, size)
            except (OSError, IOError):
                continue
        return ImageFont.load_default()

    # For title and numbers, try custom fonts first
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
        except Exception as e:
            print(f"⚠️ Could not load custom font {font_type}: {e}")

    # Fallback to system fonts
    fallback_fonts = [
        "arial.ttf", "Arial.ttf", "helvetica.ttf", "Helvetica.ttf",
        "C:\\Windows\\Fonts\\arial.ttf"
    ]

    for font_name in fallback_fonts:
        try:
            return ImageFont.truetype(font_name, size)
        except (OSError, IOError):
            continue

    return ImageFont.load_default()


# === SAFE TEXT RENDERER WITH FALLBACK ===
def safe_draw_text(draw, xy, text, primary_font, fallback_font=None, fill=(255,255,255)):
    """
    Draw text character-by-character using primary_font when possible,
    otherwise draw individual characters with fallback_font.

    This avoids missing-glyph boxes when the primary custom font lacks
    certain Unicode glyphs. Uses the 'text' system font as fallback.
    """
    if not text:
        return

    if fallback_font is None:
        fallback_font = load_font(getattr(primary_font, 'size', 18), 'text')

    x, y = xy
    for ch in text:
        try:
            # attempt to access mask for glyph; raises if glyph missing
            primary_font.getmask(ch)
            draw.text((x, y), ch, font=primary_font, fill=fill)
            bbox = draw.textbbox((0, 0), ch, font=primary_font)
            w = bbox[2] - bbox[0]
        except Exception:
            draw.text((x, y), ch, font=fallback_font, fill=fill)
            bbox = draw.textbbox((0, 0), ch, font=fallback_font)
            w = bbox[2] - bbox[0]

        x += max(1, w)


# === CRT EFFECTS ===
def add_scanlines(img, spacing=3):
    """Adds horizontal scanlines for CRT effect"""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for y in range(0, img.height, spacing):
        alpha = 50 if y % (spacing * 2) == 0 else 25
        draw.line([(0, y), (img.width, y)], fill=(0, 0, 0, alpha))

    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    result = Image.alpha_composite(img, overlay)
    return result.convert('RGB')

def add_subtle_static(img, intensity=8):
    """Adds very subtle static noise"""
    if img.mode != 'RGB':
        img = img.convert('RGB')

    pixels = img.load()
    for _ in range(intensity * 80):
        x = random.randint(0, img.width - 1)
        y = random.randint(0, img.height - 1)

        noise = random.randint(-20, 20)
        r, g, b = pixels[x, y]
        pixels[x, y] = (
            max(0, min(255, r + noise)),
            max(0, min(255, g + noise)),
            max(0, min(255, b + noise))
        )

    return img

def add_glow(img):
    """Adds subtle phosphor glow"""
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    blurred = img.filter(ImageFilter.GaussianBlur(radius=1))
    return Image.blend(img, blurred, alpha=0.25).convert('RGB')

# === FRAME ELEMENTS ===
def draw_simple_frame(draw, width, height):
    """Draws clean codec frame with corner brackets"""
    bracket_size = 30
    thickness = 3

    # Main border
    draw.rectangle([3, 3, width - 3, height - 3],
                   outline=CODEC_GREEN_PRIMARY, width=2)

    # Corner brackets
    corners = [
        (10, 10, 10 + bracket_size, 10, 10, 10 + bracket_size),  # Top-left
        (width - 10 - bracket_size, 10, width - 10, 10, width - 10, 10 + bracket_size),  # Top-right
        (10, height - 10, 10 + bracket_size, height - 10, 10, height - 10 - bracket_size),  # Bottom-left
        (width - 10 - bracket_size, height - 10, width - 10, height - 10, width - 10, height - 10 - bracket_size)  # Bottom-right
    ]

    for x1, y1, x2, y2, x3, y3 in corners:
        draw.line([(x1, y1), (x2, y2)], fill=CODEC_BORDER_BRIGHT, width=thickness)
        draw.line([(x1, y1), (x3, y3)], fill=CODEC_BORDER_BRIGHT, width=thickness)

def draw_divider(draw, x, y, width):
    """Draws horizontal divider"""
    draw.line([(x, y), (x + width, y)], fill=CODEC_GREEN_PRIMARY, width=2)

# === STREAK VISUALIZATION ===
def get_streak_color(streak_days):
    """Returns color based on streak milestone"""
    if streak_days >= 100:
        return STREAK_MILESTONE_100
    elif streak_days >= 30:
        return STREAK_MILESTONE_30
    elif streak_days >= 7:
        return STREAK_MILESTONE_7
    else:
        return STREAK_NORMAL

def draw_fire_icon(draw, x, y, size=20, color=CODEC_ORANGE):
    """Draws a simple fire emoji-style icon"""
    # Main flame body
    points = [
        (x + size//2, y),  # Top
        (x + size, y + size//2),  # Right
        (x + size*0.8, y + size),  # Bottom-right
        (x + size//2, y + size*0.7),  # Center
        (x + size*0.2, y + size),  # Bottom-left
        (x, y + size//2)  # Left
    ]
    draw.polygon(points, fill=color)

    # Inner highlight
    inner_points = [
        (x + size//2, y + size*0.3),
        (x + size*0.7, y + size*0.6),
        (x + size//2, y + size*0.8),
        (x + size*0.3, y + size*0.6)
    ]
    draw.polygon(inner_points, fill=CODEC_YELLOW)

def draw_streak_display(draw, x, y, streak_days, font_large, font_small):
    """Draws streak counter with fire icons and progress bar"""
    streak_color = get_streak_color(streak_days)

    # Fire icons
    fire_spacing = 30
    num_fires = min(streak_days, 5)  # Max 5 fire icons shown

    for i in range(num_fires):
        fire_x = x + i * fire_spacing
        draw_fire_icon(draw, fire_x, y, size=22, color=streak_color)

    # Streak number
    streak_text = f"×{streak_days}"
    draw.text((x + num_fires * fire_spacing + 10, y - 2),
             streak_text, fill=streak_color, font=font_large)

    # Milestone badge
    milestone_y = y + 35
    if streak_days >= 100:
        badge_color = STREAK_MILESTONE_100
    elif streak_days >= 30:
        badge_color = STREAK_MILESTONE_30
    elif streak_days >= 7:
        badge_color = STREAK_MILESTONE_7
    else:
        badge_color = CODEC_GREEN_TEXT

    draw.text((x, milestone_y), fill=badge_color, font=font_small)

    # Progress bar to next milestone
    milestones = [7, 30, 100]
    next_milestone = next((m for m in milestones if m > streak_days), 100)

    if streak_days < 100:
        bar_y = milestone_y + 30
        bar_width = 300
        bar_height = 8

        prev_milestone = max([m for m in [0] + milestones if m <= streak_days])
        progress = (streak_days - prev_milestone) / (next_milestone - prev_milestone)

        # Background
        draw.rectangle([x, bar_y, x + bar_width, bar_y + bar_height],
                      fill=CODEC_BG_MEDIUM, outline=CODEC_GREEN_DIM, width=1)

        # Fill
        fill_width = int(bar_width * progress)
        if fill_width > 0:
            draw.rectangle([x + 1, bar_y + 1, x + fill_width - 1, bar_y + bar_height - 1],
                          fill=streak_color)

        # Text
        progress_text = f"{streak_days}/{next_milestone} days to next milestone"
        draw.text((x, bar_y + 12), progress_text,
                 fill=CODEC_GREEN_DIM, font=font_small)

# === REWARD DISPLAY ===
def draw_reward_box(draw, x, y, label, amount, color, font_label, font_amount, width=280):
    """Draws a clean reward display box"""
    box_height = 100

    # Box background
    draw.rectangle([x, y, x + width, y + box_height],
                  fill=CODEC_BG_MEDIUM, outline=color, width=3)

    # Label
    draw.text((x + 15, y + 12), label, fill=CODEC_GREEN_DIM, font=font_label)

    # Amount (large and prominent)
    amount_text = f"+{amount:,}"
    bbox = draw.textbbox((0, 0), amount_text, font=font_amount)
    text_width = bbox[2] - bbox[0]
    text_x = x + (width - text_width) // 2

    draw.text((text_x, y + 45), amount_text, fill=color, font=font_amount)

def draw_stat_display(draw, x, y, label, value, font_label, font_value):
    """Draws a stat display"""
    draw.text((x, y), label, fill=CODEC_GREEN_DIM, font=font_label)
    draw.text((x, y + 28), str(value), fill=CODEC_GREEN_BRIGHT, font=font_value)

    bbox = draw.textbbox((x, y + 28), str(value), font=font_value)
    draw.line([(x, bbox[3] + 3), (bbox[2], bbox[3] + 3)],
              fill=CODEC_GREEN_PRIMARY, width=2)

def draw_codec_frame(draw, width, height):
    """Draws codec frame with corner brackets"""
    bracket_size = 35
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

# === PROMOTION BANNER ===
def draw_promotion_banner(draw, x, y, width, new_rank, font_large, font_medium, flash=False):
    """Draws promotion achievement banner"""
    banner_height = 70

    # Flash effect color
    bg_color = CODEC_YELLOW if flash else CODEC_BG_MEDIUM
    border_color = CODEC_ORANGE if flash else CODEC_YELLOW

    # Banner background
    draw.rectangle([x, y, x + width, y + banner_height],
                  fill=bg_color, outline=border_color, width=4)

    # Stars decoration - removed for unicode compatibility
    # star = "★"
    # draw.text((x + 15, y + 20), star, fill=CODEC_ORANGE, font=font_large)
    # draw.text((x + width - 45, y + 20), star, fill=CODEC_ORANGE, font=font_large)

    # Text
    promo_text = "PROMOTION ACHIEVED!"
    bbox = draw.textbbox((0, 0), promo_text, font=font_large)
    text_width = bbox[2] - bbox[0]
    text_x = x + (width - text_width) // 2

    text_color = CODEC_BG_DARK if flash else CODEC_ORANGE
    draw.text((text_x, y + 12), promo_text, fill=text_color, font=font_large)

    # New rank
    rank_text = f"NEW RANK: {new_rank}"
    bbox2 = draw.textbbox((0, 0), rank_text, font=font_medium)
    text_width2 = bbox2[2] - bbox2[0]
    text_x2 = x + (width - text_width2) // 2

    draw.text((text_x2, y + 42), rank_text, fill=text_color, font=font_medium)

# === MAIN GENERATOR: DAILY SUPPLY DROP ===
def generate_daily_supply_card(username, xp_reward,
                               current_xp, current_rank,
                               streak_days=1, promoted=False, new_rank=None,
                               role_granted=None):
    """
    Generates MGS Codec-style daily supply drop card

    IMPROVED: Better spacing, cleaner layout, no cramping

    Args:
        username: Display name
        xp_reward: XP received today
        current_xp: Total XP after reward
        current_rank: Current rank name
        streak_days: Consecutive days claimed
        promoted: Whether user was promoted
        new_rank: New rank if promoted
        role_granted: Discord role name if granted

    Returns:
        PIL Image object
    """
    username = sanitize_username(username)

    # Optimized dimensions for better spacing
    width, height = 750, 620

    base = Image.new("RGB", (width, height), CODEC_BG_DARK)
    draw = ImageDraw.Draw(base)

    # Load fonts
    font_title = load_font(52, "title")
    font_large = load_font(48, "numbers")
    font_medium = load_font(36, "numbers")
    font_normal = load_font(32, "text")
    font_small = load_font(18, "text")

    # === HEADER SECTION ===
    header_y = 30
    header_text = "DAILY SUPPLY DROP"
    bbox = draw.textbbox((0, 0), header_text, font=font_title)
    text_width = bbox[2] - bbox[0]
    draw.text(((width - text_width) // 2, header_y), header_text,
             fill=CODEC_BORDER_BRIGHT, font=font_title)

    # Agent name
    draw.text((90, header_y + 70), f"AGENT: {username.upper()}",
             fill=CODEC_GREEN_TEXT, font=font_medium)

    draw_divider(draw, 50, header_y + 115, width - 100)

    # === STREAK SECTION ===
    current_y = header_y + 130
    streak_color = get_streak_color(streak_days)

    # Streak display
    draw.text((50, current_y), "► OPERATION STREAK", fill=CODEC_GREEN_DIM, font=font_small)

    # Fire icons and streak count
    fire_x = 50
    fire_y = current_y + 50
    num_fires = min(streak_days, 5)
    for i in range(num_fires):
        draw_fire_icon(draw, fire_x + i * 35, fire_y, size=26, color=streak_color)

    # Align streak text vertically with icons
    bbox = draw.textbbox((0, 0), "×0 DAYS", font=font_large)
    icon_height = 15
    text_height = bbox[3] - bbox[1]
    # Center text with icons
    text_y = fire_y + (icon_height - text_height) // 2

    streak_text = f"×{streak_days} DAYS"
    draw.text((fire_x + num_fires * 35 + 15, text_y),
             streak_text, fill=streak_color, font=font_large)

    # === REWARDS SECTION ===
    current_y += 110
    draw.text((50, current_y), "► REWARDS RECEIVED", fill=CODEC_GREEN_DIM, font=font_small)

    rewards_y = current_y + 35

    box_width = 300
    box_x = 50

    # Calculate vertical position for amount text to center between header and bottom
    box_height = 100
    label_y = rewards_y + 12
    amount_text = f"+{xp_reward:,}"
    bbox_label = draw.textbbox((0, 0), "EXPERIENCE", font=font_small)
    label_bottom = label_y + (bbox_label[1] - bbox_label[1])
    amount_bbox = draw.textbbox((0, 0), amount_text, font=font_large)
    amount_height = amount_bbox[3] - amount_bbox[1]
    # Center between label_bottom and box bottom
    amount_y = label_bottom + ((rewards_y + box_height - label_bottom - amount_height) // 2)

    # Draw box
    draw.rectangle([box_x, rewards_y, box_x + box_width, rewards_y + box_height],
                   fill=CODEC_BG_MEDIUM, outline=CODEC_BORDER_BRIGHT, width=3)
    # Label
    draw.text((box_x + 15, label_y), "EXPERIENCE", fill=CODEC_GREEN_DIM, font=font_small)
    # Amount
    bbox_amount = draw.textbbox((0, 0), amount_text, font=font_large)
    text_width = bbox_amount[2] - bbox_amount[0]
    text_x = box_x + (box_width - text_width) // 2
    draw.text((text_x, amount_y), amount_text, fill=CODEC_BORDER_BRIGHT, font=font_large)

    # === CURRENT STATUS ===
    current_y = rewards_y + 130
    draw.text((50, current_y), "► UPDATED STATUS", fill=CODEC_GREEN_DIM, font=font_small)

    stats_y = current_y + 35
    draw_stat_display(draw, 50, stats_y, "TOTAL XP", f"{current_xp}",
                     font_small, font_medium)
    draw_stat_display(draw, 160, stats_y, "RANK", current_rank,
                     font_small, font_medium)
    draw_stat_display(draw, 350, stats_y, "STREAK", f"{streak_days} DAYS",
                     font_small, font_medium)

    # === FOOTER ===
    footer_y = height - 45
    draw.text((60, footer_y), "Return in 24:00:00 for next supply drop",
             fill=CODEC_GREEN_DIM, font=font_small)

    draw.text((width - 290, footer_y), "Outer Heaven: Exciled Units",
             fill=CODEC_GREEN_DIM, font=font_small)

    # === FRAME & EFFECTS ===
    draw_codec_frame(draw, width, height)
    base = add_scanlines(base, spacing=3)
    base = add_subtle_static(base, intensity=10)
    base = add_glow(base)

    return base

# === PROMOTION CARD GENERATOR ===
def generate_promotion_card(username, old_rank, new_rank, current_xp, role_granted=None):
    """
    Generates MGS Codec-style PROMOTION achievement card

    Args:
        username: Display name
        old_rank: Previous rank
        new_rank: New rank achieved
        current_xp: Total XP
        role_granted: Discord role name (optional)

    Returns:
        PIL Image object
    """
    username = sanitize_username(username)

    width, height = 800, 550

    base = Image.new("RGB", (width, height), CODEC_BG_DARK)
    draw = ImageDraw.Draw(base)

    # Load fonts
    font_title = load_font(52, "title")
    font_huge = load_font(44, "numbers")
    font_large = load_font(36, "numbers")
    font_medium = load_font(28, "text")
    font_normal = load_font(24, "text")
    font_small = load_font(20, "text")

    # === HEADER ===
    header_y = 30
    header_text = "PROMOTION ACHIEVED"
    bbox = draw.textbbox((0, 0), header_text, font=font_title)
    text_width = bbox[2] - bbox[0]
    draw.text(((width - text_width) // 2, header_y), header_text,
             fill=CODEC_YELLOW, font=font_title)

    # Agent name
    draw.text((50, header_y + 75), f"AGENT: {username.upper()}",
             fill=CODEC_GREEN_TEXT, font=font_medium)

    draw_divider(draw, 50, header_y + 115, width - 100)

    # === MAIN PROMOTION DISPLAY ===
    current_y = header_y + 150

    # Old rank
    draw.text((50, current_y), "PREVIOUS RANK", fill=CODEC_GREEN_DIM, font=font_small)
    draw.text((60, current_y + 30), old_rank, fill=CODEC_GREEN_TEXT, font=font_large)
    old_rank_bbox = draw.textbbox((60, current_y + 30), old_rank, font=font_large)
    old_padding = 10
    draw.rectangle([old_rank_bbox[0] - old_padding, old_rank_bbox[1] - old_padding,
                    old_rank_bbox[2] + old_padding, old_rank_bbox[3] + old_padding],
                   outline=CODEC_GREEN_TEXT, width=3)

    # Arrow
    arrow_x = width // 2 - 50
    arrow_y = current_y + 30
    arrow_text = ">>>>"
    draw.text((arrow_x, arrow_y), arrow_text, fill=CODEC_BORDER_BRIGHT, font=font_huge)

    # New rank (highlighted)
    new_rank_x = width // 2 + 150
    draw.text((new_rank_x, current_y), "NEW RANK", fill=CODEC_ORANGE, font=font_small)
    new_rank_name_x = new_rank_x + 10
    draw.text((new_rank_name_x, current_y + 30), new_rank, fill=CODEC_YELLOW, font=font_large)

    # Highlight box around new rank
    rank_bbox = draw.textbbox((new_rank_name_x, current_y + 30), new_rank, font=font_large)
    padding = 10
    draw.rectangle([rank_bbox[0] - padding, rank_bbox[1] - padding,
                   rank_bbox[2] + padding, rank_bbox[3] + padding],
                  outline=CODEC_YELLOW, width=3)

    # === STATS & REWARDS ===
    current_y += 120
    draw.text((50, current_y), "► PROMOTION DETAILS", fill=CODEC_GREEN_DIM, font=font_small)

    details_y = current_y + 35

    # XP Display
    draw_stat_display(draw, 50, details_y, "TOTAL EXPERIENCE", f"{current_xp:,} XP",
                     font_small, font_large)

    # === CONGRATULATIONS MESSAGE ===
    congrats_y = height - 110
    congrats_text = "MISSION ACCOMPLISHED: CONTINUE OPERATIONS"
    bbox = draw.textbbox((0, 0), congrats_text, font=font_medium)
    text_width = bbox[2] - bbox[0]
    draw.text(((width - text_width) // 2, congrats_y), congrats_text,
             fill=CODEC_BORDER_BRIGHT, font=font_medium)

    # === FOOTER ===
    footer_y = height - 45
    draw.text((60, footer_y), "Keep earning XP to reach the next rank",
             fill=CODEC_GREEN_DIM, font=font_small)

    draw.text((width - 310, footer_y), "Outer Heaven: Exciled Units",
             fill=CODEC_GREEN_DIM, font=font_small)

    # === FRAME & EFFECTS ===
    draw_codec_frame(draw, width, height)
    base = add_scanlines(base, spacing=3)
    base = add_subtle_static(base, intensity=12)
    base = add_glow(base)

    return base


# === TEST/PREVIEW ===
if __name__ == "__main__":
    print("🎮 Testing MGS Image Generators...")

    # Test Daily Supply Drop
    img1 = generate_daily_supply_card(
        username="Solid Snake",
        xp_reward=100,
        current_xp=3000,
        current_rank="Lieutenant",
        streak_days=15,
        promoted=False
    )
    img1.save("test_daily_drop.png")
    print("✅ Daily drop card saved as 'test_daily_drop.png'")

    # Test Promotion Card
    img2 = generate_promotion_card(
        username="Solid Snake",
        old_rank="Specialist",
        new_rank="Lieutenant",
        current_xp=3000,
        role_granted="Lieutenant"
    )
    img2.save("test_promotion.png")
    print("✅ Promotion card saved as 'test_promotion.png'")
