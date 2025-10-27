"""Utility commands cog - General utility commands for members"""
import discord
from discord.ext import commands
from discord.ui import LayoutView

from utils.components_builder import create_info_card


class UtilityCommands(commands.Cog):
    """Utility commands for server members."""

    # FAQ Channel ID for leveling up
    FAQ_CHANNEL_ID = 1426430395674787920

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='lvlup')
    async def lvlup(self, ctx):
        """Directs users to FAQ channel for information about the ranking system."""
        faq_channel = self.bot.get_channel(self.FAQ_CHANNEL_ID)

        if faq_channel:
            container = create_info_card(
                title="Ranking System Information",
                description=f"For information about our ranking system and how to level up, check out {faq_channel.mention}!",
                color_code="blue"
            )
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)
        else:
            # Fallback if channel is not found
            from utils.components_builder import create_info_card
            from discord.ui import LayoutView
            container = create_info_card(
                "Ranking System Information",
                f"Visit <#{self.FAQ_CHANNEL_ID}> for information about the ranking system!"
            )
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)


async def setup(bot):
    """Load the utility commands cog."""
    await bot.add_cog(UtilityCommands(bot))
