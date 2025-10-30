"""
Info Command Cog - Interactive bot information with button navigation
"""
import discord
from discord.ext import commands
from discord.ui import Button, View
from discord import ButtonStyle
from typing import Optional


class InfoView(View):
    """Interactive view for bot information with navigation buttons"""

    def __init__(self):
        super().__init__(timeout=180)  # 3 minute timeout
        self.current_page = "home"

        # Add navigation buttons
        self.home_btn = Button(label="Home", style=ButtonStyle.primary, custom_id="home")
        self.commands_btn = Button(label="Commands", style=ButtonStyle.secondary, custom_id="commands")
        self.admin_btn = Button(label="Admin Commands", style=ButtonStyle.danger, custom_id="admin")
        self.features_btn = Button(label="Features", style=ButtonStyle.secondary, custom_id="features")

        self.home_btn.callback = self.home_callback
        self.commands_btn.callback = self.commands_callback
        self.admin_btn.callback = self.admin_callback
        self.features_btn.callback = self.features_callback

        self.add_item(self.home_btn)
        self.add_item(self.commands_btn)
        self.add_item(self.features_btn)
        self.add_item(self.admin_btn)

    def get_home_content(self) -> str:
        """Get home page content"""
        return """## Kiro - Exile's Cozy Bot 🌱

Your friendly neighborhood Discord bot for r.ddle's server!
Featuring a progression system, fun mini-games, server events, and more.

**Use the buttons below to navigate:**
• **Commands** - View all available commands
• **Features** - Learn about bot features
• **Admin Commands** - Admin-only commands (requires permissions)

**Quick Links:**
• Prefix: `!`
• Server: Exile by r.ddle
• Support: <@1040597411116089424>
• Version: 3.2
"""

    def get_commands_content(self) -> str:
        """Get commands page content"""
        return """## Bot Commands

**Progression & XP:**
• `!rank` - Display your rank card with MGS Codec style
• `!rankinfo` - View rank system info and perks
• `!status` - View your XP and rank (slash command)
• `!daily` - Claim daily XP bonus and supply drops
• `!leaderboard` or `!lb` - View server leaderboard

**Word-Up Game:**
• `!wordup_status` - Check current word and game state
• `!leaderboard_wordup` or `!lb_wordup` - Word-Up points leaderboard

**Server Events:**
• `!eventstatus` - Check active event progress
• `!eventinfo` - Detailed event information and rewards

**Profile:**
• `!profile [@user]` - View your or someone's profile card
• `!setbio <text>` - Set your profile bio

**Utility:**
• `!lvlup` - Learn about the ranking system
• `!rankinfo` - Show rank system details and progression
• `!ping` - Check bot latency
• `!info` - Show this information

**Fun Commands:**
• `!avatar [@user]` - View user's avatar in high quality
• `!rps <rock|paper|scissors>` - Play Rock Paper Scissors
• `!coinflip` - Flip a coin
• `!8ball <question>` - Ask the magic 8-ball
"""

    def get_admin_commands_content(self) -> str:
        """Get admin commands page content"""
        return """## Admin Commands

**Member Management:**
• `!promote <member>` - Promote member to next rank
• `!demote <member>` - Demote member to previous rank
• `!setxp <member> <amount>` - Set member's XP
• `!givexp <member> <amount>` - Give/remove XP
• `!fix_rank <member>` - Fix member's rank (migration tool)

**Rank Migration (New!):**
• `!migrate_ranks` - Migrate all users from old MGS ranks to Cozy ranks
• `!check_migration` - Check migration status for all members

**Server Events:**
• `!eventstart [goal] [title]` - Start a new server event
• `!eventend` - End current event
• `!eventrestart` - Restart event progress
• `!eventprogress` - Force progress update
• `!eventreset` - Reset event completely

**System:**
• `!auto_promote` - Auto-promote eligible members
• `!fix_all_roles` - Fix all role assignments
• `!check_roles` - Check role configuration
• `!neon_backup` - Backup data to Neon database
• `!neon_status` - Check database connection status
• `!neon_resync` - Force resync with database

**Testing:**
• `!test_promotion <member>` - Test promotion notification
• `!test_daily <member>` - Reset daily cooldown
• `!test_supply <member>` - Reset supply cooldown
• `!test_streak <member> <days>` - Set streak days

**Word-Up Game:**
• `!wordup_reset` - Reset Word-Up game state
• `!wordup_set <word>` - Manually set current word
• `!wordup_clearwarnings <member>` - Clear member's warnings
• `!wordup_removetroll <member>` - Remove Word-Up Troll role manually
"""

    def get_features_content(self) -> str:
        """Get features page content"""
        return """## Bot Features

**🌱 Ranking System:**
• Ranks from **New Lifeform** to **Anti-Grass Toucher**
• Earn XP from messages, voice chat, reactions, and more
• Monthly XP reset with rank preservation
• Rank multipliers (1.0x - 2.0x) for faster progression
• Automatic role assignment with old role cleanup

**🎮 Word-Up Game:**
• Word chain game in dedicated <#1423506535199281254> channel
• Points for dictionary words vs slang/names
• Anti-spam and troll protection (3 strikes = 5 min timeout)
• **Auto-removal of Troll role** when punishment expires
• 3-day word cooldown prevents repeated words
• Leaderboard tracking

**🎯 Server Events:**
• Weekly/monthly community challenges
• Dynamic goal calculation based on server size
• Live progress tracking with generated images
• Reward distribution on completion
• Top contributor leaderboards and recognition

**📅 Daily Systems:**
• Daily bonus XP claims (resets at midnight)
• Supply drop mini-game with random rewards
• Login streak tracking (3, 7, 14, 30+ day bonuses)
• Consecutive day rewards (up to +40 XP per message)
• Streak XP multipliers

**👤 Profile System:**
• Custom profile cards
• Rank display with progress bars
• Stats tracking (messages, voice time, reactions)
• Bio customization with `!setbio`
• Streak and activity tracking


"""

    async def home_callback(self, interaction: discord.Interaction):
        """Home button callback"""
        self.current_page = "home"
        await interaction.response.edit_message(content=self.get_home_content(), view=self)

    async def commands_callback(self, interaction: discord.Interaction):
        """Commands button callback"""
        self.current_page = "commands"
        await interaction.response.edit_message(content=self.get_commands_content(), view=self)

    async def admin_callback(self, interaction: discord.Interaction):
        """Admin commands button callback"""
        # Check if the user clicking the button has admin permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You need administrator permissions to view this page.", ephemeral=True)
            return
        self.current_page = "admin"
        await interaction.response.edit_message(content=self.get_admin_commands_content(), view=self)

    async def features_callback(self, interaction: discord.Interaction):
        """Features button callback"""
        self.current_page = "features"
        await interaction.response.edit_message(content=self.get_features_content(), view=self)


class Info(commands.Cog):
    """Information commands for the bot"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='info')
    async def info_command(self, ctx):
        """Display interactive bot information with navigation buttons"""
        # Create view (no need to pass is_admin anymore)
        view = InfoView()

        # Send message with view
        await ctx.send(content=view.get_home_content(), view=view)


async def setup(bot):
    """Load the Info cog"""
    await bot.add_cog(Info(bot))
