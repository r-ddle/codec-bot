"""
Shop commands cog - Phase 4 implementation with buttons and image cards
"""
import discord
from discord import app_commands
from discord.ext import commands
from io import BytesIO
from utils.shop_ui import ShopView, InventoryView, ConfirmPurchaseView
from utils.image_gen import generate_rank_card
from config.settings import logger, FEATURE_FLAGS
from config.constants import MGS_RANKS
from utils.formatters import format_number


class ShopCommands(commands.Cog):
    """Shop and inventory commands with UI"""

    def __init__(self, bot):
        self.bot = bot

    # ===== SHOP COMMANDS =====

    @app_commands.command(name="shop", description="Browse the GMP shop with interactive buttons")
    async def shop_slash(self, interaction: discord.Interaction):
        """Open the interactive shop"""
        if not FEATURE_FLAGS.get('ENABLE_SHOP', False):
            await interaction.response.send_message(
                "❌ The shop is currently disabled. Contact an administrator.",
                ephemeral=True
            )
            return

        try:
            # Create shop view
            shop_view = ShopView(self.bot, interaction.user.id, interaction.guild.id)

            # Create initial embed
            member_data = self.bot.member_data.get_member_data(interaction.user.id, interaction.guild.id)
            balance = member_data.get('gmp', 0)

            embed = discord.Embed(
                title="🏪 FOXHOUND GMP SHOP",
                description="Use the buttons below to browse categories and purchase items!",
                color=0x599cff
            )
            embed.add_field(
                name="💰 Your Balance",
                value=f"```{balance:,} GMP```",
                inline=False
            )
            embed.add_field(
                name="📖 How to Use",
                value="1️⃣ Click category buttons to browse\n2️⃣ Use `/buy <item_id>` to purchase\n3️⃣ Check `/inventory` to use items",
                inline=False
            )
            embed.set_footer(text="Shop items are configurable in shop_config.py")

            await interaction.response.send_message(embed=embed, view=shop_view)

            # Auto-show first category
            await shop_view.update_shop_display(interaction)

        except Exception as e:
            logger.error(f"Error opening shop: {e}")
            await interaction.response.send_message(
                f"❌ Error opening shop: {e}",
                ephemeral=True
            )

    @commands.command(name='shop')
    async def shop_text(self, ctx):
        """Open the interactive shop (text command)"""
        # Rate limiting
        from utils.rate_limiter import rate_limiter
        can_use, remaining = rate_limiter.check_rate_limit(ctx.author.id, 'shop')
        if not can_use:
            await ctx.send(f"⏳ Please wait {remaining:.0f}s before opening shop again.", delete_after=5)
            return

        if not FEATURE_FLAGS.get('ENABLE_SHOP', False):
            await ctx.send("❌ The shop is currently disabled. Contact an administrator.")
            return

        try:
            # Create shop view
            shop_view = ShopView(self.bot, ctx.author.id, ctx.guild.id)

            # Create initial embed
            member_data = self.bot.member_data.get_member_data(ctx.author.id, ctx.guild.id)
            balance = member_data.get('gmp', 0)

            embed = discord.Embed(
                title="🏪 FOXHOUND GMP SHOP",
                description="Use the buttons below to browse categories and purchase items!",
                color=0x599cff
            )
            embed.add_field(
                name="💰 Your Balance",
                value=f"```{balance:,} GMP```",
                inline=False
            )
            embed.add_field(
                name="📖 How to Use",
                value="1️⃣ Click category buttons to browse\n2️⃣ Use `!buy <item_id>` to purchase\n3️⃣ Check `!inventory` to use items",
                inline=False
            )

            message = await ctx.send(embed=embed, view=shop_view)

        except Exception as e:
            logger.error(f"Error opening shop: {e}")
            await ctx.send(f"❌ Error opening shop: {e}")

    # ===== BUY COMMAND =====

    @app_commands.command(name="buy", description="Purchase an item from the shop")
    @app_commands.describe(item_id="The ID of the item to purchase")
    async def buy_slash(self, interaction: discord.Interaction, item_id: int):
        """Purchase an item"""
        if not FEATURE_FLAGS.get('ENABLE_SHOP', False):
            await interaction.response.send_message(
                "❌ The shop is currently disabled.",
                ephemeral=True
            )
            return

        try:
            # Get item details
            async with self.bot.neon_db.pool.acquire() as conn:
                item = await conn.fetchrow(
                    'SELECT * FROM shop_items WHERE item_id = $1 AND is_active = TRUE',
                    item_id
                )

            if not item:
                await interaction.response.send_message(
                    "❌ Item not found or unavailable!",
                    ephemeral=True
                )
                return

            item_dict = dict(item)

            # Check balance
            member_data = self.bot.member_data.get_member_data(interaction.user.id, interaction.guild.id)
            balance = member_data.get('gmp', 0)

            if balance < item_dict['price']:
                await interaction.response.send_message(
                    f"❌ Not enough GMP! Need **{item_dict['price']:,}**, have **{balance:,}**",
                    ephemeral=True
                )
                return

            # Create confirmation view
            confirm_view = ConfirmPurchaseView(self.bot, interaction.user.id, interaction.guild.id, item_dict)

            embed = discord.Embed(
                title="🛒 CONFIRM PURCHASE",
                description=f"Are you sure you want to buy this item?",
                color=0xFFD700
            )
            embed.add_field(name="Item", value=item_dict['name'], inline=True)
            embed.add_field(name="Price", value=f"{item_dict['price']:,} GMP", inline=True)
            embed.add_field(name="Your Balance", value=f"{balance:,} GMP", inline=True)
            embed.add_field(name="After Purchase", value=f"{balance - item_dict['price']:,} GMP", inline=True)
            embed.add_field(name="Description", value=item_dict['description'], inline=False)

            await interaction.response.send_message(embed=embed, view=confirm_view, ephemeral=True)

        except Exception as e:
            logger.error(f"Error in buy command: {e}")
            await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

    @commands.command(name='buy')
    async def buy_text(self, ctx, item_id: int):
        """Purchase an item (text command)"""
        # Rate limiting
        from utils.rate_limiter import rate_limiter
        can_use, remaining = rate_limiter.check_rate_limit(ctx.author.id, 'buy')
        if not can_use:
            await ctx.send(f"⏳ Please wait {remaining:.0f}s before making another purchase.", delete_after=5)
            return

        if not FEATURE_FLAGS.get('ENABLE_SHOP', False):
            await ctx.send("❌ The shop is currently disabled.")
            return

        try:
            # Get item details
            async with self.bot.neon_db.pool.acquire() as conn:
                item = await conn.fetchrow(
                    'SELECT * FROM shop_items WHERE item_id = $1 AND is_active = TRUE',
                    item_id
                )

            if not item:
                await ctx.send("❌ Item not found or unavailable!")
                return

            item_dict = dict(item)

            # Check balance
            member_data = self.bot.member_data.get_member_data(ctx.author.id, ctx.guild.id)
            balance = member_data.get('gmp', 0)

            if balance < item_dict['price']:
                await ctx.send(f"❌ Not enough GMP! Need **{item_dict['price']:,}**, have **{balance:,}**")
                return

            # Create confirmation view
            confirm_view = ConfirmPurchaseView(self.bot, ctx.author.id, ctx.guild.id, item_dict)

            embed = discord.Embed(
                title="🛒 CONFIRM PURCHASE",
                description=f"Are you sure you want to buy this item?",
                color=0xFFD700
            )
            embed.add_field(name="Item", value=item_dict['name'], inline=True)
            embed.add_field(name="Price", value=f"{item_dict['price']:,} GMP", inline=True)
            embed.add_field(name="Your Balance", value=f"{balance:,} GMP", inline=True)
            embed.add_field(name="After Purchase", value=f"{balance - item_dict['price']:,} GMP", inline=True)
            embed.add_field(name="Description", value=item_dict['description'], inline=False)

            await ctx.send(embed=embed, view=confirm_view)

        except Exception as e:
            logger.error(f"Error in buy command: {e}")
            await ctx.send(f"❌ Error: {e}")

    # ===== INVENTORY COMMANDS =====

    @app_commands.command(name="inventory", description="View your purchased items")
    async def inventory_slash(self, interaction: discord.Interaction):
        """View inventory"""
        if not FEATURE_FLAGS.get('ENABLE_SHOP', False):
            await interaction.response.send_message(
                "❌ The shop is currently disabled.",
                ephemeral=True
            )
            return

        try:
            inventory_view = InventoryView(self.bot, interaction.user.id, interaction.guild.id)
            embed = await inventory_view.create_inventory_embed()
            await interaction.response.send_message(embed=embed, view=inventory_view)

        except Exception as e:
            logger.error(f"Error showing inventory: {e}")
            await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

    @commands.command(name='inventory', aliases=['inv'])
    async def inventory_text(self, ctx):
        """View inventory (text command)"""
        if not FEATURE_FLAGS.get('ENABLE_SHOP', False):
            await ctx.send("❌ The shop is currently disabled.")
            return

        try:
            inventory_view = InventoryView(self.bot, ctx.author.id, ctx.guild.id)
            embed = await inventory_view.create_inventory_embed()
            await ctx.send(embed=embed, view=inventory_view)

        except Exception as e:
            logger.error(f"Error showing inventory: {e}")
            await ctx.send(f"❌ Error: {e}")

    # ===== USE COMMAND =====

    @app_commands.command(name="use", description="Activate an item from your inventory")
    @app_commands.describe(inventory_id="The inventory ID of the item to use")
    async def use_slash(self, interaction: discord.Interaction, inventory_id: int):
        """Use an item from inventory"""
        if not FEATURE_FLAGS.get('ENABLE_XP_BOOSTERS', False):
            await interaction.response.send_message(
                "❌ Item usage is currently disabled.",
                ephemeral=True
            )
            return

        success, message = await self.bot.shop_system.activate_booster(
            interaction.user.id, interaction.guild.id, inventory_id
        )

        if success:
            embed = discord.Embed(
                title="✅ ITEM ACTIVATED",
                description=message,
                color=0x00FF00
            )
        else:
            embed = discord.Embed(
                title="❌ ACTIVATION FAILED",
                description=message,
                color=0xFF0000
            )

        await interaction.response.send_message(embed=embed)

    @commands.command(name='use')
    async def use_text(self, ctx, inventory_id: int):
        """Use an item from inventory (text command)"""
        if not FEATURE_FLAGS.get('ENABLE_XP_BOOSTERS', False):
            await ctx.send("❌ Item usage is currently disabled.")
            return

        success, message = await self.bot.shop_system.activate_booster(
            ctx.author.id, ctx.guild.id, inventory_id
        )

        if success:
            embed = discord.Embed(
                title="✅ ITEM ACTIVATED",
                description=message,
                color=0x00FF00
            )
        else:
            embed = discord.Embed(
                title="❌ ACTIVATION FAILED",
                description=message,
                color=0xFF0000
            )

        await ctx.send(embed=embed)

    # ===== RANK CARD WITH IMAGE =====

    @app_commands.command(name="rankcard", description="View your rank card with a beautiful image")
    @app_commands.describe(user="The member to check (optional)")
    async def rankcard_slash(self, interaction: discord.Interaction, user: discord.Member = None):
        """Generate rank card image"""
        await interaction.response.defer()  # This might take a moment

        try:
            target = user or interaction.user
            member_data = self.bot.member_data.get_member_data(target.id, interaction.guild.id)

            current_rank_name = member_data.get('rank', 'Rookie')
            current_rank_icon = member_data.get('rank_icon', '🎖️')
            current_xp = member_data.get('xp', 0)
            current_gmp = member_data.get('gmp', 0)
            messages = member_data.get('messages_sent', 0)
            voice_mins = member_data.get('voice_minutes', 0)

            # Find current rank index
            current_rank_index = 0
            for i, rank_info in enumerate(MGS_RANKS):
                if rank_info.get("name") == current_rank_name:
                    current_rank_index = i
                    break

            # Get next rank if not at max
            next_rank = MGS_RANKS[current_rank_index + 1] if current_rank_index < len(MGS_RANKS) - 1 else None

            # Calculate XP needed for progress bar
            xp_max = next_rank.get("required_xp", current_xp) if next_rank else current_xp

            # Get avatar URL
            avatar_url = target.avatar.url if target.avatar else None

            # Generate the NEW tactical rank card image with correct parameters
            img = generate_rank_card(
                username=target.display_name,
                rank_badge=current_rank_icon,
                rank_name=current_rank_name,  # Pass actual rank name, not level number
                xp=current_xp,
                xp_max=xp_max,
                gmp=current_gmp,
                avatar_url=avatar_url,
                message_count=messages,
                voice_time=voice_mins
            )

            # Convert PIL Image to BytesIO for Discord
            image_bytes = BytesIO()
            img.save(image_bytes, format='PNG')
            image_bytes.seek(0)

            # Send image
            file = discord.File(fp=image_bytes, filename="rank_card.png")
            await interaction.followup.send(file=file)

        except Exception as e:
            logger.error(f"Error generating rank card: {e}")
            await interaction.followup.send(f"❌ Error generating rank card: {e}")

    @commands.command(name='rankcard', aliases=['rc'])
    async def rankcard_text(self, ctx, member: discord.Member = None):
        """Generate rank card image (text command)"""
        target = member or ctx.author

        try:
            async with ctx.typing():
                member_data = self.bot.member_data.get_member_data(target.id, ctx.guild.id)

                current_rank_name = member_data.get('rank', 'Rookie')
                current_rank_icon = member_data.get('rank_icon', '🎖️')
                current_xp = member_data.get('xp', 0)
                current_gmp = member_data.get('gmp', 0)
                messages = member_data.get('messages_sent', 0)
                voice_mins = member_data.get('voice_minutes', 0)

                # Find current rank index
                current_rank_index = 0
                for i, rank_info in enumerate(MGS_RANKS):
                    if rank_info.get("name") == current_rank_name:
                        current_rank_index = i
                        break

                # Get next rank if not at max
                next_rank = MGS_RANKS[current_rank_index + 1] if current_rank_index < len(MGS_RANKS) - 1 else None

                # Calculate XP needed for progress bar
                xp_max = next_rank.get("required_xp", current_xp) if next_rank else current_xp

                # Get avatar URL
                avatar_url = target.avatar.url if target.avatar else None

                # Generate the NEW tactical rank card image with correct parameters
                img = generate_rank_card(
                    username=target.display_name,
                    rank_badge=current_rank_icon,
                    rank_name=current_rank_name,  # Pass actual rank name, not level number
                    xp=current_xp,
                    xp_max=xp_max,
                    gmp=current_gmp,
                    avatar_url=avatar_url,
                    message_count=messages,
                    voice_time=voice_mins
                )

                # Convert PIL Image to BytesIO for Discord
                image_bytes = BytesIO()
                img.save(image_bytes, format='PNG')
                image_bytes.seek(0)

                # Send image
                file = discord.File(fp=image_bytes, filename="rank_card.png")
                await ctx.send(file=file)

        except Exception as e:
            logger.error(f"Error generating rank card: {e}")
            await ctx.send(f"❌ Error generating rank card: {e}")


async def setup(bot):
    """Load the ShopCommands cog."""
    await bot.add_cog(ShopCommands(bot))
