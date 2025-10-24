"""Utility commands cog - General utility commands for members"""
import discord
from discord.ext import commands


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
            embed = discord.Embed(
                title="Ranking System Information",
                description=f"For information about our ranking system and how to level up, check out {faq_channel.mention}!",
                color=0x599cff
            )
            await ctx.send(embed=embed)
        else:
            # Fallback if channel is not found
            await ctx.send(f"Check out the FAQ channel for information about the ranking system: <#{self.FAQ_CHANNEL_ID}>")


async def setup(bot):
    """Load the utility commands cog."""
    await bot.add_cog(UtilityCommands(bot))
