# shop_gen.py
# Author: Tom & Claude
# MGS Codec-style tactical shop generator

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import unicodedata
import random

# === AUTHENTIC MGS CODEC COLOR PALETTE ===
CODEC_BG_DARK = (5, 25, 15)
CODEC_BG_MEDIUM = (10, 35, 20)
CODEC_GREEN_PRIMARY = (50, 200, 100)
CODEC_GREEN_BRIGHT = (100, 255, 150)
CODEC_GREEN_DIM = (30, 120, 60)
CODEC_GREEN_TEXT = (80, 220, 120)
CODEC_BORDER_BRIGHT = (120, 255, 180)
CODEC_YELLOW = (255, 215, 0)

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

def generate_shop_card(user_gmp, shop_items):
    """
    Generates MGS Codec-style shop image.

    Args:
        user_gmp: Current user's GMP balance
        shop_items: List of dicts with keys: name, description, price
                   Example: [
                       {'name': 'CUSTOM ROLE', 'description': 'Customize your color and role name', 'price': 15000},
                       {'name': 'EXTRA DAILY', 'description': 'Get 2nd daily supply drop (no streak)', 'price': 5000},
                       {'name': '2HR BOOSTER', 'description': 'Extra XP/GMP + reduced cooldown (30s->10s)', 'price': 1000}
                   ]

    Returns:
        PIL Image object
    """
    width = 900
    height = 550

    # Create base
    base = Image.new("RGB", (width, height), CODEC_BG_DARK)
    draw = ImageDraw.Draw(base)

    # Load fonts
    font_title = load_font(38, "text")
    font_item_name = load_font(24, "text")
    font_desc = load_font(18, "text")
    font_price = load_font(22, "numbers")
    font_balance = load_font(20, "text")

    # === HEADER ===
    header_y = 40
    safe_draw_text(draw, (40, header_y),
                  "► GMP TACTICAL SUPPLY SHOP",
                  primary_font=font_title, fill=CODEC_BORDER_BRIGHT)

    # User balance
    balance_y = header_y + 50
    safe_draw_text(draw, (40, balance_y),
                  f"YOUR BALANCE: {user_gmp:,} GMP",
                  primary_font=font_balance, fill=CODEC_GREEN_TEXT)

    # Divider
    divider_y = balance_y + 35
    draw_codec_divider(draw, 40, divider_y, width - 80)

    # === SHOP ITEMS ===
    items_start_y = divider_y + 30
    item_height = 110

    for idx, item in enumerate(shop_items):
        item_y = items_start_y + (idx * item_height)

        # Item number
        item_num = f"[{idx + 1}]"
        safe_draw_text(draw, (40, item_y),
                      item_num,
                      primary_font=font_item_name, fill=CODEC_YELLOW)

        # Item name
        name_x = 100
        safe_draw_text(draw, (name_x, item_y),
                      item['name'].upper(),
                      primary_font=font_item_name, fill=CODEC_GREEN_BRIGHT)

        # Description
        desc_y = item_y + 30
        safe_draw_text(draw, (name_x, desc_y),
                      item['description'],
                      primary_font=font_desc, fill=CODEC_GREEN_TEXT)

        # Price (right-aligned)
        price_str = f"COST: {item['price']:,} GMP"
        try:
            bbox = draw.textbbox((0, 0), price_str, font=font_price)
            price_width = bbox[2] - bbox[0]
        except:
            price_width = len(price_str) * 12

        price_x = width - 40 - price_width
        price_y = item_y + 60

        # Check if user can afford
        if user_gmp >= item['price']:
            price_color = CODEC_GREEN_BRIGHT
        else:
            price_color = CODEC_GREEN_DIM

        safe_draw_text(draw, (price_x, price_y),
                      price_str,
                      primary_font=font_price, fill=price_color)

        # Separator line
        if idx < len(shop_items) - 1:
            line_y = item_y + item_height - 10
            draw.line([(100, line_y), (width - 40, line_y)],
                     fill=CODEC_GREEN_DIM, width=1)

    # === FOOTER ===
    footer_y = height - 40
    safe_draw_text(draw, (40, footer_y),
                  "USE: !buy <number> TO PURCHASE",
                  primary_font=font_desc, fill=CODEC_GREEN_DIM)

    # === APPLY EFFECTS ===
    draw_codec_frame(draw, width, height)
    base = add_heavy_scanlines(base, spacing=3)
    base = add_static_noise(base, intensity=12)
    base = add_phosphor_glow(base)

    return base


# === TEST ===
if __name__ == "__main__":
    test_items = [
        {'name': 'CUSTOM ROLE', 'description': 'Customize your color and role name', 'price': 15000},
        {'name': 'EXTRA DAILY', 'description': 'Get 2nd daily supply drop (no streak affect)', 'price': 5000},
        {'name': '2HR BOOSTER', 'description': 'Extra XP/GMP + reduced cooldown (30s->10s)', 'price': 1000}
    ]

    img = generate_shop_card(user_gmp=8500, shop_items=test_items)
    img.save("shop_test.png")
    print("✅ Shop card saved as 'shop_test.png'")
