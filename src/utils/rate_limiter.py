"""
Rate limiting utilities for Discord bot commands.
Prevents spam and abuse of bot commands.
"""
import time
from typing import Dict, Tuple
from collections import defaultdict
from config.settings import logger
from config.bot_settings import RATE_LIMITS, RATE_LIMIT_MAX_AGE


class CommandRateLimiter:
    """Simple rate limiter for bot commands."""

    def __init__(self):
        # Structure: {user_id: {command_name: last_used_timestamp}}
        self._user_cooldowns: Dict[int, Dict[str, float]] = defaultdict(dict)

        # Command cooldowns in seconds (loaded from bot_settings)
        self._cooldowns = RATE_LIMITS

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

    def cleanup_old_entries(self, max_age: int = None) -> None:
        """
        Remove old cooldown entries to prevent memory buildup.

        Args:
            max_age: Maximum age in seconds before cleanup (uses RATE_LIMIT_MAX_AGE if None)
        """
        if max_age is None:
            max_age = RATE_LIMIT_MAX_AGE
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


def enforce_rate_limit(command_name: str):
    """Decorator to enforce rate limits for both prefix commands and slash (interaction) commands.

    - Bypasses rate limits for users with administrator permissions.
    - Sends an appropriate cooldown message for Context or Interaction.
    """
    from functools import wraps

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Try to find a context-like or interaction-like object in args
            ctx_or_interaction = None
            # Typical method signatures: (self, ctx, ... ) or (self, interaction, ...)
            if len(args) >= 2:
                ctx_or_interaction = args[1]

            # Fallback: search kwargs for common names
            if ctx_or_interaction is None:
                for v in kwargs.values():
                    if hasattr(v, 'author') or hasattr(v, 'user'):
                        ctx_or_interaction = v
                        break

            # If we couldn't find anything, just call the function
            if ctx_or_interaction is None:
                return await func(*args, **kwargs)

            # Resolve the user object
            user = getattr(ctx_or_interaction, 'author', None) or getattr(ctx_or_interaction, 'user', None)

            # If we can't find a user, call original
            if user is None:
                return await func(*args, **kwargs)

            # Bypass for administrators
            guild_perms = getattr(user, 'guild_permissions', None)
            if guild_perms and getattr(guild_perms, 'administrator', False):
                return await func(*args, **kwargs)

            # Check rate limiter
            can_use, remaining = rate_limiter.check_rate_limit(user.id, command_name)
            if not can_use:
                # Send cooldown message depending on object type
                try:
                    # Interaction
                    if hasattr(ctx_or_interaction, 'response') and hasattr(ctx_or_interaction, 'user'):
                        # If response has already been used, use followup
                        try:
                            await ctx_or_interaction.response.send_message(f"⏳ Please wait {int(remaining)}s before using this command again.", ephemeral=True)
                        except Exception:
                            try:
                                await ctx_or_interaction.followup.send(f"⏳ Please wait {int(remaining)}s before using this command again.", ephemeral=True)
                            except Exception:
                                pass

                    # Context
                    elif hasattr(ctx_or_interaction, 'send') and hasattr(ctx_or_interaction, 'author'):
                        await ctx_or_interaction.send(f"⏳ Please wait {int(remaining)}s before using this command again.", delete_after=6)

                except Exception:
                    # If messaging fails silently, just return
                    return

                return

            # Allowed: call original
            return await func(*args, **kwargs)

        return wrapper

    return decorator
