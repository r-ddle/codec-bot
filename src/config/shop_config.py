"""
Shop configuration - Easy customization of shop items and UI
"""

# SIMPLIFIED Shop Items - Keep it simple for MGS community!
SHOP_ITEMS = [
    {
        'name': '⚡ XP Booster (2 Hours)',
        'description': 'Double XP from all activities for 2 hours. Perfect for a gaming session!',
        'category': 'booster',
        'price': 500,
        'duration_hours': 2,
        'item_type': 'xp_boost_2h',
        'emoji': '⚡',
        'color': 0xFFD700
    },
    {
        'name': '📦 Tactical Intel Bundle',
        'description': 'Bonus reward package: +500 XP and +200 GMP',
        'category': 'bundle',
        'price': 150,
        'duration_hours': 0,
        'item_type': 'intel_bundle',
        'emoji': '📦',
        'color': 0x3498DB
    },
    {
        'name': '🎁 Extra Daily Claim',
        'description': 'Get a second daily bonus today! One-time use.',
        'category': 'special',
        'price': 300,
        'duration_hours': 0,
        'item_type': 'extra_daily',
        'emoji': '🎁',
        'color': 0x2ECC71
    },
    {
        'name': '🌟 MGS Name Color',
        'description': 'Unlock special name color role! (Cosmetic - admin will apply)',
        'category': 'cosmetic',
        'price': 15000,
        'duration_hours': 0,
        'item_type': 'name_color',
        'emoji': '🌟',
        'color': 0x9B59B6
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
