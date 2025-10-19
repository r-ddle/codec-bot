"""
Member events - Handlers for member join and ready events.
"""
import discord
from discord.ext import commands
from datetime import datetime, timezone

from config.settings import WELCOME_CHANNEL_ID, FAQ_CHANNEL_ID, RULES_CHANNEL_ID, logger


class MemberEvents(commands.Cog):
    """Event handlers for member-related activities with simple streaming presence."""

    def __init__(self, bot):
        self.bot = bot

    async def _update_presence(self):
        """Update streaming presence with current member count."""
        try:
            # Calculate total members across all guilds
            total_members = sum(guild.member_count for guild in self.bot.guilds)

            activity = discord.Streaming(
                name=f"Watching over {total_members} soldiers",
                url="https://www.twitch.tv/metalgearsolid"
            )

            await self.bot.change_presence(
                activity=activity,
                status=discord.Status.online
            )
            print(f"[OK] Presence updated: Watching over {total_members} soldiers")

        except Exception as e:
            logger.error(f"Error updating presence: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        """Bot ready event handler."""
        print(f"[OK] {self.bot.user} is now online and ready!")
        print(f"[FOX] Connected to {len(self.bot.guilds)} guilds")

        for guild in self.bot.guilds:
            guild_key = str(guild.id)
            if guild_key in self.bot.member_data.data:
                member_count = len(self.bot.member_data.data[guild_key])
                print(f" Guild '{guild.name}' ({guild.id}): {member_count} members loaded")
            else:
                print(f" Guild '{guild.name}' ({guild.id}): New guild, no existing data")

        print(" Bot is fully ready and operational!")
        print(" XP-based ranking system active!")

        # Set initial streaming presence
        await self._update_presence()

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

            faq_link = f"<#{FAQ_CHANNEL_ID}>" if FAQ_CHANNEL_ID else "#faq"
            rules_link = f"<#{RULES_CHANNEL_ID}>" if RULES_CHANNEL_ID else "#rules"

            embed = discord.Embed(
                title="Welcome to Outer Heaven!",
                description=f"**{member.display_name}**, welcome to our community!\n\nPlease check out our {faq_link} and {rules_link} for important information.",
                color=0x5865F2
            )

            # Add welcome GIF - replace with your specific GIF URL
            embed.set_image(url="https://cdn.discordapp.com/attachments/1398689075049009182/1427552150296461312/Welcome_to_Outer_Heaven.gif?ex=68ef470b&is=68edf58b&hm=6a74287498217050c87037ef233c984bfc65685d90ac2b05aa030ebfcd9fcf5e&")

            embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)

            await welcome_channel.send(embed=embed)
            logger.info(f"Welcome sent to #{welcome_channel.name} for {member.name}")

            await self.bot.member_data.save_data_async()

            # Update presence with new member count
            await self._update_presence()

        except Exception as e:
            logger.error(f"Error in welcome system: {e}", exc_info=True)


async def setup(bot):
    """Load the MemberEvents cog."""
    await bot.add_cog(MemberEvents(bot))
