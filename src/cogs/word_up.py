"""
Word-Up Game Moderation Cog
Monitors the Word-Up channel and ensures players follow the game rules.

Rules:
- Players must type a word that starts with the last letter of the previous word
- Case-insensitive matching (D or d is acceptable)
- Players can send GIFs after their word
- Non-word messages (only GIFs, embeds, etc.) are allowed
- Tiered rewards: Dictionary words get more points than slang/names
- Anti-spam and anti-troll protection
- Message format: Regular English words or (word) format
"""
import discord
from discord.ext import commands, tasks
from discord.ui import LayoutView
import re
import json
import os
import asyncio
import datetime
from datetime import datetime, timedelta
from typing import Optional, Dict, Set
from config.bot_settings import WORD_UP_CHANNEL_ID, FEATURES
from config.settings import logger
from utils.components_builder import create_error_message, create_success_message, create_info_card, create_stats_container

# Word-Up role ID for trolls
WORDUP_TROLL_ROLE_ID = 1430095326114484315


class WordUpGame(commands.Cog):
    """Moderation for the Word-Up word chain game with enhanced features."""

    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'word_up_data.json'
        self.last_word = None  # Track the last valid word
        self.last_message_id = None  # Track last message with a word
        self.last_player_id = None  # Track the last player who played a valid word
        self.enabled = FEATURES.get('word_up_game', True)

        # User word history and warning tracking
        self.user_word_history: Dict[int, Dict[str, datetime]] = {}  # user_id -> {word: last_used_time}
        self.user_warnings: Dict[int, int] = {}  # user_id -> warning_count

        self.load_data()

    def load_data(self):
        """Load word-up data from JSON file."""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.last_word = data.get('last_word')
                    self.last_message_id = data.get('last_message_id')
                    self.last_player_id = data.get('last_player_id')

                    # Load user word history (convert timestamps back to datetime)
                    history_data = data.get('user_word_history', {})
                    for user_id, words in history_data.items():
                        self.user_word_history[int(user_id)] = {
                            word: datetime.fromisoformat(timestamp)
                            for word, timestamp in words.items()
                        }

                    # Load warnings
                    warnings_data = data.get('user_warnings', {})
                    self.user_warnings = {int(user_id): count for user_id, count in warnings_data.items()}

                    if self.last_word:
                        logger.info(f"Word-Up: Loaded last word '{self.last_word}' from file")
                    else:
                        logger.info("Word-Up: No previous word data found")
            else:
                logger.info("Word-Up: No data file found, starting fresh")
        except Exception as e:
            logger.error(f"Word-Up: Error loading data: {e}")
            self.last_word = None
            self.last_message_id = None
            self.last_player_id = None

    def save_data(self):
        """Save word-up data to JSON file."""
        try:
            # Convert user_word_history datetime objects to ISO format strings
            history_data = {}
            for user_id, words in self.user_word_history.items():
                history_data[str(user_id)] = {
                    word: timestamp.isoformat()
                    for word, timestamp in words.items()
                }

            data = {
                'last_word': self.last_word,
                'last_message_id': self.last_message_id,
                'last_player_id': self.last_player_id,
                'user_word_history': history_data,
                'user_warnings': {str(user_id): count for user_id, count in self.user_warnings.items()}
            }
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Word-Up: Error saving data: {e}")

    def extract_word(self, content: str) -> str:
        """
        Extract the first word from message content.
        Only accepts ASCII English letters to prevent Unicode bypasses.

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

        # Extract first word (ASCII English letters only)
        # This prevents Unicode homoglyphs and Cyrillic characters
        match = re.match(r'^([a-zA-Z]+)', cleaned)
        if match:
            word = match.group(1).lower()
            # Double-check: ensure all characters are ASCII English letters
            if all(ord(c) < 128 and c.isalpha() for c in word):
                return word
        return ""

    def is_valid_message_format(self, message: discord.Message) -> tuple[bool, str]:
        """
        Check if message follows allowed format: word, (word), or GIF only.

        Args:
            message: Discord message object

        Returns:
            Tuple of (is_valid, word_or_reason)
        """
        content = message.content.strip()

        # Check if it's a GIF attachment
        has_gif = any(
            attachment.content_type and 'gif' in attachment.content_type.lower()
            for attachment in message.attachments
        )

        # Allow GIF-only messages
        if has_gif and not content:
            return (True, "gif")

        # Check if content matches (word) pattern
        parenthesis_match = re.match(r'^\(([a-zA-Z]+)\)$', content)
        if parenthesis_match:
            word = parenthesis_match.group(1).lower()
            # Verify ASCII English letters only
            if all(ord(c) < 128 and c.isalpha() for c in word):
                return (True, word)

        # Check if it's just a regular word (ASCII English letters only)
        word_match = re.match(r'^([a-zA-Z]+)$', content)
        if word_match:
            word = word_match.group(1).lower()
            # Verify ASCII English letters only
            if all(ord(c) < 128 and c.isalpha() for c in word):
                return (True, word)

        # Check for non-English/special characters
        if content and not re.match(r'^[a-zA-Z()]*$', content):
            return (False, "non-english special characters are not allowed")

        return (False, "please send a word or GIF only")

    def detect_gibberish(self, word: str) -> bool:
        """
        Detect if a word is likely gibberish.
        Very lenient - only catches obvious spam/exploits.

        Args:
            word: Word to check

        Returns:
            True if likely gibberish, False otherwise
        """
        word = word.lower()

        # Too short or too long
        if len(word) < 2 or len(word) > 30:
            return True

        # Check for too many repeated characters (obvious spam)
        for i in range(len(word) - 4):
            if word[i] == word[i+1] == word[i+2] == word[i+3] == word[i+4]:
                return True

        # Must have at least one vowel (y counts as vowel)
        vowels = 'aeiouy'
        if not any(char in vowels for char in word):
            return True

        # Check for extreme consonant streaks (more than 7)
        consonant_streak = 0
        for char in word:
            if char not in vowels:
                consonant_streak += 1
                if consonant_streak > 7:
                    return True
            else:
                consonant_streak = 0

        return False

    def detect_invisible_chars(self, content: str) -> bool:
        """
        Detect invisible characters or zero-width characters.

        Args:
            content: Message content

        Returns:
            True if invisible chars detected, False otherwise
        """
        invisible_chars = [
            '\u200b',  # Zero width space
            '\u200c',  # Zero width non-joiner
            '\u200d',  # Zero width joiner
            '\ufeff',  # Zero width no-break space
            '\u2060',  # Word joiner
        ]
        return any(char in content for char in invisible_chars)

    def calculate_word_points(self, word: str) -> tuple[int, int]:
        """
        Calculate points and XP for a word based on length only.
        Simple system - all valid words accepted.

        Args:
            word: The word

        Returns:
            Tuple of (points, xp)
        """
        word_len = len(word)

        # Simple points by length
        if word_len <= 4:
            points = 10
            xp = 1
        elif word_len <= 6:
            points = 15
            xp = 1
        elif word_len <= 8:
            points = 20
            xp = 2
        else:
            points = 25
            xp = 2

        return points, xp

    def check_word_cooldown(self, user_id: int, word: str) -> Optional[datetime]:
        """
        Check if a user has used this word recently (3 day cooldown).

        Args:
            user_id: User ID
            word: Word to check

        Returns:
            None if word can be used, otherwise the datetime when it was last used
        """
        if user_id not in self.user_word_history:
            return None

        word = word.lower()
        if word in self.user_word_history[user_id]:
            last_used = self.user_word_history[user_id][word]
            cooldown_end = last_used + timedelta(days=3)
            if datetime.now() < cooldown_end:
                return last_used

        return None

    def record_word_usage(self, user_id: int, word: str):
        """
        Record that a user used a word.

        Args:
            user_id: User ID
            word: Word used
        """
        if user_id not in self.user_word_history:
            self.user_word_history[user_id] = {}

        # Clean up old entries (older than 3 days)
        cutoff = datetime.now() - timedelta(days=3)
        self.user_word_history[user_id] = {
            w: t for w, t in self.user_word_history[user_id].items()
            if t > cutoff
        }

        # Record new usage
        self.user_word_history[user_id][word.lower()] = datetime.now()

    async def add_warning(self, member: discord.Member) -> int:
        """
        Add a warning to a user and apply punishment if needed.

        Args:
            member: Discord member

        Returns:
            Number of warnings the user now has
        """
        user_id = member.id
        self.user_warnings[user_id] = self.user_warnings.get(user_id, 0) + 1
        warnings = self.user_warnings[user_id]

        if warnings >= 3:
            # Apply troll role and timeout
            try:
                troll_role = member.guild.get_role(WORDUP_TROLL_ROLE_ID)
                if troll_role:
                    await member.add_roles(troll_role, reason="Word-Up spam/abuse (3 warnings)")

                # Timeout for 5 minutes
                timeout_until = discord.utils.utcnow() + timedelta(minutes=5)
                await member.timeout(timeout_until, reason="Word-Up spam/abuse (3 warnings)")

                # Reset warnings after punishment
                self.user_warnings[user_id] = 0

                logger.info(f"Word-Up: Applied troll role and timeout to {member.name} (3 warnings)")
            except Exception as e:
                logger.error(f"Error applying Word-Up punishment: {e}")

        self.save_data()
        return warnings

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

        # Validate message format first
        is_valid_format, word_or_reason = self.is_valid_message_format(message)

        if not is_valid_format:
            await message.delete()
            container = create_error_message(
                title="invalid format",
                description=f"{message.author.mention} {word_or_reason}\n\nallowed formats:\n• word - regular english words\n• (word) - word in parentheses\n• gif attachments only"
            )
            view = LayoutView()
            view.add_item(container)
            await message.channel.send(view=view, delete_after=10)
            warnings = await self.add_warning(message.author)
            logger.warning(f"word-up: invalid format from {message.author.name}")
            return

        # If it's just a GIF, allow it
        if word_or_reason == "gif":
            return

        word = word_or_reason

        # Detect invisible characters (extra safety check)
        if self.detect_invisible_chars(message.content):
            await message.delete()
            container = create_error_message(
                title="invalid input",
                description="invalid characters detected"
            )
            view = LayoutView()
            view.add_item(container)
            await message.channel.send(view=view, delete_after=10)
            warnings = await self.add_warning(message.author)
            logger.warning(f"word-up: invisible chars detected from {message.author.name}")
            return

        # Detect gibberish
        if self.detect_gibberish(word):
            await message.delete()
            container = create_error_message(
                title="invalid word",
                description=f"{message.author.mention} that doesn't look like a valid word"
            )
            view = LayoutView()
            view.add_item(container)
            await message.channel.send(view=view, delete_after=10)
            warnings = await self.add_warning(message.author)
            logger.info(f"word-up: gibberish detected from {message.author.name}: {word}")
            return

        # If this is the first word, just save it
        if self.last_word is None:
            self.last_word = word
            self.last_message_id = message.id
            self.last_player_id = message.author.id
            self.save_data()

            # Award minimal points for first word
            await self.award_points(message.author, message.guild.id, 10, 0)

            logger.info(f"word-up: first word set to '{word}'")
            return

        # Check if the same player is trying to play consecutively
        if self.last_player_id == message.author.id:
            # Delete the violating message immediately
            await message.delete()

            container = create_error_message(
                title="can't play consecutively",
                description=f"{message.author.mention} you can't play two words in a row! wait for another player to go first.\n\n**last player:** {message.author.display_name} (you)\n**your word:** {word.upper()}"
            )
            view = LayoutView()
            view.add_item(container)
            await message.channel.send(view=view, delete_after=10)
            logger.info(f"word-up: {message.author.name} tried to play consecutively with '{word}'")
            return

        # Check if the word starts with the last letter of the previous word
        expected_start = self.last_word[-1].lower()
        actual_start = word[0].lower()

        if actual_start != expected_start:
            # Rule violation - delete the violating message immediately
            await message.delete()

            container = create_error_message(
                title="wrong starting letter",
                description=f"{message.author.mention} your word must start with **{expected_start.upper()}**\n\n**previous word:** {self.last_word.upper()}\n**your word:** {word.upper()} (starts with {actual_start.upper()})"
            )
            view = LayoutView()
            view.add_item(container)
            await message.channel.send(view=view, delete_after=15)
            warnings = await self.add_warning(message.author)

            logger.info(
                f"word-up violation: {message.author.name} said '{word}' "
                f"(should start with '{expected_start}') - warning {warnings}/3"
            )
            return

        # Check word cooldown (3 day duplicate prevention)
        last_used = self.check_word_cooldown(message.author.id, word)
        if last_used:
            # Delete the violating message immediately
            await message.delete()

            cooldown_end = last_used + timedelta(days=3)
            time_left = cooldown_end - datetime.now()
            hours_left = int(time_left.total_seconds() / 3600)

            container = create_error_message(
                title="Word on Cooldown",
                description=f"{message.author.mention} You used that word recently\n\n**Cooldown:** {hours_left} hours remaining"
            )
            view = LayoutView()
            view.add_item(container)
            await message.channel.send(view=view, delete_after=10)
            logger.info(f"Word-Up: {message.author.name} tried to reuse word '{word}' (cooldown)")
            return

        # Simple point calculation - all words accepted
        points, xp = self.calculate_word_points(word)

        # Award points and XP
        await self.award_points(message.author, message.guild.id, points, xp)

        # Record word usage
        self.record_word_usage(message.author.id, word)

        # Valid word - update tracker
        self.last_word = word
        self.last_message_id = message.id
        self.last_player_id = message.author.id
        self.save_data()

        # Silent - no reactions or messages for normal words
        logger.debug(f"Word-Up: Valid word '{word}' by {message.author.name} - {points} pts, {xp} XP")

    async def award_points(self, member: discord.Member, guild_id: int, points: int, xp: int):
        """
        Award Word-Up points and XP to a member.

        Args:
            member: Discord member
            guild_id: Guild ID
            points: Word-Up points to award
            xp: XP to award
        """
        try:
            member_data = self.bot.member_data.get_member_data(member.id, guild_id)

            # Initialize word_up_points if not exists
            if 'word_up_points' not in member_data:
                member_data['word_up_points'] = 0

            # Add points and XP
            member_data['word_up_points'] += points
            if xp > 0:
                member_data['xp'] = member_data.get('xp', 0) + xp

            # Update member data
            self.bot.member_data.data[str(guild_id)][str(member.id)] = member_data
            self.bot.member_data.schedule_save()

            logger.debug(f"Awarded {points} Word-Up points and {xp} XP to {member.name}")
        except Exception as e:
            logger.error(f"Error awarding Word-Up points: {e}")

    @commands.command(name='wordup_reset')
    @commands.has_permissions(manage_messages=True)
    async def reset_word_up(self, ctx):
        """Reset the Word-Up game (Admin only)."""
        self.last_word = None
        self.last_message_id = None
        self.last_player_id = None
        self.user_word_history.clear()
        self.user_warnings.clear()
        self.save_data()

        container = create_success_message(
            title="Word-Up Game Reset",
            description="The word chain has been reset. Start a new word"
        )
        view = LayoutView()
        view.add_item(container)
        await ctx.send(view=view)
        logger.info(f"Word-Up game reset by {ctx.author.name}")

    @commands.command(name='wordup_status')
    async def word_up_status(self, ctx):
        """Check the current Word-Up game status."""
        if self.last_word:
            stats = {
                "Last Word": f"**{self.last_word.upper()}**",
                "Next Letter": f"**{self.last_word[-1].upper()}**"
            }

            # Show last player if available
            if self.last_player_id:
                try:
                    last_player = await ctx.guild.fetch_member(self.last_player_id)
                    stats["Last Player"] = f"**{last_player.display_name}**"
                except:
                    stats["Last Player"] = "**Unknown**"

            container = create_stats_container(
                title="Word-Up Game Status",
                description="",
                stats=stats,
                color_code="blue"
            )
        else:
            container = create_info_card(
                title="Word-Up Game Status",
                description="No words have been played yet. Start the chain",
                color_code="blue"
            )

        view = LayoutView()
        view.add_item(container)
        await ctx.send(view=view)

    @commands.command(name='wordup_set')
    @commands.has_permissions(manage_messages=True)
    async def set_word_up(self, ctx, *, word: str):
        """Manually set the current word (Admin only)."""
        cleaned_word = self.extract_word(word)

        if not cleaned_word:
            container = create_error_message(
                title="Invalid Word",
                description="Please provide a valid word"
            )
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)
            return

        self.last_word = cleaned_word
        self.last_message_id = None
        self.last_player_id = None
        self.save_data()

        container = create_success_message(
            title="Word Set",
            description=f"Current word: **{cleaned_word.upper()}**\n**Next Letter:** {cleaned_word[-1].upper()}"
        )
        view = LayoutView()
        view.add_item(container)
        await ctx.send(view=view)
        logger.info(f"Word-Up word manually set to '{cleaned_word}' by {ctx.author.name}")

    @commands.command(name='wordup_clearwarnings')
    @commands.has_permissions(manage_messages=True)
    async def clear_warnings(self, ctx, member: discord.Member):
        """Clear warnings for a member (Admin only)."""
        if member.id in self.user_warnings:
            del self.user_warnings[member.id]
            self.save_data()

        container = create_success_message(
            title="Warnings Cleared",
            description=f"Warnings cleared for {member.mention}"
        )
        view = LayoutView()
        view.add_item(container)
        await ctx.send(view=view)
        logger.info(f"Word-Up warnings cleared for {member.name} by {ctx.author.name}")


    @commands.command(name='leaderboard_wordup', aliases=['lb_wordup', 'wordup_lb'])
    async def leaderboard_wordup(self, ctx):
        """Display Word-Up points leaderboard."""
        try:
            guild_id = ctx.guild.id
            guild_data = self.bot.member_data.data.get(str(guild_id), {})

            # Collect Word-Up scores
            scores = []
            for member_id, data in guild_data.items():
                word_up_points = data.get('word_up_points', 0)
                if word_up_points > 0:
                    try:
                        member = await ctx.guild.fetch_member(int(member_id))
                        scores.append((member.display_name, word_up_points))
                    except:
                        continue

            if not scores:
                container = create_info_card(
                    title="No Scores Yet",
                    description="No Word-Up scores yet. Start playing",
                    color_code="red"
                )
                view = LayoutView()
                view.add_item(container)
                await ctx.send(view=view)
                return

            # Sort by points
            scores.sort(key=lambda x: x[1], reverse=True)
            top_10 = scores[:10]

            # Format leaderboard data for image generation
            leaderboard_data = [
                (idx + 1, name, points, "WORD-UP")
                for idx, (name, points) in enumerate(top_10)
            ]

            # Generate leaderboard image
            from utils.leaderboard_gen import generate_leaderboard

            img = generate_leaderboard(
                leaderboard_data=leaderboard_data,
                category="WORD-UP POINTS",
                unit_suffix="PTS",
                guild_name=ctx.guild.name.upper()
            )

            # Save and send
            filename = f"wordup_leaderboard_{ctx.guild.id}.png"
            img.save(filename)

            file = discord.File(filename, filename="wordup_leaderboard.png")
            await ctx.send(file=file)

            # Clean up
            os.remove(filename)

            logger.info(f"Word-Up leaderboard generated for {ctx.guild.name}")

        except Exception as e:
            logger.error(f"Error generating Word-Up leaderboard: {e}")
            container = create_error_message(
                title="Error",
                description="Error generating leaderboard"
            )
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)


async def setup(bot):
    """Load the WordUpGame cog."""
    await bot.add_cog(WordUpGame(bot))
