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

        # Store old rank before XP change
        user_data = self.bot.member_data.get_member_data(user.id, guild_id)
        old_rank_user = user_data.get('rank', 'Rookie')

        # Give XP to reaction giver
        rank_changed, new_rank = self.bot.member_data.add_xp(
            user.id, guild_id,
            ACTIVITY_REWARDS["reaction"]["xp"],
            "reaction"
        )

        # Send promotion notification if rank changed
        if rank_changed:
            await self._send_promotion_notification(reaction.message.channel, user, old_rank_user, new_rank, "reaction")

        # Give XP to message author if different person
        if not reaction.message.author.bot and reaction.message.author.id != user.id:
            # Store old rank before XP change
            author_data = self.bot.member_data.get_member_data(reaction.message.author.id, guild_id)
            old_rank_author = author_data.get('rank', 'Rookie')

            rank_changed_author, new_rank_author = self.bot.member_data.add_xp(
                reaction.message.author.id, guild_id,
                ACTIVITY_REWARDS["reaction_received"]["xp"],
                "reaction_received"
            )

            # Send promotion notification if rank changed
            if rank_changed_author:
                await self._send_promotion_notification(
                    reaction.message.channel, reaction.message.author, old_rank_author, new_rank_author, "reaction_received"
                )

    async def _send_promotion_notification(self, channel, member, old_rank, new_rank, activity_type):
        """Helper method to send promotion notifications with image."""
        try:
            import asyncio
            from io import BytesIO
            from utils.role_manager import update_member_roles
            from utils.rank_system import get_rank_data_by_name
            from utils.daily_supply_gen import generate_promotion_card
            from config.settings import logger

            # Update Discord role
            role_updated = await update_member_roles(member, new_rank)

            # Get member data
            member_data = self.bot.member_data.get_member_data(member.id, channel.guild.id)

            # Get old rank (we need to track this better, for now use a fallback)
            # Since we don't store old_rank, we'll need to infer it or show "Previous Rank"
            old_rank = "Previous Rank"  # This is a limitation we can improve later

            # Get role name if granted
            rank_data = get_rank_data_by_name(new_rank)
            role_name = rank_data.get("role_name") if role_updated else None

            # Generate promotion card image (off the main thread)
            img = await asyncio.to_thread(
                generate_promotion_card,
                username=member.display_name,
                old_rank=old_rank,
                new_rank=new_rank,
                current_xp=member_data['xp'],
                role_granted=role_name
            )

            # Convert to Discord file
            image_bytes = BytesIO()
            await asyncio.to_thread(img.save, image_bytes, format='PNG')
            image_bytes.seek(0)

            file = discord.File(fp=image_bytes, filename="promotion.png")

            # Add context message
            if activity_type == "reaction":
                context_msg = "**Rank Promotion** - Earned through giving reactions!"
            elif activity_type == "reaction_received":
                context_msg = "**Rank Promotion** - Earned through receiving reactions!"
            else:
                context_msg = "**Rank Promotion**"

            await channel.send(content=context_msg, file=file)
            logger.info(f"PROMOTION: {member.name} promoted to {new_rank} via {activity_type}")

        except Exception as e:
            from config.settings import logger
            logger.error(f"Error sending reaction promotion notification: {e}")

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
