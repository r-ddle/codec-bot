"""
Neon PostgreSQL database integration for persistent data storage.
Provides backup and sync functionality between JSON and PostgreSQL.
"""
import os
import asyncio
import json
from typing import Dict, Any, List, Tuple, Optional
import asyncpg
from datetime import datetime
from config.settings import logger


class NeonDatabase:
    """Handles PostgreSQL operations with Neon."""

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize Neon database connection.

        Args:
            database_url: PostgreSQL connection string (from Neon)
        """
        self.database_url = database_url or os.getenv('NEON_DATABASE_URL')
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> bool:
        """
        Establish connection pool to Neon database.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            if not self.database_url:
                logger.warning("⚠️ NEON_DATABASE_URL not set - database features disabled")
                return False

            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=1,
                max_size=10,
                command_timeout=60
            )

            # Initialize database schema
            await self.init_schema()
            logger.info("✅ Connected to Neon PostgreSQL database")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to connect to Neon database: {e}")
            return False

    async def close(self):
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("🔌 Neon database connection closed")

    async def init_schema(self):
        """Create database tables if they don't exist."""
        async with self.pool.acquire() as conn:
            # Member data table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS member_data (
                    member_id BIGINT NOT NULL,
                    guild_id BIGINT NOT NULL,
                    gmp INTEGER DEFAULT 1000,
                    xp INTEGER DEFAULT 0,
                    rank VARCHAR(50) DEFAULT 'Rookie',
                    rank_icon VARCHAR(10) DEFAULT '🎖️',
                    messages_sent INTEGER DEFAULT 0,
                    voice_minutes INTEGER DEFAULT 0,
                    reactions_given INTEGER DEFAULT 0,
                    reactions_received INTEGER DEFAULT 0,
                    tactical_words_used INTEGER DEFAULT 0,
                    total_tactical_words INTEGER DEFAULT 0,
                    last_daily DATE,
                    daily_streak INTEGER DEFAULT 0,
                    last_message_time DOUBLE PRECISION DEFAULT 0,
                    last_tactical_bonus DOUBLE PRECISION DEFAULT 0,
                    verified BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (member_id, guild_id)
                )
            ''')

            # Add daily_streak column if it doesn't exist (migration)
            try:
                await conn.execute('''
                    ALTER TABLE member_data
                    ADD COLUMN IF NOT EXISTS daily_streak INTEGER DEFAULT 0
                ''')
            except Exception as e:
                logger.warning(f"Could not add daily_streak column (may already exist): {e}")

            # Create indexes for better query performance
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_member_xp ON member_data(guild_id, xp DESC)
            ''')
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_member_gmp ON member_data(guild_id, gmp DESC)
            ''')

            # Backup history table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS backup_history (
                    backup_id SERIAL PRIMARY KEY,
                    backup_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    member_count INTEGER,
                    guild_count INTEGER,
                    backup_type VARCHAR(50),
                    status VARCHAR(50)
                )
            ''')

            logger.info("📊 Database schema initialized")

    async def sync_member_data(self, member_id: int, guild_id: int, data: Dict[str, Any]):
        """
        Sync member data to Neon database.

        Args:
            member_id: Discord member ID
            guild_id: Discord guild ID
            data: Member data dictionary
        """
        if not self.pool:
            return

        try:
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO member_data (
                        member_id, guild_id, gmp, xp, rank, rank_icon,
                        messages_sent, voice_minutes, reactions_given, reactions_received,
                        tactical_words_used, total_tactical_words,
                        last_daily, daily_streak, last_message_time, last_tactical_bonus, verified,
                        updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, CURRENT_TIMESTAMP)
                    ON CONFLICT (member_id, guild_id)
                    DO UPDATE SET
                        gmp = EXCLUDED.gmp,
                        xp = EXCLUDED.xp,
                        rank = EXCLUDED.rank,
                        rank_icon = EXCLUDED.rank_icon,
                        messages_sent = EXCLUDED.messages_sent,
                        voice_minutes = EXCLUDED.voice_minutes,
                        reactions_given = EXCLUDED.reactions_given,
                        reactions_received = EXCLUDED.reactions_received,
                        tactical_words_used = EXCLUDED.tactical_words_used,
                        total_tactical_words = EXCLUDED.total_tactical_words,
                        last_daily = EXCLUDED.last_daily,
                        daily_streak = EXCLUDED.daily_streak,
                        last_message_time = EXCLUDED.last_message_time,
                        last_tactical_bonus = EXCLUDED.last_tactical_bonus,
                        verified = EXCLUDED.verified,
                        updated_at = CURRENT_TIMESTAMP
                ''',
                    member_id, guild_id,
                    data.get('gmp', 1000),
                    data.get('xp', 0),
                    data.get('rank', 'Rookie'),
                    data.get('rank_icon', '🎖️'),
                    data.get('messages_sent', 0),
                    data.get('voice_minutes', 0),
                    data.get('reactions_given', 0),
                    data.get('reactions_received', 0),
                    data.get('tactical_words_used', 0),
                    data.get('total_tactical_words', 0),
                    self._parse_date(data.get('last_daily')),
                    data.get('daily_streak', 0),
                    data.get('last_message_time', 0),
                    data.get('last_tactical_bonus', 0),
                    data.get('verified', False)
                )

        except Exception as e:
            logger.error(f"Error syncing member data to Neon: {e}")

    def _parse_date(self, date_value):
        """
        Parse date string to date object for PostgreSQL.

        Args:
            date_value: Date string in format 'YYYY-MM-DD' or None

        Returns:
            datetime.date object or None
        """
        if date_value is None:
            return None

        if isinstance(date_value, str):
            try:
                from datetime import datetime
                return datetime.strptime(date_value, '%Y-%m-%d').date()
            except (ValueError, AttributeError):
                return None

        return date_value

    async def backup_all_data(self, json_data: Dict[str, Dict[str, Any]], target_guild_id: Optional[int] = None, recalculate_ranks: bool = False) -> bool:
        """
        Backup all member data from JSON to Neon.

        Args:
            json_data: Complete member data dictionary
            target_guild_id: If specified, only backup data for this guild
            recalculate_ranks: If True, recalculate all ranks based on XP before syncing

        Returns:
            True if backup successful
        """
        if not self.pool:
            logger.warning("Neon database not connected - skipping backup")
            return False

        try:
            # Filter data to only the target guild if specified
            if target_guild_id:
                target_guild_str = str(target_guild_id)
                if target_guild_str in json_data:
                    filtered_data = {target_guild_str: json_data[target_guild_str]}
                else:
                    logger.warning(f"Target guild {target_guild_id} not found in data - skipping backup")
                    return False
            else:
                filtered_data = json_data

            total_members = 0
            guild_count = len(filtered_data)
            # Import here to avoid circular dependency
            if recalculate_ranks:
                from utils.rank_system import calculate_rank_from_xp
                logger.info("🔄 Recalculating ranks based on XP...")

            for guild_id, members in filtered_data.items():
                for member_id, data in members.items():
                    # Recalculate rank if requested
                    if recalculate_ranks:
                        correct_rank, correct_icon = calculate_rank_from_xp(data.get('xp', 0))
                        data['rank'] = correct_rank
                        data['rank_icon'] = correct_icon

                    await self.sync_member_data(int(member_id), int(guild_id), data)
                    total_members += 1

            # Record backup history
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO backup_history (member_count, guild_count, backup_type, status)
                    VALUES ($1, $2, $3, $4)
                ''', total_members, guild_count, 'guild_backup' if target_guild_id else 'full_backup' if not recalculate_ranks else 'full_backup_with_rank_fix', 'success')

            if target_guild_id:
                logger.info(f"✅ Backed up {total_members} members from guild {target_guild_id} to Neon")
            else:
                logger.info(f"✅ Backed up {total_members} members from {guild_count} guild(s) to Neon")
            if recalculate_ranks:
                logger.info("✅ All ranks recalculated and synced")
            return True

        except Exception as e:
            logger.error(f"❌ Error backing up data to Neon: {e}")
            return False

    async def restore_member_data(self, member_id: int, guild_id: int) -> Optional[Dict[str, Any]]:
        """
        Restore member data from Neon database.

        Args:
            member_id: Discord member ID
            guild_id: Discord guild ID

        Returns:
            Member data dictionary or None
        """
        if not self.pool:
            return None

        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow('''
                    SELECT * FROM member_data
                    WHERE member_id = $1 AND guild_id = $2
                ''', member_id, guild_id)

                if row:
                    return {
                        'gmp': row['gmp'],
                        'xp': row['xp'],
                        'rank': row['rank'],
                        'rank_icon': row['rank_icon'],
                        'messages_sent': row['messages_sent'],
                        'voice_minutes': row['voice_minutes'],
                        'reactions_given': row['reactions_given'],
                        'reactions_received': row['reactions_received'],
                        'tactical_words_used': row['tactical_words_used'],
                        'total_tactical_words': row['total_tactical_words'],
                        'last_daily': row['last_daily'].isoformat() if row['last_daily'] else None,
                        'daily_streak': row.get('daily_streak', 0),
                        'last_message_time': row['last_message_time'],
                        'last_tactical_bonus': row['last_tactical_bonus'],
                        'verified': row['verified']
                    }

        except Exception as e:
            logger.error(f"Error restoring member data from Neon: {e}")

        return None

    async def get_leaderboard(self, guild_id: int, sort_by: str = 'xp', limit: int = 10) -> List[Tuple[int, Dict[str, Any]]]:
        """
        Get leaderboard from database.

        Args:
            guild_id: Discord guild ID
            sort_by: Field to sort by
            limit: Maximum results

        Returns:
            List of (member_id, data) tuples
        """
        if not self.pool:
            return []

        valid_columns = ['xp', 'gmp', 'messages_sent', 'tactical_words_used', 'total_tactical_words']
        if sort_by not in valid_columns:
            sort_by = 'xp'

        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(f'''
                    SELECT * FROM member_data
                    WHERE guild_id = $1 AND (messages_sent > 0 OR xp > 0)
                    ORDER BY {sort_by} DESC
                    LIMIT $2
                ''', guild_id, limit)

                results = []
                for row in rows:
                    data = {
                        'gmp': row['gmp'],
                        'xp': row['xp'],
                        'rank': row['rank'],
                        'rank_icon': row['rank_icon'],
                        'messages_sent': row['messages_sent'],
                        'voice_minutes': row['voice_minutes'],
                        'reactions_given': row['reactions_given'],
                        'reactions_received': row['reactions_received'],
                        'tactical_words_used': row['tactical_words_used'],
                        'total_tactical_words': row['total_tactical_words'],
                    }
                    results.append((row['member_id'], data))

                return results

        except Exception as e:
            logger.error(f"Error getting leaderboard from Neon: {e}")
            return []

    async def get_backup_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent backup history.

        Args:
            limit: Maximum number of records

        Returns:
            List of backup records
        """
        if not self.pool:
            return []

        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch('''
                    SELECT * FROM backup_history
                    ORDER BY backup_date DESC
                    LIMIT $1
                ''', limit)

                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Error getting backup history: {e}")
            return []

    async def cleanup_other_guilds(self, target_guild_id: int) -> bool:
        """
        Remove all member data from guilds other than the target guild.

        Args:
            target_guild_id: The guild ID to keep data for

        Returns:
            True if cleanup successful
        """
        if not self.pool:
            logger.warning("Neon database not connected - cannot cleanup")
            return False

        try:
            async with self.pool.acquire() as conn:
                # Get count of members to be deleted
                count_result = await conn.fetchval('''
                    SELECT COUNT(*) FROM member_data
                    WHERE guild_id != $1
                ''', target_guild_id)

                if count_result == 0:
                    logger.info(f"✅ No other guild data found to cleanup")
                    return True

                # Delete data from other guilds
                await conn.execute('''
                    DELETE FROM member_data
                    WHERE guild_id != $1
                ''', target_guild_id)

                logger.info(f"🧹 Cleaned up {count_result} members from other guilds, keeping only guild {target_guild_id}")
                return True

        except Exception as e:
            logger.error(f"❌ Error cleaning up other guild data: {e}")
            return False

    async def load_all_member_data(self, target_guild_id: Optional[int] = None) -> Dict[str, Dict[str, Any]]:
        """
        Load all member data from Neon database.

        Args:
            target_guild_id: If specified, only load data for this guild. If None, load all guilds.

        Returns:
            Dictionary with guild_id -> {member_id -> data} structure
        """
        if not self.pool:
            logger.warning("Neon database not connected - cannot load data")
            return {}

        try:
            async with self.pool.acquire() as conn:
                if target_guild_id:
                    # Only load data for the specific guild
                    rows = await conn.fetch('''
                        SELECT * FROM member_data
                        WHERE guild_id = $1
                        ORDER BY member_id
                    ''', target_guild_id)
                else:
                    # Load all guilds (legacy behavior)
                    rows = await conn.fetch('''
                        SELECT * FROM member_data
                        ORDER BY guild_id, member_id
                    ''')

                data = {}
                for row in rows:
                    guild_id = str(row['guild_id'])
                    member_id = str(row['member_id'])

                    if guild_id not in data:
                        data[guild_id] = {}

                    # Convert database row to member data format
                    member_data = {
                        'gmp': row['gmp'],
                        'xp': row['xp'],
                        'rank': row['rank'],
                        'rank_icon': row['rank_icon'],
                        'messages_sent': row['messages_sent'],
                        'voice_minutes': row['voice_minutes'],
                        'reactions_given': row['reactions_given'],
                        'reactions_received': row['reactions_received'],
                        'tactical_words_used': row['tactical_words_used'],
                        'total_tactical_words': row['total_tactical_words'],
                        'last_daily': row['last_daily'].isoformat() if row['last_daily'] else None,
                        'daily_streak': row['daily_streak'],
                        'last_message_time': row['last_message_time'],
                        'last_tactical_bonus': row['last_tactical_bonus'],
                        'verified': row['verified']
                    }

                    data[guild_id][member_id] = member_data

                total_members = sum(len(members) for members in data.values())
                guild_count = len(data)
                if target_guild_id:
                    logger.info(f"📥 Loaded {total_members} members from guild {target_guild_id} from Neon database")
                else:
                    logger.info(f"📥 Loaded {total_members} members from {guild_count} guild(s) from Neon database")
                return data

        except Exception as e:
            logger.error(f"Error loading member data from Neon: {e}")
            return {}
