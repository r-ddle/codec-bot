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

    @commands.command(name='rps5', aliases=['battle', 'chaos'])
    async def random_battle(self, ctx, rounds: str = "1", opponent: Optional[discord.Member] = None):
        """
        Epic random item battle! 5 random items, AI judges the winner!

        Usage:
        - !rps5 @user (single round)
        - !rps5 3r @user (best of 3)
        - !rps5 5r @user (best of 5)
        """
        # Parse rounds
        try:
            if rounds.endswith('r'):
                num_rounds = int(rounds[:-1])
            else:
                # Check if rounds is actually the opponent mention
                if rounds.startswith('<@'):
                    opponent = await commands.MemberConverter().convert(ctx, rounds)
                    num_rounds = 1
                else:
                    num_rounds = int(rounds)
        except:
            num_rounds = 1

        # Validate rounds
        if num_rounds not in [1, 3, 5, 7]:
            container = create_error_message(
                "invalid rounds",
                "choose 1, 3, 5, or 7 rounds\n\n"
                "**usage:** `!rps5 3r @user` or `!rps5 @user`"
            )
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)
            return

        # Check if opponent is provided
        if not opponent:
            container = create_error_message(
                "no opponent specified",
                "you need to mention someone to battle\n\n"
                "**usage:** `!rps5 [rounds] @user`\n"
                "**examples:**\n"
                "• `!rps5 @friend` - single round\n"
                "• `!rps5 3r @friend` - best of 3\n"
                "• `!rps5 5r @friend` - best of 5"
            )
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)
            return

        # Validation checks
        if opponent.id == ctx.author.id:
            container = create_error_message(
                "can't battle yourself",
                "you can't battle against yourself, find an opponent"
            )
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)
            return

        if opponent.bot:
            container = create_error_message(
                "can't battle bots",
                "you can't challenge a bot to battle"
            )
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)
            return

        # Create and start the game
        game = RPS5Game(ctx.author, opponent, num_rounds, self.bot)
        await game.start(ctx)


class RPS5Game:
    """Random 5-item battle game with AI judging."""

    # Massive pool of random items for chaos
    ITEM_POOL = [
        # Weapons & Tools
        "Atomic Bomb", "Nuclear Missile", "Laser Cannon", "Katana", "Chainsaw",
        "Baseball Bat", "Rubber Chicken", "Spoon", "Fork", "Butter Knife",
        "Pencil", "Eraser", "Stapler", "Paper Clip", "Thumbtack",

        # Living Things
        "Dragon", "Unicorn", "Zombie", "Vampire", "Werewolf",
        "Newborn Baby", "Toddler", "Teenager", "Karen", "Florida Man",
        "Cat", "Dog", "Hamster", "Eagle", "Pigeon",
        "Goldfish", "Shark", "Whale", "Ant", "Spider",

        # Nature & Elements
        "Black Hole", "Supernova", "Lightning Bolt", "Tornado", "Tsunami",
        "Earthquake", "Volcano", "Avalanche", "Wildfire", "Blizzard",
        "Raindrop", "Snowflake", "Leaf", "Pebble", "Grain of Sand",

        # Technology
        "Smartphone", "Laptop", "Gaming PC", "Calculator", "Toaster",
        "Microwave", "Refrigerator", "Vacuum Cleaner", "Robot", "AI",
        "Nuclear Power Plant", "Solar Panel", "Wind Turbine", "Battery", "Charger",

        # Food & Drink
        "Pizza", "Burger", "Hot Dog", "Taco", "Sushi",
        "Banana", "Apple", "Orange", "Grape", "Watermelon",
        "Coffee", "Tea", "Water", "Soda", "Energy Drink",
        "Bread", "Cheese", "Milk", "Egg", "Bacon",

        # Abstract Concepts
        "Love", "Hate", "Fear", "Joy", "Anger",
        "Time", "Space", "Gravity", "Entropy", "Chaos",
        "Mathematics", "Philosophy", "Art", "Music", "Poetry",

        # Random Objects
        "Rock", "Paper", "Scissors", "Sock", "Shoe",
        "Hat", "Umbrella", "Sunglasses", "Mirror", "Lamp",
        "Chair", "Table", "Bed", "Pillow", "Blanket",
        "Book", "Pen", "Keyboard", "Mouse", "Monitor",

        # Memes & Pop Culture
        "Shrek", "Thanos", "John Cena", "Rick Astley", "Doge",
        "Pepe", "Wojak", "Chad", "Sigma Male", "Based God",
        "UNO Reverse Card", "No U", "Ligma", "Joe Mama", "Deez Nuts",

        # Completely Random
        "Existential Dread", "Monday Morning", "Traffic Jam", "Lag Spike", "Loading Screen",
        "404 Error", "Blue Screen", "Low Battery", "Wet Socks", "Stepping on LEGO",
        "Brain Freeze", "Stubbed Toe", "Paper Cut", "Hiccups", "Cringe",
    ]

    def __init__(self, player1: discord.Member, player2: discord.Member, rounds: int, bot):
        self.player1 = player1
        self.player2 = player2
        self.rounds = rounds
        self.bot = bot
        self.player1_score = 0
        self.player2_score = 0
        self.current_round = 0
        self.game_message = None

    async def start(self, ctx):
        """Start the battle game."""
        # Announce game start with component
        rounds_text = "single round" if self.rounds == 1 else f"best of {self.rounds}"

        container = create_info_card(
            title="randomizer game started",
            description=f"{self.player1.mention} vs {self.player2.mention}\n\n"
                       f"**format:** {rounds_text}\n"
                       f"**status:** generating random items...\n\n",
            color_code="blue"
        )
        view = LayoutView()
        view.add_item(container)

        message = await ctx.send(view=view)
        self.game_message = message

        # Play rounds
        while self.current_round < self.rounds:
            if self.player1_score > self.rounds // 2 or self.player2_score > self.rounds // 2:
                break  # Someone already won

            self.current_round += 1
            await asyncio.sleep(2)  # Dramatic pause
            await self.play_round(ctx)

        # Announce final winner
        await self.announce_winner(ctx)

    async def play_round(self, ctx):
        """Play a single round."""
        # Generate 5 random items
        items = random.sample(self.ITEM_POOL, 5)

        # Create item selection view
        view = RPS5SelectView(self.player1, self.player2, items, self)

        # Create info container (no buttons yet)
        container = create_info_card(
            title=f"round {self.current_round} of {self.rounds}",
            description=f"**score:** {self.player1.mention} {self.player1_score} - {self.player2_score} {self.player2.mention}\n\n"
                       f"**choose your fighter:**\n"
                       f"1️⃣ {items[0]}\n"
                       f"2️⃣ {items[1]}\n"
                       f"3️⃣ {items[2]}\n"
                       f"4️⃣ {items[3]}\n"
                       f"5️⃣ {items[4]}",
            footer="30 seconds to choose",
            color_code="blue"
        )
        layout_view = LayoutView()
        layout_view.add_item(container)

        # First update with info
        await self.game_message.edit(view=layout_view)

        # Then send a reply message with buttons
        button_message = await self.game_message.reply(
            content="select your item:",
            view=view
        )

        view.message = button_message
        view.info_message = self.game_message

        # Wait for both players to choose (or timeout)
        await view.wait()

    def judge_battle(self, item1: str, item2: str) -> tuple[str, str]:
        """Use predefined rules to judge which item wins."""
        from config.constants import BATTLE_RULES

        # Check if same item (tie)
        if item1 == item2:
            winner = random.choice([item1, item2])  # Random tiebreaker
            return winner, f"Both chose {item1}! Tiebreaker favors player who chose first."

        # Try direct lookup
        matchup = f"{item1} vs {item2}"
        if matchup in BATTLE_RULES:
            winner, explanation = BATTLE_RULES[matchup]
            return winner, explanation

        # Try reverse lookup
        reverse_matchup = f"{item2} vs {item1}"
        if reverse_matchup in BATTLE_RULES:
            winner, explanation = BATTLE_RULES[reverse_matchup]
            return winner, explanation

        # Fallback: Use simple logic based on item categories
        return self.fallback_judge(item1, item2)

    def fallback_judge(self, item1: str, item2: str) -> tuple[str, str]:
        """Fallback logic when no rule exists."""
        # Define power tiers
        cosmic_tier = ["Black Hole", "Supernova", "Space", "Time", "Entropy"]
        catastrophic_tier = ["Atomic Bomb", "Nuclear Missile", "Tsunami", "Earthquake", "Volcano", "Tornado"]
        mythical_tier = ["Dragon", "Unicorn", "Vampire", "Werewolf", "Zombie"]
        powerful_tier = ["Lightning Bolt", "Wildfire", "Blizzard", "Avalanche", "Robot", "AI"]

        # Check tiers
        for tier_name, tier_items, power_level in [
            ("cosmic", cosmic_tier, 5),
            ("catastrophic", catastrophic_tier, 4),
            ("mythical", mythical_tier, 3),
            ("powerful", powerful_tier, 2),
        ]:
            if item1 in tier_items and item2 not in tier_items:
                return item1, f"{item1} dominates through sheer power. Superior tier wins."
            elif item2 in tier_items and item1 not in tier_items:
                return item2, f"{item2} dominates through sheer power. Superior tier wins."

        # Random selection with creative explanations
        winner = random.choice([item1, item2])
        explanations = [
            f"{winner} wins through unexpected advantage. Chaos favors the bold.",
            f"{winner} outmaneuvers opponent cleverly. Strategy beats strength.",
            f"{winner} prevails in close match. Victory by narrow margin.",
            f"{winner} triumphs unexpectedly. Underdog energy activated.",
            f"{winner} dominates decisively. Clear superiority demonstrated.",
        ]
        return winner, random.choice(explanations)

    async def announce_winner(self, ctx):
        """Announce the final winner of the match."""
        if self.player1_score > self.player2_score:
            winner = self.player1
            winner_score = self.player1_score
            loser_score = self.player2_score
        else:
            winner = self.player2
            winner_score = self.player2_score
            loser_score = self.player1_score

        container = create_success_message(
            "game complete",
            f"**winner:** {winner.mention}\n"
            f"**final score:** {winner_score} - {loser_score}\n\n"
            f"good game!"
        )
        view = LayoutView()
        view.add_item(container)

        await self.game_message.edit(view=view)


class RPS5SelectView(View):
    """View for selecting items in RPS5."""

    def __init__(self, player1: discord.Member, player2: discord.Member, items: list, game):
        super().__init__(timeout=30.0)
        self.player1 = player1
        self.player2 = player2
        self.items = items
        self.game = game
        self.player1_choice = None
        self.player2_choice = None
        self.message = None  # Button message
        self.info_message = None  # Info container message

        # Add number buttons with item labels
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
        for i, emoji in enumerate(emojis):
            button = Button(
                style=ButtonStyle.primary,
                emoji=emoji,
                label=items[i][:80],  # Discord button label limit
                custom_id=f"rps5_item_{i}"
            )
            button.callback = self.make_callback(i)
            self.add_item(button)

    def make_callback(self, index):
        """Create callback for item selection."""
        async def callback(interaction: discord.Interaction):
            # Check if user is a player
            if interaction.user.id not in [self.player1.id, self.player2.id]:
                await interaction.response.send_message(
                    "This isn't your game!",
                    ephemeral=True
                )
                return

            # Check if player already chose
            if interaction.user.id == self.player1.id:
                if self.player1_choice:
                    await interaction.response.send_message(
                        "you already made your choice",
                        ephemeral=True
                    )
                    return
                self.player1_choice = self.items[index]
                await interaction.response.send_message(
                    f"you chose: **{self.items[index]}**",
                    ephemeral=True
                )
            else:
                if self.player2_choice:
                    await interaction.response.send_message(
                        "you already made your choice",
                        ephemeral=True
                    )
                    return
                self.player2_choice = self.items[index]
                await interaction.response.send_message(
                    f"you chose: **{self.items[index]}**",
                    ephemeral=True
                )

            # Check if both players chose
            if self.player1_choice and self.player2_choice:
                await self.resolve_round()

        return callback

    async def resolve_round(self):
        """Resolve the round with AI judging."""
        # Delete button message
        try:
            await self.message.delete()
        except:
            pass

        # Update info message - judging in progress
        container = create_info_card(
            title=f"round {self.game.current_round} of {self.game.rounds}",
            description=f"{self.player1.mention} chose: {self.player1_choice}\n"
                       f"{self.player2.mention} chose: {self.player2_choice}\n\n"
                       f"determining winner...",
            color_code="blue"
        )
        view = LayoutView()
        view.add_item(container)

        await self.info_message.edit(view=view)

        # Small delay for dramatic effect
        await asyncio.sleep(1)

        # Get judgment from rules dataset
        winner_item, explanation = self.game.judge_battle(
            self.player1_choice,
            self.player2_choice
        )

        # Determine winner
        if winner_item == self.player1_choice:
            winner = self.player1
            self.game.player1_score += 1
        else:
            winner = self.player2
            self.game.player2_score += 1

        # Show result with component
        result_container = create_info_card(
            title=f"round {self.game.current_round} of {self.game.rounds}",
            description=f"{self.player1.mention} chose: {self.player1_choice}\n"
                       f"{self.player2.mention} chose: {self.player2_choice}\n\n"
                       f"**winner:** {winner.mention}\n\n"
                       f"{explanation}\n\n"
                       f"**score:** {self.player1.mention} {self.game.player1_score} - {self.game.player2_score} {self.player2.mention}",
            color_code="green"
        )
        result_view = LayoutView()
        result_view.add_item(result_container)

        await self.info_message.edit(view=result_view)

        # Wait 4 seconds to show the result before continuing
        await asyncio.sleep(4)

        self.stop()

    async def on_timeout(self):
        """Handle timeout - players took too long."""
        try:
            await self.message.delete()
        except:
            pass

        # Update info message with timeout
        container = create_error_message(
            "round timeout",
            "Both players must select within 30 seconds!\n\n"
            "Game cancelled."
        )
        view = LayoutView()
        view.add_item(container)

        await self.info_message.edit(view=view)
        self.stop()


async def setup(bot):
    """Load the fun commands cog."""
    await bot.add_cog(FunCommands(bot))
