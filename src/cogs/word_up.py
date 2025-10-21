"""
Word-Up Game Moderation Cog
Monitors the Word-Up channel and ensures players follow the game rules.

Rules:
- Players must type a word that starts with the last letter of the previous word
- Case-insensitive matching (D or d is acceptable)
- Players can send GIFs after their word
- Non-word messages (only GIFs, embeds, etc.) are allowed
- Tiered rewards: Dictionary words get more points than slang/names
- Daily challenges for bonus rewards
- Anti-spam and anti-troll protection
"""
import discord
from discord.ext import commands, tasks
import re
import json
import os
import aiohttp
import asyncio
import random
from datetime import datetime, timedelta
from typing import Optional, Dict, Set
from config.bot_settings import WORD_UP_CHANNEL_ID, FEATURES
from config.settings import logger

# Word-Up role ID for trolls
WORDUP_TROLL_ROLE_ID = 1430095326114484315


class WordUpGame(commands.Cog):
    """Moderation for the Word-Up word chain game with enhanced features."""

    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'word_up_data.json'
        self.last_word = None  # Track the last valid word
        self.last_message_id = None  # Track last message with a word
        self.enabled = FEATURES.get('word_up_game', True)

        # Daily challenge system
        self.daily_challenge = None
        self.daily_challenge_word = None
        self.daily_challenge_expires = None
        self.challenge_participants = set()

        # User word history and warning tracking
        self.user_word_history: Dict[int, Dict[str, datetime]] = {}  # user_id -> {word: last_used_time}
        self.user_warnings: Dict[int, int] = {}  # user_id -> warning_count

        self.load_data()
        self.daily_challenge_task.start()
        self.challenge_expiry_check.start()

        # Word list for daily challenges (sophisticated words)
        self.challenge_words = [
            'ephemeral', 'ubiquitous', 'juxtapose', 'paradigm', 'eloquent',
            'resilient', 'pragmatic', 'meticulous', 'ambiguous', 'profound',
            'tenacious', 'benevolent', 'eloquence', 'luminous', 'intricate',
            'magnificent', 'serene', 'vivacious', 'zealous', 'aesthetic',
            'catalyst', 'diligent', 'elaborate', 'facetious', 'gregarious',
            'harmonious', 'innovative', 'judicious', 'kinetic', 'labyrinth'
        ]

    def load_data(self):
        """Load word-up data from JSON file."""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.last_word = data.get('last_word')
                    self.last_message_id = data.get('last_message_id')

                    # Load daily challenge data
                    self.daily_challenge = data.get('daily_challenge')
                    self.daily_challenge_word = data.get('daily_challenge_word')
                    challenge_expires_str = data.get('daily_challenge_expires')
                    if challenge_expires_str:
                        self.daily_challenge_expires = datetime.fromisoformat(challenge_expires_str)

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
                'daily_challenge': self.daily_challenge,
                'daily_challenge_word': self.daily_challenge_word,
                'daily_challenge_expires': self.daily_challenge_expires.isoformat() if self.daily_challenge_expires else None,
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

    async def validate_word_dictionary(self, word: str) -> tuple[bool, str]:
        """
        Validate if a word exists in the dictionary using Free Dictionary API.
        Only used for daily challenge validation.

        Args:
            word: Word to validate

        Returns:
            Tuple of (is_valid, word_type) - always returns (True, 'valid') for regular game
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://api.dictionaryapi.dev/api/v2/entries/en/{word.lower()}",
                    timeout=aiohttp.ClientTimeout(total=3)
                ) as response:
                    if response.status == 200:
                        return True, 'dictionary'
                    else:
                        return True, 'valid'
        except Exception as e:
            logger.debug(f"Dictionary API error (ignored): {e}")
            return True, 'valid'

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

    @tasks.loop(minutes=1)
    async def daily_challenge_task(self):
        """Generate a new daily challenge at random times throughout the day."""
        try:
            # Only trigger if no active challenge and random chance (roughly every 30-90 minutes)
            if not self.daily_challenge and random.random() < 0.033:  # ~5% chance per minute = ~1 challenge per 20 mins
                # Pick a random sophisticated word that starts with the current last letter
                if self.last_word:
                    target_letter = self.last_word[-1].lower()
                    # Filter words that start with the target letter
                    valid_words = [w for w in self.challenge_words if w[0].lower() == target_letter]

                    if valid_words:
                        self.daily_challenge_word = random.choice(valid_words)
                    else:
                        # If no words match, pick any word
                        self.daily_challenge_word = random.choice(self.challenge_words)

                    self.daily_challenge = target_letter
                    self.daily_challenge_expires = datetime.now() + timedelta(seconds=30)
                    self.challenge_participants.clear()

                    # Post challenge in the word-up channel
                    channel = self.bot.get_channel(WORD_UP_CHANNEL_ID)
                    if channel:
                        embed = discord.Embed(
                            title="Daily Challenge",
                            description=f"Find a sophisticated word starting with **{target_letter.upper()}**",
                            color=0x599cff
                        )
                        embed.add_field(
                            name="Time Limit",
                            value="30 seconds",
                            inline=True
                    )
                    embed.add_field(
                        name="Reward",
                        value="150 points + 5 XP",
                        inline=True
                    )
                    await channel.send(embed=embed)

                self.save_data()
                logger.info(f"Word-Up: Daily challenge started - word: {self.daily_challenge_word}")
        except Exception as e:
            logger.error(f"Error in daily challenge task: {e}")

    @daily_challenge_task.before_loop
    async def before_daily_challenge(self):
        """Wait until the bot is ready before starting the task."""
        await self.bot.wait_until_ready()

    @tasks.loop(seconds=5)
    async def challenge_expiry_check(self):
        """Check if daily challenge has expired and announce if someone won."""
        try:
            if (self.daily_challenge and
                self.daily_challenge_expires and
                datetime.now() > self.daily_challenge_expires):

                # Challenge expired - announce winner or timeout
                channel = self.bot.get_channel(WORD_UP_CHANNEL_ID)

                if self.challenge_participants:
                    logger.info(f"Word-Up: Challenge completed by {len(self.challenge_participants)} participant(s)")
                else:
                    if channel:
                        embed = discord.Embed(
                            title="Daily Challenge Expired",
                            description=f"Time's up! No one found the word: **{self.daily_challenge_word.upper()}**",
                            color=0xFF6B6B
                        )
                        await channel.send(embed=embed)
                    logger.info(f"Word-Up: Challenge expired - word was: {self.daily_challenge_word}")

                # Clear challenge
                self.daily_challenge = None
                self.daily_challenge_word = None
                self.daily_challenge_expires = None
                self.challenge_participants.clear()
                self.save_data()

                # Remind about the current game state
                if self.last_word and channel:
                    embed = discord.Embed(
                        description=f"Challenge over! Next word must start with **{self.last_word[-1].upper()}**",
                        color=0x599cff
                    )
                    await channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in challenge expiry check: {e}")
        except Exception as e:
            logger.error(f"Error in challenge expiry check: {e}")

    @challenge_expiry_check.before_loop
    async def before_challenge_expiry(self):
        """Wait until the bot is ready before starting the task."""
        await self.bot.wait_until_ready()

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

        # Check if daily challenge is active
        if (self.daily_challenge and
            self.daily_challenge_expires and
            datetime.now() < self.daily_challenge_expires):

            # Challenge is active - only accept challenge words
            if word.lower() == self.daily_challenge_word.lower():
                # This will be handled below in the challenge section
                pass
            else:
                # During challenge, ignore regular words and remind them after challenge ends
                logger.debug(f"Word-Up: Ignoring regular word '{word}' during challenge - waiting for '{self.daily_challenge_word}'")
                return

        # Detect invisible characters
        if self.detect_invisible_chars(message.content):
            await message.delete()
            embed = discord.Embed(
                description="Invalid characters detected",
                color=0xFF6B6B
            )
            await message.channel.send(embed=embed, delete_after=10)
            warnings = await self.add_warning(message.author)
            logger.warning(f"Word-Up: Invisible chars detected from {message.author.name}")
            return

        # Detect gibberish
        if self.detect_gibberish(word):
            await message.delete()
            embed = discord.Embed(
                description=f"{message.author.mention} That doesn't look like a valid word",
                color=0xFF6B6B
            )
            await message.channel.send(embed=embed, delete_after=10)
            warnings = await self.add_warning(message.author)
            logger.info(f"Word-Up: Gibberish detected from {message.author.name}: {word}")
            return

        # If this is the first word, just save it
        if self.last_word is None:
            self.last_word = word
            self.last_message_id = message.id
            self.save_data()

            # Award minimal points for first word
            await self.award_points(message.author, message.guild.id, 10, 0)

            logger.info(f"Word-Up: First word set to '{word}'")
            return

        # Check if the word starts with the last letter of the previous word
        expected_start = self.last_word[-1].lower()
        actual_start = word[0].lower()

        if actual_start != expected_start:
            # Rule violation
            embed = discord.Embed(
                description=f"{message.author.mention} Your word must start with **{expected_start.upper()}**",
                color=0xFF6B6B
            )
            embed.add_field(
                name="Previous word",
                value=f"{self.last_word.upper()}",
                inline=True
            )
            embed.add_field(
                name="Your word",
                value=f"{word.upper()} (starts with {actual_start.upper()})",
                inline=True
            )

            await message.reply(embed=embed, mention_author=False, delete_after=15)
            warnings = await self.add_warning(message.author)

            logger.info(
                f"Word-Up violation: {message.author.name} said '{word}' "
                f"(should start with '{expected_start}') - Warning {warnings}/3"
            )
            return

        # Check word cooldown (3 day duplicate prevention)
        last_used = self.check_word_cooldown(message.author.id, word)
        if last_used:
            cooldown_end = last_used + timedelta(days=3)
            time_left = cooldown_end - datetime.now()
            hours_left = int(time_left.total_seconds() / 3600)

            embed = discord.Embed(
                description=f"{message.author.mention} You used that word recently",
                color=0xFF6B6B
            )
            embed.add_field(
                name="Cooldown",
                value=f"{hours_left} hours remaining",
                inline=False
            )

            await message.reply(embed=embed, mention_author=False, delete_after=10)
            logger.info(f"Word-Up: {message.author.name} tried to reuse word '{word}' (cooldown)")
            return

        # Simple point calculation - all words accepted
        points, xp = self.calculate_word_points(word)

        # Check for daily challenge completion
        bonus_points = 0
        bonus_xp = 0
        is_challenge = False

        if (self.daily_challenge and
            self.daily_challenge_expires and
            datetime.now() < self.daily_challenge_expires and
            message.author.id not in self.challenge_participants and
            word.lower() == self.daily_challenge_word.lower()):

            # Challenge word found! Award bonus
            bonus_points = 150
            bonus_xp = 5
            is_challenge = True
            self.challenge_participants.add(message.author.id)
            logger.info(f"Word-Up: {message.author.name} completed daily challenge with '{word}'!")

        # Award points and XP
        total_points = points + bonus_points
        total_xp = xp + bonus_xp
        await self.award_points(message.author, message.guild.id, total_points, total_xp)

        # Record word usage
        self.record_word_usage(message.author.id, word)

        # Valid word - update tracker
        self.last_word = word
        self.last_message_id = message.id
        self.save_data()

        # Only announce daily challenge completion
        if is_challenge:
            embed = discord.Embed(
                title="Daily Challenge Complete",
                description=f"{message.author.mention} found the word",
                color=0x00D166
            )
            embed.add_field(name="Word", value=word.upper(), inline=True)
            embed.add_field(name="Reward", value=f"{total_points} pts, {total_xp} XP", inline=True)
            await message.channel.send(embed=embed)

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
        self.user_word_history.clear()
        self.user_warnings.clear()
        self.save_data()

        embed = discord.Embed(
            title="Word-Up Game Reset",
            description="The word chain has been reset. Start a new word",
            color=0x00D166
        )
        await ctx.send(embed=embed)
        logger.info(f"Word-Up game reset by {ctx.author.name}")

    @commands.command(name='wordup_status')
    async def word_up_status(self, ctx):
        """Check the current Word-Up game status."""
        embed = discord.Embed(
            title="Word-Up Game Status",
            color=0x599cff
        )

        if self.last_word:
            embed.add_field(
                name="Last Word",
                value=f"**{self.last_word.upper()}**",
                inline=True
            )
            embed.add_field(
                name="Next Letter",
                value=f"**{self.last_word[-1].upper()}**",
                inline=True
            )
        else:
            embed.description = "No words have been played yet. Start the chain"

        # Show daily challenge status
        if self.daily_challenge and self.daily_challenge_expires:
            if datetime.now() < self.daily_challenge_expires:
                time_left = (self.daily_challenge_expires - datetime.now()).seconds
                embed.add_field(
                    name="Daily Challenge",
                    value=f"Active - {time_left}s remaining",
                    inline=False
                )

        await ctx.send(embed=embed)

    @commands.command(name='wordup_set')
    @commands.has_permissions(manage_messages=True)
    async def set_word_up(self, ctx, *, word: str):
        """Manually set the current word (Admin only)."""
        cleaned_word = self.extract_word(word)

        if not cleaned_word:
            embed = discord.Embed(
                description="Please provide a valid word",
                color=0xFF6B6B
            )
            await ctx.send(embed=embed)
            return

        self.last_word = cleaned_word
        self.last_message_id = None
        self.save_data()

        embed = discord.Embed(
            title="Word Set",
            description=f"Current word: **{cleaned_word.upper()}**",
            color=0x00D166
        )
        embed.add_field(
            name="Next Letter",
            value=f"**{cleaned_word[-1].upper()}**",
            inline=False
        )
        await ctx.send(embed=embed)
        logger.info(f"Word-Up word manually set to '{cleaned_word}' by {ctx.author.name}")

    @commands.command(name='wordup_challenge')
    @commands.has_permissions(manage_messages=True)
    async def start_challenge(self, ctx):
        """Manually start a daily challenge (Admin only)."""
        if not self.last_word:
            embed = discord.Embed(
                description="No active word. Start the game first",
                color=0xFF6B6B
            )
            await ctx.send(embed=embed)
            return

        target_letter = self.last_word[-1].lower()
        valid_words = [w for w in self.challenge_words if w[0].lower() == target_letter]

        if valid_words:
            self.daily_challenge_word = random.choice(valid_words)
        else:
            self.daily_challenge_word = random.choice(self.challenge_words)

        self.daily_challenge = target_letter
        self.daily_challenge_expires = datetime.now() + timedelta(seconds=30)
        self.challenge_participants.clear()
        self.save_data()

        embed = discord.Embed(
            title="Daily Challenge",
            description=f"Find a sophisticated word starting with **{target_letter.upper()}**",
            color=0x599cff
        )
        embed.add_field(name="Time Limit", value="30 seconds", inline=True)
        embed.add_field(name="Reward", value="150 points + 5 XP", inline=True)
        await ctx.send(embed=embed)

        logger.info(f"Word-Up challenge started by {ctx.author.name}")

    @commands.command(name='wordup_clearwarnings')
    @commands.has_permissions(manage_messages=True)
    async def clear_warnings(self, ctx, member: discord.Member):
        """Clear warnings for a member (Admin only)."""
        if member.id in self.user_warnings:
            del self.user_warnings[member.id]
            self.save_data()

        embed = discord.Embed(
            description=f"Warnings cleared for {member.mention}",
            color=0x00D166
        )
        await ctx.send(embed=embed)
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
                embed = discord.Embed(
                    description="No Word-Up scores yet. Start playing",
                    color=0xFF6B6B
                )
                await ctx.send(embed=embed)
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
            embed = discord.Embed(
                description="Error generating leaderboard",
                color=0xFF6B6B
            )
            await ctx.send(embed=embed)


async def setup(bot):
    """Load the WordUpGame cog."""
    await bot.add_cog(WordUpGame(bot))
