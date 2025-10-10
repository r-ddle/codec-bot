"""
Member events - Handlers for member join and ready events.
"""
import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone
import random
import asyncio

from config.settings import WELCOME_CHANNEL_ID, logger


class MemberEvents(commands.Cog):
    """Event handlers for member-related activities with MGS-themed activity rotation."""

    def __init__(self, bot):
        self.bot = bot
        self.activity_mode = 0  # 0=Rich, 1=Streaming, 2=Quote

        # MGS1 Codec Quotes
        self.mgs_quotes = [
            "A surveillance camera?!",
            "Snake, what happened? Snake? SNAAAAKE!",
            "It's just like one of my Japanese animes!",
            "You're that ninja...",
            "Metal Gear?! It can't be!",
            "Colonel, what's a Russian gunship doing here?",
            "War has changed.",
            "Kept you waiting, huh?",
            "This is Snake. Colonel, can you hear me?",
            "Whose footprints are these?",
            "I'm no hero. Never was, never will be.",
            "Stealth camouflage?!",
            "Cipher... Zero... Such a lust for revenge!",
            "Nanomachines, son!",
            "Age hasn't slowed you down one bit."
        ]

        self.activity_rotation.start()

    def cog_unload(self):
        """Clean shutdown of background task"""
        self.activity_rotation.cancel()

    @tasks.loop(minutes=5)
    async def activity_rotation(self):
        """
        Rotates through three activity types every 5 minutes.

        Trade-off Analysis:
        - 5min interval: Balances freshness vs API rate limits
        - Sequential rotation: Predictable pattern, easy to debug
        """
        try:
            if self.activity_mode == 0:
                await self._set_rich_presence()
            elif self.activity_mode == 1:
                await self._set_streaming_activity()
            else:
                await self._set_quote_activity()

            # Cycle to next mode
            self.activity_mode = (self.activity_mode + 1) % 3

        except discord.HTTPException as e:
            logger.error(f"HTTP error setting activity: {e.status} - {e.text}")
        except discord.InvalidData as e:
            logger.error(f"Invalid activity data: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in activity rotation: {type(e).__name__}: {e}")

    @activity_rotation.before_loop
    async def before_activity_rotation(self):
        """Wait for bot to be ready before starting activity rotation"""
        await self.bot.wait_until_ready()
        print("🎮 MGS Activity System initialized")

    async def _set_rich_presence(self):
        """
        Rich Presence with Codec theme.

        IMPORTANT: Requires Discord Developer Portal setup:
        1. Go to: https://discord.com/developers/applications/{YOUR_APP_ID}/rich-presence/assets
        2. Upload assets with these exact names:
           - 'codec_screen' (400x400px PNG - green terminal aesthetic)
           - 'foxhound_logo' (256x256px PNG - FOXHOUND emblem)
        """
        activity = discord.Activity(
            type=discord.ActivityType.playing,
            name="Metal Gear Solid",
            state="Infiltrating Shadow Moses",
            details="Codec Frequency: 140.85",
            timestamps={"start": int(datetime.now(timezone.utc).timestamp())},
            assets={
                "large_image": "codec_screen",
                "large_text": "Tactical Espionage Action",
                "small_image": "foxhound_logo",
                "small_text": "FOXHOUND"
            }
        )

        await self.bot.change_presence(
            activity=activity,
            status=discord.Status.online
        )
        print("✅ Activity: Rich Presence (Codec Mode)")

    async def _set_streaming_activity(self):
        """
        Streaming activity showing server management stats.

        Why Streaming type?
        - Displays purple "LIVE" indicator
        - Allows dynamic member count in name
        - URL can link to actual server info (optional)
        """
        # Calculate total members across all guilds
        total_members = sum(guild.member_count for guild in self.bot.guilds)

        activity = discord.Streaming(
            name=f"Managing {total_members} Soldiers",
            url="https://www.twitch.tv/metalgearsolid",  # Required for Streaming type
            details="Server Operations",
            state="Tactical Command"
        )

        await self.bot.change_presence(
            activity=activity,
            status=discord.Status.dnd  # Red status for "on a mission"
        )
        print(f"✅ Activity: Streaming Mode ({total_members} members)")

    async def _set_quote_activity(self):
        """
        Rotating MGS quotes in Game activity.

        Why Game type for quotes?
        - Simplest API (no asset requirements)
        - "Playing [quote]" format fits naturally
        - Lowest rate limit risk
        """
        quote = random.choice(self.mgs_quotes)

        activity = discord.Game(name=quote)

        await self.bot.change_presence(
            activity=activity,
            status=discord.Status.idle  # Yellow status for alert phase
        )
        print(f"✅ Activity: Quote Mode - '{quote}'")

    @commands.Cog.listener()
    async def on_ready(self):
        """Bot ready event handler."""
        print(f"✅ {self.bot.user} is now online and ready!")
        print(f"🦊 Connected to {len(self.bot.guilds)} guilds")

        for guild in self.bot.guilds:
            guild_key = str(guild.id)
            if guild_key in self.bot.member_data.data:
                member_count = len(self.bot.member_data.data[guild_key])
                print(f" Guild '{guild.name}' ({guild.id}): {member_count} members loaded")
            else:
                print(f" Guild '{guild.name}' ({guild.id}): New guild, no existing data")

        print(" Bot is fully ready and operational!")
        print(" XP-based ranking system active!")
        print("🎮 MGS Activity System will start rotating presences")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Welcome system for new members."""
        logger.info(f"NEW MEMBER JOINED: {member.name} (ID: {member.id}) in {member.guild.name}")

        try:
            self.bot.member_data.get_member_data(member.id, member.guild.id)
            self.bot.member_data.mark_member_verified(member.id, member.guild.id)

            welcome_channel = None

            if WELCOME_CHANNEL_ID:
                welcome_channel = member.guild.get_channel(WELCOME_CHANNEL_ID)

            if not welcome_channel:
                for channel_name in ['welcome', 'general', 'main', 'chat']:
                    welcome_channel = discord.utils.get(member.guild.text_channels, name=channel_name)
                    if welcome_channel:
                        break

            if not welcome_channel:
                for channel in member.guild.text_channels:
                    if channel.permissions_for(member.guild.me).send_messages:
                        welcome_channel = channel
                        break

            if not welcome_channel:
                logger.warning(f"No suitable welcome channel found in {member.guild.name}")
                return

            embed = discord.Embed(
                title="New Operative Detected",
                description=f"**{member.display_name}** has joined Outer Heaven!",
                color=0x5865F2
            )

            embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)

            embed.add_field(
                name="Rank Up Info",
                value="Chat in the server to earn XP!\nFirst promotion: **Private** role at 100 XP",
                inline=False
            )

            embed.set_footer(text=f"Joined: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")

            await welcome_channel.send(f" **Welcome to Mother Base, {member.mention}!**", embed=embed)
            logger.info(f"Welcome sent to #{welcome_channel.name} for {member.name}")

            await self.bot.member_data.save_data_async()

        except Exception as e:
            logger.error(f"Error in welcome system: {e}", exc_info=True)


async def setup(bot):
    """Load the MemberEvents cog."""
    await bot.add_cog(MemberEvents(bot))
