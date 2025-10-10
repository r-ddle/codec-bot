"""
Discord UI components for shop and inventory with buttons and views
"""
import discord
from discord import ui
from typing import List, Dict, Any
from config.shop_config import SHOP_UI_CONFIG, INVENTORY_UI_CONFIG, SHOP_CATEGORIES
from config.settings import logger


class ShopView(ui.View):
    """Interactive shop view with category buttons"""

    def __init__(self, bot, user_id: int, guild_id: int, timeout: int = 180):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.user_id = user_id
        self.guild_id = guild_id
        self.current_category = 'booster'
        self.current_page = 0

    @ui.button(label="⚡ Boosters", style=discord.ButtonStyle.primary, custom_id="cat_booster")
    async def booster_button(self, interaction: discord.Interaction, button: ui.Button):
        """Show booster items"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This isn't your shop!", ephemeral=True)
            return

        self.current_category = 'booster'
        self.current_page = 0
        await self.update_shop_display(interaction)

    @ui.button(label="💰 Currency", style=discord.ButtonStyle.success, custom_id="cat_currency")
    async def currency_button(self, interaction: discord.Interaction, button: ui.Button):
        """Show currency items"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This isn't your shop!", ephemeral=True)
            return

        self.current_category = 'currency'
        self.current_page = 0
        await self.update_shop_display(interaction)

    @ui.button(label="🔄 Refresh", style=discord.ButtonStyle.secondary, custom_id="refresh")
    async def refresh_button(self, interaction: discord.Interaction, button: ui.Button):
        """Refresh shop display"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This isn't your shop!", ephemeral=True)
            return

        await self.update_shop_display(interaction)

    @ui.button(label="📦 Inventory", style=discord.ButtonStyle.secondary, custom_id="inventory")
    async def inventory_button(self, interaction: discord.Interaction, button: ui.Button):
        """Show user's inventory"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This isn't your shop!", ephemeral=True)
            return

        # Show inventory
        inventory_view = InventoryView(self.bot, self.user_id, self.guild_id)
        embed = await inventory_view.create_inventory_embed()
        await interaction.response.edit_message(embed=embed, view=inventory_view)

    async def update_shop_display(self, interaction: discord.Interaction):
        """Update the shop display with current category"""
        try:
            # Get items for current category
            items = await self.bot.shop_system.get_shop_items(self.current_category)

            # Get user's balance
            member_data = self.bot.member_data.get_member_data(self.user_id, self.guild_id)
            balance = member_data.get('gmp', 0)

            # Create embed
            embed = discord.Embed(
                title=SHOP_UI_CONFIG['title'],
                description=SHOP_UI_CONFIG['description'],
                color=SHOP_UI_CONFIG['color']
            )

            # Add balance
            if SHOP_UI_CONFIG['show_balance']:
                embed.add_field(
                    name="💰 Your GMP Balance",
                    value=f"```{balance:,} GMP```",
                    inline=False
                )

            # Add category info
            cat_info = SHOP_CATEGORIES.get(self.current_category, {})
            embed.add_field(
                name=f"{cat_info.get('emoji', '')} Current Category: {cat_info.get('name', 'Unknown')}",
                value=cat_info.get('description', ''),
                inline=False
            )

            # Add items
            if items:
                for item in items[:SHOP_UI_CONFIG['items_per_page']]:
                    emoji = "⚡" if item['category'] == 'booster' else "💰"
                    duration = f" ({item['duration_hours']}h)" if item.get('duration_hours', 0) > 0 else ""

                    can_afford = "✅" if balance >= item['price'] else "❌"

                    embed.add_field(
                        name=f"{emoji} {item['name']}{duration}",
                        value=f"{item['description']}\n**Price:** {item['price']:,} GMP {can_afford}\n`/buy {item['item_id']}`",
                        inline=False
                    )
            else:
                embed.add_field(
                    name="❌ No items available",
                    value="Check back later!",
                    inline=False
                )

            embed.set_footer(text=SHOP_UI_CONFIG['footer'])

            await interaction.response.edit_message(embed=embed, view=self)

        except Exception as e:
            logger.error(f"Error updating shop display: {e}")
            await interaction.response.send_message(
                f"❌ Error loading shop: {e}",
                ephemeral=True
            )


class InventoryView(ui.View):
    """Interactive inventory view"""

    def __init__(self, bot, user_id: int, guild_id: int, timeout: int = 180):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.user_id = user_id
        self.guild_id = guild_id
        self.current_page = 0

    @ui.button(label="◀️ Previous", style=discord.ButtonStyle.secondary, custom_id="prev")
    async def prev_button(self, interaction: discord.Interaction, button: ui.Button):
        """Go to previous page"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This isn't your inventory!", ephemeral=True)
            return

        if self.current_page > 0:
            self.current_page -= 1
            embed = await self.create_inventory_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("❌ Already on first page!", ephemeral=True)

    @ui.button(label="▶️ Next", style=discord.ButtonStyle.secondary, custom_id="next")
    async def next_button(self, interaction: discord.Interaction, button: ui.Button):
        """Go to next page"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This isn't your inventory!", ephemeral=True)
            return

        # Check if there are more items
        items = await self.bot.shop_system.get_member_inventory(self.user_id, self.guild_id)
        max_pages = (len(items) - 1) // INVENTORY_UI_CONFIG['items_per_page'] + 1

        if self.current_page < max_pages - 1:
            self.current_page += 1
            embed = await self.create_inventory_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("❌ Already on last page!", ephemeral=True)

    @ui.button(label="🔄 Refresh", style=discord.ButtonStyle.primary, custom_id="refresh_inv")
    async def refresh_button(self, interaction: discord.Interaction, button: ui.Button):
        """Refresh inventory"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This isn't your inventory!", ephemeral=True)
            return

        embed = await self.create_inventory_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @ui.button(label="🏪 Back to Shop", style=discord.ButtonStyle.secondary, custom_id="back_shop")
    async def back_button(self, interaction: discord.Interaction, button: ui.Button):
        """Go back to shop"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This isn't your inventory!", ephemeral=True)
            return

        shop_view = ShopView(self.bot, self.user_id, self.guild_id)
        await shop_view.update_shop_display(interaction)

    async def create_inventory_embed(self) -> discord.Embed:
        """Create inventory embed"""
        try:
            items = await self.bot.shop_system.get_member_inventory(self.user_id, self.guild_id)

            # Filter out expired if configured
            if INVENTORY_UI_CONFIG['show_expired'] == False:
                from datetime import datetime
                items = [item for item in items if not item.get('expires_at') or item['expires_at'] > datetime.now()]

            embed = discord.Embed(
                title=INVENTORY_UI_CONFIG['title'],
                description=f"Total items: {len(items)}",
                color=INVENTORY_UI_CONFIG['color']
            )

            # Pagination
            start_idx = self.current_page * INVENTORY_UI_CONFIG['items_per_page']
            end_idx = start_idx + INVENTORY_UI_CONFIG['items_per_page']
            page_items = items[start_idx:end_idx]

            if page_items:
                for item in page_items:
                    status = "🟢 Active" if item.get('is_active') else "⚪ Ready to use"
                    expires = ""

                    if item.get('expires_at'):
                        from datetime import datetime
                        expires_at = item['expires_at']
                        if expires_at > datetime.now():
                            time_left = expires_at - datetime.now()
                            hours = int(time_left.total_seconds() // 3600)
                            expires = f"\n⏰ Expires in {hours}h"
                        else:
                            status = "❌ Expired"

                    embed.add_field(
                        name=f"{item['name']} - {status}",
                        value=f"{item['description']}{expires}\n`/use {item['inventory_id']}`",
                        inline=False
                    )
            else:
                embed.add_field(
                    name="📦 Inventory Empty",
                    value="Purchase items from the shop to get started!",
                    inline=False
                )

            # Page info
            max_pages = (len(items) - 1) // INVENTORY_UI_CONFIG['items_per_page'] + 1 if items else 1
            embed.set_footer(text=f"{INVENTORY_UI_CONFIG['footer']} | Page {self.current_page + 1}/{max_pages}")

            return embed

        except Exception as e:
            logger.error(f"Error creating inventory embed: {e}")
            return discord.Embed(
                title="❌ Error",
                description=f"Failed to load inventory: {e}",
                color=0xFF0000
            )


class ConfirmPurchaseView(ui.View):
    """Confirmation dialog for purchases"""

    def __init__(self, bot, user_id: int, guild_id: int, item_data: Dict[str, Any], timeout: int = 60):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.user_id = user_id
        self.guild_id = guild_id
        self.item_data = item_data
        self.confirmed = False

    @ui.button(label="✅ Confirm Purchase", style=discord.ButtonStyle.success, custom_id="confirm")
    async def confirm_button(self, interaction: discord.Interaction, button: ui.Button):
        """Confirm the purchase"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This isn't your purchase!", ephemeral=True)
            return

        # Process purchase
        success, message, item_data = await self.bot.shop_system.purchase_item(
            self.user_id, self.guild_id, self.item_data['item_id']
        )

        if success:
            embed = discord.Embed(
                title="✅ PURCHASE SUCCESSFUL",
                description=message,
                color=0x00FF00
            )
            embed.add_field(name="Item", value=self.item_data['name'], inline=True)
            embed.add_field(name="Price", value=f"{self.item_data['price']:,} GMP", inline=True)
            embed.set_footer(text="Check /inventory to use your item!")
        else:
            embed = discord.Embed(
                title="❌ PURCHASE FAILED",
                description=message,
                color=0xFF0000
            )

        # Disable buttons
        for child in self.children:
            child.disabled = True

        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()

    @ui.button(label="❌ Cancel", style=discord.ButtonStyle.danger, custom_id="cancel")
    async def cancel_button(self, interaction: discord.Interaction, button: ui.Button):
        """Cancel the purchase"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This isn't your purchase!", ephemeral=True)
            return

        embed = discord.Embed(
            title="❌ PURCHASE CANCELLED",
            description="Your purchase was cancelled.",
            color=0xFF9900
        )

        # Disable buttons
        for child in self.children:
            child.disabled = True

        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()
