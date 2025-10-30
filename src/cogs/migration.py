"""
Admin migration command to migrate all users from old rank system to new cozy ranks.
"""
import discord
from discord.ext import commands
from typing import Dict, Any
from config.settings import logger
from utils.rank_migration import migrate_member_rank, is_old_rank


class Migration(commands.Cog):
    """Migration utilities for transitioning rank systems."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='migrate_ranks', hidden=True)
    @commands.is_owner()
    async def migrate_ranks(self, ctx):
        """
        Migrate all users from old MGS rank system to new Cozy rank system.
        This command can only be run by the bot owner.
        """
        await ctx.send("🔄 Starting rank migration process...")

        guild_id = ctx.guild.id
        guild_key = str(guild_id)

        if guild_key not in self.bot.member_data.data:
            await ctx.send("❌ No data found for this guild.")
            return

        guild_data = self.bot.member_data.data[guild_key]

        migrated_count = 0
        skipped_count = 0
        error_count = 0

        # Progress message
        progress_msg = await ctx.send(f"🔄 Processing {len(guild_data)} members...")

        for member_id_str, member_data in guild_data.items():
            try:
                current_rank = member_data.get("rank", "")

                # Skip if already using new system
                if not is_old_rank(current_rank):
                    skipped_count += 1
                    continue

                # Perform migration
                was_migrated, new_rank, new_icon, new_xp = migrate_member_rank(member_data)

                if was_migrated:
                    # Update the data
                    member_data["rank"] = new_rank
                    member_data["rank_icon"] = new_icon
                    member_data["xp"] = new_xp

                    migrated_count += 1
                    logger.info(f"Migrated {member_id_str}: {current_rank} -> {new_rank} (XP: {new_xp})")
                else:
                    skipped_count += 1

            except Exception as e:
                error_count += 1
                logger.error(f"Error migrating member {member_id_str}: {e}")

        # Save all changes
        await self.bot.member_data.save_data_async(force=True)

        # Update progress message with results
        result_msg = f"""✅ **Migration Complete!**

**Results:**
• Migrated: {migrated_count} members
• Skipped (already new system): {skipped_count} members
• Errors: {error_count} members

All data has been saved to database."""

        await progress_msg.edit(content=result_msg)

    @commands.command(name='check_migration', hidden=True)
    @commands.is_owner()
    async def check_migration(self, ctx):
        """
        Check migration status - shows how many users still need migration.
        """
        guild_id = ctx.guild.id
        guild_key = str(guild_id)

        if guild_key not in self.bot.member_data.data:
            await ctx.send("❌ No data found for this guild.")
            return

        guild_data = self.bot.member_data.data[guild_key]

        old_rank_count = 0
        new_rank_count = 0
        invalid_rank_count = 0

        old_rank_users = []

        for member_id_str, member_data in guild_data.items():
            current_rank = member_data.get("rank", "")

            if is_old_rank(current_rank):
                old_rank_count += 1
                old_rank_users.append(f"{member_id_str}: {current_rank} (XP: {member_data.get('xp', 0)})")
            else:
                new_rank_count += 1

        # Build response
        response = f"""📊 **Migration Status**

**Total Members:** {len(guild_data)}
• Using new Cozy ranks: {new_rank_count}
• Using old MGS ranks: {old_rank_count}
• Invalid/Unknown ranks: {invalid_rank_count}
"""

        if old_rank_count > 0:
            response += f"\n⚠️ **Members needing migration ({min(10, old_rank_count)} shown):**\n"
            for user_info in old_rank_users[:10]:
                response += f"• {user_info}\n"

            if old_rank_count > 10:
                response += f"\n...and {old_rank_count - 10} more"

            response += f"\n\n💡 Run `{ctx.prefix}migrate_ranks` to migrate all users."
        else:
            response += "\n✅ All users are using the new rank system!"

        await ctx.send(response)

    @commands.command(name='fix_rank', hidden=True)
    @commands.has_permissions(administrator=True)
    async def fix_rank(self, ctx, member: discord.Member = None):
        """
        Manually fix/recalculate rank for a specific member.
        Usage: !fix_rank @member or !fix_rank (for yourself)
        """
        if member is None:
            member = ctx.author

        member_id = member.id
        guild_id = ctx.guild.id

        member_data = self.bot.member_data.get_member_data(member_id, guild_id)
        old_rank = member_data.get("rank", "")
        old_xp = member_data.get("xp", 0)

        # Check if migration needed
        if is_old_rank(old_rank):
            was_migrated, new_rank, new_icon, new_xp = migrate_member_rank(member_data)

            if was_migrated:
                member_data["rank"] = new_rank
                member_data["rank_icon"] = new_icon
                member_data["xp"] = new_xp

                await self.bot.member_data.save_data_async(force=True)

                await ctx.send(f"""✅ **Rank Fixed for {member.mention}**

**Before:**
• Rank: {old_rank}
• XP: {old_xp}

**After:**
• Rank: {new_rank} {new_icon}
• XP: {new_xp}

Migration complete!""")
            else:
                await ctx.send(f"ℹ️ {member.mention} already uses the new rank system.")
        else:
            # Just recalculate rank from XP
            from utils.rank_system import calculate_rank_from_xp

            correct_rank, correct_icon = calculate_rank_from_xp(old_xp)

            if correct_rank != old_rank:
                member_data["rank"] = correct_rank
                member_data["rank_icon"] = correct_icon

                await self.bot.member_data.save_data_async(force=True)

                await ctx.send(f"""✅ **Rank Recalculated for {member.mention}**

• Old Rank: {old_rank}
• New Rank: {correct_rank} {correct_icon}
• XP: {old_xp}

Rank has been corrected based on XP!""")
            else:
                await ctx.send(f"✅ {member.mention}'s rank is already correct: {old_rank} {member_data.get('rank_icon', '')} (XP: {old_xp})")


async def setup(bot):
    """Load the Migration cog."""
    await bot.add_cog(Migration(bot))
