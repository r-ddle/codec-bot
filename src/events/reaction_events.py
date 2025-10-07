"""
Reaction events - Handlers for reaction-based XP rewards.
"""
import discord
from discord.ext import commands

from config.constants import ACTIVITY_REWARDS


class ReactionEvents(commands.Cog):
    """Event handlers for reaction activities."""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Handle reaction add events and award XP."""
        if user.bot:
            return
            
        guild_id = reaction.message.guild.id
        
        # Give XP to reaction giver
        self.bot.member_data.add_xp_and_gmp(
            user.id, guild_id,
            ACTIVITY_REWARDS["reaction"]["gmp"],
            ACTIVITY_REWARDS["reaction"]["xp"],
            "reaction"
        )
        
        # Give XP to message author if different person
        if not reaction.message.author.bot and reaction.message.author.id != user.id:
            self.bot.member_data.add_xp_and_gmp(
                reaction.message.author.id, guild_id,
                ACTIVITY_REWARDS["reaction_received"]["gmp"],
                ACTIVITY_REWARDS["reaction_received"]["xp"],
                "reaction_received"
            )

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Handle command errors."""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(" Insufficient security clearance!")
        elif isinstance(error, commands.CommandNotFound):
            await ctx.send(" Unknown codec frequency")
        else:
            await ctx.send(" Operation failed.")
            from config.settings import logger
            logger.error(f"Command error: {error}")


async def setup(bot):
    """Load the ReactionEvents cog."""
    await bot.add_cog(ReactionEvents(bot))
