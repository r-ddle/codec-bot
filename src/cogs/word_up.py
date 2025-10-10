"""
Word-Up Game Moderation Cog
Monitors the Word-Up channel and ensures players follow the game rules.

Rules:
- Players must type a word that starts with the last letter of the previous word
- Case-insensitive matching (D or d is acceptable)
- Players can send GIFs after their word
- Non-word messages (only GIFs, embeds, etc.) are allowed
"""
import discord
from discord.ext import commands
import re
from config.bot_settings import WORD_UP_CHANNEL_ID, FEATURES
from config.settings import logger


class WordUpGame(commands.Cog):
    """Moderation for the Word-Up word chain game."""

    def __init__(self, bot):
        self.bot = bot
        self.last_word = None  # Track the last valid word
        self.last_message_id = None  # Track last message with a word
        self.enabled = FEATURES.get('word_up_game', True)

    def extract_word(self, content: str) -> str:
        """
        Extract the first word from message content.

        Args:
            content: Message content

        Returns:
            First word found, or empty string if none
        """
        # Remove URLs, mentions, emojis, and extra whitespace
        cleaned = re.sub(r'https?://\S+', '', content)  # Remove URLs
        cleaned = re.sub(r'<@!?\d+>', '', cleaned)  # Remove user mentions
        cleaned = re.sub(r'<@&\d+>', '', cleaned)  # Remove role mentions
        cleaned = re.sub(r'<#\d+>', '', cleaned)  # Remove channel mentions
        cleaned = re.sub(r'<a?:\w+:\d+>', '', cleaned)  # Remove custom emojis
        cleaned = cleaned.strip()

        # Extract first word (letters only)
        match = re.match(r'^([a-zA-Z]+)', cleaned)
        if match:
            return match.group(1).lower()
        return ""

    @commands.Cog.listener()
    async def on_message(self, message):
        """Monitor messages in the Word-Up channel."""
        # Ignore bots
        if message.author.bot:
            return

        # Check if feature is enabled
        if not self.enabled:
            return

        # Only monitor the Word-Up channel
        if message.channel.id != WORD_UP_CHANNEL_ID:
            return

        # Extract word from message
        word = self.extract_word(message.content)

        # If no word found, it might be just a GIF/image - that's allowed
        if not word:
            return

        # If this is the first word, just save it
        if self.last_word is None:
            self.last_word = word
            self.last_message_id = message.id
            logger.info(f"Word-Up: First word set to '{word}'")
            return

        # Check if the word starts with the last letter of the previous word
        expected_start = self.last_word[-1].lower()
        actual_start = word[0].lower()

        if actual_start != expected_start:
            # Rule violation - send warning
            embed = discord.Embed(
                title="Word-Up Rule Violation",
                description=f"{message.author.mention}, your word doesn't follow the rules",
                color=0xFF6B6B
            )

            embed.add_field(
                name="How To Play",
                value=(
                    f"The previous word was: **{self.last_word.upper()}**\n"
                    f"Your word must start with: **{expected_start.upper()}**\n"
                    f"You typed: **{word.upper()}** (starts with {actual_start.upper()})"
                ),
                inline=False
            )

            embed.add_field(
                name="Example",
                value=(
                    f"If the previous word is **{self.last_word.upper()}**, "
                    f"you could say: **{expected_start.upper()}agle**, **{expected_start.upper()}uke**, etc."
                ),
                inline=False
            )

            embed.set_footer(text="Word-Up Game")

            # Reply to the incorrect message
            await message.reply(embed=embed, mention_author=True)

            logger.info(
                f"Word-Up violation: {message.author.name} said '{word}' "
                f"(should start with '{expected_start}')"
            )
        else:
            # Valid word - update tracker
            self.last_word = word
            self.last_message_id = message.id
            logger.debug(f"Word-Up: Valid word '{word}' by {message.author.name}")

    @commands.command(name='wordup_reset')
    @commands.has_permissions(manage_messages=True)
    async def reset_word_up(self, ctx):
        """Reset the Word-Up game (Admin only)."""
        self.last_word = None
        self.last_message_id = None

        embed = discord.Embed(
            title="WORD-UP GAME RESET",
            description="The word chain has been reset. Start a new word!",
            color=0x00D166
        )
        await ctx.send(embed=embed)
        logger.info(f"Word-Up game reset by {ctx.author.name}")

    @commands.command(name='wordup_status')
    async def word_up_status(self, ctx):
        """Check the current Word-Up game status."""
        if self.last_word:
            embed = discord.Embed(
                title="WORD-UP GAME STATUS",
                description=f"The last valid word was: **{self.last_word.upper()}**",
                color=0x599cff
            )
            embed.add_field(
                name="Next Word Must Start With:",
                value=f"**{self.last_word[-1].upper()}**",
                inline=False
            )
        else:
            embed = discord.Embed(
                title="WORD-UP GAME STATUS",
                description="No words have been played yet. Start the chain!",
                color=0x599cff
            )

        await ctx.send(embed=embed)

    @commands.command(name='wordup_set')
    @commands.has_permissions(manage_messages=True)
    async def set_word_up(self, ctx, *, word: str):
        """Manually set the current word (Admin only)."""
        # Extract just the word (first alphabetic sequence)
        cleaned_word = self.extract_word(word)

        if not cleaned_word:
            await ctx.send("❌ Please provide a valid word (letters only).")
            return

        self.last_word = cleaned_word
        self.last_message_id = None

        embed = discord.Embed(
            title="WORD-UP WORD SET",
            description=f"Current word set to: **{cleaned_word.upper()}**",
            color=0x00D166
        )
        embed.add_field(
            name="Next Word Must Start With:",
            value=f"**{cleaned_word[-1].upper()}**",
            inline=False
        )
        await ctx.send(embed=embed)
        logger.info(f"Word-Up word manually set to '{cleaned_word}' by {ctx.author.name}")


async def setup(bot):
    """Load the WordUpGame cog."""
    await bot.add_cog(WordUpGame(bot))
