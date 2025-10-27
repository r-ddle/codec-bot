"""Utility commands cog - General utility commands for members"""
import discord
from discord.ext import commands
from discord.ui import LayoutView

from utils.components_builder import create_info_card, create_rank_perks_info
from config.settings import FAQ_CHANNEL_ID


class UtilityCommands(commands.Cog):
    """Utility commands for server members."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='lvlup')
    async def lvlup(self, ctx):
        """Directs users to FAQ channel for information about the ranking system."""
        faq_channel_id = FAQ_CHANNEL_ID or 1426430395674787920
        faq_channel = self.bot.get_channel(faq_channel_id)

        if faq_channel:
            container = create_info_card(
                title="ranking system information",
                description=f"for information about our ranking system and how to level up, check out {faq_channel.mention}",
                color_code="blue"
            )
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)
        else:
            # Fallback if channel is not found
            container = create_info_card(
                "ranking system information",
                f"visit <#{faq_channel_id}> for information about the ranking system"
            )
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)

    @commands.command(name='rankinfo', aliases=['ranks', 'perks'])
    async def rank_info(self, ctx):
        """Show detailed rank system information with perks."""
        faq_channel_id = FAQ_CHANNEL_ID or 1426430395674787920

        container, button_view = create_rank_perks_info(faq_channel_id)

        layout_view = LayoutView()
        layout_view.add_item(container)

        # Send with layout_view (Container objects), buttons handled separately if needed
        await ctx.send(view=layout_view)


async def setup(bot):
    """Load the utility commands cog."""
    await bot.add_cog(UtilityCommands(bot))
