"""
Rich Presence Manager for Kiro - Your Chill Hangout Bot
Handles modernized Rich Presence with dynamic updates, cozy vibes, and server details.

Features:
- Large and small image display (external URLs)
- Minecraft detection - auto-update when members play
- Timer/timestamp tracking
- Server and friend statistics
- Dynamic status rotation
- Custom party information
- Modern game-like RPC appearance
"""

import discord
from discord.ext import tasks
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import asyncio
from config.settings import logger
import random

# Rich Presence Asset URLs (External URLs - not Discord assets)
LARGE_IMAGE_URL = "https://media1.tenor.com/m/VOYttVmmcKIAAAAC/pixel-art.gif"  # Cozy pixel art
SMALL_IMAGE_URL = "https://cdn.discordapp.com/avatars/1040597411116089424/98393527a622a959476a47dd4c955edd.webp?size=1024"  # r.ddle avatar

# Button URL
EXILE_SERVER_URL = "https://exiledunits.vercel.app/"

# Activity type enum (discord.ActivityType)
# 0 = PLAYING, 1 = STREAMING, 2 = LISTENING, 3 = WATCHING, 4 = CUSTOM, 5 = COMPETING


class RichPresenceManager:
    """
    Manages dynamic Rich Presence for Kiro - the chill hangout bot.

    Features:
    - Large and small image display
    - Timer/timestamp tracking
    - Server and friend statistics
    - Dynamic status rotation
    - Minecraft detection & auto-update
    - Custom party information
    - Modern friendly RPC appearance
    """

    def __init__(self, bot):
        """
        Initialize the Rich Presence Manager.

        Args:
            bot: The Kiro bot instance
        """
        self.bot = bot
        self.rpc_start_time = datetime.now()
        self.minecraft_detected = False

        # Simple RPC - no rotation
        self.rpc_template = {
            "name": "Listening to Exile",
            "state": "With {members} friends!",
            "type": discord.ActivityType.listening,
        }

    async def initialize_presence(self):
        """Initialize Rich Presence when bot starts."""
        try:
            await self.update_rich_presence()
            logger.info("✅ Rich Presence initialized")
            # Start the Minecraft detection loop
            self.monitor_minecraft_activity.start()
        except Exception as e:
            logger.error(f"❌ Failed to initialize Rich Presence: {e}")

    @tasks.loop(seconds=10)
    async def monitor_minecraft_activity(self):
        """Monitor for members playing Minecraft and update RPC accordingly."""
        try:
            minecraft_players = []

            # Check all guilds and members for Minecraft activity
            for guild in self.bot.guilds:
                for member in guild.members:
                    # Skip bot accounts
                    if member.bot:
                        continue

                    # Check each member's activities
                    if member.activities:
                        for activity in member.activities:
                            # Check if this is a Game activity named Minecraft
                            if isinstance(activity, discord.Game):
                                # Match "Minecraft", "minecraft", "MINECRAFT", etc.
                                if activity.name and "minecraft" in activity.name.lower():
                                    minecraft_players.append(member.name)
                                    logger.debug(f"🎮 Found Minecraft player: {member.name} - Activity: {activity.name}")

            # If Minecraft players detected, update RPC
            if minecraft_players and not self.minecraft_detected:
                self.minecraft_detected = True
                await self.update_minecraft_presence()
                logger.info(f"🎮 Minecraft detected! Players: {', '.join(minecraft_players[:3])}")

            # If no Minecraft players, restore normal RPC
            elif not minecraft_players and self.minecraft_detected:
                self.minecraft_detected = False
                await self.update_rich_presence()
                logger.info("🎮 Minecraft activity ended, restored normal RPC")

        except Exception as e:
            logger.error(f"Error monitoring Minecraft activity: {e}")

    @monitor_minecraft_activity.before_loop
    async def before_monitor(self):
        """Wait until bot is ready before monitoring."""
        await self.bot.wait_until_ready()

    async def update_minecraft_presence(self):
        """Update RPC to show Minecraft SMP is active."""
        try:
            # Create the Activity object with Minecraft info
            activity = discord.Activity(
                name="Playing Exiled SMP",
                type=discord.ActivityType.playing,
                state="at exiledunits.aternos.me",
                details="Join the exile!",
                application_id=self.bot.application_id,

                # Assets - Using external URLs
                assets={
                    "large_image": LARGE_IMAGE_URL,
                    "large_text": "Kira - r.ddle's Hangout Bot",
                    "small_image": SMALL_IMAGE_URL,
                    "small_text": "Exile",
                },

                # Timestamps
                timestamps={
                    "start": int(datetime.now().timestamp()),
                },

                # Party Information
                party={
                    "id": f"kiro_minecraft_{self.bot.application_id}",
                    "size": [1, 100],
                },

                # Single button to server website
                buttons=[
                    {"label": "Join Exile", "url": EXILE_SERVER_URL},
                ],
            )

            # Update the bot's presence
            await self.bot.change_presence(
                activity=activity,
                status=discord.Status.online
            )

            logger.debug(f"🎮 Minecraft RPC Updated")

        except Exception as e:
            logger.error(f"Error updating Minecraft presence: {e}")

    async def update_rich_presence(self):
        """
        Update the bot's Rich Presence - simple version.
        Shows: "Listening to Exile" with "With {member_count} friends"
        """
        try:
            # Get member count from the main server
            member_count = 0
            if self.bot.guilds:
                member_count = self.bot.guilds[0].member_count or 0

            # Create the Activity object
            activity = discord.Activity(
                name=self.rpc_template["name"],
                type=self.rpc_template["type"],
                state=self.rpc_template["state"].format(members=member_count),
                application_id=self.bot.application_id,

                # Assets - Using external URLs
                assets={
                    "large_image": LARGE_IMAGE_URL,
                    "large_text": "Kira - r.ddle's Hangout Bot",
                    "small_image": SMALL_IMAGE_URL,
                    "small_text": "Exile",
                },

                # Timestamps
                timestamps={
                    "start": int(self.rpc_start_time.timestamp()),
                },

                # Party Information
                party={
                    "id": f"kiro_hangout_{self.bot.application_id}",
                    "size": [member_count, member_count + 100],
                },

                # Single button to server website
                buttons=[
                    {"label": "Visit Exile", "url": EXILE_SERVER_URL},
                ],
            )

            # Update the bot's presence
            await self.bot.change_presence(
                activity=activity,
                status=discord.Status.online
            )

            logger.debug(f"🎮 RPC Updated: Listening to Exile - With {member_count} friends")

        except Exception as e:
            logger.error(f"Error updating Rich Presence: {e}")

    async def rotate_presence(self):
        """No-op since we don't rotate anymore."""
        pass

    def get_elapsed_time(self) -> str:
        """Get formatted elapsed time since bot start."""
        elapsed = datetime.now() - self.rpc_start_time
        hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}h {minutes}m {seconds}s"

    def get_status_summary(self) -> Dict[str, Any]:
        """Get current Rich Presence status summary."""
        try:
            # Get member count from the main server
            member_count = 0
            if self.bot.guilds:
                member_count = self.bot.guilds[0].member_count or 0

            current_activity = "Playing Minecraft SMP" if self.minecraft_detected else "Listening to Exile"

            return {
                "status": "online",
                "current_activity": current_activity,
                "minecraft_active": self.minecraft_detected,
                "members": member_count,
                "uptime": self.get_elapsed_time(),
                "large_image": LARGE_IMAGE_URL,
                "small_image": SMALL_IMAGE_URL,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error getting status summary: {e}")
            return {}

    async def update_with_custom_activity(
        self,
        name: str,
        state: Optional[str] = None,
        details: Optional[str] = None,
        activity_type: discord.ActivityType = discord.ActivityType.playing,
        duration: Optional[int] = None,
    ):
        """
        Update Rich Presence with a custom activity.

        Args:
            name: Activity name (game/application name)
            state: Current state of activity
            details: Additional details
            activity_type: Type of activity
            duration: How long to show this activity (seconds), None for permanent
        """
        try:
            activity = discord.Activity(
                name=name,
                type=activity_type,
                state=state,
                details=details,
                application_id=self.bot.application_id,
                assets={
                    "large_image": LARGE_IMAGE_URL,
                    "large_text": "Kiro - Your Chill Hangout Bot",
                    "small_image": SMALL_IMAGE_URL,
                    "small_text": "Exiled Units",
                },
                timestamps={
                    "start": int(datetime.now().timestamp()),
                },
                buttons=[
                    {"label": "Visit Exile", "url": EXILE_SERVER_URL},
                ],
            )

            await self.bot.change_presence(activity=activity, status=discord.Status.online)
            logger.info(f"🎮 Custom RPC Set: {name}")

            # If duration specified, schedule restore to default
            if duration:
                await asyncio.sleep(duration)
                await self.update_rich_presence()

        except Exception as e:
            logger.error(f"Error updating custom activity: {e}")

    async def set_special_status(self, message: str, duration: int = 60):
        """
        Set a temporary special status message.

        Args:
            message: The special status message
            duration: How long to display (seconds)
        """
        await self.update_with_custom_activity(
            name="✨ Fun Times",
            state=message,
            details="Check it out!",
            activity_type=discord.ActivityType.playing,
            duration=duration,
        )

    async def start_rpc_rotation_loop(self, interval: int = 300):
        """
        Start automatic RPC rotation loop.

        Args:
            interval: Seconds between rotations (default 5 minutes)
        """
        @tasks.loop(seconds=interval)
        async def rpc_rotation():
            try:
                await self.rotate_presence()
            except Exception as e:
                logger.error(f"Error in RPC rotation loop: {e}")

        @rpc_rotation.before_loop
        async def before_rotation():
            await self.bot.wait_until_ready()

        rpc_rotation.start()
        logger.info(f"🔄 RPC rotation started (interval: {interval}s)")
