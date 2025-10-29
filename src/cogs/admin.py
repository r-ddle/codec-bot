"""
Admin cog - Administrative commands for role management and testing.
"""
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from typing import Optional

from config.constants import COZY_RANKS
from config.settings import logger
from utils.rank_system import get_rank_data_by_name, calculate_rank_from_xp
from utils.role_manager import update_member_roles
from utils.daily_supply_gen import generate_daily_supply_card
from utils.components_builder import (
    create_status_container,
    create_success_message,
    create_error_message,
    create_info_card,
    create_simple_message
)
from utils.admin_modals import AddXPModal, RemoveXPModal, SetRankModal
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
            container = create_error_message(
                "Cannot Promote Bot",
                "Bots cannot be promoted. This command only works for server members, not bots."
            )
            from discord.ui import LayoutView
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)
            return

        try:
            member_data = self.bot.member_data.get_member_data(member.id, ctx.guild.id)
            current_rank = member_data['rank']
            current_xp = member_data['xp']

            # Find current rank index
            current_index = 0
            for i, rank_data in enumerate(COZY_RANKS):
                if rank_data["name"] == current_rank:
                    current_index = i
                    break

            # Check if can be promoted
            if current_index >= len(COZY_RANKS) - 1:
                container = create_info_card(
                    "Maximum Rank Reached",
                    f"{member.display_name} is already at maximum rank: {current_rank}. This member cannot be promoted any further."
                )
                from discord.ui import LayoutView
                view = LayoutView()
                view.add_item(container)
                await ctx.send(view=view)
                return

            # Get next rank
            next_rank = COZY_RANKS[current_index + 1]
            old_roles = [role.id for role in member.roles if role.id in [r["role_id"] for r in COZY_RANKS if r.get("role_id")]]

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
                    # Fallback to component display if image fails
                    new_roles = [role.id for role in member.roles if role.id in [r["role_id"] for r in COZY_RANKS if r.get("role_id")]]

                    container = create_status_container(
                        title="🎖️ RANK PROMOTION TEST",
                        fields=[
                            {
                                "name": "RANK CHANGE",
                                "value": f"```\n{current_rank} → {next_rank['name']} {next_rank['icon']}\n```"
                            },
                            {
                                "name": "ROLE CHANGE",
                                "value": f"```\nOld Roles: {', '.join(old_roles) if old_roles else 'None'}\nNew Roles: {', '.join(new_roles) if new_roles else 'None'}\nUpdated: {'✅ Yes' if role_updated else '❌ No'}\n```"
                            },
                            {
                                "name": "XP ADJUSTMENT",
                                "value": f"```\nOld XP: {current_xp:,}\nNew XP: {member_data['xp']:,}\nRequirement: {next_rank['required_xp']:,} XP\n```"
                            }
                        ],
                        footer=f"⚠️ Image generation failed: {e}"
                    )

                    from discord.ui import LayoutView
                    view = LayoutView()
                    view.add_item(container)
                    await ctx.send(view=view)

        except Exception as e:
            container = create_error_message(
                "Test Failed",
                f"Promotion test encountered an error: {str(e)}"
            )
            from discord.ui import LayoutView
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)
            logger.error(f"Error in test_promotion: {e}")

    @commands.command(name='auto_promote')
    @commands.has_permissions(administrator=True)
    async def auto_promote(self, ctx):
        """Auto-promote all members based on their database XP."""
        container = create_simple_message(
            "Auto-Promotion System",
            "AUTO-PROMOTION SYSTEM ACTIVE...\nScanning database XP levels..."
        )
        from discord.ui import LayoutView
        view = LayoutView()
        view.add_item(container)
        status_msg = await ctx.send(view=view)

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

            promotion_fields = [
                {
                    "name": "OPERATION RESULTS",
                    "value": f"```\nProcessed: {processed_count} members\nPromoted: {promoted_count} members\nDatabase Members: {len(existing_members)}\n```"
                }
            ]

            if promotions:
                promotion_text = "```\n" + "\n".join(promotions[:10]) + "\n```"
                if len(promotions) > 10:
                    promotion_text += f"\n*...and {len(promotions) - 10} more promotions*"

                promotion_fields.append({
                    "name": "RECENT PROMOTIONS",
                    "value": promotion_text
                })

            promotion_fields.append({
                "name": "RANK REQUIREMENTS",
                "value": """```
Private: 100 XP       | Captain: 1,000 XP
Specialist: 200 XP    | Major: 1,500 XP
Corporal: 350 XP      | Colonel: 2,500 XP
Sergeant: 500 XP      | FOXHOUND: 4,000 XP
Lieutenant: 750 XP
```"""
            })

            container = create_status_container(
                title="✅ AUTO-PROMOTION COMPLETE",
                fields=promotion_fields,
                footer="Database XP scan complete. Promotions applied successfully."
            )

            from discord.ui import LayoutView
            view = LayoutView()
            view.add_item(container)
            await status_msg.edit(content="", view=view)

        except Exception as e:
            error_container = create_error_message(
                "Auto-Promotion Failed",
                f"The auto-promotion system encountered an error: {str(e)}"
            )
            from discord.ui import LayoutView
            error_view = LayoutView()
            error_view.add_item(error_container)
            await status_msg.edit(content="", view=error_view)
            logger.error(f"Error in auto_promote command: {e}")

    @commands.command(name='fix_all_roles')
    @commands.has_permissions(administrator=True)
    async def fix_all_roles(self, ctx):
        """Fix all member roles based on current database ranks (Admin only)."""
        container = create_simple_message(
            "Role Sync System",
            "FIXING ALL MEMBER ROLES...\nSyncing Discord roles with database ranks..."
        )
        from discord.ui import LayoutView
        view = LayoutView()
        view.add_item(container)
        status_msg = await ctx.send(view=view)

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

            container = create_status_container(
                title="✅ ROLE FIX COMPLETE",
                fields=[
                    {
                        "name": "OPERATION RESULTS",
                        "value": f"```\nProcessed: {processed_count} members\nFixed: {updated_count} roles\nFailed: {failed_count} members\nDatabase Members: {len(existing_members)}\n```"
                    },
                    {
                        "name": "WHAT THIS DOES",
                        "value": "```\n✓ Reads each member's rank from database\n✓ Removes incorrect Discord roles\n✓ Assigns correct Discord roles\n✓ Does NOT change XP or ranks\n✓ Only syncs roles with stored data\n```"
                    },
                    {
                        "name": "ROLE REQUIREMENTS",
                        "value": "```\nRequired Discord roles:\nPrivate, Specialist, Corporal, Sergeant,\nLieutenant, Captain, Major, Colonel,\nFOXHOUND\n\nBot needs 'Manage Roles' permission!\n```"
                    }
                ],
                footer="Role synchronization complete"
            )

            from discord.ui import LayoutView
            view = LayoutView()
            view.add_item(container)
            await status_msg.edit(content="", view=view)

        except Exception as e:
            await status_msg.edit(content=f"```\n Role fix failed: {str(e)}\n```")
            logger.error(f"Error in fix_all_roles command: {e}")

    @commands.command(name='check_roles')
    @commands.has_permissions(administrator=True)
    async def check_roles(self, ctx):
        """Check if all required rank roles exist."""
        required_role_ids = [rank["role_id"] for rank in COZY_RANKS if rank.get("role_id")]

        missing_roles = []
        existing_roles = []

        for role_id in required_role_ids:
            role = ctx.guild.get_role(role_id)
            # Get the rank name for display
            rank_name = next((r["name"] for r in COZY_RANKS if r.get("role_id") == role_id), f"Role ID {role_id}")
            if role:
                existing_roles.append(f"✅ {rank_name} (ID: {role_id})")
            else:
                missing_roles.append(f"❌ {rank_name} (ID: {role_id})")

        fields = []

        if existing_roles:
            fields.append({
                "name": "EXISTING ROLES",
                "value": "\n".join(existing_roles)
            })

        if missing_roles:
            fields.append({
                "name": "MISSING ROLES",
                "value": "\n".join(missing_roles) + "\n\n**Create these roles manually!**"
            })
        else:
            fields.append({
                "name": "STATUS",
                "value": "```\n✓ All rank roles found!\n✓ Ready for role-based ranking\n```"
            })

        fields.append({
            "name": "BOT PERMISSIONS",
            "value": f"```\nManage Roles: {'✅' if ctx.guild.me.guild_permissions.manage_roles else '❌'}\n```"
        })

        container = create_status_container(
            title="🔍 ROLE VERIFICATION",
            fields=fields
        )

        from discord.ui import LayoutView
        view = LayoutView()
        view.add_item(container)
        await ctx.send(view=view)

    @commands.command(name='neon_backup')
    @commands.has_permissions(administrator=True)
    async def neon_backup(self, ctx):
        """Manually trigger backup to Neon database (Admin only)."""
        if not self.bot.neon_db:
            container = create_error_message("Neon database module not initialized!")
            from discord.ui import LayoutView
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)
            return

        if not self.bot.neon_db.pool:
            container = create_error_message("Neon database not connected", "Attempting to reconnect...")
            from discord.ui import LayoutView
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)

            connected, error = await self.bot.neon_db.connect()
            if not connected:
                error_container = create_error_message(f"Failed to reconnect to Neon database", f"{error}")
                error_view = LayoutView()
                error_view.add_item(error_container)
                await ctx.send(view=error_view)
                return

            success_container = create_success_message("Successfully reconnected to Neon database!", [])
            success_view = LayoutView()
            success_view.add_item(success_container)
            await ctx.send(view=success_view)

        try:
            container = create_simple_message("🔄 Backup In Progress", "Starting backup to Neon database...", "💾")
            from discord.ui import LayoutView
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)

            success = await self.bot.neon_db.backup_all_data(self.bot.member_data.data)

            if success:
                total_members = sum(len(members) for members in self.bot.member_data.data.values())
                guild_count = len(self.bot.member_data.data)

                result_container = create_success_message(
                    "NEON BACKUP COMPLETE",
                    [
                        f"Members Backed Up: {total_members}",
                        f"Guilds: {guild_count}",
                        "All member data successfully backed up to cloud database"
                    ]
                )

                result_view = LayoutView()
                result_view.add_item(result_container)
                await ctx.send(view=result_view)
                logger.info(f"Manual Neon backup triggered by {ctx.author}")
            else:
                error_container = create_error_message("Backup failed", "Check logs for details.")
                error_view = LayoutView()
                error_view.add_item(error_container)
                await ctx.send(view=error_view)

        except Exception as e:
            error_container = create_error_message("Error during backup", str(e))
            error_view = LayoutView()
            error_view.add_item(error_container)
            await ctx.send(view=error_view)
            logger.error(f"Error in manual Neon backup: {e}")

    @commands.command(name='neon_status')
    @commands.has_permissions(administrator=True)
    async def neon_status(self, ctx):
        """Check Neon database connection status (Admin only)."""
        fields = []

        if self.bot.neon_db and self.bot.neon_db.pool:
            fields.append({"name": "Connection", "value": "✅ Connected"})

            # Get backup history
            try:
                history = await self.bot.neon_db.get_backup_history(limit=5)
                if history:
                    history_text = "\n".join([
                        f"`{record['backup_date'].strftime('%Y-%m-%d %H:%M')}` - {record['member_count']} members"
                        for record in history[:5]
                    ])
                    fields.append({"name": "Recent Backups", "value": history_text})
                else:
                    fields.append({"name": "Recent Backups", "value": "No backups yet"})

            except Exception as e:
                fields.append({"name": "Backup History", "value": f"Error: {e}"})

        else:
            fields.append({"name": "Connection", "value": "❌ Not Connected"})
            fields.append({"name": "Note", "value": "Add `NEON_DATABASE_URL` to .env file"})

        container = create_status_container(
            title="💾 NEON DATABASE STATUS",
            fields=fields
        )

        from discord.ui import LayoutView
        view = LayoutView()
        view.add_item(container)
        await ctx.send(view=view)

    @commands.command(name='neon_resync')
    @commands.has_permissions(administrator=True)
    async def neon_resync(self, ctx):
        """Force full resync to Neon with rank recalculation (Admin only)."""
        if not self.bot.neon_db:
            container = create_error_message("Neon database module not initialized!")
            from discord.ui import LayoutView
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)
            return

        if not self.bot.neon_db.pool:
            container = create_simple_message("🔄 Reconnecting", "Neon database not connected. Attempting to reconnect...")
            from discord.ui import LayoutView
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)

            connected, error = await self.bot.neon_db.connect()
            if not connected:
                error_container = create_error_message("Failed to reconnect to Neon database", str(error))
                error_view = LayoutView()
                error_view.add_item(error_container)
                await ctx.send(view=error_view)
                return

            success_container = create_success_message("Successfully reconnected to Neon database!", [])
            success_view = LayoutView()
            success_view.add_item(success_container)
            await ctx.send(view=success_view)

        try:
            # First, reload data from member_data.json to ensure we have latest
            reload_container = create_simple_message("📂 Loading", "Reloading latest member data from disk...")
            from discord.ui import LayoutView
            view = LayoutView()
            view.add_item(reload_container)
            await ctx.send(view=view)

            self.bot.member_data.data = self.bot.member_data.load_data()

            sync_container = create_simple_message("🔄 Syncing", "Starting full resync with rank recalculation...")
            sync_view = LayoutView()
            sync_view.add_item(sync_container)
            await ctx.send(view=sync_view)

            success = await self.bot.neon_db.backup_all_data(self.bot.member_data.data, recalculate_ranks=True)

            if success:
                total_members = sum(len(members) for members in self.bot.member_data.data.values())
                guild_count = len(self.bot.member_data.data)

                result_container = create_success_message(
                    "NEON FULL RESYNC COMPLETE",
                    [
                        f"Members Synced: {total_members}",
                        f"Guilds: {guild_count}",
                        "✅ Ranks recalculated",
                        "✅ Data reloaded from disk",
                        "✅ Synced to Neon"
                    ],
                    footer="All member data reloaded, ranks recalculated, and synced to cloud database"
                )

                result_view = LayoutView()
                result_view.add_item(result_container)
                await ctx.send(view=result_view)
                logger.info(f"Full Neon resync with rank fix triggered by {ctx.author}")
            else:
                error_container = create_error_message("Resync failed", "Check logs for details.")
                error_view = LayoutView()
                error_view.add_item(error_container)
                await ctx.send(view=error_view)

        except Exception as e:
            error_container = create_error_message("Error during resync", str(e))
            error_view = LayoutView()
            error_view.add_item(error_container)
            await ctx.send(view=error_view)
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

            container = create_status_container(
                title="✅ DAILY COOLDOWN RESET",
                fields=[
                    {"name": "Status", "value": f"Can now claim !daily immediately\nTarget: {target.mention}"},
                    {"name": "Current Streak", "value": f"{current_streak} days"},
                    {"name": "Next Claim Streak", "value": f"{next_streak} days"}
                ],
                footer="Testing command - Administrators only | Streak preserved"
            )

            from discord.ui import LayoutView
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)

        except Exception as e:
            error_container = create_error_message("Error resetting cooldown", str(e))
            from discord.ui import LayoutView
            error_view = LayoutView()
            error_view.add_item(error_container)
            await ctx.send(view=error_view)
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

                container = create_status_container(
                    title="✅ SUPPLY DROP COOLDOWN RESET",
                    fields=[
                        {"name": "Status", "value": f"Can now claim supply drop immediately\nTarget: {target.mention}"}
                    ],
                    footer="Testing command - Commanders only"
                )

                from discord.ui import LayoutView
                view = LayoutView()
                view.add_item(container)
                await ctx.send(view=view)
            else:
                container = create_error_message(
                    "Supply drop tracking not enabled",
                    f"{target.mention} doesn't have supply drop tracking enabled"
                )
                from discord.ui import LayoutView
                view = LayoutView()
                view.add_item(container)
                await ctx.send(view=view)

        except Exception as e:
            error_container = create_error_message("Error resetting cooldown", str(e))
            from discord.ui import LayoutView
            error_view = LayoutView()
            error_view.add_item(error_container)
            await ctx.send(view=error_view)
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

            container = create_status_container(
                title="💰 FORCED DAILY BONUS",
                fields=[
                    {"name": "Target", "value": target.mention},
                    {"name": "XP Granted", "value": f"+{xp_reward} XP"},
                    {"name": "New Total", "value": f"XP: {member_data['xp']:,}"}
                ],
                footer="Testing command - Commanders only (bypassed cooldown)"
            )

            from discord.ui import LayoutView
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)

        except Exception as e:
            error_container = create_error_message("Error forcing daily", str(e))
            from discord.ui import LayoutView
            error_view = LayoutView()
            error_view.add_item(error_container)
            await ctx.send(view=error_view)
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

            container = create_status_container(
                title="✅ STREAK MODIFIED",
                fields=[
                    {"name": "Target", "value": target.mention},
                    {"name": "Streak Days", "value": f"{days} days"},
                    {"name": "Milestone", "value": milestone},
                    {"name": "Verification", "value": f"Saved: {member_data.get('daily_streak', 0)} days"}
                ],
                footer="Testing command - Administrators only"
            )

            from discord.ui import LayoutView
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)

        except Exception as e:
            error_container = create_error_message("Error setting streak", str(e))
            from discord.ui import LayoutView
            error_view = LayoutView()
            error_view.add_item(error_container)
            await ctx.send(view=error_view)
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
                for rank in COZY_RANKS:
                    if rank["name"].lower() == rank_name.lower():
                        target_rank = rank
                        break

                if not target_rank:
                    available_ranks = ", ".join([f'"{r["name"]}"' for r in COZY_RANKS])
                    container = create_error_message(
                        "Invalid rank name",
                        f"Available ranks:\n{available_ranks}"
                    )
                    from discord.ui import LayoutView
                    view = LayoutView()
                    view.add_item(container)
                    await ctx.send(view=view)
                    return
            else:
                # Promote to next rank
                current_index = 0
                for i, rank in enumerate(COZY_RANKS):
                    if rank["name"] == old_rank:
                        current_index = i
                        break

                if current_index >= len(COZY_RANKS) - 1:
                    container = create_error_message(
                        "Already at maximum rank",
                        f"{member.display_name} is already at maximum rank: {old_rank}"
                    )
                    from discord.ui import LayoutView
                    view = LayoutView()
                    view.add_item(container)
                    await ctx.send(view=view)
                    return

                target_rank = COZY_RANKS[current_index + 1]

            member_data['rank'] = target_rank['name']
            member_data['rank_icon'] = target_rank['icon']
            member_data['xp'] = target_rank['required_xp']

            # Update Discord role
            role_updated = await update_member_roles(member, target_rank["name"])

            # Save
            self.bot.member_data.schedule_save()
            await self.bot.member_data.save_data_async()

            container = create_success_message(
                "MEMBER PROMOTED",
                [
                    f"Target: {member.mention}",
                    f"Old Rank: {old_rank}",
                    f"New Rank: {target_rank['icon']} {target_rank['name']}",
                    f"XP Set: {target_rank['required_xp']:,}",
                    f"Discord Role: {'✅ Applied' if role_updated else '⚠️ Role not found'}"
                ],
                footer=f"Promoted by {ctx.author}"
            )

            from discord.ui import LayoutView
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)

        except Exception as e:
            error_container = create_error_message("Error promoting member", str(e))
            from discord.ui import LayoutView
            error_view = LayoutView()
            error_view.add_item(error_container)
            await ctx.send(view=error_view)
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
            container = create_error_message("Cannot demote bots")
            from discord.ui import LayoutView
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)
            return

        try:
            member_data = self.bot.member_data.get_member_data(member.id, ctx.guild.id)
            old_rank = member_data.get('rank', 'Rookie')
            current_xp = member_data.get('xp', 0)

            if rank_name:
                # Demote to specific rank
                target_rank = None
                for rank in COZY_RANKS:
                    if rank["name"].lower() == rank_name.lower():
                        target_rank = rank
                        break

                if not target_rank:
                    available_ranks = ", ".join([f'"{r["name"]}"' for r in COZY_RANKS])
                    container = create_error_message(
                        "Invalid rank name",
                        f"Available ranks:\n{available_ranks}"
                    )
                    from discord.ui import LayoutView
                    view = LayoutView()
                    view.add_item(container)
                    await ctx.send(view=view)
                    return
            else:
                # Demote to previous rank
                current_index = 0
                for i, rank in enumerate(COZY_RANKS):
                    if rank["name"] == old_rank:
                        current_index = i
                        break

                if current_index <= 0:
                    container = create_error_message(
                        "Already at lowest rank",
                        f"{member.display_name} is already at the lowest rank: {old_rank}"
                    )
                    from discord.ui import LayoutView
                    view = LayoutView()
                    view.add_item(container)
                    await ctx.send(view=view)
                    return

                target_rank = COZY_RANKS[current_index - 1]

            member_data['rank'] = target_rank['name']
            member_data['rank_icon'] = target_rank['icon']
            # XP remains unchanged for monthly reset system

            # Update Discord role
            role_updated = await update_member_roles(member, target_rank["name"])

            # Save
            self.bot.member_data.schedule_save()
            await self.bot.member_data.save_data_async()

            container = create_status_container(
                title="⬇️ MEMBER DEMOTED",
                fields=[
                    {"name": "Target", "value": member.mention},
                    {"name": "Old Rank", "value": old_rank},
                    {"name": "New Rank", "value": f"{target_rank['icon']} {target_rank['name']}"},
                    {"name": "XP (Unchanged)", "value": f"{current_xp:,}"},
                    {"name": "Discord Role", "value": "✅ Applied" if role_updated else "⚠️ Role not found"}
                ],
                footer=f"Demoted by {ctx.author} | XP unchanged for monthly reset system"
            )

            from discord.ui import LayoutView
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)

        except Exception as e:
            error_container = create_error_message("Error demoting member", str(e))
            from discord.ui import LayoutView
            error_view = LayoutView()
            error_view.add_item(error_container)
            await ctx.send(view=error_view)
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
            container = create_error_message("Cannot set XP for bots")
            from discord.ui import LayoutView
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)
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

            fields = [
                {"name": "Target", "value": member.mention},
                {"name": "Old XP", "value": f"{old_xp:,}"},
                {"name": "New XP", "value": f"{new_xp:,}"},
                {"name": "XP Change", "value": f"{new_xp - old_xp:+,}"}
            ]

            if rank_changed:
                fields.append({
                    "name": "RANK CHANGED",
                    "value": f"{old_rank} → {new_rank_icon} {new_rank_name}"
                })
                fields.append({
                    "name": "Discord Role",
                    "value": "✅ Updated" if role_updated else "⚠️ Role not found"
                })
            else:
                fields.append({
                    "name": "Current Rank",
                    "value": f"{new_rank_icon} {new_rank_name}"
                })

            container = create_status_container(
                title="✅ XP SET",
                fields=fields,
                footer=f"Modified by {ctx.author}"
            )

            from discord.ui import LayoutView
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)

        except Exception as e:
            error_container = create_error_message("Error setting XP", str(e))
            from discord.ui import LayoutView
            error_view = LayoutView()
            error_view.add_item(error_container)
            await ctx.send(view=error_view)
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

            fields = [
                {"name": "Target", "value": member.mention},
                {"name": "XP Change", "value": f"{amount:+,}"},
                {"name": "Old XP", "value": f"{old_xp:,}"},
                {"name": "New XP", "value": f"{new_xp:,}"}
            ]

            if rank_changed:
                fields.append({
                    "name": "RANK CHANGED",
                    "value": f"{old_rank} → {new_rank_icon} {new_rank_name}"
                })
            else:
                fields.append({
                    "name": "Current Rank",
                    "value": f"{member_data.get('rank_icon', '')} {member_data.get('rank', 'Rookie')}"
                })

            container = create_status_container(
                title=f"{'✅' if amount > 0 else '⚠️'} XP MODIFIED",
                fields=fields,
                footer=f"Modified by {ctx.author}"
            )

            from discord.ui import LayoutView
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)

        except Exception as e:
            error_container = create_error_message("Error giving XP", str(e))
            from discord.ui import LayoutView
            error_view = LayoutView()
            error_view.add_item(error_container)
            await ctx.send(view=error_view)
            logger.error(f"Error in givexp: {e}")

    @commands.command(name='adminhelp')
    @commands.has_permissions(administrator=True)
    async def admin_help(self, ctx):
        """Display all available admin commands (Admin only)"""
        container = create_status_container(
            title="🛠️ ADMIN COMMANDS",
            fields=[
                {
                    "name": "📊 RANK MANAGEMENT",
                    "value": """```
!promote @user ["Rank"]    - Promote to rank or next (sets XP)
!demote @user ["Rank"]     - Demote to rank or previous (XP unchanged)
!auto_promote              - Auto-promote all members by XP
!test_promotion [@user]    - Test promotion system
```"""
                },
                {
                    "name": "💰 XP MANAGEMENT",
                    "value": """```
!setxp @user 5000       - Set exact XP amount
!givexp @user 1000      - Add XP (use negative to remove)
```"""
                },
                {
                    "name": "🎭 ROLE MANAGEMENT",
                    "value": """```
!fix_all_roles          - Sync all Discord roles with ranks
!check_roles            - Check role sync status
```"""
                },
                {
                    "name": "🧪 TESTING",
                    "value": """```
!test_daily [@user]     - Test daily reward system
!test_supply            - Test supply card generation
!force_daily @user      - Force daily claim reset
!test_streak @user 5    - Set daily streak for testing
```"""
                },
                {
                    "name": "💾 DATABASE",
                    "value": """```
!neon_backup           - Manual backup to Neon DB
!neon_status           - Check DB connection
!neon_resync           - Full resync with database
```"""
                },
                {
                    "name": "📈 SERVER STATS",
                    "value": """```
!serveravg             - Check server average messages
```"""
                },
                {
                    "name": "📝 NOTES",
                    "value": "• **Monthly Reset System**: Use `!demote` instead of changing XP\n"
                          "• **XP Changes**: `!setxp` and `!givexp` auto-update ranks\n"
                          "• **Rank Names**: Rookie, Private, Specialist, Corporal, Sergeant, Lieutenant, Captain, Major, Colonel, FOXHOUND"
                }
            ],
            footer="All commands require Administrator permissions"
        )

        from discord.ui import LayoutView
        view = LayoutView()
        view.add_item(container)
        await ctx.send(view=view)

    # Modal-based admin commands
    @app_commands.command(name="add_xp", description="add xp to a member (admin only)")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(member="the member to add xp to")
    async def add_xp_slash(self, interaction: discord.Interaction, member: discord.Member):
        """Add XP to a member using a modal form."""
        if member.bot:
            await interaction.response.send_message("cannot add xp to bots", ephemeral=True)
            return

        modal = AddXPModal(self.bot, member)
        await interaction.response.send_modal(modal)

    @app_commands.command(name="remove_xp", description="remove xp from a member (admin only)")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(member="the member to remove xp from")
    async def remove_xp_slash(self, interaction: discord.Interaction, member: discord.Member):
        """Remove XP from a member using a modal form."""
        if member.bot:
            await interaction.response.send_message("cannot remove xp from bots", ephemeral=True)
            return

        modal = RemoveXPModal(self.bot, member)
        await interaction.response.send_modal(modal)

    @app_commands.command(name="set_rank", description="set a member's rank directly (admin only)")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(member="the member to set rank for")
    async def set_rank_slash(self, interaction: discord.Interaction, member: discord.Member):
        """Set a member's rank using a modal form."""
        if member.bot:
            await interaction.response.send_message("cannot set rank for bots", ephemeral=True)
            return

        modal = SetRankModal(self.bot, member)
        await interaction.response.send_modal(modal)

    @commands.command(name='monthly_reset', aliases=['reset_monthly'])
    @commands.has_permissions(administrator=True)
    async def monthly_reset(self, ctx, force: bool = False):
        """
        Perform a monthly XP reset with data archiving.

        Args:
            force: If True, performs reset even if not the 1st of the month

        Usage:
            !monthly_reset - Check if reset is needed
            !monthly_reset true - Force reset regardless of date
        """
        from datetime import date
        from discord.ui import LayoutView

        current_date = date.today()

        # Check if we should perform the reset
        should_reset = force or current_date.day == 1

        if not force and current_date.day != 1:
            container = create_info_card(
                title="📅 Monthly Reset Status",
                description=f"**Current Date:** {current_date.strftime('%B %d, %Y')}\n\n"
                          f"Monthly resets occur automatically on the 1st of each month.\n\n"
                          f"**Next Reset:** {current_date.replace(day=1).replace(month=current_date.month % 12 + 1).strftime('%B 1, %Y')}\n\n"
                          f"To force a reset right now, use:\n`!monthly_reset true`",
                color_code="blue"
            )
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)
            return

        # Check if already reset this month
        if self.bot.last_monthly_reset and \
           self.bot.last_monthly_reset.month == current_date.month and \
           self.bot.last_monthly_reset.year == current_date.year and \
           not force:
            container = create_error_message(
                "Already Reset",
                f"Monthly reset was already performed on {self.bot.last_monthly_reset.strftime('%B %d, %Y')}.\n\n"
                f"Use `!monthly_reset true` to force another reset."
            )
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)
            return

        # Confirm before proceeding
        container = create_info_card(
            title="⚠️ Confirm Monthly Reset",
            description=f"**This will:**\n"
                      f"• Archive current member data to database\n"
                      f"• Reset all XP to 0\n"
                      f"• Reset all Word-Up points to 0\n"
                      f"• Preserve ranks and other stats\n\n"
                      f"**Force Reset:** {'Yes' if force else 'No'}\n\n"
                      f"React with ✅ to confirm or ❌ to cancel.",
            color_code="yellow"
        )
        view = LayoutView()
        view.add_item(container)
        message = await ctx.send(view=view)

        await message.add_reaction("✅")
        await message.add_reaction("❌")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == message.id

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)

            if str(reaction.emoji) == "❌":
                container = create_simple_message("❌ Monthly reset cancelled.")
                view = LayoutView()
                view.add_item(container)
                await message.edit(view=view)
                return

        except asyncio.TimeoutError:
            container = create_error_message("Timeout", "Confirmation timed out. Reset cancelled.")
            view = LayoutView()
            view.add_item(container)
            await message.edit(view=view)
            return

        # Perform the reset
        status_container = create_info_card(
            title="🌙 Monthly Reset In Progress...",
            description="Archiving data and resetting XP...",
            color_code="blue"
        )
        view = LayoutView()
        view.add_item(status_container)
        await message.edit(view=view)

        # Archive previous month's data
        previous_month = current_date.month - 1 if current_date.month > 1 else 12
        previous_year = current_date.year if current_date.month > 1 else current_date.year - 1

        archived_count = 0
        if self.bot.neon_db and self.bot.neon_db.pool:
            logger.info(f"📦 Archiving data from {previous_month}/{previous_year}...")
            success, archived_count = await self.bot.neon_db.archive_monthly_data(
                self.bot.member_data.data,
                previous_month,
                previous_year
            )
            if not success:
                logger.error("❌ Failed to archive monthly data!")

        # Reset XP while preserving ranks
        reset_count = 0
        total_guilds = len(self.bot.member_data.data)
        preserved_ranks = 0

        for guild_id, guild_data in self.bot.member_data.data.items():
            # Get the guild object to check member roles
            guild = self.bot.get_guild(int(guild_id))

            for member_id, member_data_entry in guild_data.items():
                # Preserve the current rank before resetting XP
                current_rank = member_data_entry.get('rank', 'New Lifeform')
                current_rank_icon = member_data_entry.get('rank_icon', '🥚')

                # Check if member has a rank role in Discord (verify rank is legitimate)
                if guild:
                    member = guild.get_member(int(member_id))
                    if member:
                        # Find the highest rank role the member has
                        highest_rank = None
                        highest_rank_xp = -1

                        for rank_data in COZY_RANKS:
                            role_id = rank_data.get('role_id')
                            if role_id:
                                role = guild.get_role(role_id)
                                if role and role in member.roles:
                                    if rank_data['required_xp'] > highest_rank_xp:
                                        highest_rank = rank_data['name']
                                        highest_rank_xp = rank_data['required_xp']
                                        current_rank_icon = rank_data['icon']

                        # If member has a rank role, use that as their preserved rank
                        if highest_rank:
                            current_rank = highest_rank
                            preserved_ranks += 1

                # Reset XP but keep the rank
                if member_data_entry.get('xp', 0) > 0:
                    member_data_entry['xp'] = 0
                    reset_count += 1

                # Preserve rank and icon (don't reset to "New Lifeform")
                member_data_entry['rank'] = current_rank
                member_data_entry['rank_icon'] = current_rank_icon

                # Reset Word-Up points
                if member_data_entry.get('word_up_points', 0) > 0:
                    member_data_entry['word_up_points'] = 0

        # Mark reset as completed
        self.bot.last_monthly_reset = current_date
        self.bot.save_bot_metadata()

        # Force save the changes
        await self.bot.member_data.save_data_async(force=True)

        logger.info(f"✅ Preserved ranks for {preserved_ranks} members based on Discord roles")

        logger.info(f"✅ Manual monthly XP reset completed by {ctx.author}: {reset_count} members")

        # Send success message
        container = create_success_message(
            "✅ Monthly Reset Complete!",
            f"**Reset Summary:**\n"
            f"• Archived: {archived_count} members to database\n"
            f"• Reset XP: {reset_count} members\n"
            f"• Ranks Preserved: {preserved_ranks} members\n"
            f"• Guilds: {total_guilds}\n"
            f"• Month: {previous_month}/{previous_year}\n\n"
            f"**Reset Date:** {current_date.strftime('%B %d, %Y')}\n"
            f"**Forced:** {'Yes' if force else 'No'}"
        )
        view = LayoutView()
        view.add_item(container)
        await message.edit(view=view)

        # Announce in current channel
        announcement = create_info_card(
            title="🌙 MONTHLY XP RESET",
            description=f"**{current_date.strftime('%B %Y')}** XP reset completed!\n\n"
                      f"• All XP has been reset to 0\n"
                      f"• Word-Up points reset to 0\n"
                      f"• Ranks and multipliers are preserved\n"
                      f"• Previous month's data archived\n"
                      f"• New monthly competition begins now!",
            footer="Higher ranks = better multipliers for the new month!",
            color_code="blue"
        )
        view = LayoutView()
        view.add_item(announcement)
        await ctx.send(view=view)

    @commands.command(name='purge_members', aliases=['purge'])
    @commands.has_permissions(administrator=True)
    async def purge_non_members(self, ctx):
        """Remove members who left the server from database."""
        from discord.ui import LayoutView

        # Send initial status
        status = create_info_card(
            title="🧹 Member Purge",
            description="Checking for members who left the server...",
            color_code="blue"
        )
        view = LayoutView()
        view.add_item(status)
        message = await ctx.send(view=view)

        try:
            # Run purge
            purged_count = await self.bot.member_data.purge_non_members(ctx.guild)

            # Send result
            if purged_count > 0:
                result = create_success_message(
                    f"🧹 Database Purged",
                    f"Successfully removed **{purged_count}** members who left the server.\n\n"
                    f"**Database Updated:** ✅\n"
                    f"**Backup Synced:** ✅"
                )
            else:
                result = create_success_message(
                    f"✅ Database Clean",
                    f"No members to purge. All database entries are current server members."
                )

            view = LayoutView()
            view.add_item(result)
            await message.edit(view=view)

        except Exception as e:
            logger.error(f"Error during member purge: {e}")
            error = create_error_message(
                "Purge Failed",
                f"An error occurred: {str(e)}"
            )
            view = LayoutView()
            view.add_item(error)
            await message.edit(view=view)


async def setup(bot):
    """Load the Admin cog."""
    await bot.add_cog(Admin(bot))
