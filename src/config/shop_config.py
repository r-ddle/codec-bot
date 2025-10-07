"""
Shop configuration - Easy customization of shop items and UI
"""

# Shop Items Configuration
SHOP_ITEMS = [
    {
        'name': 'XP Booster 2x (1 hour)',
        'description': 'Double XP from all activities for 1 hour',
        'category': 'booster',
        'price': 300,
        'duration_hours': 1,
        'item_type': 'xp_boost_1h',
        'emoji': '⚡',
        'color': 0xFFD700
    },
    {
        'name': 'XP Booster 2x (24 hours)',
        'description': 'Double XP from all activities for 24 hours',
        'category': 'booster',
        'price': 2000,
        'duration_hours': 24,
        'item_type': 'xp_boost_24h',
        'emoji': '🔥',
        'color': 0xFF6B6B
    },
    {
        'name': 'XP Booster 2x (1 week)',
        'description': 'Double XP from all activities for 7 days',
        'category': 'booster',
        'price': 5000,
        'duration_hours': 168,
        'item_type': 'xp_boost_1w',
        'emoji': '💎',
        'color': 0x9B59B6
    },
    {
        'name': 'Daily Bonus Multiplier',
        'description': 'Double your next daily bonus (one-time use)',
        'category': 'booster',
        'price': 500,
        'duration_hours': 0,
        'item_type': 'daily_multiplier',
        'emoji': '🎁',
        'color': 0x3498DB
    },
    {
        'name': 'GMP Pack (Small)',
        'description': 'Get 1,000 bonus GMP instantly',
        'category': 'currency',
        'price': 0,  # Free or can be set
        'duration_hours': 0,  # Instant use
        'gmp_amount': 1000,
        'item_type': 'gmp_small',
        'emoji': '💰',
        'color': 0x2ECC71
    },
]

# Shop UI Configuration
SHOP_UI_CONFIG = {
    'title': '🏪 FOXHOUND GMP SHOP',
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
