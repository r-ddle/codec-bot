"""
Admin modal forms for managing member XP and ranks.
"""
import discord
from discord import ui
from typing import Optional


class AddXPModal(ui.Modal, title="add xp to member"):
    """Modal for adding XP to a member."""

    xp_amount = ui.TextInput(
        label="xp amount",
        placeholder="enter xp amount to add (e.g., 500)",
        required=True,
        min_length=1,
        max_length=10
    )

    reason = ui.TextInput(
        label="reason (optional)",
        placeholder="reason for adding xp",
        required=False,
        max_length=200,
        style=discord.TextStyle.paragraph
    )

    def __init__(self, bot, target_member: discord.Member):
        super().__init__()
        self.bot = bot
        self.target_member = target_member

    async def on_submit(self, interaction: discord.Interaction):
        """Handle form submission."""
        try:
            xp_value = int(self.xp_amount.value)

            if xp_value <= 0:
                await interaction.response.send_message(
                    "xp amount must be positive",
                    ephemeral=True
                )
                return

            # Get member data
            member_data = self.bot.member_data.get_member_data(
                self.target_member.id,
                interaction.guild.id
            )

            old_xp = member_data['xp']
            new_xp = old_xp + xp_value

            # Update XP
            member_data['xp'] = new_xp

            # Check for rank up
            from utils.rank_system import calculate_rank_from_xp
            from utils.role_manager import update_member_roles

            new_rank_data = calculate_rank_from_xp(new_xp)
            old_rank = member_data['rank']

            if new_rank_data['name'] != old_rank:
                member_data['rank'] = new_rank_data['name']
                member_data['rank_icon'] = new_rank_data['icon']
                await update_member_roles(self.target_member, new_rank_data['name'])
                rank_changed = True
            else:
                rank_changed = False

            # Save data
            self.bot.member_data.schedule_save()

            # Build response
            reason_text = f"\nreason: {self.reason.value}" if self.reason.value else ""
            rank_text = f"\nrank updated: {old_rank} → {new_rank_data['name']}" if rank_changed else ""

            response = (
                f"xp added successfully\n"
                f"member: {self.target_member.mention}\n"
                f"xp added: +{xp_value:,}\n"
                f"total xp: {old_xp:,} → {new_xp:,}"
                f"{rank_text}"
                f"{reason_text}"
            )

            await interaction.response.send_message(response, ephemeral=True)

        except ValueError:
            await interaction.response.send_message(
                "invalid xp amount. please enter a number.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"error adding xp: {str(e)}",
                ephemeral=True
            )


class RemoveXPModal(ui.Modal, title="remove xp from member"):
    """Modal for removing XP from a member."""

    xp_amount = ui.TextInput(
        label="xp amount",
        placeholder="enter xp amount to remove (e.g., 500)",
        required=True,
        min_length=1,
        max_length=10
    )

    reason = ui.TextInput(
        label="reason (optional)",
        placeholder="reason for removing xp",
        required=False,
        max_length=200,
        style=discord.TextStyle.paragraph
    )

    def __init__(self, bot, target_member: discord.Member):
        super().__init__()
        self.bot = bot
        self.target_member = target_member

    async def on_submit(self, interaction: discord.Interaction):
        """Handle form submission."""
        try:
            xp_value = int(self.xp_amount.value)

            if xp_value <= 0:
                await interaction.response.send_message(
                    "xp amount must be positive",
                    ephemeral=True
                )
                return

            # Get member data
            member_data = self.bot.member_data.get_member_data(
                self.target_member.id,
                interaction.guild.id
            )

            old_xp = member_data['xp']
            new_xp = max(0, old_xp - xp_value)  # Don't go below 0

            # Update XP
            member_data['xp'] = new_xp

            # Check for rank down
            from utils.rank_system import calculate_rank_from_xp
            from utils.role_manager import update_member_roles

            new_rank_data = calculate_rank_from_xp(new_xp)
            old_rank = member_data['rank']

            if new_rank_data['name'] != old_rank:
                member_data['rank'] = new_rank_data['name']
                member_data['rank_icon'] = new_rank_data['icon']
                await update_member_roles(self.target_member, new_rank_data['name'])
                rank_changed = True
            else:
                rank_changed = False

            # Save data
            self.bot.member_data.schedule_save()

            # Build response
            reason_text = f"\nreason: {self.reason.value}" if self.reason.value else ""
            rank_text = f"\nrank updated: {old_rank} → {new_rank_data['name']}" if rank_changed else ""

            response = (
                f"xp removed successfully\n"
                f"member: {self.target_member.mention}\n"
                f"xp removed: -{xp_value:,}\n"
                f"total xp: {old_xp:,} → {new_xp:,}"
                f"{rank_text}"
                f"{reason_text}"
            )

            await interaction.response.send_message(response, ephemeral=True)

        except ValueError:
            await interaction.response.send_message(
                "invalid xp amount. please enter a number.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"error removing xp: {str(e)}",
                ephemeral=True
            )


class SetRankModal(ui.Modal, title="set member rank"):
    """Modal for setting a member's rank directly."""

    rank_name = ui.TextInput(
        label="rank name",
        placeholder="enter rank name (e.g., sergeant, lieutenant)",
        required=True,
        max_length=50
    )

    reason = ui.TextInput(
        label="reason (optional)",
        placeholder="reason for rank change",
        required=False,
        max_length=200,
        style=discord.TextStyle.paragraph
    )

    def __init__(self, bot, target_member: discord.Member):
        super().__init__()
        self.bot = bot
        self.target_member = target_member

    async def on_submit(self, interaction: discord.Interaction):
        """Handle form submission."""
        try:
            from utils.rank_system import get_rank_data_by_name
            from utils.role_manager import update_member_roles

            # Validate rank name
            rank_data = get_rank_data_by_name(self.rank_name.value)

            if not rank_data:
                # List available ranks
                from config.constants import MGS_RANKS
                available_ranks = ", ".join([r["name"].lower() for r in MGS_RANKS])
                await interaction.response.send_message(
                    f"invalid rank name. available ranks:\n{available_ranks}",
                    ephemeral=True
                )
                return

            # Get member data
            member_data = self.bot.member_data.get_member_data(
                self.target_member.id,
                interaction.guild.id
            )

            old_rank = member_data['rank']
            old_xp = member_data['xp']

            # Update rank and XP
            member_data['rank'] = rank_data['name']
            member_data['rank_icon'] = rank_data['icon']
            member_data['xp'] = rank_data['required_xp']

            # Update Discord role
            await update_member_roles(self.target_member, rank_data['name'])

            # Save data
            self.bot.member_data.schedule_save()

            # Build response
            reason_text = f"\nreason: {self.reason.value}" if self.reason.value else ""

            response = (
                f"rank set successfully\n"
                f"member: {self.target_member.mention}\n"
                f"rank: {old_rank} → {rank_data['name']}\n"
                f"xp: {old_xp:,} → {rank_data['required_xp']:,}"
                f"{reason_text}"
            )

            await interaction.response.send_message(response, ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(
                f"error setting rank: {str(e)}",
                ephemeral=True
            )
