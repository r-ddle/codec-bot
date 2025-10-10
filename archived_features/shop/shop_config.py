"""
Shop configuration - Easy customization of shop items and UI
"""

# SIMPLIFIED Shop Items - Keep it simple for MGS community!
SHOP_ITEMS = [
    {
        'name': 'CUSTOM ROLE',
        'description': 'Customize your color and role name',
        'category': 'cosmetic',
        'price': 15000,
        'duration_hours': 0,
        'item_type': 'custom_role',
        'color': 0x9B59B6
    },
    {
        'name': 'EXTRA DAILY',
        'description': 'Get 2nd daily supply drop (no streak affect)',
        'category': 'special',
        'price': 5000,
        'duration_hours': 0,
        'item_type': 'extra_daily',
        'color': 0x2ECC71
    },
    {
        'name': '2HR BOOSTER',
        'description': 'Extra XP/GMP + reduced cooldown (30s->10s)',
        'category': 'booster',
        'price': 1000,
        'duration_hours': 2,
        'item_type': 'xp_boost_2h',
        'color': 0xFFD700
    },
]

# Shop UI Configuration
SHOP_UI_CONFIG = {
    'title': '🏪 GMP SHOP',
    'description': 'Use your GMP to purchase boosters and upgrades',
    'color': 0x599cff,
    'footer': 'Check your inventory with /inventory',
    'items_per_page': 5,
    'show_balance': True,
}

# Rank Card Configuration
RANK_CARD_CONFIG = {
    'width': 900,
    'height': 300,
    'background_color': (20, 20, 30),  # Dark blue-grey
    'accent_color': (89, 156, 255),  # Blue accent
    'text_color': (255, 255, 255),
    'secondary_text_color': (150, 150, 150),
    'progress_bar_bg': (40, 40, 50),
    'progress_bar_fill': (89, 156, 255),
    'show_avatar': True,
    'show_rank_icon': True,
    'font_name': 'arial.ttf',  # Will try MGS-style font if available
    'font_size_name': 32,
    'font_size_rank': 24,
    'font_size_stats': 20,
}

# Inventory UI Configuration
INVENTORY_UI_CONFIG = {
    'title': '📦 YOUR INVENTORY',
    'color': 0x599cff,
    'items_per_page': 5,
    'show_expired': False,  # Hide expired items
    'footer': 'Use items with /use <item_id>',
}

# Shop Categories
SHOP_CATEGORIES = {
    'booster': {
        'name': '⚡ Boosters',
        'description': 'XP multipliers and bonus items',
        'emoji': '⚡'
    },
    'currency': {
        'name': '💰 Currency',
        'description': 'GMP packs and bundles',
        'emoji': '💰'
    },
    'cosmetic': {
        'name': '🎨 Cosmetics',
        'description': 'Profile customization (coming soon)',
        'emoji': '🎨'
    },
}
