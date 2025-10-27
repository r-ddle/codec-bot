"""
Message events - Handlers for message-related activities and XP rewards.
"""
import discord
from discord.ext import commands
import asyncio
import time
import random

from config.constants import ACTIVITY_REWARDS
from config.settings import MESSAGE_COOLDOWN, logger
from utils.formatters import format_number
from utils.rank_system import get_rank_data_by_name
from utils.role_manager import update_member_roles


class MessageEvents(commands.Cog):
    """Event handlers for message activities."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle message events and XP rewards."""
        # Ignore bot messages
        if message.author.bot:
            return

        # Ignore DM messages (no guild)
        if message.guild is None:
            return

        member_id = message.author.id
        guild_id = message.guild.id
        current_time = time.time()

        member_data = self.bot.member_data.get_member_data(member_id, guild_id)
        last_msg_time = member_data.get("last_message_time", 0)

        # Store old rank for comparison
        old_rank = member_data["rank"]
        rank_changed = False
        new_rank = old_rank

        # Message rewards only if cooldown has passed
        if current_time - last_msg_time > MESSAGE_COOLDOWN:
            member_data["last_message_time"] = current_time

            # Update activity streak
            streak_info = self.bot.member_data.update_activity_streak(member_id, guild_id)

            # Calculate XP with streak bonus
            base_message_xp = ACTIVITY_REWARDS["message"]["xp"]
            streak_bonus = streak_info.get('xp_bonus', 0)
            total_xp = base_message_xp + streak_bonus

            # Give message rewards with streak bonus
            message_rank_changed, message_new_rank = self.bot.member_data.add_xp(
                member_id, guild_id,
                total_xp,
                "message"
            )

            if message_rank_changed:
                rank_changed = True
                new_rank = message_new_rank

            # ONLY notify if there's a genuine rank change
            if rank_changed and old_rank != new_rank:
                try:
                    from io import BytesIO
                    from utils.daily_supply_gen import generate_promotion_card

                    await message.add_reaction("🎖️")
                    role_updated = await update_member_roles(message.author, new_rank)

                    # Get role name if granted
                    rank_data = get_rank_data_by_name(new_rank)
                    role_name = rank_data.get("role_name") if role_updated else None

                    # Get updated member data
                    updated_member_data = self.bot.member_data.get_member_data(member_id, guild_id)

                    # Generate promotion card image (off the main thread)
                    img = await asyncio.to_thread(
                        generate_promotion_card,
                        username=message.author.display_name,
                        old_rank=old_rank,
                        new_rank=new_rank,
                        current_xp=updated_member_data['xp'],
                        role_granted=role_name
                    )

                    # Convert to Discord file
                    image_bytes = BytesIO()
                    await asyncio.to_thread(img.save, image_bytes, format='PNG')
                    image_bytes.seek(0)

                    file = discord.File(fp=image_bytes, filename="promotion.png")

                    # Add context message
                    context_msg = f"**rank promotion** - {message.author.mention} promoted from **{old_rank}** to **{new_rank}**!"

                    await message.channel.send(content=context_msg, file=file)

                    # Schedule a background save; avoid forcing Neon sync on the event loop
                    self.bot.member_data.schedule_save()
                    asyncio.create_task(self.bot.member_data.save_data_async(force=False))

                    logger.info(f"PROMOTION: {message.author.name} promoted from {old_rank} to {new_rank}")

                except Exception as e:
                    logger.error(f"Error in promotion system: {e}")


async def setup(bot):
    """Load the MessageEvents cog."""
    await bot.add_cog(MessageEvents(bot))
