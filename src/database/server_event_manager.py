"""
Server Event Manager - Weekly Community Events
Tracks messages, manages rewards, and generates progress updates
"""
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from config.settings import logger


class ServerEventManager:
    """Manages weekly server events"""

    def __init__(self, data_file: str = "src/server_event_data.json", bot=None):
        self.data_file = Path(data_file)
        self.data = self._load_data()
        self.save_lock = asyncio.Lock()
        self.bot = bot  # Bot instance for accessing member_data

    def _load_data(self) -> Dict:
        """Load event data from JSON file"""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading server event data: {e}")
                return self._default_data()
        return self._default_data()

    def _default_data(self) -> Dict:
        """Create default event data structure"""
        return {
            "active": False,
            "event_title": "Weekly Community Challenge",
            "event_type": "message",  # Type of event: message, xp, reaction
            "message_goal": 1500,  # Default fallback
            "start_date": None,
            "end_date": None,
            "total_messages": 0,
            "participants": {},  # user_id: message_count
            "participation_history": {},  # user_id: [event_ids they participated in]
            "event_history": [],  # List of past events with stats
            "last_progress_update": None
        }

    def calculate_dynamic_event_goal(self, guild_id: int) -> int:
        """
        Calculate a dynamic event goal based on server average activity.
        Similar to profile bio algorithm but scaled for community goals.

        Uses 2-3x multiplier of server average (more challenging than individual 75% goal).
        For weekly events, scales down proportionally from monthly average.

        Args:
            guild_id: The guild ID to calculate for

        Returns:
            Dynamic message goal for the event
        """
        try:
            if not self.bot or not hasattr(self.bot, 'member_data'):
                return 1500  # Fallback if bot not available

            all_members = self.bot.member_data.data.get(guild_id, {})

            # Filter active members (those with messages)
            active_members = [
                data for data in all_members.values()
                if isinstance(data, dict) and data.get('messages_sent', 0) > 0
            ]

            if not active_members:
                return 1500  # Fallback if no data

            # Calculate average messages per member
            total_messages = sum(m.get('messages_sent', 0) for m in active_members)
            avg_per_member = total_messages // len(active_members)

            # For weekly events: use 2.5x multiplier of server average
            # This creates a community challenge (harder than individual 75% goal)
            weekly_goal = int(avg_per_member * len(active_members) * 2.5)

            # Clamp between reasonable bounds (500-30000)
            return max(500, min(30000, weekly_goal))

        except Exception as e:
            logger.error(f"Error calculating dynamic event goal: {e}")
            return 1500  # Fallback on error

    async def save_data(self):
        """Save event data to JSON file"""
        async with self.save_lock:
            try:
                self.data_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.data_file, 'w', encoding='utf-8') as f:
                    json.dump(self.data, f, indent=2, ensure_ascii=False)
            except Exception as e:
                logger.error(f"Error saving server event data: {e}")

    def is_event_active(self) -> bool:
        """Check if event is currently active"""
        return self.data.get("active", False)

    def get_event_info(self) -> Dict:
        """Get current event information"""
        return {
            "active": self.data.get("active", False),
            "title": self.data.get("event_title", "Weekly Community Challenge"),
            "goal": self.data.get("message_goal", 15000),
            "current": self.data.get("total_messages", 0),
            "start_date": self.data.get("start_date"),
            "end_date": self.data.get("end_date"),
            "participants": len(self.data.get("participants", {}))
        }

    async def start_event(
        self,
        title: Optional[str] = None,
        message_goal: Optional[int] = None,
        custom_end_date: Optional[datetime] = None,
        guild_id: Optional[int] = None,
        event_type: str = "message",
        goal: Optional[int] = None,
        duration_days: int = 7
    ) -> Dict:
        """
        Start a new weekly event with dynamic goal calculation.

        If message_goal is not provided, calculates a dynamic goal based on
        server activity (2.5x multiplier of server average for community challenge).

        Args:
            title: Event title
            message_goal: Target message count (if None, calculates dynamically)
            custom_end_date: Custom end date (if None, uses Sunday 23:59)
            guild_id: Guild ID for dynamic goal calculation
            event_type: Type of event (message, xp, reaction)
            goal: Target goal amount (alias for message_goal)
            duration_days: Duration of event in days

        Returns:
            Dict with event details for announcement
        """
        now = datetime.now()

        # Use 'goal' if message_goal is not provided (for backwards compatibility)
        if message_goal is None and goal is not None:
            message_goal = goal

        # Calculate dynamic goal if not provided
        if message_goal is None:
            if guild_id is not None:
                message_goal = self.calculate_dynamic_event_goal(guild_id)
                logger.info(f"Dynamic event goal calculated: {message_goal:,} messages")
            else:
                message_goal = 1500  # Fallback
                logger.warning("No guild_id provided for dynamic goal, using fallback")

        # Calculate start (Monday) and end based on duration_days
        if custom_end_date:
            end_date = custom_end_date
        else:
            # Calculate end date based on duration_days
            end_date = now + timedelta(days=duration_days)
            end_date = end_date.replace(hour=23, minute=59, second=59)

        self.data = {
            "active": True,
            "event_title": title or "Weekly Community Challenge",
            "event_type": event_type,
            "message_goal": message_goal,
            "start_date": now.isoformat(),
            "end_date": end_date.isoformat(),
            "total_messages": 0,
            "participants": {},
            "last_progress_update": now.isoformat()
        }

        await self.save_data()
        logger.info(f"✅ Server event started: {self.data['event_title']} ({event_type})")

        return {
            "title": self.data["event_title"],
            "goal": self.data["message_goal"],
            "event_type": event_type,
            "start_date": now.strftime("%A, %b %d"),
            "end_date": end_date.strftime("%A, %b %d")
        }

    async def track_message(self, user_id: int, username: str):
        """Track a message from a user during the event"""
        if not self.is_event_active():
            return

        user_id_str = str(user_id)

        # Initialize participant if new
        if user_id_str not in self.data["participants"]:
            self.data["participants"][user_id_str] = {
                "username": username,
                "message_count": 0
            }
            # Track participation in this event
            self.track_participation(user_id)

        # Increment message count
        self.data["participants"][user_id_str]["message_count"] += 1
        self.data["participants"][user_id_str]["username"] = username  # Update username
        self.data["total_messages"] += 1

        # Save periodically (every 10 messages)
        if self.data["total_messages"] % 10 == 0:
            await self.save_data()

    def should_send_progress_update(self) -> bool:
        """Check if it's time to send a progress update (every 3-5 hours)"""
        if not self.is_event_active():
            return False

        last_update = self.data.get("last_progress_update")
        if not last_update:
            return True

        last_update_dt = datetime.fromisoformat(last_update)
        now = datetime.now()
        hours_since_update = (now - last_update_dt).total_seconds() / 3600

        # Random interval between 3-5 hours (using 4 as midpoint)
        return hours_since_update >= 4

    async def mark_progress_update_sent(self):
        """Mark that a progress update was sent"""
        self.data["last_progress_update"] = datetime.now().isoformat()
        await self.save_data()

    def get_progress_data(self) -> Optional[Dict]:
        """Get data for progress update image"""
        if not self.is_event_active():
            return None

        end_date = datetime.fromisoformat(self.data["end_date"])
        now = datetime.now()
        time_left = end_date - now

        # Format time remaining
        days = time_left.days
        hours = time_left.seconds // 3600

        if days > 0:
            time_str = f"{days} day{'s' if days != 1 else ''}, {hours} hour{'s' if hours != 1 else ''}"
        else:
            time_str = f"{hours} hour{'s' if hours != 1 else ''}"

        # Get top contributors
        participants = self.data.get("participants", {})
        sorted_participants = sorted(
            participants.items(),
            key=lambda x: x[1]["message_count"],
            reverse=True
        )

        top_contributors = [
            (p[1]["username"], p[1]["message_count"])
            for p in sorted_participants[:3]
        ]

        return {
            "title": self.data["event_title"],
            "current": self.data["total_messages"],
            "goal": self.data["message_goal"],
            "time_remaining": time_str,
            "participants": len(participants),
            "top_contributors": top_contributors
        }

    def should_end_event(self) -> bool:
        """Check if event should end (Sunday passed)"""
        if not self.is_event_active():
            return False

        end_date = datetime.fromisoformat(self.data["end_date"])
        return datetime.now() >= end_date

    async def end_event(self) -> Dict:
        """
        End the event and prepare results

        Returns:
            Dict with results data including rewards to distribute
        """
        if not self.is_event_active():
            return None

        participants = self.data.get("participants", {})

        # Sort by message count
        sorted_participants = sorted(
            participants.items(),
            key=lambda x: x[1]["message_count"],
            reverse=True
        )

        # Filter participants with at least 5 messages
        eligible_participants = [
            (user_id, data) for user_id, data in sorted_participants
            if data["message_count"] >= 5
        ]

        # Prepare leaderboard for image
        leaderboard = [
            (data["username"], data["message_count"])
            for _, data in sorted_participants
        ]

        # Prepare rewards
        rewards = {
            "all_participants": [],  # Users with 5+ messages
            "top_3": []  # Top 3 users
        }

        for user_id, data in eligible_participants:
            rewards["all_participants"].append({
                "user_id": int(user_id),
                "username": data["username"],
                "messages": data["message_count"],
                "xp": 100
            })

        # Top 3 get bonus
        for user_id, data in sorted_participants[:3]:
            if int(user_id) in [p["user_id"] for p in rewards["all_participants"]]:
                rewards["top_3"].append({
                    "user_id": int(user_id),
                    "username": data["username"],
                    "messages": data["message_count"],
                    "bonus_xp": 500
                })

        results = {
            "title": self.data["event_title"],
            "total_messages": self.data["total_messages"],
            "goal": self.data["message_goal"],
            "goal_reached": self.data["total_messages"] >= self.data["message_goal"],
            "leaderboard": leaderboard,
            "participant_count": len(eligible_participants),
            "rewards": rewards
        }

        # Save event to history before marking inactive
        self.save_event_to_history()

        # Mark event as inactive
        self.data["active"] = False
        await self.save_data()

        logger.info(f"✅ Server event ended: {results['title']}")
        logger.info(f"   Total messages: {results['total_messages']:,}")
        logger.info(f"   Eligible participants: {results['participant_count']}")

        return results

    def get_leaderboard(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get current leaderboard"""
        if not self.is_event_active():
            return []

        participants = self.data.get("participants", {})
        sorted_participants = sorted(
            participants.items(),
            key=lambda x: x[1]["message_count"],
            reverse=True
        )

        return [
            (data["username"], data["message_count"])
            for _, data in sorted_participants[:limit]
        ]

    def track_participation(self, user_id: int, event_id: str = None):
        """
        Track user participation in events.

        Args:
            user_id: Discord user ID
            event_id: Event identifier (uses current event title if None)
        """
        if "participation_history" not in self.data:
            self.data["participation_history"] = {}

        user_id_str = str(user_id)
        if user_id_str not in self.data["participation_history"]:
            self.data["participation_history"][user_id_str] = []

        event_identifier = event_id or self.data.get("event_title", "unknown")

        # Add event to user's participation history if not already there
        if event_identifier not in self.data["participation_history"][user_id_str]:
            self.data["participation_history"][user_id_str].append(event_identifier)

    def get_participation_stats(self, user_id: int) -> Dict:
        """
        Get participation statistics for a user.

        Args:
            user_id: Discord user ID

        Returns:
            Dict with participation stats
        """
        user_id_str = str(user_id)
        participation_history = self.data.get("participation_history", {})

        events_participated = participation_history.get(user_id_str, [])

        return {
            "total_events": len(events_participated),
            "events": events_participated,
            "current_event_active": self.is_event_active(),
            "current_event_contribution": self.data.get("participants", {}).get(user_id_str, {}).get("message_count", 0) if self.is_event_active() else 0
        }

    def get_top_participants(self, limit: int = 10) -> List[Tuple[str, int]]:
        """
        Get users who participated in the most events.

        Args:
            limit: Maximum number of participants to return

        Returns:
            List of (user_id, event_count) tuples
        """
        participation_history = self.data.get("participation_history", {})

        # Sort by number of events participated
        sorted_participants = sorted(
            participation_history.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )

        return [
            (user_id, len(events))
            for user_id, events in sorted_participants[:limit]
        ]

    def save_event_to_history(self):
        """Save current event to history when it ends."""
        if not self.is_event_active():
            return

        if "event_history" not in self.data:
            self.data["event_history"] = []

        event_record = {
            "title": self.data.get("event_title"),
            "event_type": self.data.get("event_type", "message"),
            "start_date": self.data.get("start_date"),
            "end_date": self.data.get("end_date"),
            "goal": self.data.get("message_goal"),
            "total_messages": self.data.get("total_messages", 0),
            "participant_count": len(self.data.get("participants", {})),
            "goal_reached": self.data.get("total_messages", 0) >= self.data.get("message_goal", 0),
            "ended_at": datetime.now().isoformat()
        }

        self.data["event_history"].append(event_record)

        # Keep only last 20 events in history
        if len(self.data["event_history"]) > 20:
            self.data["event_history"] = self.data["event_history"][-20:]

    def get_event_history(self, limit: int = 10) -> List[Dict]:
        """Get past event history."""
        return self.data.get("event_history", [])[-limit:]
