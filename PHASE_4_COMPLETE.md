# 🎨 Phase 4 Complete - Shop UI & Image System

## ✅ What's Implemented

### **Image Generation System**
- Beautiful MGS-themed rank cards with 80s aesthetic
- Circular avatars
- Grid pattern background
- Progress bars with gradient
- Corner accents (MGS-style)
- Auto-downloads user avatars

### **Button-Based Shop UI**
- Category navigation (Boosters, Currency)
- Interactive inventory
- Purchase confirmations
- Pagination support
- Real-time balance display

### **Configuration System**
- `shop_config.py` - Easy item management
- Customizable colors, prices, durations
- UI settings (page size, colors, text)
- Rank card appearance settings

---

## 📋 ALL COMMANDS

### **Shop Commands**

#### Slash Commands:
- `/shop` - Open interactive shop with buttons
- `/buy <item_id>` - Purchase item with confirmation
- `/inventory` - View your items with buttons
- `/use <inventory_id>` - Activate a booster
- `/rankcard [user]` - Generate beautiful rank image
- `/rank [user]` - Text-based rank card
- `/daily` - Claim daily bonus
- `/leaderboard [type]` - View top 10

#### Text Commands (! prefix):
- `!shop` - Open interactive shop
- `!buy <item_id>` - Purchase item
- `!inventory` (or `!inv`) - View items
- `!use <inventory_id>` - Activate booster
- `!rankcard [user]` (or `!rc`) - Generate rank image
- `!rank [user]` - Text rank card
- `!daily` - Daily bonus
- `!gmp` - Your stats

### **Admin Commands**
- `!shop_init` - Initialize shop items
- `!shop_list` - List all shop items
- `!shop_test_buy <item_id>` - Test purchase
- `!shop_test_inventory [user]` - View inventory
- `!shop_test_activate <inventory_id>` - Test activation
- `!shop_give_gmp <user> <amount>` - Give GMP
- `!neon_backup` - Manual backup
- `!neon_status` - Database status
- `!neon_resync` - Force resync with rank fix

---

## 🎮 How to Enable

### 1. Enable Features in `settings.py`:
```python
FEATURE_FLAGS = {
    'ENABLE_SHOP': True,              # ← Enable this
    'ENABLE_XP_BOOSTERS': True,       # ← Enable this
    'ENABLE_SLASH_COMMANDS': True,
}
```

### 2. Restart bot and initialize:
```
!shop_init
```

### 3. Test it:
```
/shop
/rankcard
```

---

## 🛠️ Customization

### Edit Shop Items (`config/shop_config.py`):
```python
SHOP_ITEMS = [
    {
        'name': 'Your Item Name',
        'description': 'What it does',
        'category': 'booster',  # or 'currency', 'cosmetic'
        'price': 300,
        'duration_hours': 1,
        'item_type': 'unique_id',
        'emoji': '⚡',
        'color': 0xFFD700
    },
]
```

### Edit Rank Card Appearance:
```python
RANK_CARD_CONFIG = {
    'width': 900,
    'height': 300,
    'background_color': (20, 20, 30),
    'accent_color': (89, 156, 255),
    # ... more options
}
```

---

## 📦 New Files Created

1. `src/config/shop_config.py` - Shop & UI configuration
2. `src/utils/image_gen.py` - Rank card image generation
3. `src/utils/shop_ui.py` - Discord button views
4. `src/cogs/shop_commands.py` - Shop commands (slash + text)

---

## 🎯 Features

### Shop System:
✅ Category browsing with buttons
✅ Purchase confirmations
✅ Inventory management
✅ Item activation
✅ Balance checking
✅ Pagination

### Image System:
✅ Beautiful rank cards
✅ MGS-themed design
✅ User avatars (circular)
✅ Progress bars
✅ Grid pattern background
✅ Custom fonts support

### Both Command Types:
✅ Slash commands (`/shop`)
✅ Text commands (`!shop`)
✅ Same functionality

---

## 🚀 Quick Test

1. **Enable shop**: Edit `settings.py` feature flags
2. **Restart bot**
3. **Initialize**: `!shop_init`
4. **Give yourself GMP**: `!shop_give_gmp @you 10000`
5. **Open shop**: `/shop`
6. **Browse categories**: Click buttons
7. **Buy item**: `/buy 1`
8. **View inventory**: `/inventory`
9. **Use item**: `/use <inventory_id>`
10. **Check rank card**: `/rankcard`

---

## 💡 Tips

- Shop items are fully configurable in `shop_config.py`
- Add new categories by adding to `SHOP_CATEGORIES`
- Rank card colors are in `RANK_CARD_CONFIG`
- All buttons timeout after 3 minutes (configurable)
- Items show ✅ if you can afford, ❌ if not
- Expired items are hidden in inventory (configurable)

---

## 🎨 Rank Card Features

- **Circular avatar** with smooth edges
- **MGS-style grid pattern** background
- **Corner accents** (tactical espionage aesthetic)
- **Progress bar** to next rank
- **XP & GMP** display
- **Activity stats** (messages, tactical words)
- **Modern + retro** 80s MGS vibes

---

**Phase 4 Complete! Shop system fully functional with beautiful images and interactive UI! 🎉**
