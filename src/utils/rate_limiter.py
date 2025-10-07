"""
Rate limiting utilities for Discord bot commands.
Prevents spam and abuse of bot commands.
"""
import time
from typing import Dict, Tuple
from collections import defaultdict
from config.settings import logger


class CommandRateLimiter:
    """Simple rate limiter for bot commands."""

    def __init__(self):
        # Structure: {user_id: {command_name: last_used_timestamp}}
        self._user_cooldowns: Dict[int, Dict[str, float]] = defaultdict(dict)

        # Command cooldowns in seconds
        self._cooldowns = {
            'daily': 60,  # 1 minute between checks
            'shop': 5,    # 5 seconds between shop opens
            'buy': 3,     # 3 seconds between purchases
            'inventory': 5,
            'use': 10,    # 10 seconds between item uses
            'gmp': 5,
            'rank': 10,
            'leaderboard': 15,
            'intel': 30,
        }

    def check_rate_limit(self, user_id: int, command_name: str) -> Tuple[bool, float]:
        """
        Check if user is rate limited for a command.

        Args:
            user_id: Discord user ID
            command_name: Command name to check

        Returns:
            Tuple of (can_use, remaining_cooldown)
                can_use: True if command can be used
                remaining_cooldown: Seconds remaining if on cooldown, 0 if can use
        """
        if command_name not in self._cooldowns:
            return True, 0.0

        current_time = time.time()
        cooldown_duration = self._cooldowns[command_name]

        user_data = self._user_cooldowns[user_id]
        last_used = user_data.get(command_name, 0)

        time_since_use = current_time - last_used

        if time_since_use >= cooldown_duration:
            # Update last used time
            user_data[command_name] = current_time
            return True, 0.0
        else:
            # Still on cooldown
            remaining = cooldown_duration - time_since_use
            return False, remaining

    def reset_cooldown(self, user_id: int, command_name: str) -> None:
        """
        Reset cooldown for a specific command (admin use).

        Args:
            user_id: Discord user ID
            command_name: Command to reset
        """
        if user_id in self._user_cooldowns:
            if command_name in self._user_cooldowns[user_id]:
                del self._user_cooldowns[user_id][command_name]
                logger.info(f"Reset cooldown for user {user_id} command {command_name}")

    def cleanup_old_entries(self, max_age: int = 3600) -> None:
        """
        Remove old cooldown entries to prevent memory buildup.

        Args:
            max_age: Maximum age in seconds before cleanup
        """
        current_time = time.time()
        users_to_remove = []

        for user_id, commands in self._user_cooldowns.items():
            commands_to_remove = []

            for command_name, last_used in commands.items():
                if current_time - last_used > max_age:
                    commands_to_remove.append(command_name)

            for command_name in commands_to_remove:
                del commands[command_name]

            if not commands:
                users_to_remove.append(user_id)

        for user_id in users_to_remove:
            del self._user_cooldowns[user_id]

        if users_to_remove or any(commands_to_remove for commands in self._user_cooldowns.values()):
            logger.info(f"Cleaned up cooldowns for {len(users_to_remove)} users")


# Global rate limiter instance
rate_limiter = CommandRateLimiter()
