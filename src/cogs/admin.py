"""
Admin cog - Administrative commands for role management and testing.
"""
import discord
from discord.ext import commands
import asyncio
from typing import Optional

from config.constants import MGS_RANKS
from config.settings import logger
from utils.rank_system import get_rank_data_by_name, calculate_rank_from_xp
from utils.role_manager import update_member_roles
from utils.daily_supply_gen import generate_daily_supply_card
from io import BytesIO


class Admin(commands.Cog):
    """Administrative commands for server management."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='test_promotion')
    @commands.has_permissions(administrator=True)
    async def test_promotion(self, ctx, member: Optional[discord.Member] = None):
        """Test rank promotion system (Admin only)."""
        if member is None:
            member = ctx.author

        if member.bot:
            await ctx.send(" Cannot promote bots.")
            return

        try:
            member_data = self.bot.member_data.get_member_data(member.id, ctx.guild.id)
            current_rank = member_data['rank']
            current_xp = member_data['xp']

            # Find current rank index
            current_index = 0
            for i, rank_data in enumerate(MGS_RANKS):
                if rank_data["name"] == current_rank:
                    current_index = i
                    break

            # Check if can be promoted
            if current_index >= len(MGS_RANKS) - 1:
                await ctx.send(f" {member.display_name} is already at maximum rank: {current_rank}")
                return

            # Get next rank
            next_rank = MGS_RANKS[current_index + 1]
            old_roles = [role.name for role in member.roles if role.name in [r["role_name"] for r in MGS_RANKS if r["role_name"]]]

            # Force promote by setting XP to required amount
            member_data["xp"] = next_rank["required_xp"]
            member_data["rank"] = next_rank["name"]
            member_data["rank_icon"] = next_rank["icon"]

            # Update Discord role
            role_updated = await update_member_roles(member, next_rank["name"])
            role_granted = next_rank["role_name"] if role_updated else None

            # Save the test changes locally and schedule a background Neon sync (non-blocking)
            self.bot.member_data.schedule_save()
            # Kick off a background save (non-blocking) but do not force Neon sync here
            asyncio.create_task(self.bot.member_data.save_data_async(force=False))

            # Generate beautiful promotion image (simulates daily bonus with promotion)
            async with ctx.typing():
                try:
                    # Run CPU-bound Pillow generation off the event loop
                    img = await asyncio.to_thread(
                        generate_daily_supply_card,
                        username=member.display_name,
                        xp_reward=50,    # Simulated daily reward
                        current_xp=member_data['xp'],
                        current_rank=next_rank['name'],
                        streak_days=1,  # Test with 1-day streak
                        promoted=True,
                        new_rank=next_rank['name'],
                        role_granted=role_granted
                    )

                    # Convert to Discord file (do this quickly in thread as well)
                    image_bytes = BytesIO()
                    await asyncio.to_thread(img.save, image_bytes, format='PNG')
                    image_bytes.seek(0)

                    file = discord.File(fp=image_bytes, filename="test_promotion.png")

                    # Send text message with image
                    await ctx.send(
                        f"✅ **TEST PROMOTION COMPLETE**\n"
                        f"🎖️ {current_rank} → {next_rank['name']} {next_rank['icon']}\n"
                        f"💰 New XP: {member_data['xp']:,} (was {current_xp:,})\n"
                        f"{'✓ Discord role granted' if role_updated else '⚠️ Role not granted'}",
                        file=file
                    )

                except Exception as e:
                    # Fallback to embed if image fails
                    new_roles = [role.name for role in member.roles if role.name in [r["role_name"] for r in MGS_RANKS if r["role_name"]]]

                    embed = discord.Embed(
                        title=" RANK PROMOTION TEST",
                        description=f"Testing promotion system for {member.mention}",
                        color=0x00ff00
                    )

                    embed.add_field(
                        name="RANK CHANGE",
                        value=f"```\n{current_rank}  {next_rank['name']} {next_rank['icon']}\n```",
                        inline=False
                    )

                    embed.add_field(
                        name="ROLE CHANGE",
                        value=f"```\nOld Roles: {', '.join(old_roles) if old_roles else 'None'}\nNew Roles: {', '.join(new_roles) if new_roles else 'None'}\nUpdated: {' Yes' if role_updated else ' No'}\n```",
                        inline=False
                    )

                    embed.add_field(
                        name="XP ADJUSTMENT",
                        value=f"```\nOld XP: {current_xp}\nNew XP: {member_data['xp']}\nRequirement: {next_rank['required_xp']} XP\n```",
                        inline=False
                    )

                    embed.set_footer(text=f"⚠️ Image generation failed: {e}")
                    await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f" Test failed: {str(e)}")
            logger.error(f"Error in test_promotion: {e}")

    @commands.command(name='auto_promote')
    @commands.has_permissions(administrator=True)
    async def auto_promote(self, ctx):
        """Auto-promote all members based on their database XP."""
        status_msg = await ctx.send("```\n AUTO-PROMOTION SYSTEM ACTIVE...\nScanning database XP levels...\n```")

        try:
            promoted_count = 0
            processed_count = 0
            promotions = []

            guild_key = str(ctx.guild.id)
            if guild_key not in self.bot.member_data.data:
                await status_msg.edit(content="```\n No member data found for this guild.\n```")
                return

            existing_members = self.bot.member_data.data[guild_key]

            for member in ctx.guild.members:
                if member.bot:
                    continue

                processed_count += 1
                member_key = str(member.id)

                try:
                    if member_key not in existing_members:
                        continue

                    member_data = existing_members[member_key]
                    legacy_mode = self.bot.member_data.ensure_progression_mode(member_data)
                    current_xp = member_data.get('xp', 0)
                    stored_rank = member_data.get('rank', 'Rookie')

                    # Calculate correct rank based on XP
                    correct_rank, correct_icon = calculate_rank_from_xp(current_xp, use_legacy=legacy_mode)

                    # Check if they need promotion
                    if stored_rank != correct_rank:
                        # Update database rank
                        member_data['rank'] = correct_rank
                        member_data['rank_icon'] = correct_icon

                        # Update Discord role
                        role_updated = await update_member_roles(member, correct_rank)

                        if role_updated:
                            promoted_count += 1
                            rank_data = get_rank_data_by_name(correct_rank, use_legacy=legacy_mode)
                            role_name = rank_data.get("role_name", correct_rank)
                            promotions.append(f"{member.display_name}: {stored_rank}  {correct_rank} ({role_name})")
                            logger.info(f"AUTO-PROMOTED: {member.name} from {stored_rank} to {correct_rank} ({current_xp} XP)")

                    await asyncio.sleep(0.2)

                except Exception as e:
                    logger.error(f"Error processing {member.name}: {e}")

            # Save database changes (schedule background Neon sync to avoid blocking)
            self.bot.member_data.schedule_save()
            asyncio.create_task(self.bot.member_data.save_data_async(force=False))

            embed = discord.Embed(
                title=" AUTO-PROMOTION COMPLETE",
                description="```\n> DATABASE XP SCAN COMPLETE\n> PROMOTIONS APPLIED\n> STATUS: SUCCESS\n```",
                color=0x00ff00
            )

            embed.add_field(
                name="OPERATION RESULTS",
                value=f"```\nProcessed: {processed_count} members\nPromoted: {promoted_count} members\nDatabase Members: {len(existing_members)}\n```",
                inline=False
            )

            if promotions:
                promotion_text = "```\n" + "\n".join(promotions[:10]) + "\n```"
                if len(promotions) > 10:
                    promotion_text += f"\n*...and {len(promotions) - 10} more promotions*"

                embed.add_field(
                    name="RECENT PROMOTIONS",
                    value=promotion_text,
                    inline=False
                )

            embed.add_field(
                name="RANK REQUIREMENTS",
                value="""```
Private: 100 XP       | Captain: 1,000 XP
Specialist: 200 XP    | Major: 1,500 XP
Corporal: 350 XP      | Colonel: 2,500 XP
Sergeant: 500 XP      | FOXHOUND: 4,000 XP
Lieutenant: 750 XP
```""",
                inline=False
            )

            await status_msg.edit(content="", embed=embed)

        except Exception as e:
            await status_msg.edit(content=f"```\n Auto-promotion failed: {str(e)}\n```")
            logger.error(f"Error in auto_promote command: {e}")

    @commands.command(name='fix_all_roles')
    @commands.has_permissions(administrator=True)
    async def fix_all_roles(self, ctx):
        """Fix all member roles based on current database ranks (Admin only)."""
        status_msg = await ctx.send("```\n FIXING ALL MEMBER ROLES...\nSyncing Discord roles with database ranks...\n```")

        try:
            updated_count = 0
            failed_count = 0
            processed_count = 0

            guild_key = str(ctx.guild.id)
            if guild_key not in self.bot.member_data.data:
                await status_msg.edit(content="```\n No member data found for this guild.\n```")
                return

            existing_members = self.bot.member_data.data[guild_key]

            for member in ctx.guild.members:
                if member.bot:
                    continue

                processed_count += 1
                member_key = str(member.id)

                try:
                    if member_key not in existing_members:
                        continue

                    # Get member's current rank from database
                    member_data = existing_members[member_key]
                    current_rank = member_data.get('rank', 'Rookie')

                    # Update Discord roles to match database rank
                    role_updated = await update_member_roles(member, current_rank)

                    if role_updated:
                        updated_count += 1
                        logger.info(f"Fixed roles for {member.name} -> {current_rank}")
                    else:
                        failed_count += 1
                        logger.warning(f"Failed to fix roles for {member.name}")

                    # Small delay to avoid rate limits
                    await asyncio.sleep(0.3)

                except Exception as e:
                    failed_count += 1
                    logger.error(f"Error fixing {member.name}: {e}")

            embed = discord.Embed(
                title=" ROLE FIX COMPLETE",
                description="```\n> ROLE SYNCHRONIZATION COMPLETE\n> STATUS: SUCCESS\n```",
                color=0x00ff00
            )

            embed.add_field(
                name="OPERATION RESULTS",
                value=f"```\nProcessed: {processed_count} members\nFixed: {updated_count} roles\nFailed: {failed_count} members\nDatabase Members: {len(existing_members)}\n```",
                inline=False
            )

            embed.add_field(
                name="WHAT THIS DOES",
                value="```\n Reads each member's rank from database\n Removes incorrect Discord roles\n Assigns correct Discord roles\n Does NOT change XP or ranks\n Only syncs roles with stored data\n```",
                inline=False
            )

            embed.add_field(
                name="ROLE REQUIREMENTS",
                value="```\nRequired Discord roles:\nPrivate, Specialist, Corporal, Sergeant,\nLieutenant, Captain, Major, Colonel,\nFOXHOUND\n\nBot needs 'Manage Roles' permission!\n```",
                inline=False
            )

            await status_msg.edit(content="", embed=embed)

        except Exception as e:
            await status_msg.edit(content=f"```\n Role fix failed: {str(e)}\n```")
            logger.error(f"Error in fix_all_roles command: {e}")

    @commands.command(name='check_roles')
    @commands.has_permissions(administrator=True)
    async def check_roles(self, ctx):
        """Check if all required rank roles exist."""
        required_roles = [rank["role_name"] for rank in MGS_RANKS if rank["role_name"]]

        embed = discord.Embed(title=" ROLE VERIFICATION", color=0x599cff)

        missing_roles = []
        existing_roles = []

        for role_name in required_roles:
            role = discord.utils.get(ctx.guild.roles, name=role_name)
            if role:
                existing_roles.append(f" {role_name}")
            else:
                missing_roles.append(f" {role_name}")

        if existing_roles:
            embed.add_field(
                name="EXISTING ROLES",
                value="\n".join(existing_roles),
                inline=False
            )

        if missing_roles:
            embed.add_field(
                name="MISSING ROLES",
                value="\n".join(missing_roles) + "\n\n**Create these roles manually!**",
                inline=False
            )
            embed.color = 0xff0000
        else:
            embed.add_field(
                name="STATUS",
                value="```\n All rank roles found!\n Ready for role-based ranking\n```",
                inline=False
            )

        embed.add_field(
            name="BOT PERMISSIONS",
            value=f"```\nManage Roles: {'' if ctx.guild.me.guild_permissions.manage_roles else ''}\n```",
            inline=False
        )

        await ctx.send(embed=embed)

    @commands.command(name='neon_backup')
    @commands.has_permissions(administrator=True)
    async def neon_backup(self, ctx):
        """Manually trigger backup to Neon database (Admin only)."""
        if not self.bot.neon_db or not self.bot.neon_db.pool:
            await ctx.send(" Neon database is not connected!")
            return

        try:
            await ctx.send(" Starting backup to Neon database...")

            success = await self.bot.neon_db.backup_all_data(self.bot.member_data.data)

            if success:
                total_members = sum(len(members) for members in self.bot.member_data.data.values())
                guild_count = len(self.bot.member_data.data)

                embed = discord.Embed(
                    title=" NEON BACKUP COMPLETE",
                    description="All member data successfully backed up to cloud database",
                    color=0x00ff00
                )
                embed.add_field(name="Members Backed Up", value=str(total_members), inline=True)
                embed.add_field(name="Guilds", value=str(guild_count), inline=True)

                await ctx.send(embed=embed)
                logger.info(f"Manual Neon backup triggered by {ctx.author}")
            else:
                await ctx.send(" Backup failed. Check logs for details.")

        except Exception as e:
            await ctx.send(f" Error during backup: {e}")
            logger.error(f"Error in manual Neon backup: {e}")

    @commands.command(name='neon_status')
    @commands.has_permissions(administrator=True)
    async def neon_status(self, ctx):
        """Check Neon database connection status (Admin only)."""
        embed = discord.Embed(
            title=" NEON DATABASE STATUS",
            color=0x599cff
        )

        if self.bot.neon_db and self.bot.neon_db.pool:
            embed.add_field(name="Connection", value="✅ Connected", inline=False)

            # Get backup history
            try:
                history = await self.bot.neon_db.get_backup_history(limit=5)
                if history:
                    history_text = "\n".join([
                        f"`{record['backup_date'].strftime('%Y-%m-%d %H:%M')}` - {record['member_count']} members"
                        for record in history[:5]
                    ])
                    embed.add_field(name="Recent Backups", value=history_text, inline=False)
                else:
                    embed.add_field(name="Recent Backups", value="No backups yet", inline=False)

            except Exception as e:
                embed.add_field(name="Backup History", value=f"Error: {e}", inline=False)

        else:
            embed.add_field(name="Connection", value="❌ Not Connected", inline=False)
            embed.add_field(name="Note", value="Add `NEON_DATABASE_URL` to .env file", inline=False)

        await ctx.send(embed=embed)

    @commands.command(name='neon_resync')
    @commands.has_permissions(administrator=True)
    async def neon_resync(self, ctx):
        """Force full resync to Neon with rank recalculation (Admin only)."""
        if not self.bot.neon_db or not self.bot.neon_db.pool:
            await ctx.send(" Neon database is not connected!")
            return

        try:
            # First, reload data from member_data.json to ensure we have latest
            await ctx.send(" Reloading latest member data from disk...")
            self.bot.member_data.data = self.bot.member_data.load_data()

            await ctx.send(" Starting full resync with rank recalculation...")

            success = await self.bot.neon_db.backup_all_data(self.bot.member_data.data, recalculate_ranks=True)

            if success:
                total_members = sum(len(members) for members in self.bot.member_data.data.values())
                guild_count = len(self.bot.member_data.data)

                embed = discord.Embed(
                    title=" NEON FULL RESYNC COMPLETE",
                    description="All member data reloaded, ranks recalculated, and synced to cloud database",
                    color=0x00ff00
                )
                embed.add_field(name="Members Synced", value=str(total_members), inline=True)
                embed.add_field(name="Guilds", value=str(guild_count), inline=True)
                embed.add_field(name="Actions", value="✅ Ranks recalculated\n✅ Data reloaded from disk\n✅ Synced to Neon", inline=False)

                await ctx.send(embed=embed)
                logger.info(f"Full Neon resync with rank fix triggered by {ctx.author}")
            else:
                await ctx.send(" Resync failed. Check logs for details.")

        except Exception as e:
            await ctx.send(f" Error during resync: {e}")
            logger.error(f"Error in Neon resync: {e}")

    # === TESTING COMMANDS (Commander Role Only) ===

    # === TESTING COMMANDS (Commander Role Only) ===
    @commands.command(name='test_daily')
    @commands.has_permissions(administrator=True)
    async def test_daily(self, ctx, member: Optional[discord.Member] = None):
        """Reset daily bonus cooldown for testing (Commanders only)."""
        from datetime import datetime, timedelta, timezone
        from utils.rate_limiter import rate_limiter

        target = member or ctx.author

        try:
            member_data = self.bot.member_data.get_member_data(target.id, ctx.guild.id)

            # Reset last daily to yesterday to preserve streak
            # This allows immediate claim while maintaining streak continuity
            yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime('%Y-%m-%d')
            member_data['last_daily'] = yesterday

            # Also reset the rate limiter for the daily command
            rate_limiter.reset_cooldown(target.id, 'daily')

            # Save locally and schedule a background Neon sync (non-blocking)
            self.bot.member_data.schedule_save()
            asyncio.create_task(self.bot.member_data.save_data_async(force=False))

            current_streak = member_data.get('daily_streak', 0)
            next_streak = current_streak + 1  # Will be this after claiming

            embed = discord.Embed(
                title="✅ DAILY COOLDOWN RESET",
                description=f"Reset daily bonus cooldown for {target.mention}",
                color=0x00ff00
            )
            embed.add_field(name="Status", value="Can now claim !daily immediately", inline=False)
            embed.add_field(name="Current Streak", value=f"{current_streak} days", inline=True)
            embed.add_field(name="Next Claim Streak", value=f"{next_streak} days", inline=True)
            embed.set_footer(text="Testing command - Administrators only | Streak preserved")
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Error resetting cooldown: {e}")
            logger.error(f"Error in test_daily: {e}")

    @commands.command(name='test_supply')
    @commands.has_permissions(administrator=True)
    async def test_supply(self, ctx, member: Optional[discord.Member] = None):
        """Reset supply drop cooldown for testing (Commanders only)."""
        target = member or ctx.author

        try:
            member_data = self.bot.member_data.get_member_data(target.id, ctx.guild.id)

            # Reset last supply drop timestamp
            if 'last_supply_drop' in member_data:
                member_data['last_supply_drop'] = None
                self.bot.member_data.schedule_save()

                embed = discord.Embed(
                    title="✅ SUPPLY DROP COOLDOWN RESET",
                    description=f"Reset supply drop cooldown for {target.mention}",
                    color=0x00ff00
                )
                embed.add_field(name="Status", value="Can now claim supply drop immediately", inline=False)
                embed.set_footer(text="Testing command - Commanders only")
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"⚠️ {target.mention} doesn't have supply drop tracking enabled")

        except Exception as e:
            await ctx.send(f"❌ Error resetting cooldown: {e}")
            logger.error(f"Error in test_supply: {e}")

    @commands.command(name='force_daily')
    @commands.has_permissions(administrator=True)
    async def force_daily(self, ctx, member: Optional[discord.Member] = None):
        """Force grant daily bonus bypassing cooldown (Commanders only)."""
        target = member or ctx.author

        try:
            member_data = self.bot.member_data.get_member_data(target.id, ctx.guild.id)

            # Grant rewards
            xp_reward = 50

            member_data['xp'] = member_data.get('xp', 0) + xp_reward
            self.bot.member_data.schedule_save()

            embed = discord.Embed(
                title="💰 FORCED DAILY BONUS",
                description=f"Force-granted daily bonus to {target.mention}",
                color=0xffaa00
            )
            embed.add_field(name="XP Granted", value=f"+{xp_reward} XP", inline=True)
            embed.add_field(
                name="New Total",
                value=f"XP: {member_data['xp']:,}",
                inline=False
            )
            embed.set_footer(text="Testing command - Commanders only (bypassed cooldown)")
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Error forcing daily: {e}")
            logger.error(f"Error in force_daily: {e}")

    @commands.command(name='test_streak')
    @commands.has_permissions(administrator=True)
    async def test_streak(self, ctx, member: Optional[discord.Member] = None, days: int = 7):
        """Set daily streak to specific value for testing (Commanders only)."""
        target = member or ctx.author

        if days < 0:
            await ctx.send("❌ Streak days must be non-negative")
            return

        try:
            member_data = self.bot.member_data.get_member_data(target.id, ctx.guild.id)

            # Set streak
            member_data['daily_streak'] = days

            # Save locally and schedule a background Neon sync (non-blocking)
            self.bot.member_data.schedule_save()
            asyncio.create_task(self.bot.member_data.save_data_async(force=False))

            # Determine milestone
            if days >= 100:
                milestone = "🏆 LEGENDARY STREAK"
            elif days >= 30:
                milestone = "⭐ ELITE STREAK"
            elif days >= 7:
                milestone = "🔥 HOT STREAK"
            else:
                milestone = f"DAY {days} OPERATION"

            embed = discord.Embed(
                title="✅ STREAK MODIFIED",
                description=f"Set daily streak for {target.mention}",
                color=0x00ff00
            )
            embed.add_field(name="Streak Days", value=f"{days} days", inline=True)
            embed.add_field(name="Milestone", value=milestone, inline=True)
            embed.add_field(name="Verification", value=f"Saved: {member_data.get('daily_streak', 0)} days", inline=False)
            embed.set_footer(text="Testing command - Administrators only")
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Error setting streak: {e}")
            logger.error(f"Error in test_streak: {e}")

    # REMOVED: test_supply_anim command
    # Animation feature disabled to reduce server load and improve performance

    @commands.command(name='promote')
    @commands.has_permissions(administrator=True)
    async def promote_member(self, ctx, member: discord.Member, rank_name: Optional[str] = None):
        """
        Manually promote a member to a specific rank or next rank.

        Usage: !promote @user "Rank Name"  (to specific rank)
               !promote @user              (to next rank)
        Example: !promote @Snake "Big Boss"
                 !promote @Snake           (promotes one rank up)
        """
        if member.bot:
            await ctx.send("❌ Cannot promote bots.")
            return

        try:
            member_data = self.bot.member_data.get_member_data(member.id, ctx.guild.id)
            old_rank = member_data.get('rank', 'Recruit')
            current_xp = member_data.get('xp', 0)

            if rank_name:
                # Promote to specific rank
                target_rank = None
                for rank in MGS_RANKS:
                    if rank["name"].lower() == rank_name.lower():
                        target_rank = rank
                        break

                if not target_rank:
                    available_ranks = ", ".join([f'"{r["name"]}"' for r in MGS_RANKS])
                    await ctx.send(f"❌ Invalid rank name. Available ranks:\n{available_ranks}")
                    return
            else:
                # Promote to next rank
                current_index = 0
                for i, rank in enumerate(MGS_RANKS):
                    if rank["name"] == old_rank:
                        current_index = i
                        break

                if current_index >= len(MGS_RANKS) - 1:
                    await ctx.send(f"❌ {member.display_name} is already at maximum rank: {old_rank}")
                    return

                target_rank = MGS_RANKS[current_index + 1]

            member_data['rank'] = target_rank['name']
            member_data['rank_icon'] = target_rank['icon']
            member_data['xp'] = target_rank['required_xp']

            # Update Discord role
            role_updated = await update_member_roles(member, target_rank["name"])

            # Save
            self.bot.member_data.schedule_save()
            await self.bot.member_data.save_data_async()

            embed = discord.Embed(
                title="✅ MEMBER PROMOTED",
                description=f"{member.mention} has been promoted!",
                color=0x00ff00
            )
            embed.add_field(name="Old Rank", value=old_rank, inline=True)
            embed.add_field(name="New Rank", value=f"{target_rank['icon']} {target_rank['name']}", inline=True)
            embed.add_field(name="XP Set", value=f"{target_rank['required_xp']:,}", inline=False)
            embed.add_field(name="Discord Role", value="✅ Applied" if role_updated else "⚠️ Role not found", inline=False)
            embed.set_footer(text=f"Promoted by {ctx.author}")
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Error promoting member: {e}")
            logger.error(f"Error in promote: {e}")

    @commands.command(name='demote')
    @commands.has_permissions(administrator=True)
    async def demote_member(self, ctx, member: discord.Member, rank_name: Optional[str] = None):
        """
        Manually demote a member to a specific rank or previous rank (no XP change).

        Usage: !demote @user "Rank Name"  (to specific rank)
               !demote @user              (to previous rank)
        Example: !demote @Snake Private
                 !demote @Snake           (demotes one rank down)
        Note: Only changes rank, XP remains unchanged (for monthly reset system)
        """
        if member.bot:
            await ctx.send("❌ Cannot demote bots.")
            return

        try:
            member_data = self.bot.member_data.get_member_data(member.id, ctx.guild.id)
            old_rank = member_data.get('rank', 'Rookie')
            current_xp = member_data.get('xp', 0)

            if rank_name:
                # Demote to specific rank
                target_rank = None
                for rank in MGS_RANKS:
                    if rank["name"].lower() == rank_name.lower():
                        target_rank = rank
                        break

                if not target_rank:
                    available_ranks = ", ".join([f'"{r["name"]}"' for r in MGS_RANKS])
                    await ctx.send(f"❌ Invalid rank name. Available ranks:\n{available_ranks}")
                    return
            else:
                # Demote to previous rank
                current_index = 0
                for i, rank in enumerate(MGS_RANKS):
                    if rank["name"] == old_rank:
                        current_index = i
                        break

                if current_index <= 0:
                    await ctx.send(f"❌ {member.display_name} is already at the lowest rank: {old_rank}")
                    return

                target_rank = MGS_RANKS[current_index - 1]

            member_data['rank'] = target_rank['name']
            member_data['rank_icon'] = target_rank['icon']
            # XP remains unchanged for monthly reset system

            # Update Discord role
            role_updated = await update_member_roles(member, target_rank["name"])

            # Save
            self.bot.member_data.schedule_save()
            await self.bot.member_data.save_data_async()

            embed = discord.Embed(
                title="✅ MEMBER DEMOTED",
                description=f"{member.mention} has been demoted!",
                color=0xff9900
            )
            embed.add_field(name="Old Rank", value=old_rank, inline=True)
            embed.add_field(name="New Rank", value=f"{target_rank['icon']} {target_rank['name']}", inline=True)
            embed.add_field(name="XP (Unchanged)", value=f"{current_xp:,}", inline=False)
            embed.add_field(name="Discord Role", value="✅ Applied" if role_updated else "⚠️ Role not found", inline=False)
            embed.set_footer(text=f"Demoted by {ctx.author} | XP unchanged for monthly reset system")
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Error demoting member: {e}")
            logger.error(f"Error in demote: {e}")

    @commands.command(name='setxp')
    @commands.has_permissions(administrator=True)
    async def set_xp(self, ctx, member: discord.Member, amount: int):
        """
        Set a member's XP to a specific amount and update rank.

        Usage: !setxp @user 5000
        Note: This will auto-calculate and update the rank based on XP
        """
        if member.bot:
            await ctx.send("❌ Cannot set XP for bots.")
            return

        try:
            member_data = self.bot.member_data.get_member_data(member.id, ctx.guild.id)
            old_xp = member_data.get('xp', 0)
            old_rank = member_data.get('rank', 'Rookie')

            # Set new XP
            new_xp = max(0, amount)  # Don't go below 0
            member_data['xp'] = new_xp

            # Calculate new rank based on XP
            legacy_mode = self.bot.member_data.ensure_progression_mode(member_data)
            new_rank_name, new_rank_icon = calculate_rank_from_xp(new_xp, use_legacy=legacy_mode)
            rank_changed = new_rank_name != old_rank

            member_data['rank'] = new_rank_name
            member_data['rank_icon'] = new_rank_icon

            # Update Discord role
            role_updated = await update_member_roles(member, new_rank_name)

            # Save
            self.bot.member_data.schedule_save()
            await self.bot.member_data.save_data_async()

            embed = discord.Embed(
                title="✅ XP SET",
                description=f"XP set for {member.mention}",
                color=0x00ff00
            )
            embed.add_field(name="Old XP", value=f"{old_xp:,}", inline=True)
            embed.add_field(name="New XP", value=f"{new_xp:,}", inline=True)
            embed.add_field(name="XP Change", value=f"{new_xp - old_xp:+,}", inline=True)

            if rank_changed:
                embed.add_field(
                    name="RANK CHANGED",
                    value=f"{old_rank} → {new_rank_icon} {new_rank_name}",
                    inline=False
                )
                embed.add_field(name="Discord Role", value="✅ Updated" if role_updated else "⚠️ Role not found", inline=False)
            else:
                embed.add_field(
                    name="Current Rank",
                    value=f"{new_rank_icon} {new_rank_name}",
                    inline=False
                )

            embed.set_footer(text=f"Modified by {ctx.author}")
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Error setting XP: {e}")
            logger.error(f"Error in setxp: {e}")

    @commands.command(name='givexp')
    @commands.has_permissions(administrator=True)
    async def give_xp(self, ctx, member: discord.Member, amount: int):
        """
        Give XP to a member and update their rank if needed.

        Usage: !givexp @user 1000
        Use negative amounts to remove XP: !givexp @user -500
        """
        if member.bot:
            await ctx.send("❌ Cannot give XP to bots.")
            return

        try:
            member_data = self.bot.member_data.get_member_data(member.id, ctx.guild.id)
            old_xp = member_data.get('xp', 0)
            old_rank = member_data.get('rank', 'Rookie')

            # Add XP (can be negative)
            new_xp = max(0, old_xp + amount)  # Don't go below 0
            member_data['xp'] = new_xp

            # Check if rank changed using appropriate progression table
            legacy_mode = self.bot.member_data.ensure_progression_mode(member_data)
            new_rank_name, new_rank_icon = calculate_rank_from_xp(new_xp, use_legacy=legacy_mode)
            rank_changed = new_rank_name != old_rank

            if rank_changed:
                member_data['rank'] = new_rank_name
                member_data['rank_icon'] = new_rank_icon
                await update_member_roles(member, new_rank_name)

            # Save
            self.bot.member_data.schedule_save()
            await self.bot.member_data.save_data_async()

            embed = discord.Embed(
                title="✅ XP MODIFIED",
                description=f"XP {'added to' if amount > 0 else 'removed from'} {member.mention}",
                color=0x00ff00 if amount > 0 else 0xff9900
            )
            embed.add_field(name="XP Change", value=f"{amount:+,}", inline=True)
            embed.add_field(name="Old XP", value=f"{old_xp:,}", inline=True)
            embed.add_field(name="New XP", value=f"{new_xp:,}", inline=True)

            if rank_changed:
                embed.add_field(
                    name="RANK CHANGED",
                    value=f"{old_rank} → {new_rank_icon} {new_rank_name}",
                    inline=False
                )
            else:
                embed.add_field(
                    name="Current Rank",
                    value=f"{member_data.get('rank_icon', '')} {member_data.get('rank', 'Rookie')}",
                    inline=False
                )

            embed.set_footer(text=f"Modified by {ctx.author}")
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Error giving XP: {e}")
            logger.error(f"Error in givexp: {e}")

    @commands.command(name='adminhelp')
    @commands.has_permissions(administrator=True)
    async def admin_help(self, ctx):
        """Display all available admin commands (Admin only)"""
        embed = discord.Embed(
            title="🛠️ ADMIN COMMANDS",
            description="Administrative tools for server management",
            color=0x00ff00
        )

        # Rank Management
        embed.add_field(
            name="📊 RANK MANAGEMENT",
            value="""```
!promote @user ["Rank"]    - Promote to rank or next (sets XP)
!demote @user ["Rank"]     - Demote to rank or previous (XP unchanged)
!auto_promote              - Auto-promote all members by XP
!test_promotion [@user]    - Test promotion system
```""",
            inline=False
        )

        # XP Management
        embed.add_field(
            name="💰 XP MANAGEMENT",
            value="""```
!setxp @user 5000       - Set exact XP amount
!givexp @user 1000      - Add XP (use negative to remove)
```""",
            inline=False
        )

        # Role Management
        embed.add_field(
            name="🎭 ROLE MANAGEMENT",
            value="""```
!fix_all_roles          - Sync all Discord roles with ranks
!check_roles            - Check role sync status
```""",
            inline=False
        )

        # Testing Commands
        embed.add_field(
            name="🧪 TESTING",
            value="""```
!test_daily [@user]     - Test daily reward system
!test_supply            - Test supply card generation
!force_daily @user      - Force daily claim reset
!test_streak @user 5    - Set daily streak for testing
```""",
            inline=False
        )

        # Database Management
        embed.add_field(
            name="💾 DATABASE",
            value="""```
!neon_backup           - Manual backup to Neon DB
!neon_status           - Check DB connection
!neon_resync           - Full resync with database
```""",
            inline=False
        )

        # Server Stats
        embed.add_field(
            name="📈 SERVER STATS",
            value="""```
!serveravg             - Check server average messages
```""",
            inline=False
        )

        embed.add_field(
            name="📝 NOTES",
            value="• **Monthly Reset System**: Use `!demote` instead of changing XP\n"
                  "• **XP Changes**: `!setxp` and `!givexp` auto-update ranks\n"
                  "• **Rank Names**: Rookie, Private, Specialist, Corporal, Sergeant, Lieutenant, Captain, Major, Colonel, FOXHOUND",
            inline=False
        )

        embed.set_footer(text="All commands require Administrator permissions")
        await ctx.send(embed=embed)


async def setup(bot):
    """Load the Admin cog."""
    await bot.add_cog(Admin(bot))
