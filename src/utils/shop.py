"""
Shop system backend - purchase logic and inventory management.
This module handles GMP shop items, purchases, inventory, and boosters.
"""
from datetime import datetime, timedelta
from config.settings import logger, FEATURE_FLAGS


class ShopSystem:
    """Manages the GMP shop, purchases, inventory, and active boosters."""

    def __init__(self, bot):
        self.bot = bot
        self.initialized = False

    async def initialize_shop_items(self):
        """
        Populate shop with initial items from config.
        Only runs if shop tables exist and shop is enabled.
        """
        if not FEATURE_FLAGS.get('ENABLE_SHOP', False):
            logger.info("Shop system disabled via feature flag")
            return False

        if not self.bot.neon_db or not self.bot.neon_db.pool:
            logger.warning("Cannot initialize shop - Neon database not connected")
            return False

        if not self.bot.db_extensions.initialized:
            logger.warning("Cannot initialize shop - database extensions not initialized")
            return False

        try:
            # Import shop items from config
            from config.shop_config import SHOP_ITEMS

            items = SHOP_ITEMS            # Insert items into database
            async with self.bot.neon_db.pool.acquire() as conn:
                for item in items:
                    # Check if item already exists
                    exists = await conn.fetchval(
                        'SELECT EXISTS(SELECT 1 FROM shop_items WHERE item_type = $1)',
                        item['item_type']
                    )

                    if not exists:
                        await conn.execute('''
                            INSERT INTO shop_items (name, description, category, price, duration_hours, item_type)
                            VALUES ($1, $2, $3, $4, $5, $6)
                        ''', item['name'], item['description'], item['category'],
                             item['price'], item['duration_hours'], item['item_type'])

            self.initialized = True
            logger.info("✅ Shop items initialized successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Error initializing shop items: {e}")
            return False

    async def get_shop_items(self, category: str = None):
        """
        Get all available shop items, optionally filtered by category.

        Returns: List of item dictionaries
        """
        if not FEATURE_FLAGS.get('ENABLE_SHOP', False):
            return []

        if not self.bot.neon_db or not self.bot.neon_db.pool:
            return []

        try:
            async with self.bot.neon_db.pool.acquire() as conn:
                if category:
                    items = await conn.fetch('''
                        SELECT * FROM shop_items
                        WHERE is_active = TRUE AND category = $1
                        ORDER BY price ASC
                    ''', category)
                else:
                    items = await conn.fetch('''
                        SELECT * FROM shop_items
                        WHERE is_active = TRUE
                        ORDER BY category, price ASC
                    ''')

                return [dict(item) for item in items]

        except Exception as e:
            logger.error(f"Error fetching shop items: {e}")
            return []

    async def purchase_item(self, member_id: int, guild_id: int, item_id: int):
        """
        Purchase an item from the shop.

        Args:
            member_id: Discord member ID
            guild_id: Discord guild ID
            item_id: Shop item ID to purchase

        Returns: (success: bool, message: str, item_data: dict or None)
        """
        if not FEATURE_FLAGS.get('ENABLE_SHOP', False):
            return False, "Shop system is currently disabled", None

        if not self.bot.neon_db or not self.bot.neon_db.pool:
            return False, "Shop database not available", None

        try:
            async with self.bot.neon_db.pool.acquire() as conn:
                # Get item details
                item = await conn.fetchrow(
                    'SELECT * FROM shop_items WHERE item_id = $1 AND is_active = TRUE',
                    item_id
                )

                if not item:
                    return False, "Item not found or unavailable", None

                # Check if member has enough GMP
                member_data = self.bot.member_data.get_member_data(member_id, guild_id)
                if member_data['gmp'] < item['price']:
                    return False, f"Not enough GMP! Need **{item['price']}**, have **{member_data['gmp']}**", None

                # Deduct GMP (modify local data)
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

                logger.info(f"✅ Member {member_id} purchased {item['name']} for {item['price']} GMP")
                return True, f"Successfully purchased **{item['name']}**! Check `/inventory` to use it.", dict(item)

        except Exception as e:
            logger.error(f"Error purchasing item: {e}")
            return False, "Purchase failed - please contact an admin", None

    async def get_member_inventory(self, member_id: int, guild_id: int):
        """
        Get all items in a member's inventory.

        Returns: List of inventory items with details
        """
        if not FEATURE_FLAGS.get('ENABLE_SHOP', False):
            return []

        if not self.bot.neon_db or not self.bot.neon_db.pool:
            return []

        try:
            async with self.bot.neon_db.pool.acquire() as conn:
                items = await conn.fetch('''
                    SELECT i.*, s.name, s.description, s.item_type, s.duration_hours
                    FROM member_inventory i
                    JOIN shop_items s ON i.item_id = s.item_id
                    WHERE i.member_id = $1 AND i.guild_id = $2
                    ORDER BY i.purchased_at DESC
                ''', member_id, guild_id)

                return [dict(item) for item in items]

        except Exception as e:
            logger.error(f"Error fetching inventory: {e}")
            return []

    async def activate_booster(self, member_id: int, guild_id: int, inventory_id: int):
        """
        Activate a booster from inventory.

        Returns: (success: bool, message: str)
        """
        if not FEATURE_FLAGS.get('ENABLE_XP_BOOSTERS', False):
            return False, "XP boosters are currently disabled"

        if not self.bot.neon_db or not self.bot.neon_db.pool:
            return False, "Shop database not available"

        try:
            async with self.bot.neon_db.pool.acquire() as conn:
                # Get item from inventory
                inventory_item = await conn.fetchrow('''
                    SELECT i.*, s.item_type, s.duration_hours, s.name
                    FROM member_inventory i
                    JOIN shop_items s ON i.item_id = s.item_id
                    WHERE i.inventory_id = $1
                      AND i.member_id = $2
                      AND i.guild_id = $3
                      AND i.is_active = FALSE
                ''', inventory_id, member_id, guild_id)

                if not inventory_item:
                    return False, "Item not found in inventory or already active"

                # Check if expired
                if inventory_item['expires_at'] and inventory_item['expires_at'] < datetime.now():
                    return False, "Item has expired"

                # Check if member already has an active booster of this type
                existing = await conn.fetchval('''
                    SELECT EXISTS(
                        SELECT 1 FROM active_boosters
                        WHERE member_id = $1 AND guild_id = $2
                          AND booster_type = $3
                          AND expires_at > CURRENT_TIMESTAMP
                    )
                ''', member_id, guild_id, inventory_item['item_type'])

                if existing:
                    return False, f"You already have an active **{inventory_item['name']}**!"

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
                ''', inventory_id)

                hours = inventory_item['duration_hours']
                duration_text = f"{hours} hour{'s' if hours != 1 else ''}" if hours < 24 else f"{hours // 24} day{'s' if hours > 24 else ''}"

                logger.info(f"✅ Member {member_id} activated {inventory_item['name']}")
                return True, f"**{inventory_item['name']}** activated! Active for {duration_text} 🚀"

        except Exception as e:
            logger.error(f"Error activating booster: {e}")
            return False, "Activation failed - please contact an admin"

    async def get_active_multiplier(self, member_id: int, guild_id: int):
        """
        Get current XP multiplier for member based on active boosters.

        Returns: float (1.0 = no boost, 2.0 = 2x boost, etc.)
        """
        if not FEATURE_FLAGS.get('ENABLE_XP_BOOSTERS', False):
            return 1.0

        if not self.bot.neon_db or not self.bot.neon_db.pool:
            return 1.0

        try:
            async with self.bot.neon_db.pool.acquire() as conn:
                # Check for active XP boosters (get highest multiplier if multiple)
                booster = await conn.fetchrow('''
                    SELECT multiplier FROM active_boosters
                    WHERE member_id = $1 AND guild_id = $2
                      AND booster_type LIKE 'xp_boost%'
                      AND expires_at > CURRENT_TIMESTAMP
                    ORDER BY multiplier DESC, expires_at DESC
                    LIMIT 1
                ''', member_id, guild_id)

                if booster:
                    return float(booster['multiplier'])
                return 1.0

        except Exception as e:
            logger.error(f"Error getting multiplier: {e}")
            return 1.0

    async def cleanup_expired_boosters(self):
        """Remove expired boosters from the database (periodic cleanup)."""
        if not self.bot.neon_db or not self.bot.neon_db.pool:
            return

        try:
            async with self.bot.neon_db.pool.acquire() as conn:
                result = await conn.execute('''
                    DELETE FROM active_boosters
                    WHERE expires_at < CURRENT_TIMESTAMP
                ''')

                if result != 'DELETE 0':
                    logger.info(f"Cleaned up expired boosters: {result}")

        except Exception as e:
            logger.error(f"Error cleaning up boosters: {e}")
