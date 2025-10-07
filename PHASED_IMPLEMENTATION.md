# 🛠️ Phased Implementation Plan - Safe & Incremental

## 🎯 Philosophy: Build Without Breaking

Each phase is:
- ✅ **Self-contained** - Can work independently
- ✅ **Tested thoroughly** - Before moving to next phase
- ✅ **Backward compatible** - Old features keep working
- ✅ **Rollback-ready** - Can revert if issues arise
- ✅ **Member-safe** - No data loss or corruption

---

## 📊 Phase Overview

```
Phase 0: Foundation & Safety     [1-2 days]   ← We are here
Phase 1: Database Extensions     [3-4 days]   ← Safe additions only
Phase 2: Basic Slash Commands    [1 week]     ← Simple conversions
Phase 3: GMP Shop Backend        [1 week]     ← Core shop logic
Phase 4: Shop UI & Items         [1 week]     ← User-facing shop
Phase 5: Missions System         [1.5 weeks]  ← Daily missions
Phase 6: Achievements            [1 week]     ← Tracking & badges
Phase 7: Enhanced Features       [2 weeks]    ← Profiles, transfers
Phase 8: Polish & Optimize       [1 week]     ← Bug fixes, performance
```

**Total Timeline: ~8-10 weeks of safe, incremental development**

---

## 🔧 Phase 0: Foundation & Safety [1-2 days]

### Goal: Prepare for changes without breaking anything

### Tasks:
1. ✅ **Fix Neon sync issues** (DONE)
2. ✅ **Document current state** (DONE)
3. **Create backup strategy**
4. **Add feature flags system**
5. **Create test environment**

### What to Do:

#### Step 1: Enhanced Backup System
```python
# Add to config/settings.py
FEATURE_FLAGS = {
    'ENABLE_SHOP': False,
    'ENABLE_MISSIONS': False,
    'ENABLE_SLASH_COMMANDS': False,
    'ENABLE_ACHIEVEMENTS': False,
}

# Can enable/disable features without code changes
```

#### Step 2: Create Test Commands
```python
# Add test cog for safe testing
@commands.command(name='test_feature')
@commands.has_permissions(administrator=True)
async def test_feature(self, ctx, feature_name: str):
    """Test new features in isolation"""
    pass
```

#### Step 3: Version Tracking
```python
# Add version to bot
BOT_VERSION = "2.0.0-alpha"
MIGRATION_VERSION = 1  # Track database schema version
```

### Deliverables:
- ✅ Feature flags system
- ✅ Backup commands
- ✅ Test environment ready
- ✅ Version tracking

### Testing:
```
1. Run bot normally - ensure everything works
2. Enable/disable feature flags - bot should still run
3. Test backup/restore - verify data integrity
```

### Success Criteria:
- Bot runs without errors
- All existing commands work
- Backups are automated
- Can safely test new features

---

## 🗄️ Phase 1: Database Extensions [3-4 days]

### Goal: Add new tables WITHOUT touching existing data

### What to Add:

```sql
-- New tables (separate from member_data)

CREATE TABLE shop_items (
    item_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50),  -- 'booster', 'cosmetic', 'role'
    price INTEGER NOT NULL,
    duration_hours INTEGER,  -- For temporary items
    item_type VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE member_inventory (
    inventory_id SERIAL PRIMARY KEY,
    member_id BIGINT NOT NULL,
    guild_id BIGINT NOT NULL,
    item_id INTEGER REFERENCES shop_items(item_id),
    quantity INTEGER DEFAULT 1,
    purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT FALSE
);

CREATE TABLE active_boosters (
    booster_id SERIAL PRIMARY KEY,
    member_id BIGINT NOT NULL,
    guild_id BIGINT NOT NULL,
    booster_type VARCHAR(50),  -- 'xp_2x', 'daily_2x'
    multiplier DECIMAL(3,2) DEFAULT 2.0,
    activated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);

-- Simple mission tracking
CREATE TABLE mission_progress (
    progress_id SERIAL PRIMARY KEY,
    member_id BIGINT NOT NULL,
    guild_id BIGINT NOT NULL,
    mission_type VARCHAR(50),  -- 'daily_messages', 'daily_tactical'
    progress_value INTEGER DEFAULT 0,
    target_value INTEGER NOT NULL,
    completed BOOLEAN DEFAULT FALSE,
    reset_date DATE,  -- When progress resets
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Implementation:

#### File: `src/database/extensions.py` (NEW)
```python
"""
Database extensions for new features.
Separate from member_data to ensure safety.
"""
import asyncpg
from config.settings import logger

class DatabaseExtensions:
    def __init__(self, neon_db):
        self.neon_db = neon_db

    async def init_extended_schema(self):
        """Create new tables if they don't exist"""
        if not self.neon_db or not self.neon_db.pool:
            logger.warning("Neon not connected - skipping extensions")
            return False

        try:
            async with self.neon_db.pool.acquire() as conn:
                # Create shop_items table
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS shop_items (
                        item_id SERIAL PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        description TEXT,
                        category VARCHAR(50),
                        price INTEGER NOT NULL,
                        duration_hours INTEGER,
                        item_type VARCHAR(50),
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Create member_inventory table
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS member_inventory (
                        inventory_id SERIAL PRIMARY KEY,
                        member_id BIGINT NOT NULL,
                        guild_id BIGINT NOT NULL,
                        item_id INTEGER REFERENCES shop_items(item_id),
                        quantity INTEGER DEFAULT 1,
                        purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP,
                        is_active BOOLEAN DEFAULT FALSE
                    )
                ''')

                # Create active_boosters table
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS active_boosters (
                        booster_id SERIAL PRIMARY KEY,
                        member_id BIGINT NOT NULL,
                        guild_id BIGINT NOT NULL,
                        booster_type VARCHAR(50),
                        multiplier DECIMAL(3,2) DEFAULT 2.0,
                        activated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP NOT NULL
                    )
                ''')

                # Create mission_progress table
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS mission_progress (
                        progress_id SERIAL PRIMARY KEY,
                        member_id BIGINT NOT NULL,
                        guild_id BIGINT NOT NULL,
                        mission_type VARCHAR(50),
                        progress_value INTEGER DEFAULT 0,
                        target_value INTEGER NOT NULL,
                        completed BOOLEAN DEFAULT FALSE,
                        reset_date DATE,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                logger.info("✅ Extended database schema initialized")
                return True

        except Exception as e:
            logger.error(f"❌ Error creating extended schema: {e}")
            return False
```

#### Update `src/core/bot_instance.py`:
```python
# Add to imports
from database.extensions import DatabaseExtensions

# In __init__
self.db_extensions = DatabaseExtensions(self.neon_db)

# In setup_hook
await self.db_extensions.init_extended_schema()
```

### Testing Phase 1:
```
1. Restart bot - tables should be created
2. Check Neon dashboard - verify new tables exist
3. Run existing commands - ensure nothing broke
4. Check logs - no errors
```

### Success Criteria:
- ✅ New tables created successfully
- ✅ Old data untouched
- ✅ Bot runs normally
- ✅ No errors in logs

### Rollback Plan:
If issues occur:
```sql
-- Drop new tables (safe, doesn't touch member_data)
DROP TABLE IF EXISTS mission_progress;
DROP TABLE IF EXISTS active_boosters;
DROP TABLE IF EXISTS member_inventory;
DROP TABLE IF EXISTS shop_items;
```

---

## 💬 Phase 2: Basic Slash Commands [1 week]

### Goal: Convert existing commands to slash, keep old ones working

### Why Start Here?
- Low risk - just UI changes
- High impact - better UX
- Easy to test
- Doesn't require new data

### Commands to Convert:

#### Week 1: Simple Commands
```python
/rank [user] - View rank card
/daily - Claim daily bonus
/leaderboard [type] - View rankings
/help - Show help message
```

### Implementation:

#### File: `src/cogs/slash_commands.py` (UPDATE)

```python
@app_commands.command(name="rank", description="View your or another member's rank card")
@app_commands.describe(user="The member to check (optional)")
async def rank_slash(self, interaction: discord.Interaction, user: discord.Member = None):
    """Slash command version of !rank"""
    target = user or interaction.user

    # Use existing logic from progression.py
    member_data = self.bot.member_data.get_member_data(target.id, interaction.guild.id)

    # Create embed (same as !rank command)
    embed = discord.Embed(
        title=f"🎖️ {target.display_name}",
        description=f"**Rank:** {member_data['rank']}\n**GMP:** {member_data['gmp']}\n**XP:** {member_data['xp']}",
        color=0x599cff
    )

    await interaction.response.send_message(embed=embed)

@app_commands.command(name="daily", description="Claim your daily bonus")
async def daily_slash(self, interaction: discord.Interaction):
    """Slash command version of !daily"""
    # Use existing daily bonus logic
    success, gmp, xp, rank_changed, new_rank = self.bot.member_data.award_daily_bonus(
        interaction.user.id,
        interaction.guild.id
    )

    if success:
        embed = discord.Embed(
            title="📅 DAILY BONUS CLAIMED",
            description=f"You received **{gmp} GMP** and **{xp} XP**!",
            color=0x00ff00
        )
        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(
            title="⏰ DAILY BONUS CLAIMED",
            description="You've already claimed your daily bonus. Come back tomorrow!",
            color=0xff9900
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
```

### Keep Old Commands:
```python
# In progression.py - don't remove these!
@commands.command(name='rank')
async def rank_command(self, ctx, member: discord.Member = None):
    """Text command version - kept for backward compatibility"""
    # Existing code stays unchanged
```

### Testing Phase 2:
```
1. Both /rank and !rank should work
2. Both /daily and !daily should work
3. Test with different users
4. Test error cases
5. Verify old commands still function
```

### Success Criteria:
- ✅ Slash commands work perfectly
- ✅ Old ! commands still work
- ✅ No breaking changes
- ✅ Same functionality, better UI

---

## 🏪 Phase 3: GMP Shop Backend [1 week]

### Goal: Build shop logic WITHOUT user interface yet

### Why Backend First?
- Test purchase logic safely
- Build inventory system
- Create admin tools for testing
- No user-facing changes until ready

### What to Build:

#### File: `src/utils/shop.py` (NEW)

```python
"""
Shop system backend - purchase logic and inventory management.
"""
from datetime import datetime, timedelta
from config.settings import logger

class ShopSystem:
    def __init__(self, bot):
        self.bot = bot

    async def initialize_shop_items(self):
        """Populate shop with initial items"""
        if not self.bot.db_extensions:
            return

        items = [
            {
                'name': 'XP Booster 2x (1 hour)',
                'description': 'Double XP for 1 hour',
                'category': 'booster',
                'price': 300,
                'duration_hours': 1,
                'item_type': 'xp_boost_1h'
            },
            {
                'name': 'XP Booster 2x (24 hours)',
                'description': 'Double XP for 24 hours',
                'category': 'booster',
                'price': 2000,
                'duration_hours': 24,
                'item_type': 'xp_boost_24h'
            },
            {
                'name': 'Daily Bonus Multiplier',
                'description': 'Double your next daily bonus',
                'category': 'booster',
                'price': 500,
                'duration_hours': 0,  # One-time use
                'item_type': 'daily_multiplier'
            },
        ]

        # Insert items into database
        async with self.bot.neon_db.pool.acquire() as conn:
            for item in items:
                await conn.execute('''
                    INSERT INTO shop_items (name, description, category, price, duration_hours, item_type)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT DO NOTHING
                ''', item['name'], item['description'], item['category'],
                     item['price'], item['duration_hours'], item['item_type'])

        logger.info("✅ Shop items initialized")

    async def purchase_item(self, member_id: int, guild_id: int, item_id: int):
        """
        Purchase an item from the shop.

        Returns: (success: bool, message: str)
        """
        try:
            async with self.bot.neon_db.pool.acquire() as conn:
                # Get item details
                item = await conn.fetchrow(
                    'SELECT * FROM shop_items WHERE item_id = $1 AND is_active = TRUE',
                    item_id
                )

                if not item:
                    return False, "Item not found or unavailable"

                # Check if member has enough GMP
                member_data = self.bot.member_data.get_member_data(member_id, guild_id)
                if member_data['gmp'] < item['price']:
                    return False, f"Not enough GMP! Need {item['price']}, have {member_data['gmp']}"

                # Deduct GMP
                member_data['gmp'] -= item['price']
                self.bot.member_data.schedule_save()

                # Add to inventory
                expires_at = None
                if item['duration_hours'] and item['duration_hours'] > 0:
                    expires_at = datetime.now() + timedelta(hours=item['duration_hours'])

                await conn.execute('''
                    INSERT INTO member_inventory
                    (member_id, guild_id, item_id, purchased_at, expires_at)
                    VALUES ($1, $2, $3, CURRENT_TIMESTAMP, $4)
                ''', member_id, guild_id, item_id, expires_at)

                logger.info(f"✅ {member_id} purchased {item['name']} for {item['price']} GMP")
                return True, f"Successfully purchased {item['name']}!"

        except Exception as e:
            logger.error(f"Error purchasing item: {e}")
            return False, "Purchase failed - please contact an admin"

    async def activate_booster(self, member_id: int, guild_id: int, item_id: int):
        """Activate a booster from inventory"""
        try:
            async with self.bot.neon_db.pool.acquire() as conn:
                # Get item from inventory
                inventory_item = await conn.fetchrow('''
                    SELECT i.*, s.item_type, s.duration_hours
                    FROM member_inventory i
                    JOIN shop_items s ON i.item_id = s.item_id
                    WHERE i.member_id = $1 AND i.guild_id = $2
                      AND i.item_id = $3 AND i.is_active = FALSE
                    LIMIT 1
                ''', member_id, guild_id, item_id)

                if not inventory_item:
                    return False, "Item not found in inventory or already active"

                # Check if expired
                if inventory_item['expires_at'] and inventory_item['expires_at'] < datetime.now():
                    return False, "Item has expired"

                # Activate booster
                expires_at = datetime.now() + timedelta(hours=inventory_item['duration_hours'])

                await conn.execute('''
                    INSERT INTO active_boosters
                    (member_id, guild_id, booster_type, activated_at, expires_at)
                    VALUES ($1, $2, $3, CURRENT_TIMESTAMP, $4)
                ''', member_id, guild_id, inventory_item['item_type'], expires_at)

                # Mark item as used
                await conn.execute('''
                    UPDATE member_inventory
                    SET is_active = TRUE
                    WHERE inventory_id = $1
                ''', inventory_item['inventory_id'])

                return True, f"Booster activated! Active for {inventory_item['duration_hours']} hours"

        except Exception as e:
            logger.error(f"Error activating booster: {e}")
            return False, "Activation failed"

    async def get_active_multiplier(self, member_id: int, guild_id: int):
        """Get current XP multiplier for member"""
        try:
            async with self.bot.neon_db.pool.acquire() as conn:
                # Check for active XP boosters
                booster = await conn.fetchrow('''
                    SELECT multiplier FROM active_boosters
                    WHERE member_id = $1 AND guild_id = $2
                      AND booster_type LIKE 'xp_boost%'
                      AND expires_at > CURRENT_TIMESTAMP
                    ORDER BY expires_at DESC
                    LIMIT 1
                ''', member_id, guild_id)

                if booster:
                    return float(booster['multiplier'])
                return 1.0  # Default multiplier

        except Exception as e:
            logger.error(f"Error getting multiplier: {e}")
            return 1.0
```

### Admin Testing Commands:

#### File: `src/cogs/admin.py` (ADD)

```python
@commands.command(name='shop_init')
@commands.has_permissions(administrator=True)
async def shop_init(self, ctx):
    """Initialize shop items (Admin only)"""
    if not hasattr(self.bot, 'shop_system'):
        await ctx.send("❌ Shop system not initialized")
        return

    await self.bot.shop_system.initialize_shop_items()
    await ctx.send("✅ Shop items initialized!")

@commands.command(name='shop_test_buy')
@commands.has_permissions(administrator=True)
async def shop_test_buy(self, ctx, item_id: int):
    """Test purchasing an item (Admin only)"""
    success, message = await self.bot.shop_system.purchase_item(
        ctx.author.id, ctx.guild.id, item_id
    )

    if success:
        await ctx.send(f"✅ {message}")
    else:
        await ctx.send(f"❌ {message}")

@commands.command(name='shop_test_activate')
@commands.has_permissions(administrator=True)
async def shop_test_activate(self, ctx, item_id: int):
    """Test activating a booster (Admin only)"""
    success, message = await self.bot.shop_system.activate_booster(
        ctx.author.id, ctx.guild.id, item_id
    )

    await ctx.send(f"{'✅' if success else '❌'} {message}")
```

### Update XP System to Use Multiplier:

#### File: `src/events/message_events.py` (MODIFY)

```python
# In on_message, when awarding XP:
async def on_message(self, message):
    # ... existing code ...

    # Get multiplier if shop system exists
    multiplier = 1.0
    if hasattr(self.bot, 'shop_system'):
        multiplier = await self.bot.shop_system.get_active_multiplier(
            message.author.id, message.guild.id
        )

    # Apply multiplier to XP rewards
    xp_reward = int(ACTIVITY_REWARDS["message"]["xp"] * multiplier)
    gmp_reward = ACTIVITY_REWARDS["message"]["gmp"]  # GMP not affected

    message_rank_changed, message_new_rank = self.bot.member_data.add_xp_and_gmp(
        member_id, guild_id, gmp_reward, xp_reward, "message"
    )

    # ... rest of existing code ...
```

### Testing Phase 3:
```
1. Run !shop_init - creates shop items
2. Run !shop_test_buy 1 - test purchase
3. Check GMP deducted correctly
4. Run !shop_test_activate 1 - test activation
5. Send messages - verify XP boost works
6. Check database - verify records created
```

### Success Criteria:
- ✅ Can purchase items programmatically
- ✅ GMP deducted correctly
- ✅ Items added to inventory
- ✅ Boosters activate and work
- ✅ XP multiplier applied correctly
- ✅ No errors in logs

---

## 🎨 Phase 4: Shop UI & User Commands [1 week]

### Goal: Add user-facing shop interface

### What to Build:

#### User Commands:

```python
/shop - Browse shop with buttons
/shop buy <item> - Purchase item
/inventory - View owned items
/use <item> - Activate booster
```

#### Button-Based Shop UI:

```python
class ShopView(discord.ui.View):
    def __init__(self, bot, user_id, guild_id):
        super().__init__(timeout=180)
        self.bot = bot
        self.user_id = user_id
        self.guild_id = guild_id
        self.current_category = 'booster'

    @discord.ui.button(label="🎲 Boosters", style=discord.ButtonStyle.primary)
    async def boosters_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_category = 'booster'
        await self.update_shop_display(interaction)

    @discord.ui.button(label="🎨 Cosmetics", style=discord.ButtonStyle.secondary)
    async def cosmetics_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_category = 'cosmetic'
        await self.update_shop_display(interaction)

    async def update_shop_display(self, interaction):
        # Fetch items from database
        # Create embed with items
        # Update message
        pass
```

### Testing Phase 4:
```
1. Run /shop - UI appears
2. Click category buttons - categories change
3. Purchase items - confirmation works
4. Check /inventory - items show up
5. Run /use <item> - activation works
6. Verify all edge cases
```

---

## 🎯 Phase 5: Missions System [1.5 weeks]

### Goal: Add daily missions with auto-tracking

### Start Simple:
```
3 Daily Missions:
1. Send 10 messages → 100 GMP + 10 XP
2. Use 3 tactical words → 150 GMP + 15 XP
3. React to 5 messages → 50 GMP + 5 XP
```

### Testing Phase 5:
```
1. Missions reset at midnight
2. Progress tracks automatically
3. Rewards given on completion
4. /missions shows progress
```

---

## 🏆 Phase 6-8: [Later Phases]

Will detail once Phases 1-5 are stable.

---

## ✅ Safety Checklist (Every Phase)

Before deploying each phase:

```
□ All existing commands still work
□ No errors in logs
□ Database backups created
□ Feature can be disabled with flag
□ Rollback plan documented
□ Tested with admin account first
□ Tested with regular user account
□ Edge cases handled
□ Error messages are clear
□ Performance is acceptable
```

---

## 🚨 Emergency Rollback Procedure

If something breaks:

```python
# Step 1: Disable feature
FEATURE_FLAGS['ENABLE_SHOP'] = False  # or whatever broke

# Step 2: Restart bot
# Bot will skip broken feature

# Step 3: Check logs
# Identify the issue

# Step 4: Fix or remove
# Either fix the bug or remove the feature

# Step 5: Restore from backup if needed
!neon_restore  # or restore JSON backup
```

---

## 📅 Recommended Timeline

```
Week 1: Phase 0 + Phase 1 (Foundation + Database)
Week 2-3: Phase 2 (Slash Commands)
Week 4-5: Phase 3 (Shop Backend)
Week 6-7: Phase 4 (Shop UI)
Week 8-9: Phase 5 (Missions)
Week 10+: Phases 6-8 (Polish)
```

**Take your time between phases. Better to go slow and safe than fast and broken!**

---

## 🎯 Next Step: Phase 0

Let's start with Phase 0 right now:

1. Add feature flags system
2. Create backup commands
3. Add version tracking
4. Test current bot stability

**Ready to begin Phase 0?** Let me know and I'll start implementing! 🚀
