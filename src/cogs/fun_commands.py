"""
Fun Commands - Games and entertainment features for the server.
"""
import discord
from discord.ext import commands
from discord.ui import LayoutView, Button, View
from discord import ButtonStyle
import random
import asyncio
from typing import Optional

from utils.components_builder import (
    create_info_card,
    create_success_message,
    create_error_message
)
from config.settings import logger


class RPSButton(Button):
    """Rock Paper Scissors button for game selection."""

    def __init__(self, choice: str, emoji: str, game_view):
        super().__init__(
            style=ButtonStyle.primary,
            label=choice,
            emoji=emoji,
            custom_id=f"rps_{choice.lower()}"
        )
        self.choice = choice
        self.game_view = game_view

    async def callback(self, interaction: discord.Interaction):
        """Handle player choice."""
        # Check if the interaction user is one of the players
        if interaction.user.id not in [self.game_view.player1_id, self.game_view.player2_id]:
            await interaction.response.send_message(
                "This isn't your game!",
                ephemeral=True
            )
            return

        # Check if this player already made a choice
        if interaction.user.id == self.game_view.player1_id and self.game_view.player1_choice:
            await interaction.response.send_message(
                "You already made your choice!",
                ephemeral=True
            )
            return
        elif interaction.user.id == self.game_view.player2_id and self.game_view.player2_choice:
            await interaction.response.send_message(
                "You already made your choice!",
                ephemeral=True
            )
            return

        # Acknowledge the interaction
        await interaction.response.defer()

        # Process the game
        await self.game_view.process_game(interaction, self.choice)


class RPSGameView(View):
    """View for Rock Paper Scissors game."""

    def __init__(self, player1: discord.Member, player2: discord.Member, bot):
        super().__init__(timeout=60.0)
        self.player1_id = player1.id
        self.player2_id = player2.id
        self.player1 = player1
        self.player2 = player2
        self.bot = bot
        self.player1_choice = None
        self.player2_choice = None
        self.message = None

        # Add buttons
        self.add_item(RPSButton("Rock", "🪨", self))
        self.add_item(RPSButton("Paper", "📄", self))
        self.add_item(RPSButton("Scissors", "✂️", self))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check if the user is one of the players."""
        if interaction.user.id not in [self.player1_id, self.player2_id]:
            await interaction.response.send_message(
                "This isn't your game!",
                ephemeral=True
            )
            return False
        return True

    async def process_game(self, interaction: discord.Interaction, choice: str):
        """Process player choice and determine winner."""
        # Store choice for the player who clicked
        if interaction.user.id == self.player1_id:
            self.player1_choice = choice
        elif interaction.user.id == self.player2_id:
            self.player2_choice = choice

        # Check if both players have chosen
        if self.player1_choice and self.player2_choice:
            # Both players chose - disable buttons and show result
            for item in self.children:
                item.disabled = True

            # Determine winner
            winner = self.determine_winner(
                self.player1_choice,
                self.player2_choice
            )

            # Create result message
            if winner == "tie":
                result_text = "🤝 **IT'S A TIE!**"
                description = (
                    f"{self.player1.mention} chose {self.player1_choice}\n"
                    f"{self.player2.mention} chose {self.player2_choice}\n\n"
                    f"Nobody wins this round!"
                )
            elif winner == "player1":
                result_text = f"🎉 {self.player1.mention} WINS!"
                description = (
                    f"{self.player1.mention} chose {self.player1_choice}\n"
                    f"{self.player2.mention} chose {self.player2_choice}\n\n"
                    f"**{self.player1_choice} beats {self.player2_choice}!**"
                )
            else:
                result_text = f"🎉 {self.player2.mention} WINS!"
                description = (
                    f"{self.player1.mention} chose {self.player1_choice}\n"
                    f"{self.player2.mention} chose {self.player2_choice}\n\n"
                    f"**{self.player2_choice} beats {self.player1_choice}!**"
                )

            # Update the message with result using plain content
            await self.message.edit(
                content=f"{result_text}\n\n{description}",
                view=None  # Remove buttons
            )
            self.stop()
        else:
            # Only one player chose - update message but keep buttons
            waiting_player = self.player2 if interaction.user.id == self.player1_id else self.player1

            # Update message with waiting status, keeping buttons active
            await self.message.edit(
                content=f"🪨📄✂️ **Rock Paper Scissors Challenge!**\n\n"
                       f"{self.player1.mention} vs {self.player2.mention}\n\n"
                       f"✅ {interaction.user.mention} has made their choice!\n"
                       f"⏳ Waiting for {waiting_player.mention} to choose...\n"
                       f"⏱️ Time limit: 60 seconds",
                view=self  # Keep the buttons
            )

    def determine_winner(self, choice1: str, choice2: str) -> str:
        """Determine the winner of the game."""
        if choice1 == choice2:
            return "tie"

        winning_combos = {
            "Rock": "Scissors",
            "Paper": "Rock",
            "Scissors": "Paper"
        }

        if winning_combos[choice1] == choice2:
            return "player1"
        else:
            return "player2"

    async def on_timeout(self):
        """Handle timeout."""
        if self.message:
            try:
                await self.message.edit(
                    content="⏰ **Game Timed Out**\n\nThe game was cancelled due to inactivity.",
                    view=None  # Remove buttons
                )
            except:
                pass


class FunCommands(commands.Cog):
    """Fun commands and mini-games for server entertainment."""

    def __init__(self, bot):
        self.bot = bot
        # Counting channel and milestone settings
        self.counting_channel_id = 1423506534872387593
        self.milestone_channel_id = 1423506534658474181
        self.milestones = [1000, 10000, 25000, 50000, 75000, 100000, 250000, 500000, 1000000]
        self.last_milestone = 0  # Track last milestone announced

        # 8ball responses
        self.eight_ball_responses = {
            "positive": [
                "🎱 Yes, definitely!",
                "🎱 It is certain.",
                "🎱 Without a doubt.",
                "🎱 You may rely on it.",
                "🎱 As I see it, yes.",
                "🎱 Most likely.",
                "🎱 Outlook good.",
                "🎱 Yes.",
                "🎱 Signs point to yes.",
                "🎱 Absolutely!"
            ],
            "neutral": [
                "🎱 Reply hazy, try again.",
                "🎱 Ask again later.",
                "🎱 Better not tell you now.",
                "🎱 Cannot predict now.",
                "🎱 Concentrate and ask again.",
                "🎱 Maybe..."
            ],
            "negative": [
                "🎱 Don't count on it.",
                "🎱 My reply is no.",
                "🎱 My sources say no.",
                "🎱 Outlook not so good.",
                "🎱 Very doubtful.",
                "🎱 Definitely not.",
                "🎱 No way.",
                "🎱 Absolutely not."
            ]
        }

    @commands.command(name='8ball', aliases=['eightball'])
    async def eight_ball(self, ctx, *, question: str = None):
        """
        Ask the magic 8-ball a question.

        Usage: !8ball <question>
        """
        if not question:
            container = create_error_message(
                "No Question Asked",
                "You need to ask a question!\n\n"
                "**Usage:** `!8ball <your question>`\n"
                "**Example:** `!8ball Will I get good RNG today?`"
            )
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)
            return

        # Randomly select a category then a response
        category = random.choices(
            ["positive", "neutral", "negative"],
            weights=[40, 30, 30]
        )[0]

        response = random.choice(self.eight_ball_responses[category])

        container = create_info_card(
            title="🔮 Magic 8-Ball",
            description=f"**Question:** {question}\n\n**Answer:** {response}",
            color_code="blue"
        )
        view = LayoutView()
        view.add_item(container)
        await ctx.send(view=view)

    @commands.command(name='rps', aliases=['rockpaperscissors'])
    async def rock_paper_scissors(self, ctx, opponent: Optional[discord.Member] = None):
        """
        Challenge someone to Rock Paper Scissors!

        Usage: !rps @user
        """
        # Check if opponent is provided
        if not opponent:
            container = create_error_message(
                "No Opponent Specified",
                "You need to mention someone to challenge!\n\n"
                "**Usage:** `!rps @user`\n"
                "**Example:** `!rps @friend`"
            )
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)
            return

        # Check if trying to play against self
        if opponent.id == ctx.author.id:
            container = create_error_message(
                "Can't Play Yourself",
                "You can't play Rock Paper Scissors against yourself!"
            )
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)
            return

        # Check if trying to play against a bot
        if opponent.bot:
            container = create_error_message(
                "Can't Play Against Bots",
                "You can't challenge a bot to Rock Paper Scissors!"
            )
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)
            return

        # Create game view with buttons
        game_view = RPSGameView(ctx.author, opponent, self.bot)

        # Send message with text content and buttons (no LayoutView)
        message = await ctx.send(
            content=f"🪨📄✂️ **Rock Paper Scissors Challenge!**\n\n"
                   f"{ctx.author.mention} vs {opponent.mention}\n"
                   f"Both players: Click your choice below!\n"
                   f"⏱️ Time limit: 60 seconds",
            view=game_view
        )

        game_view.message = message

    @commands.command(name='coinflip', aliases=['flip', 'cf'])
    async def coinflip(self, ctx, choice: Optional[str] = None):
        """
        Flip a coin! Optionally guess heads or tails.

        Usage:
        - !coinflip (just flip)
        - !coinflip heads (guess heads)
        - !coinflip tails (guess tails)
        """
        # Normalize choice if provided
        if choice:
            choice = choice.lower()
            if choice not in ["heads", "tails", "h", "t"]:
                container = create_error_message(
                    "Invalid Choice",
                    "Please choose either **heads** or **tails**!\n\n"
                    "**Usage:** `!coinflip [heads/tails]`"
                )
                view = LayoutView()
                view.add_item(container)
                await ctx.send(view=view)
                return

            # Normalize h/t to full words
            if choice == "h":
                choice = "heads"
            elif choice == "t":
                choice = "tails"

        # Flip the coin
        result = random.choice(["heads", "tails"])
        emoji = "🪙" if result == "heads" else "🌙"

        # Build description based on whether they guessed
        if choice:
            if choice == result:
                title = "🎉 YOU WIN!"
                description = (
                    f"You guessed **{choice}**\n"
                    f"The coin landed on **{emoji} {result.upper()}**!\n\n"
                    f"**Nice prediction!** ✨"
                )
                color = "green"
            else:
                title = "❌ YOU LOSE!"
                description = (
                    f"You guessed **{choice}**\n"
                    f"The coin landed on **{emoji} {result.upper()}**\n\n"
                    f"Better luck next time!"
                )
                color = "red"
        else:
            title = "🪙 Coin Flip Result"
            description = f"The coin landed on **{emoji} {result.upper()}**!"
            color = "blue"

        container = create_info_card(
            title=title,
            description=description,
            color_code=color
        )
        view = LayoutView()
        view.add_item(container)
        await ctx.send(view=view)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen for counting milestones in the counting channel."""
        # Ignore if not in counting channel
        if message.channel.id != self.counting_channel_id:
            return

        # Ignore bot messages (except Countr bot for counting)
        if message.author.bot and message.author.id != 467377486141980682:  # Countr bot ID
            return

        # Try to parse the count from message
        try:
            # Check if message content is just a number
            count = int(message.content.strip())

            # Check if this count hits a milestone we haven't announced
            for milestone in self.milestones:
                if count == milestone and count > self.last_milestone:
                    # Send milestone message
                    await self.announce_milestone(count)
                    self.last_milestone = count
                    break

        except (ValueError, AttributeError):
            # Not a valid count message, ignore
            pass

    async def announce_milestone(self, count: int):
        """Announce a counting milestone in the milestone channel."""
        milestone_channel = self.bot.get_channel(self.milestone_channel_id)

        if not milestone_channel:
            logger.warning(f"Milestone channel {self.milestone_channel_id} not found!")
            return

        # Format the number nicely
        formatted_count = f"{count:,}"

        # Different messages based on milestone size
        if count >= 1000000:
            emoji = "🏆"
            title = "🎉 LEGENDARY MILESTONE REACHED! 🎉"
            description = f"**The server has counted to {formatted_count}!**\n\n" \
                        f"An absolutely legendary achievement! This server's dedication is unmatched! 👑"
        elif count >= 100000:
            emoji = "💎"
            title = "💎 DIAMOND MILESTONE ACHIEVED! 💎"
            description = f"**The server has counted to {formatted_count}!**\n\n" \
                        f"Incredible dedication! This is a massive accomplishment! ✨"
        elif count >= 10000:
            emoji = "🌟"
            title = "🌟 MAJOR MILESTONE UNLOCKED! 🌟"
            description = f"**The server has counted to {formatted_count}!**\n\n" \
                        f"What an amazing achievement! Keep up the great work! 🎊"
        else:  # 1000
            emoji = "🎯"
            title = "🎯 MILESTONE REACHED! 🎯"
            description = f"**The server has counted to {formatted_count}!**\n\n" \
                        f"Great job everyone! The counting continues! 🎉"

        container = create_success_message(
            title,
            description
        )
        view = LayoutView()
        view.add_item(container)

        await milestone_channel.send(view=view)
        logger.info(f"🎉 Counting milestone announced: {formatted_count}")


async def setup(bot):
    """Load the fun commands cog."""
    await bot.add_cog(FunCommands(bot))
