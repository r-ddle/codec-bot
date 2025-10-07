# daily_supply_gen.py
# Author: Tom & GitHub Copilot + Claude
# MGS Codec-style Daily Supply Drop card generator with GIF animation support

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageSequence
import io
import random

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

# === FONT LOADING ===
def load_font(size, bold=False):
    """Load readable fonts with Helvetica priority"""
    fonts_to_try = [
        "arial.ttf",
        "Arial.ttf",
        "helvetica.ttf",
        "Helvetica.ttf",
        "DejaVuSans.ttf",
        "LiberationSans-Regular.ttf",
        "FreeSans.ttf"
    ]

    bold_fonts = [
        "arialbd.ttf",
        "Arial-Bold.ttf",
        "helveticabd.ttf",
        "Helvetica-Bold.ttf",
        "DejaVuSans-Bold.ttf",
        "LiberationSans-Bold.ttf",
        "FreeSans-Bold.ttf"
    ]

    font_list = bold_fonts if bold else fonts_to_try

    for font_name in font_list:
        try:
            return ImageFont.truetype(font_name, size)
        except:
            continue

    return ImageFont.load_default()

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
        badge_text = "🏆 LEGENDARY STREAK"
        badge_color = STREAK_MILESTONE_100
    elif streak_days >= 30:
        badge_text = "⭐ ELITE STREAK"
        badge_color = STREAK_MILESTONE_30
    elif streak_days >= 7:
        badge_text = "🔥 HOT STREAK"
        badge_color = STREAK_MILESTONE_7
    else:
        badge_text = f"DAY {streak_days} OPERATION"
        badge_color = CODEC_GREEN_TEXT

    draw.text((x, milestone_y), badge_text, fill=badge_color, font=font_small)

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
def draw_reward_box(draw, x, y, label, amount, color, font_label, font_amount):
    """Draws a reward box with icon and amount"""
    box_width = 200
    box_height = 80

    # Box background with glow
    draw.rectangle([x, y, x + box_width, y + box_height],
                  fill=CODEC_BG_MEDIUM, outline=color, width=3)

    # Label
    draw.text((x + 10, y + 10), label, fill=CODEC_GREEN_DIM, font=font_label)

    # Amount (large and centered)
    amount_text = f"+{amount:,}"
    bbox = draw.textbbox((0, 0), amount_text, font=font_amount)
    text_width = bbox[2] - bbox[0]
    text_x = x + (box_width - text_width) // 2

    draw.text((text_x, y + 35), amount_text, fill=color, font=font_amount)

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

    # Stars decoration
    star = "★"
    draw.text((x + 15, y + 20), star, fill=CODEC_ORANGE, font=font_large)
    draw.text((x + width - 45, y + 20), star, fill=CODEC_ORANGE, font=font_large)

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

# === MAIN GENERATOR (STATIC) ===
def generate_daily_supply_card(username, gmp_reward, xp_reward,
                               current_gmp, current_xp, current_rank,
                               streak_days=1, promoted=False, new_rank=None,
                               role_granted=None):
    """
    Generates MGS Codec-style daily supply drop card

    Args:
        username: Display name
        gmp_reward: GMP received today
        xp_reward: XP received today
        current_gmp: Total GMP after reward
        current_xp: Total XP after reward
        current_rank: Current rank name
        streak_days: Consecutive days claimed
        promoted: Whether user was promoted
        new_rank: New rank if promoted
        role_granted: Discord role name if granted

    Returns:
        PIL Image object
    """
    width, height = 900, 500

    # Create base
    base = Image.new("RGB", (width, height), CODEC_BG_DARK)
    draw = ImageDraw.Draw(base)

    # Load fonts (larger, more readable)
    font_title = load_font(42, bold=True)
    font_large = load_font(32, bold=True)
    font_medium = load_font(24, bold=True)
    font_normal = load_font(22)
    font_small = load_font(18)
    font_tiny = load_font(14)

    # === HEADER ===
    header_y = 25
    header_text = "◄◄ DAILY SUPPLY DROP ►►"
    bbox = draw.textbbox((0, 0), header_text, font=font_title)
    text_width = bbox[2] - bbox[0]
    text_x = (width - text_width) // 2

    draw.text((text_x, header_y), header_text,
             fill=CODEC_BORDER_BRIGHT, font=font_title)

    # Subheader
    subheader = f"AGENT: {username.upper()}"
    draw.text((40, header_y + 55), subheader,
             fill=CODEC_GREEN_TEXT, font=font_normal)

    # Divider
    draw_divider(draw, 40, header_y + 90, width - 80)

    # === STREAK DISPLAY ===
    streak_y = header_y + 110
    draw.text((40, streak_y), "► OPERATION STREAK",
             fill=CODEC_GREEN_DIM, font=font_small)

    draw_streak_display(draw, 40, streak_y + 30, streak_days,
                       font_large, font_small)

    # === REWARDS SECTION ===
    rewards_y = streak_y + 130
    draw.text((40, rewards_y), "► REWARDS RECEIVED",
             fill=CODEC_GREEN_DIM, font=font_small)

    rewards_content_y = rewards_y + 30

    # GMP Box
    draw_reward_box(draw, 40, rewards_content_y, "GMP", gmp_reward,
                   CODEC_GREEN_BRIGHT, font_small, font_large)

    # XP Box
    draw_reward_box(draw, 260, rewards_content_y, "EXPERIENCE", xp_reward,
                   CODEC_BORDER_BRIGHT, font_small, font_large)

    # === UPDATED STATS ===
    stats_y = rewards_content_y + 100
    draw.text((40, stats_y), "► UPDATED STATUS",
             fill=CODEC_GREEN_DIM, font=font_small)

    stats_content_y = stats_y + 30
    stats_text = f"GMP: {current_gmp:,}  |  XP: {current_xp:,}  |  RANK: {current_rank}"
    draw.text((40, stats_content_y), stats_text,
             fill=CODEC_GREEN_TEXT, font=font_normal)

    # === PROMOTION BANNER (if applicable) ===
    if promoted and new_rank:
        promo_y = stats_content_y + 50
        draw_promotion_banner(draw, 40, promo_y, width - 80, new_rank,
                            font_medium, font_normal, flash=False)

        # Role granted text
        if role_granted:
            role_y = promo_y + 80
            role_text = f"✓ Discord Role Granted: {role_granted}"
            draw.text((40, role_y), role_text,
                     fill=CODEC_YELLOW, font=font_small)

    # === FOOTER ===
    footer_y = height - 35
    footer_text = "Return in 24:00:00 for next supply drop"
    draw.text((40, footer_y), footer_text,
             fill=CODEC_GREEN_DIM, font=font_tiny)

    # Copyright
    draw.text((width - 320, footer_y),
             "©1987 2001 Konami Computer Entertainment",
             fill=CODEC_GREEN_DIM, font=font_tiny)

    # === FRAME ===
    draw_simple_frame(draw, width, height)

    # === APPLY EFFECTS ===
    base = add_scanlines(base, spacing=3)
    base = add_subtle_static(base, intensity=8)
    base = add_glow(base)

    return base

# === GIF ANIMATION GENERATOR ===
def generate_daily_supply_animated(username, gmp_reward, xp_reward,
                                  current_gmp, current_xp, current_rank,
                                  streak_days=1, promoted=False, new_rank=None,
                                  role_granted=None, output_path="daily_drop.gif"):
    """
    Generates animated GIF version with effects:
    - Scanline movement
    - Promotion banner flash (if promoted)
    - Static interference pulses

    Returns:
        Path to saved GIF file
    """
    width, height = 900, 500
    frames = []
    num_frames = 20 if promoted else 10

    for frame_idx in range(num_frames):
        # Create base frame
        base = Image.new("RGB", (width, height), CODEC_BG_DARK)
        draw = ImageDraw.Draw(base)

        # Load fonts
        font_title = load_font(42, bold=True)
        font_large = load_font(32, bold=True)
        font_medium = load_font(24, bold=True)
        font_normal = load_font(22)
        font_small = load_font(18)
        font_tiny = load_font(14)

        # === HEADER ===
        header_y = 25
        header_text = "◄◄ DAILY SUPPLY DROP ►►"
        bbox = draw.textbbox((0, 0), header_text, font=font_title)
        text_width = bbox[2] - bbox[0]
        text_x = (width - text_width) // 2

        draw.text((text_x, header_y), header_text,
                 fill=CODEC_BORDER_BRIGHT, font=font_title)

        subheader = f"AGENT: {username.upper()}"
        draw.text((40, header_y + 55), subheader,
                 fill=CODEC_GREEN_TEXT, font=font_normal)

        draw_divider(draw, 40, header_y + 90, width - 80)

        # === STREAK ===
        streak_y = header_y + 110
        draw.text((40, streak_y), "► OPERATION STREAK",
                 fill=CODEC_GREEN_DIM, font=font_small)

        draw_streak_display(draw, 40, streak_y + 30, streak_days,
                           font_large, font_small)

        # === REWARDS ===
        rewards_y = streak_y + 130
        draw.text((40, rewards_y), "► REWARDS RECEIVED",
                 fill=CODEC_GREEN_DIM, font=font_small)

        rewards_content_y = rewards_y + 30
        draw_reward_box(draw, 40, rewards_content_y, "GMP", gmp_reward,
                       CODEC_GREEN_BRIGHT, font_small, font_large)
        draw_reward_box(draw, 260, rewards_content_y, "EXPERIENCE", xp_reward,
                       CODEC_BORDER_BRIGHT, font_small, font_large)

        # === STATS ===
        stats_y = rewards_content_y + 100
        draw.text((40, stats_y), "► UPDATED STATUS",
                 fill=CODEC_GREEN_DIM, font=font_small)

        stats_content_y = stats_y + 30
        stats_text = f"GMP: {current_gmp:,}  |  XP: {current_xp:,}  |  RANK: {current_rank}"
        draw.text((40, stats_content_y), stats_text,
                 fill=CODEC_GREEN_TEXT, font=font_normal)

        # === PROMOTION (animated flash) ===
        if promoted and new_rank:
            promo_y = stats_content_y + 50
            # Flash every other frame
            flash = (frame_idx % 4) < 2
            draw_promotion_banner(draw, 40, promo_y, width - 80, new_rank,
                                font_medium, font_normal, flash=flash)

            if role_granted:
                role_y = promo_y + 80
                role_text = f"✓ Discord Role Granted: {role_granted}"
                draw.text((40, role_y), role_text,
                         fill=CODEC_YELLOW, font=font_small)

        # === FOOTER ===
        footer_y = height - 35
        footer_text = "Return in 24:00:00 for next supply drop"
        draw.text((40, footer_y), footer_text,
                 fill=CODEC_GREEN_DIM, font=font_tiny)

        draw.text((width - 320, footer_y),
                 "©1987 2001 Konami Computer Entertainment",
                 fill=CODEC_GREEN_DIM, font=font_tiny)

        # === FRAME ===
        draw_simple_frame(draw, width, height)

        # === ANIMATED EFFECTS ===
        # Offset scanlines slightly each frame
        offset = frame_idx % 3
        base = add_scanlines(base, spacing=3)

        # Pulse static
        static_intensity = 8 + (frame_idx % 3) * 2
        base = add_subtle_static(base, intensity=static_intensity)

        base = add_glow(base)

        frames.append(base)

    # Save as GIF
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=100,  # 100ms per frame
        loop=0  # Infinite loop
    )

    return output_path

# === TEST/PREVIEW ===
if __name__ == "__main__":
    # Test 1: Normal daily (no promotion)
    img1 = generate_daily_supply_card(
        username="Solid Snake",
        gmp_reward=200,
        xp_reward=50,
        current_gmp=1615,
        current_xp=1493,
        current_rank="Private",
        streak_days=3
    )
    img1.save("daily_normal.png")
    print("✅ Normal daily saved as 'daily_normal.png'")

    # Test 2: With promotion
    img2 = generate_daily_supply_card(
        username="Big Boss",
        gmp_reward=200,
        xp_reward=50,
        current_gmp=5420,
        current_xp=3250,
        current_rank="Sergeant",
        streak_days=7,
        promoted=True,
        new_rank="Sergeant",
        role_granted="Sergeant"
    )
    img2.save("daily_promotion.png")
    print("✅ Promotion daily saved as 'daily_promotion.png'")

    # Test 3: High streak milestone
    img3 = generate_daily_supply_card(
        username="The Boss",
        gmp_reward=200,
        xp_reward=50,
        current_gmp=50000,
        current_xp=15000,
        current_rank="Colonel",
        streak_days=30
    )
    img3.save("daily_milestone.png")
    print("✅ Milestone daily saved as 'daily_milestone.png'")

    # Test 4: Animated GIF (promotion)
    generate_daily_supply_animated(
        username="Revolver Ocelot",
        gmp_reward=200,
        xp_reward=50,
        current_gmp=2840,
        current_xp=1750,
        current_rank="Corporal",
        streak_days=5,
        promoted=True,
        new_rank="Corporal",
        role_granted="Corporal",
        output_path="daily_animated.gif"
    )
    print("✅ Animated GIF saved as 'daily_animated.gif'")
