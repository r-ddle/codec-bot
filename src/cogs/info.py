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
        return """## Codec Bot - MGS Discord Bot

A feature-rich Discord bot with XP-based ranking system, Word-Up game, server events, and more.

**Use the buttons below to navigate:**
• **Commands** - View all available commands
• **Features** - Learn about bot features
• **Admin Commands** - Admin-only commands (requires permissions)

**Quick Links:**
• Prefix: `!`
• Support: Contact server administrators
• Version: 2.0
"""

    def get_commands_content(self) -> str:
        """Get commands page content"""
        return """## Bot Commands

**Progression & XP:**
• `!rank` - Display your rank card
• `!rankinfo` - View rank system info and perks
• `!status` - View your XP and rank (slash command)
• `!daily` - Claim daily XP bonus
• `!leaderboard` - View server leaderboard

**Word-Up Game:**
• `!wordup_status` - Check current word
• `!leaderboard_wordup` - Word-Up leaderboard

**Server Events:**
• `!eventstatus` - Check active event progress
• `!eventinfo` - Detailed event information

**Utility:**
• `!lvlup` - Learn about the ranking system
• `!rankinfo` - Show rank system info
• `!ping` - Check bot latency
• `!info` - Show this information

**Profile:**
• `!profile` - View your profile
"""

    def get_admin_commands_content(self) -> str:
        """Get admin commands page content"""
        return """## Admin Commands

**Member Management:**
• `!promote <member>` - Promote member to next rank
• `!demote <member>` - Demote member to previous rank
• `!setxp <member> <amount>` - Set member's XP
• `!givexp <member> <amount>` - Give/remove XP

**Server Events:**
• `!eventstart [goal] [title]` - Start a new event
• `!eventend` - End current event
• `!eventrestart` - Restart event progress
• `!eventprogress` - Force progress update

**System:**
• `!auto_promote` - Auto-promote eligible members
• `!fix_all_roles` - Fix role assignments
• `!check_roles` - Check role configuration
• `!neon_backup` - Backup to database
• `!neon_status` - Check database status
• `!neon_resync` - Resync with database

**Testing:**
• `!test_promotion <member>` - Test promotion
• `!test_daily <member>` - Reset daily cooldown
• `!test_supply <member>` - Reset supply cooldown
• `!test_streak <member> <days>` - Set streak

**Word-Up:**
• `!wordup_reset` - Reset Word-Up game
• `!wordup_set <word>` - Set current word
• `!wordup_clearwarnings <member>` - Clear warnings
"""

    def get_features_content(self) -> str:
        """Get features page content"""
        return """## Bot Features

**XP & Ranking System:**
• Earn XP from chatting and voice activity
• Monthly XP reset with rank preservation
• Rank multipliers for faster progression
• Automatic role assignment based on ranks

**Word-Up Game:**
• Word chain game in dedicated channel
• Points for dictionary words vs slang
• Anti-spam and troll protection
• 3-day word cooldown system
• Leaderboard tracking

**Server Events:**
• Weekly community challenges
• Dynamic goal calculation
• Progress tracking with images
• Reward distribution on completion
• Top contributor leaderboards

**Daily Systems:**
• Daily bonus XP claims
• Supply drop mini-game
• Login streak tracking
• Consecutive day rewards

**Profile System:**
• Custom profile cards
• Rank display with progress
• Stats and achievements
• Thumbnail support

**Database:**
• PostgreSQL (Neon) integration
• Automatic backups
• Real-time syncing
• Data persistence
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
