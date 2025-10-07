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
            new_roles = [role.name for role in member.roles if role.name in [r["role_name"] for r in MGS_RANKS if r["role_name"]]]

            # Show results
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

            embed.add_field(
                name="TEST RESULTS",
                value="**Role Assignment:** Discord roles granted based on XP level\n**System Status:** XP-based ranking working correctly",
                inline=False
            )

            await ctx.send(embed=embed)

            # Save the test changes
            await self.bot.member_data.save_data_async(force=True)

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
                    current_xp = member_data.get('xp', 0)
                    stored_rank = member_data.get('rank', 'Rookie')

                    # Calculate correct rank based on XP
                    correct_rank, correct_icon = calculate_rank_from_xp(current_xp)

                    # Check if they need promotion
                    if stored_rank != correct_rank:
                        # Update database rank
                        member_data['rank'] = correct_rank
                        member_data['rank_icon'] = correct_icon

                        # Update Discord role
                        role_updated = await update_member_roles(member, correct_rank)

                        if role_updated:
                            promoted_count += 1
                            rank_data = get_rank_data_by_name(correct_rank)
                            role_name = rank_data.get("role_name", correct_rank)
                            promotions.append(f"{member.display_name}: {stored_rank}  {correct_rank} ({role_name})")
                            logger.info(f"AUTO-PROMOTED: {member.name} from {stored_rank} to {correct_rank} ({current_xp} XP)")

                    await asyncio.sleep(0.2)

                except Exception as e:
                    logger.error(f"Error processing {member.name}: {e}")

            # Save database changes
            await self.bot.member_data.save_data_async(force=True)

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

    # ===== PHASE 3: SHOP SYSTEM ADMIN COMMANDS =====

    @commands.command(name='shop_init')
    @commands.has_permissions(administrator=True)
    async def shop_init(self, ctx):
        """Initialize shop items in database (Admin only - Phase 3)."""
        if not hasattr(self.bot, 'shop_system'):
            await ctx.send("❌ Shop system not initialized")
            return

        await ctx.send("🔄 Initializing shop items...")
        success = await self.bot.shop_system.initialize_shop_items()

        if success:
            embed = discord.Embed(
                title="✅ SHOP INITIALIZED",
                description="Shop items have been added to the database",
                color=0x00ff00
            )
            embed.add_field(name="Items Added", value="4 XP Boosters", inline=False)
            embed.set_footer(text="Use !shop_list to view all items")
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Failed to initialize shop. Check logs for details.")

    @commands.command(name='shop_list')
    @commands.has_permissions(administrator=True)
    async def shop_list(self, ctx):
        """List all shop items (Admin only)."""
        if not hasattr(self.bot, 'shop_system'):
            await ctx.send("❌ Shop system not initialized")
            return

        items = await self.bot.shop_system.get_shop_items()

        if not items:
            await ctx.send("❌ No shop items found. Use !shop_init first.")
            return

        embed = discord.Embed(
            title="🏪 SHOP ITEMS",
            description="All available items in the shop",
            color=0x599cff
        )

        for item in items:
            duration = f" ({item['duration_hours']}h)" if item['duration_hours'] > 0 else " (One-time)"
            embed.add_field(
                name=f"{item['name']}{duration}",
                value=f"**ID:** {item['item_id']}\n**Price:** {item['price']} GMP\n{item['description']}",
                inline=False
            )

        await ctx.send(embed=embed)

    @commands.command(name='shop_test_buy')
    @commands.has_permissions(administrator=True)
    async def shop_test_buy(self, ctx, item_id: int):
        """Test purchasing an item (Admin only)."""
        if not hasattr(self.bot, 'shop_system'):
            await ctx.send("❌ Shop system not initialized")
            return

        await ctx.send(f"🔄 Testing purchase of item ID {item_id}...")

        success, message, item_data = await self.bot.shop_system.purchase_item(
            ctx.author.id, ctx.guild.id, item_id
        )

        if success:
            embed = discord.Embed(
                title="✅ PURCHASE SUCCESSFUL",
                description=message,
                color=0x00ff00
            )
            if item_data:
                embed.add_field(name="Item", value=item_data['name'], inline=True)
                embed.add_field(name="Price", value=f"{item_data['price']} GMP", inline=True)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ {message}")

    @commands.command(name='shop_test_inventory')
    @commands.has_permissions(administrator=True)
    async def shop_test_inventory(self, ctx, member: discord.Member = None):
        """View a member's inventory (Admin only)."""
        target = member or ctx.author

        if not hasattr(self.bot, 'shop_system'):
            await ctx.send("❌ Shop system not initialized")
            return

        items = await self.bot.shop_system.get_member_inventory(target.id, ctx.guild.id)

        if not items:
            await ctx.send(f"📦 {target.display_name} has no items in inventory")
            return

        embed = discord.Embed(
            title=f"📦 {target.display_name}'s Inventory",
            description=f"Total items: {len(items)}",
            color=0x599cff
        )

        for item in items[:10]:  # Show first 10
            status = "🟢 Active" if item['is_active'] else "⚪ Not Used"
            expires = f"\nExpires: {item['expires_at'].strftime('%Y-%m-%d %H:%M')}" if item['expires_at'] else ""
            embed.add_field(
                name=f"{item['name']} - {status}",
                value=f"**Inventory ID:** {item['inventory_id']}\nPurchased: {item['purchased_at'].strftime('%Y-%m-%d')}{expires}",
                inline=False
            )

        await ctx.send(embed=embed)

    @commands.command(name='shop_test_activate')
    @commands.has_permissions(administrator=True)
    async def shop_test_activate(self, ctx, inventory_id: int):
        """Test activating a booster (Admin only)."""
        if not hasattr(self.bot, 'shop_system'):
            await ctx.send("❌ Shop system not initialized")
            return

        await ctx.send(f"🔄 Testing activation of inventory item {inventory_id}...")

        success, message = await self.bot.shop_system.activate_booster(
            ctx.author.id, ctx.guild.id, inventory_id
        )

        if success:
            embed = discord.Embed(
                title="✅ BOOSTER ACTIVATED",
                description=message,
                color=0x00ff00
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ {message}")

    @commands.command(name='shop_give_gmp')
    @commands.has_permissions(administrator=True)
    async def shop_give_gmp(self, ctx, member: discord.Member, amount: int):
        """Give GMP to a member for testing (Admin only)."""
        if amount <= 0:
            await ctx.send("❌ Amount must be positive")
            return

        member_data = self.bot.member_data.get_member_data(member.id, ctx.guild.id)
        member_data['gmp'] += amount
        self.bot.member_data.schedule_save()

        embed = discord.Embed(
            title="💰 GMP GRANTED",
            description=f"Gave **{amount} GMP** to {member.mention}",
            color=0x00ff00
        )
        embed.add_field(name="New Balance", value=f"{member_data['gmp']} GMP", inline=False)
        await ctx.send(embed=embed)


async def setup(bot):
    """Load the Admin cog."""
    await bot.add_cog(Admin(bot))
