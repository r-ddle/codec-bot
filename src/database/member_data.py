"""
Member data management and persistence layer.
Handles loading, saving, and updating member progression data.
                # Backward compatibility: add daily_streak if missing
            if "daily_streak" not in existing_data:
                existing_data["daily_streak"] = 0

            # Add join date for legacy progression if missing
            if "join_date" not in existing_data:
                from datetime import datetime
                # Default to today for new check, but existing users get legacy status
                existing_data["join_date"] = datetime.now().strftime('%Y-%m-%d')

            return existing_datamport os
import json
import asyncio
import shutil
import time
from typing import Dict, Any, List, Tuple, Optional
from config.settings import DATABASE_FILE, logger
from config.constants import ACTIVITY_REWARDS
from utils.rank_system import calculate_rank_from_xp


class MemberData:
    """Handles all member data storage and progression."""

    def __init__(self, neon_db=None):
        self.data: Dict[str, Dict[str, Any]] = self.load_data()
        self._save_lock = asyncio.Lock()
        self._pending_saves = False
        self.neon_db = neon_db  # Neon database instance
        logger.info(f"💾 Loaded data for {len(self.data)} guild(s)")

    def load_data(self) -> Dict[str, Dict[str, Any]]:
        """Load data from JSON file."""
        try:
            if os.path.exists(DATABASE_FILE):
                with open(DATABASE_FILE, 'r') as f:
                    raw_data = json.load(f)

                if not raw_data:
                    logger.info("Empty database file found, starting fresh")
                    return {}

                if isinstance(raw_data, dict):
                    guild_like_keys = [k for k in raw_data.keys() if k.isdigit() and len(k) > 10]

                    if guild_like_keys:
                        logger.info(f"Found existing guild data for {len(guild_like_keys)} guild(s)")
                        return raw_data
                    else:
                        logger.info("No valid guild data found in file")
                        return {}
                else:
                    logger.warning("Invalid data format in database file")
                    return {}
            else:
                logger.info("No database file found, starting fresh")
                return {}

        except Exception as e:
            logger.error(f"Error loading member data: {e}")
            return {}

    async def save_data_async(self, force: bool = False) -> None:
        """Save data with atomic write operation and sync to Neon."""
        async with self._save_lock:
            try:
                # Save to JSON first (local backup)
                if os.path.exists(DATABASE_FILE):
                    backup_file = f"{DATABASE_FILE}.backup"
                    shutil.copy2(DATABASE_FILE, backup_file)

                temp_file = f"{DATABASE_FILE}.tmp"
                with open(temp_file, 'w') as f:
                    json.dump(self.data, f, indent=2)

                os.replace(temp_file, DATABASE_FILE)
                self._pending_saves = False
                logger.info("💾 Member data saved to JSON successfully")

                # Sync to Neon database if available
                if self.neon_db and self.neon_db.pool:
                    await self.neon_db.backup_all_data(self.data)

            except Exception as e:
                logger.error(f"❌ Error saving member data: {e}")
                if os.path.exists(f"{DATABASE_FILE}.tmp"):
                    os.remove(f"{DATABASE_FILE}.tmp")

    def schedule_save(self) -> None:
        """Schedule a data save operation."""
        self._pending_saves = True

    def get_member_data(self, member_id: int, guild_id: int) -> Dict[str, Any]:
        """
        Get member data for specific guild.

        Args:
            member_id: Discord member ID
            guild_id: Discord guild ID

        Returns:
            Member data dictionary
        """
        guild_key = str(guild_id)
        member_key = str(member_id)

        # Ensure guild exists in data
        if guild_key not in self.data:
            self.data[guild_key] = {}
            logger.info(f"Created new guild data for {guild_key}")

        # Check if member exists
        if member_key in self.data[guild_key]:
            existing_data = self.data[guild_key][member_key]
            # Ensure rank matches XP
            correct_rank, correct_icon = calculate_rank_from_xp(existing_data.get("xp", 0))
            existing_data["rank"] = correct_rank
            existing_data["rank_icon"] = correct_icon

            # Backward compatibility: add daily_streak if missing
            if "daily_streak" not in existing_data:
                existing_data["daily_streak"] = 0

            return existing_data
        else:
            # New member, create default data
            from datetime import datetime
            default_member = {
                "gmp": 1000,
                "xp": 0,
                "rank": "Rookie",
                "rank_icon": "🎖️",
                "messages_sent": 0,
                "voice_minutes": 0,
                "reactions_given": 0,
                "reactions_received": 0,
                "last_daily": None,
                "daily_streak": 0,
                "tactical_words_used": 0,
                "verified": False,
                "total_tactical_words": 0,
                "last_message_time": 0,
                "last_tactical_bonus": 0,
                "join_date": datetime.now().strftime('%Y-%m-%d')
            }

            self.data[guild_key][member_key] = default_member.copy()
            self.schedule_save()
            logger.info(f"Created new member {member_key} in guild {guild_key}")
            return self.data[guild_key][member_key]

    def add_xp_and_gmp(
        self,
        member_id: int,
        guild_id: int,
        gmp_change: int,
        xp_change: int,
        activity_type: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Add XP and GMP to member and check for rank changes.

        Args:
            member_id: Discord member ID
            guild_id: Discord guild ID
            gmp_change: Amount of GMP to add
            xp_change: Amount of XP to add
            activity_type: Type of activity (for tracking stats)

        Returns:
            Tuple of (rank_changed, new_rank)
        """
        member_data = self.get_member_data(member_id, guild_id)

        # Store old values
        old_rank = member_data["rank"]
        old_xp = member_data["xp"]

        # Update stats based on activity type
        if activity_type:
            if activity_type == "message":
                member_data["messages_sent"] += 1
            elif activity_type == "voice_minute":
                member_data["voice_minutes"] += 1
            elif activity_type == "reaction":
                member_data["reactions_given"] += 1
            elif activity_type == "reaction_received":
                member_data["reactions_received"] += 1
            elif activity_type == "tactical_word":
                member_data["tactical_words_used"] += 1
                member_data["total_tactical_words"] += 1
                member_data["last_tactical_bonus"] = time.time()

        # Add GMP and XP
        member_data["gmp"] += gmp_change
        member_data["xp"] += xp_change

        # Recalculate rank based on new XP
        new_rank, new_icon = calculate_rank_from_xp(member_data["xp"])
        member_data["rank"] = new_rank
        member_data["rank_icon"] = new_icon

        # Schedule save
        self.schedule_save()

        # Log the change
        logger.debug(f"Member {member_id}: +{xp_change} XP ({old_xp} -> {member_data['xp']}), Rank: {old_rank} -> {new_rank}")

        # Return whether rank changed
        return old_rank != new_rank, new_rank

    def award_daily_bonus(self, member_id: int, guild_id: int) -> Tuple[bool, int, int, bool, Optional[str]]:
        """
        Award daily bonus to member.

        Args:
            member_id: Discord member ID
            guild_id: Discord guild ID

        Returns:
            Tuple of (success, gmp_bonus, xp_bonus, rank_changed, new_rank)
        """
        from datetime import datetime, timedelta, timezone

        member_data = self.get_member_data(member_id, guild_id)
        # Use UTC to avoid timezone issues
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        last_daily = member_data.get("last_daily")

        if last_daily != today:
            # Check if streak continues (claimed yesterday)
            if last_daily:
                last_daily_date = datetime.strptime(last_daily, '%Y-%m-%d')
                today_date = datetime.strptime(today, '%Y-%m-%d')
                days_diff = (today_date - last_daily_date).days

                if days_diff == 1:
                    # Streak continues!
                    member_data["daily_streak"] = member_data.get("daily_streak", 0) + 1
                elif days_diff > 1:
                    # Streak broken, reset to 1
                    member_data["daily_streak"] = 1
                else:
                    # Same day (shouldn't happen, but just in case)
                    pass
            else:
                # First time claiming or no previous data
                member_data["daily_streak"] = 1

            member_data["last_daily"] = today

            gmp_bonus = ACTIVITY_REWARDS["daily_bonus"]["gmp"]
            xp_bonus = ACTIVITY_REWARDS["daily_bonus"]["xp"]

            rank_changed, new_rank = self.add_xp_and_gmp(
                member_id, guild_id, gmp_bonus, xp_bonus
            )

            # Schedule immediate save to ensure streak is persisted
            self.schedule_save()

            return True, gmp_bonus, xp_bonus, rank_changed, new_rank

        return False, 0, 0, False, None

    def get_leaderboard(self, guild_id: int, sort_by: str = "xp", limit: int = 10) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Get leaderboard for specific guild.

        Args:
            guild_id: Discord guild ID
            sort_by: Field to sort by
            limit: Maximum number of results

        Returns:
            List of (member_id, member_data) tuples
        """
        guild_key = str(guild_id)

        if guild_key not in self.data:
            return []

        valid_sort_options = ["gmp", "xp", "tactical_words_used", "messages_sent", "total_tactical_words"]
        if sort_by not in valid_sort_options:
            sort_by = "xp"

        active_members = {k: v for k, v in self.data[guild_key].items()
                         if v.get('messages_sent', 0) > 0 or v.get('xp', 0) > 0}

        sorted_members = sorted(
            active_members.items(),
            key=lambda x: x[1].get(sort_by, 0),
            reverse=True
        )

        return sorted_members[:limit]

    def mark_member_verified(self, member_id: int, guild_id: int) -> None:
        """Mark member as verified."""
        member_data = self.get_member_data(member_id, guild_id)
        member_data["verified"] = True
        self.schedule_save()
