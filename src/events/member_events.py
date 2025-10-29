"""
Member events - Handlers for member join and ready events.
"""
import discord
from discord.ext import commands
from discord.ui import LayoutView, Container, Section, TextDisplay, Thumbnail, View, Button
from datetime import datetime, timezone

from config.settings import WELCOME_CHANNEL_ID, FAQ_CHANNEL_ID, RULES_CHANNEL_ID, logger


class MemberEvents(commands.Cog):
    """Event handlers for member-related activities with simple streaming presence."""

    def __init__(self, bot):
        self.bot = bot



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

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Welcome system for new members."""
        logger.info(f"new member joined: {member.name} (ID: {member.id}) in {member.guild.name}")

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
                logger.warning(f"no suitable welcome channel found in {member.guild.name}")
                return

            # Create welcome container with Components v2
            container = Container()
            container.image_url = "https://cdn.discordapp.com/attachments/1398689075049009182/1427552150296461312/Welcome_to_Outer_Heaven.gif?ex=68ef470b&is=68edf58b&hm=6a74287498217050c87037ef233c984bfc65685d90ac2b05aa030ebfcd9fcf5e&"

            # Add thumbnail
            thumbnail = Thumbnail(member.avatar.url if member.avatar else member.default_avatar.url)

            # Create welcome section
            section = Section()
            welcome_text = TextDisplay(
                content=f"# welcome to exile\n**{member.display_name}**, welcome to our community\n\ncheck out the buttons below for important information"
            )
            section.add_item(welcome_text)
            section.add_item(thumbnail)

            container.add_item(section)

            # Create view with buttons
            layout_view = LayoutView()
            layout_view.add_item(container)

            # Create button view
            button_view = View(timeout=None)

            # FAQ button
            if FAQ_CHANNEL_ID:
                faq_button = Button(
                    style=discord.ButtonStyle.gray,
                    label="faq",
                    custom_id="welcome_faq"
                )
                faq_button.callback = lambda interaction: self._faq_button_callback(interaction, FAQ_CHANNEL_ID)
                button_view.add_item(faq_button)

            # Rules button
            if RULES_CHANNEL_ID:
                rules_button = Button(
                    style=discord.ButtonStyle.gray,
                    label="rules",
                    custom_id="welcome_rules"
                )
                rules_button.callback = lambda interaction: self._rules_button_callback(interaction, RULES_CHANNEL_ID)
                button_view.add_item(rules_button)

            # Get started button
            start_button = Button(
                style=discord.ButtonStyle.gray,
                label="get started",
                custom_id="welcome_start"
            )
            start_button.callback = self._get_started_callback
            button_view.add_item(start_button)

            # Add buttons to layout view
            for item in button_view.children:
                layout_view.add_item(item)

            await welcome_channel.send(view=layout_view)
            logger.info(f"welcome sent to #{welcome_channel.name} for {member.name}")

            await self.bot.member_data.save_data_async()

            # Update presence with new member count
            await self._update_presence()

        except Exception as e:
            logger.error(f"error in welcome system: {e}", exc_info=True)

    async def _faq_button_callback(self, interaction: discord.Interaction, channel_id: int):
        """Handle FAQ button click."""
        await interaction.response.send_message(
            f"check out <#{channel_id}> for frequently asked questions",
            ephemeral=True
        )

    async def _rules_button_callback(self, interaction: discord.Interaction, channel_id: int):
        """Handle Rules button click."""
        await interaction.response.send_message(
            f"please read our rules in <#{channel_id}>",
            ephemeral=True
        )

    async def _get_started_callback(self, interaction: discord.Interaction):
        """Handle Get Started button click."""
        await interaction.response.send_message(
            "welcome to exile\n\n"
            "start chatting to earn xp and rank up through our ranking system\n"
            "use `!status` to check your progress\n"
            "use `!help` to see available commands",
            ephemeral=True
        )


async def setup(bot):
    """Load the MemberEvents cog."""
    await bot.add_cog(MemberEvents(bot))
