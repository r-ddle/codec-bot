"""
Info cog - Commands for bot information, help, and interactive features.
"""
import discord
from discord.ext import commands
import asyncio
import time

from config.constants import ACTIVITY_REWARDS
from config.settings import logger
from utils.rate_limiter import enforce_rate_limit


class Info(commands.Cog):
    """Commands for bot information and help."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='codec')
    @enforce_rate_limit('intel')
    async def codec(self, ctx):
        """Interactive MGS codec conversation."""
        messages = [
            "*codec ring*",
            "Snake, do you copy?",
            f"I read you, {ctx.author.name}.",
            "Mission briefing incoming...",
        ]

        msg = await ctx.send(messages[0])
        for i in range(1, len(messages)):
            await asyncio.sleep(1.5)
            await msg.edit(content='\n'.join(messages[:i+1]))

        self.bot.codec_conversations[ctx.channel.id] = {
            'active': True,
            'start_time': time.time(),
            'messages': 0
        }

        await asyncio.sleep(2)
        await ctx.send("**You can now respond to continue the codec conversation...**")

    @commands.command(name='tactical_test')
    @enforce_rate_limit('intel')
    async def tactical_test(self, ctx, *, message: str = ""):
        """Test tactical word detection."""
        if not message:
            await ctx.send("**Usage:** `!tactical_test <your message>`\n**Example:** `!tactical_test infiltrate the enemy base`")
            return

        tactical_count = self.bot.check_tactical_words(message)

        embed = discord.Embed(
            title=" TACTICAL ANALYSIS",
            color=0x00ff00 if tactical_count > 0 else 0xff0000
        )

        embed.add_field(name="MESSAGE", value=f"```\n{message}\n```", inline=False)

        if tactical_count > 0:
            potential_gmp = tactical_count * ACTIVITY_REWARDS["tactical_word"]["gmp"]
            potential_xp = tactical_count * ACTIVITY_REWARDS["tactical_word"]["xp"]

            embed.add_field(
                name=" TACTICAL WORDS DETECTED",
                value=f"**Words Found:** {tactical_count}\n**Bonus:** +{potential_gmp} GMP, +{potential_xp} XP",
                inline=False
            )
        else:
            embed.add_field(
                name=" NO TACTICAL WORDS",
                value="Try using military, stealth, or MGS-related terms.",
                inline=False
            )

        await ctx.send(embed=embed)

    @commands.command(name='help')
    @enforce_rate_limit('leaderboard')
    async def help_command(self, ctx):
        """Enhanced help command with categories."""
        embed = discord.Embed(
            title=" TACTICAL OPERATIONS CENTER - COMMAND MANUAL",
            description="```\n> XP-BASED RANKING SYSTEM ACTIVE\n> SECURITY STATUS:  SECURE\n> TYPE: COMPREHENSIVE MANUAL\n```",
            color=0x599cff
        )

        # Basic Operations
        embed.add_field(
            name=" BASIC OPERATIONS",
            value="""```
!codec       - Interactive codec communication
!gmp         - Check status & rank
!rank [@user] - View rank status
!daily       - Daily supply drop
!tactical_test - Test tactical word detection
!info        - Quick command reference
```""",
            inline=False
        )

        # Ranking System
        embed.add_field(
            name=" XP-BASED RANKING GUIDE",
            value="""```
EARN DISCORD ROLES BY REACHING XP LEVELS:
 Private: 100 XP
 Specialist: 200 XP
 Corporal: 350 XP
 Sergeant: 500 XP
 Lieutenant: 750 XP
 Captain: 1,000 XP
 Major: 1,500 XP
 Colonel: 2,500 XP
 FOXHOUND: 4,000 XP

 AUTOMATIC: Roles assigned when you
reach the XP requirement!
```""",
            inline=False
        )

        # Leaderboard
        embed.add_field(
            name=" LEADERBOARDS",
            value="""```
!leaderboard [category] - View rankings
  Categories:
  xp, gmp, tactical, messages

Example: !lb xp
```""",
            inline=False
        )

        # Admin Commands
        if ctx.author.guild_permissions.kick_members or ctx.author.guild_permissions.administrator:
            embed.add_field(
                name=" MODERATION COMMANDS",
                value="""```
!kick <user> [reason]     - Remove operative
!ban <user> [reason]      - Permanently terminate
!clear <amount>           - Delete messages (1-100)
!auto_promote             - Auto-assign roles by XP
!fix_all_roles            - Sync roles with database
!check_roles              - Verify Discord roles
!test_promotion [@user]   - Test promotion system
```""",
                inline=False
            )

        # Progression Guide
        embed.add_field(
            name=" HOW TO EARN XP",
            value="""```
 Send messages (+3 XP every 30 sec)
 Voice activity (+2 XP per minute)
 Give reactions (+1 XP)
 Receive reactions (+2 XP)
 Daily bonus (+50 XP)
 Tactical words (+8 XP each)

⭐ Ranking based on XP only!
GMP is for stats and activities.
```""",
            inline=False
        )

        embed.set_footer(text=" XP-Based Ranking: Earn Discord roles through progression!")
        await ctx.send(embed=embed)

    @commands.command(name='info')
    @enforce_rate_limit('gmp')
    async def info(self, ctx):
        """Show bot information and commands."""
        embed = discord.Embed(
            title=" MOTHER BASE COMMAND CENTER",
            description="Available operations for all personnel:",
            color=0x599cff
        )

        embed.add_field(
            name=" BASIC COMMANDS",
            value="""```
!gmp         - Check status & rank
!rank [@user] - View rank info
!daily       - Daily supply drop
!leaderboard - Top operatives
!codec       - Interactive communication
!tactical_test - Test tactical words
```""",
            inline=False
        )

        # Show moderation commands if user has permissions
        if ctx.author.guild_permissions.kick_members or ctx.author.guild_permissions.manage_messages:
            embed.add_field(
                name=" MODERATION TOOLS",
                value="""```
!kick <user> [reason]  - Remove member
!ban <user> [reason]   - Ban member
!clear <amount>        - Delete messages
```""",
                inline=False
            )

        # Show admin commands if user has admin permissions
        if ctx.author.guild_permissions.administrator:
            embed.add_field(
                name=" ADMIN TOOLS",
                value="""```
!auto_promote      - Auto-assign roles
!test_promotion    - Test rank system
!check_roles       - Verify roles exist
```""",
                inline=False
            )

        embed.add_field(
            name=" XP-BASED RANKING",
            value="""```
Private: 100 XP
Specialist: 200 XP
Corporal: 350 XP
Sergeant: 500 XP
Lieutenant: 750 XP
Captain: 1,000 XP
...and more ranks!

Earn Discord roles automatically!
```""",
            inline=False
        )

        embed.add_field(
            name=" HOW TO EARN XP",
            value="""```
 Send messages      +3 XP
 Voice activity     +2 XP/min
 Reactions          +1-2 XP
 Daily bonus        +50 XP
 Tactical words     +8 XP each

Ranking based on XP only!
```""",
            inline=False
        )

        embed.set_footer(text="Use !help for complete command manual")

        await ctx.send(embed=embed)


async def setup(bot):
    """Load the Info cog."""
    await bot.add_cog(Info(bot))
