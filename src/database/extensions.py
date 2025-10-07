"""
Database extensions for new features.
Separate from member_data to ensure safety - does NOT touch existing tables.
"""
import asyncpg
from datetime import datetime
from config.settings import logger


class DatabaseExtensions:
    """Manages extended database schema for new features"""

    def __init__(self, neon_db):
        self.neon_db = neon_db
        self.initialized = False

    async def init_extended_schema(self):
        """Create new tables if they don't exist (safe - won't affect existing data)"""
        if not self.neon_db or not self.neon_db.pool:
            logger.warning("Neon not connected - skipping database extensions")
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

                self.initialized = True
                logger.info("✅ Extended database schema initialized successfully")
                return True

        except Exception as e:
            logger.error(f"❌ Error creating extended schema: {e}")
            return False

    async def check_table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database"""
        if not self.neon_db or not self.neon_db.pool:
            return False

        try:
            async with self.neon_db.pool.acquire() as conn:
                result = await conn.fetchval('''
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = $1
                    )
                ''', table_name)
                return result
        except Exception as e:
            logger.error(f"Error checking table existence: {e}")
            return False
