"""
Kira - Custom Discord Bot for Exile
A chill hangout bot made by r.ddle for Exile server

This bot features:
- XP-based ranking system
- Automatic Discord role assignment based on XP
- Daily bonuses and leaderboards
- Custom commands and interactions
- Server events

Exclusive to: Exile - r.ddle's hangout server
Owner: r.ddle
"""
import asyncio
from config.settings import TOKEN, logger
from core.bot_instance import KiraBot


async def load_extensions(bot: KiraBot):
    """Load all cogs (command modules and event handlers)."""
    extensions = [
        # Command cogs
        'cogs.progression',
        'cogs.profile',  # Profile commands
        'cogs.info',
        'cogs.admin',
        'cogs.migration',  # Rank migration utilities
        'cogs.slash_commands',
        'cogs.server_event',  # Weekly server events
        'cogs.word_up',  # Word-Up game moderation
        'cogs.utility',  # Utility commands
        'cogs.fun_commands',  # Fun games and entertainment
        'cogs.rich_presence',  # Rich Presence management
        # Event handlers
        'events.member_events',
        'events.message_events',
        'events.reaction_events',
        'events.voice_events',  # Voice channel tracking
    ]

    for extension in extensions:
        try:
            await bot.load_extension(extension)
            logger.info(f" Loaded extension: {extension}")
        except Exception as e:
            logger.error(f" Failed to load extension {extension}: {e}")


async def main():
    """Main bot initialization and startup."""
    if not TOKEN:
        logger.error(" CRITICAL ERROR: DISCORD_TOKEN not found!")
        logger.error("Please add DISCORD_TOKEN=your_bot_token to your .env file")
        return

    bot = KiraBot()

    async with bot:
        await load_extensions(bot)
        logger.info(" Starting Kira Discord Bot with XP-Based Ranking...")
        try:
            await bot.start(TOKEN)
        except Exception as e:
            logger.error(f" Mission failed! Error: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info(" Bot shutdown requested by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
