"""
Message events - Handlers for message-related activities and XP rewards.
"""
import discord
from discord.ext import commands
import asyncio
import time
import random

from config.constants import ACTIVITY_REWARDS, CODEC_RESPONSES
from config.settings import MESSAGE_COOLDOWN, CODEC_CONVERSATION_TIMEOUT, logger
from utils.formatters import format_number
from utils.rank_system import get_rank_data_by_name
from utils.role_manager import update_member_roles


class MessageEvents(commands.Cog):
    """Event handlers for message activities."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle message events, XP rewards, and codec conversations."""
        # Ignore bot messages
        if message.author.bot:
            return

        # Ignore DM messages (no guild)
        if message.guild is None:
            return

        # Check for codec conversation responses
        if message.channel.id in self.bot.codec_conversations and self.bot.codec_conversations[message.channel.id]['active']:
            codec_data = self.bot.codec_conversations[message.channel.id]

            if time.time() - codec_data['start_time'] < CODEC_CONVERSATION_TIMEOUT:
                response = random.choice(CODEC_RESPONSES)

                if codec_data['messages'] >= 3:
                    response = "I can talk now well... *codec static* Campbell out."
                    self.bot.codec_conversations[message.channel.id]['active'] = False

                await asyncio.sleep(2)
                await message.channel.send(response)
                codec_data['messages'] += 1
            else:
                self.bot.codec_conversations[message.channel.id]['active'] = False

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

        # Get XP multiplier if shop system is enabled (Phase 3)
        xp_multiplier = 1.0
        if hasattr(self.bot, 'shop_system'):
            xp_multiplier = await self.bot.shop_system.get_active_multiplier(member_id, guild_id)

        # Message rewards only if cooldown has passed
        if current_time - last_msg_time > MESSAGE_COOLDOWN:
            member_data["last_message_time"] = current_time

            # Give base message rewards (apply XP multiplier)
            message_xp = int(ACTIVITY_REWARDS["message"]["xp"] * xp_multiplier)
            message_rank_changed, message_new_rank = self.bot.member_data.add_xp(
                member_id, guild_id,
                message_xp,
                "message"
            )

            if message_rank_changed:
                rank_changed = True
                new_rank = message_new_rank

            # ONLY notify if there's a genuine rank change
            if rank_changed and old_rank != new_rank:
                try:
                    await message.add_reaction("")
                    role_updated = await update_member_roles(message.author, new_rank)

                    embed = discord.Embed(
                        title=" RANK PROMOTION",
                        description=f"**{message.author.display_name}** promoted from **{old_rank}** to **{new_rank}**!",
                        color=0x599cff
                    )

                    if role_updated:
                        rank_data = get_rank_data_by_name(new_rank)
                        role_name = rank_data.get("role_name", new_rank)
                        embed.add_field(name=" ROLE ASSIGNED", value=f"Discord role **{role_name}** granted!", inline=False)
                    else:
                        embed.add_field(name=" ROLE UPDATE", value="Role assignment failed - contact admin", inline=False)

                    # Show current stats
                    updated_member_data = self.bot.member_data.get_member_data(member_id, guild_id)
                    embed.add_field(
                        name="CURRENT STATUS",
                        value=f"```\nRank: {new_rank}\nXP: {format_number(updated_member_data['xp'])}\n```",
                        inline=False
                    )

                    await message.channel.send(embed=embed)
                    # Schedule a background save; avoid forcing Neon sync on the event loop
                    self.bot.member_data.schedule_save()
                    asyncio.create_task(self.bot.member_data.save_data_async(force=False))

                    logger.info(f"PROMOTION: {message.author.name} promoted from {old_rank} to {new_rank}")

                except Exception as e:
                    logger.error(f"Error in promotion system: {e}")


async def setup(bot):
    """Load the MessageEvents cog."""
    await bot.add_cog(MessageEvents(bot))
