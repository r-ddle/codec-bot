"""
Rich Presence Management Commands
Text-based commands for controlling Kiro's Rich Presence.
Uses the new components system for modern message display.
"""

import discord
from discord.ext import commands
from discord.ui import LayoutView
from config.settings import logger, COMMAND_PREFIX
from utils.components_builder import create_status_container, create_simple_message
import asyncio


class RichPresenceCommands(commands.Cog):
    """Text-based commands for managing the bot's Rich Presence."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="rpcstatus", aliases=["rpc"])
    async def rpc_status(self, ctx: commands.Context):
        """Display current Rich Presence information."""
        try:
            status_data = self.bot.rich_presence.get_status_summary()

            # Create simple status display
            container = create_status_container(
                title="🎧 Current Vibe",
                fields=[
                    {
                        "name": "Activity",
                        "value": "Listening to Exile"
                    },
                    {
                        "name": "Status",
                        "value": f"With {status_data.get('members', 0)} friends"
                    },
                    {
                        "name": "Minecraft",
                        "value": "🎮 Active" if status_data.get('minecraft_active') else "Off"
                    },
                ],
                thumbnail_url=status_data.get('large_image'),
                footer="Exile"
            )

            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)
            logger.info(f"Status displayed to {ctx.author}")

        except Exception as e:
            logger.error(f"Error displaying RPC status: {e}")
            error_container = create_simple_message(
                "❌ Error",
                f"{str(e)}"
            )
            view = LayoutView()
            view.add_item(error_container)
            await ctx.send(view=view)


    @commands.command(name="rpcrestore", aliases=["rpcreset"])
    async def rpc_restore(self, ctx: commands.Context):
        """Restore default RPC."""
        try:
            await self.bot.rich_presence.update_rich_presence()

            restore_msg = create_status_container(
                title="✅ Restored",
                fields=[
                    {"name": "Activity", "value": "Listening to Exile"},
                    {"name": "Status", "value": "With friends"},
                ],
                footer="Exile"
            )

            view = LayoutView()
            view.add_item(restore_msg)
            await ctx.send(view=view)
            logger.info(f"Rich Presence restored by {ctx.author}")

        except Exception as e:
            logger.error(f"Error restoring RPC: {e}")
            error_msg = create_simple_message(
                "❌ Error",
                f"Couldn't restore: {str(e)}"
            )
            view = LayoutView()
            view.add_item(error_msg)
            await ctx.send(view=view)


async def setup(bot):
    """Load the Rich Presence Commands cog."""
    await bot.add_cog(RichPresenceCommands(bot))
    logger.info("✅ Loaded RichPresenceCommands cog")
