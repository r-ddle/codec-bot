import os
import json
import asyncio
import shutil
import time
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta
from config.settings import DATABASE_FILE, logger, NEON_SYNC_INTERVAL_MINUTES
from config.constants import ACTIVITY_REWARDS, DEFAULT_MEMBER_DATA, RANK_XP_MULTIPLIERS, STREAK_XP_BONUSES
from utils.rank_system import calculate_rank_from_xp


class MemberData:
    """Handles all member data storage and progression."""

    def __init__(self, neon_db=None):
        self.neon_db = neon_db  # Neon database instance - set this first
        self.data: Dict[str, Dict[str, Any]] = self.load_data()
        self._save_lock = asyncio.Lock()
        self._pending_saves = False
        # Track last time we synced to Neon to avoid too many requests
        self._last_neon_sync = 0.0

        # Don't set _needs_db_load here - it will be determined in setup_hook
        self._needs_db_load = False

        if self.data:
            logger.info(f"💾 Loaded data for {len(self.data)} guild(s)")

    def load_data(self) -> Dict[str, Dict[str, Any]]:
        """Load data from JSON file or Neon database if JSON doesn't exist."""
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
                # JSON file doesn't exist, try loading from Neon database
                logger.info("No local JSON file found, attempting to load from Neon database...")
                if self.neon_db and self.neon_db.pool:
                    try:
                        # This needs to be run in an event loop, but for now we'll handle it in __init__
                        logger.info("Database available - will load data from Neon in __init__")
                        return {}  # Return empty dict, will be populated in __init__
                    except Exception as e:
                        logger.error(f"Failed to load from Neon database: {e}")
                        return {}
                else:
                    logger.info("No database file found and Neon not available, starting fresh")
                    return {}

        except Exception as e:
            logger.error(f"Error loading member data: {e}")
            return {}

    async def load_from_database(self, target_guild_id: int = 1423506532745875560) -> None:
        """Load member data from Neon database for a specific guild."""
        if not self.neon_db or not self.neon_db.pool:
            logger.warning("Cannot load from database: Neon database not available")
            return

        try:
            self.data = await self.neon_db.load_all_member_data(target_guild_id=target_guild_id)
            self._needs_db_load = False
            logger.info(f"✅ Loaded data for {len(self.data)} guild(s) from Neon database")
        except Exception as e:
            logger.error(f"Failed to load data from database: {e}")
            self.data = {}
            self._needs_db_load = False

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

                # Sync to Neon database if available, but throttle by NEON_SYNC_INTERVAL_MINUTES
                now = time.time()
                minutes_since_last = (now - getattr(self, '_last_neon_sync', 0)) / 60.0

                if self.neon_db and self.neon_db.pool:
                    if force or minutes_since_last >= NEON_SYNC_INTERVAL_MINUTES:
                        # Only backup data for our specific guild
                        await self.neon_db.backup_all_data(self.data, target_guild_id=1423506532745875560)
                        self._last_neon_sync = now
                    else:
                        logger.debug(f"Skipping Neon sync (only {minutes_since_last:.1f}m since last). Will sync later.")

            except Exception as e:
                logger.error(f"❌ Error saving member data: {e}")
                if os.path.exists(f"{DATABASE_FILE}.tmp"):
                    os.remove(f"{DATABASE_FILE}.tmp")

    def schedule_save(self) -> None:
        """Schedule a data save operation."""
        self._pending_saves = True

    async def purge_non_members(self, guild) -> int:
        """
        Remove members who left the server from the database.

        Args:
            guild: Discord guild object

        Returns:
            Number of members purged
        """
        guild_key = str(guild.id)

        if guild_key not in self.data:
            logger.info(f"No data found for guild {guild_key}")
            return 0

        guild_data = self.data[guild_key]
        members_to_remove = []

        # Check each member in database
        for member_id_str in guild_data.keys():
            try:
                member_id = int(member_id_str)
                # Check if member still exists in guild
                if not guild.get_member(member_id):
                    members_to_remove.append(member_id_str)
            except (ValueError, AttributeError):
                continue

        # Remove members who left
        purged_count = 0
        for member_id_str in members_to_remove:
            del guild_data[member_id_str]
            purged_count += 1

        if purged_count > 0:
            logger.info(f"🧹 Purged {purged_count} members who left from guild {guild_key}")
            # Save after purging
            await self.save_data_async(force=True)
        else:
            logger.info(f"✅ No members to purge from guild {guild_key}")

        return purged_count

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
            # New member, create default data (from constants - single source of truth)
            default_member = DEFAULT_MEMBER_DATA.copy()
            # Update join_date to current date
            default_member["join_date"] = datetime.now().strftime('%Y-%m-%d')

            self.data[guild_key][member_key] = default_member
            self.schedule_save()
            logger.info(f"Created new member {member_key} in guild {guild_key}")
            return self.data[guild_key][member_key]

    def add_xp(
        self,
        member_id: int,
        guild_id: int,
        xp_change: int,
        activity_type: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Add XP to member and check for rank changes.

        Args:
            member_id: Discord member ID
            guild_id: Discord guild ID
            xp_change: Amount of XP to add
            activity_type: Type of activity (for tracking stats)

        Returns:
            Tuple of (rank_changed, new_rank)
        """
        member_data = self.get_member_data(member_id, guild_id)

        # Store old values
        old_rank = member_data["rank"]
        old_xp = member_data["xp"]

        # Apply rank-based XP multiplier
        multiplier = RANK_XP_MULTIPLIERS.get(old_rank, 1.0)
        xp_change = int(xp_change * multiplier)

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

        # Add XP
        member_data["xp"] += xp_change

        # Recalculate rank based on new XP
        new_rank, new_icon = calculate_rank_from_xp(member_data["xp"])
        member_data["rank"] = new_rank
        member_data["rank_icon"] = new_icon

        # Schedule save
        self.schedule_save()

        # Log the change
        logger.debug(f"Member {member_id}: +{xp_change} XP ({old_xp} -> {member_data['xp']}) [x{multiplier}], Rank: {old_rank} -> {new_rank}")

        # Return whether rank changed
        return old_rank != new_rank, new_rank

    def award_daily_bonus(self, member_id: int, guild_id: int) -> Tuple[bool, int, bool, Optional[str]]:
        """
        Award daily bonus to member.

        Args:
            member_id: Discord member ID
            guild_id: Discord guild ID

        Returns:
            Tuple of (success, xp_bonus, rank_changed, new_rank)
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

            xp_bonus = ACTIVITY_REWARDS["daily_bonus"]["xp"]

            rank_changed, new_rank = self.add_xp(
                member_id, guild_id, xp_bonus
            )

            # Schedule immediate save to ensure streak is persisted
            self.schedule_save()

            return True, xp_bonus, rank_changed, new_rank

        return False, 0, False, None

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

        valid_sort_options = ["xp", "messages_sent"]
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

    def update_activity_streak(self, member_id: int, guild_id: int) -> Dict[str, Any]:
        """
        Update member's activity streak and return streak info.

        Returns:
            Dict with streak info: {
                'current_streak': int,
                'streak_broken': bool,
                'is_new_day': bool,
                'xp_bonus': int
            }
        """
        member_data = self.get_member_data(member_id, guild_id)

        today = datetime.now().date()
        last_activity = member_data.get("last_activity_date")

        # Convert string to date if needed
        if isinstance(last_activity, str):
            try:
                last_activity = datetime.fromisoformat(last_activity).date()
            except:
                last_activity = None

        streak_info = {
            'current_streak': member_data.get('current_streak', 0),
            'streak_broken': False,
            'is_new_day': False,
            'xp_bonus': 0
        }

        # First time user is active
        if last_activity is None:
            member_data['current_streak'] = 1
            member_data['longest_streak'] = 1
            member_data['last_activity_date'] = today.isoformat()
            streak_info['current_streak'] = 1
            streak_info['is_new_day'] = True
            self.schedule_save()
            return streak_info

        days_diff = (today - last_activity).days

        # Same day - no streak change
        if days_diff == 0:
            streak_info['current_streak'] = member_data.get('current_streak', 0)
            streak_info['xp_bonus'] = self._get_streak_bonus(member_data.get('current_streak', 0))
            return streak_info

        # Next day - continue streak
        elif days_diff == 1:
            member_data['current_streak'] = member_data.get('current_streak', 0) + 1
            member_data['last_activity_date'] = today.isoformat()

            # Update longest streak if needed
            if member_data['current_streak'] > member_data.get('longest_streak', 0):
                member_data['longest_streak'] = member_data['current_streak']

            streak_info['current_streak'] = member_data['current_streak']
            streak_info['is_new_day'] = True
            streak_info['xp_bonus'] = self._get_streak_bonus(member_data['current_streak'])
            self.schedule_save()
            return streak_info

        # Streak broken (more than 1 day gap)
        else:
            member_data['current_streak'] = 1
            member_data['last_activity_date'] = today.isoformat()
            streak_info['current_streak'] = 1
            streak_info['streak_broken'] = True
            streak_info['is_new_day'] = True
            streak_info['xp_bonus'] = 0
            self.schedule_save()
            return streak_info

    def _get_streak_bonus(self, streak_days: int) -> int:
        """Calculate XP bonus based on streak days."""
        bonus = 0
        for threshold, xp_bonus in sorted(STREAK_XP_BONUSES.items(), reverse=True):
            if streak_days >= threshold:
                bonus = xp_bonus
                break
        return bonus

    def get_streak_info(self, member_id: int, guild_id: int) -> Dict[str, Any]:
        """Get streak information for a member."""
        member_data = self.get_member_data(member_id, guild_id)

        return {
            'current_streak': member_data.get('current_streak', 0),
            'longest_streak': member_data.get('longest_streak', 0),
            'xp_bonus': self._get_streak_bonus(member_data.get('current_streak', 0)),
            'last_activity_date': member_data.get('last_activity_date')
        }
