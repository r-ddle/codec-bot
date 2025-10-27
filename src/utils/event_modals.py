"""
Server event modal forms for creating and managing events.
"""
import discord
from discord import ui
from datetime import datetime, timedelta
from typing import Optional


class CreateEventModal(ui.Modal, title="create server event"):
    """Modal for creating a new server event."""

    event_title = ui.TextInput(
        label="event title",
        placeholder="e.g., message marathon, xp race",
        required=True,
        max_length=100
    )

    goal_amount = ui.TextInput(
        label="goal amount",
        placeholder="target number (leave empty for dynamic goal)",
        required=False,
        max_length=10
    )

    duration_days = ui.TextInput(
        label="duration (days)",
        placeholder="event duration in days (default: 7)",
        required=False,
        max_length=2
    )

    description = ui.TextInput(
        label="description (optional)",
        placeholder="event description or special rules",
        required=False,
        max_length=200,
        style=discord.TextStyle.paragraph
    )

    def __init__(self, event_manager, event_channel_id: int, event_role_id: int, event_type: str = "message"):
        super().__init__()
        self.event_manager = event_manager
        self.event_channel_id = event_channel_id
        self.event_role_id = event_role_id
        self.event_type = event_type  # Store the selected event type

    async def on_submit(self, interaction: discord.Interaction):
        """Handle event creation form submission."""
        try:
            # Event type is already selected and stored
            event_type = self.event_type

            # Parse goal amount
            if self.goal_amount.value.strip():
                try:
                    goal = int(self.goal_amount.value.strip())
                    if goal <= 0:
                        await interaction.response.send_message(
                            "goal amount must be positive",
                            ephemeral=True
                        )
                        return
                except ValueError:
                    await interaction.response.send_message(
                        "invalid goal amount. please enter a number",
                        ephemeral=True
                    )
                    return
            else:
                # Calculate dynamic goal based on server activity
                goal = self.event_manager.calculate_dynamic_event_goal(interaction.guild.id)

            # Parse duration
            duration_days = 7  # Default
            if self.duration_days.value.strip():
                try:
                    duration_days = int(self.duration_days.value.strip())
                    if duration_days < 1 or duration_days > 30:
                        await interaction.response.send_message(
                            "duration must be between 1 and 30 days",
                            ephemeral=True
                        )
                        return
                except ValueError:
                    await interaction.response.send_message(
                        "invalid duration. please enter a number",
                        ephemeral=True
                    )
                    return

            # Check if event is already active
            if self.event_manager.is_event_active():
                await interaction.response.send_message(
                    "an event is already active. end the current event first",
                    ephemeral=True
                )
                return

            await interaction.response.defer()

            # Start the event
            event_info = await self.event_manager.start_event(
                title=self.event_title.value,
                event_type=event_type,
                goal=goal,
                duration_days=duration_days
            )

            # Send event announcement
            event_channel = interaction.guild.get_channel(self.event_channel_id)
            if event_channel:
                from utils.server_event_gen import generate_event_start_banner
                from io import BytesIO
                import asyncio

                # Generate event banner
                img = await asyncio.to_thread(
                    generate_event_start_banner,
                    event_title=self.event_title.value,
                    event_type=event_type,
                    message_goal=goal,
                    start_date=event_info['start_date'],
                    end_date=event_info['end_date']
                )

                buffer = BytesIO()
                await asyncio.to_thread(img.save, buffer, 'PNG')
                buffer.seek(0)

                file = discord.File(buffer, filename='event_start.png')

                # Send only the image without text (image contains all relevant info)
                await event_channel.send(file=file)

            await interaction.followup.send(
                f"event '{self.event_title.value}' created successfully\n"
                f"type: {event_type}\n"
                f"goal: {goal:,}\n"
                f"duration: {duration_days} days",
                ephemeral=True
            )

        except Exception as e:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"error creating event: {str(e)}",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    f"error creating event: {str(e)}",
                    ephemeral=True
                )


class EndEventModal(ui.Modal, title="end server event"):
    """Modal for ending the current event with confirmation."""

    confirmation = ui.TextInput(
        label="type 'confirm' to end the event",
        placeholder="confirm",
        required=True,
        max_length=10
    )

    reason = ui.TextInput(
        label="reason (optional)",
        placeholder="reason for ending event early",
        required=False,
        max_length=200,
        style=discord.TextStyle.paragraph
    )

    def __init__(self, event_manager, event_cog):
        super().__init__()
        self.event_manager = event_manager
        self.event_cog = event_cog

    async def on_submit(self, interaction: discord.Interaction):
        """Handle event end confirmation."""
        if self.confirmation.value.lower().strip() != "confirm":
            await interaction.response.send_message(
                "event end cancelled. you must type 'confirm' to end the event",
                ephemeral=True
            )
            return

        if not self.event_manager.is_event_active():
            await interaction.response.send_message(
                "no active event to end",
                ephemeral=True
            )
            return

        await interaction.response.defer()

        try:
            # End event and distribute rewards
            await self.event_cog._end_event_and_distribute_rewards()

            reason_text = ""
            if self.reason.value.strip():
                reason_text = f"\nreason: {self.reason.value}"

            await interaction.followup.send(
                f"event ended successfully{reason_text}",
                ephemeral=True
            )

        except Exception as e:
            await interaction.followup.send(
                f"error ending event: {str(e)}",
                ephemeral=True
            )


class EventProgressModal(ui.Modal, title="send progress update"):
    """Modal for manually sending event progress update."""

    custom_message = ui.TextInput(
        label="custom message (optional)",
        placeholder="add a custom message to the progress update",
        required=False,
        max_length=200,
        style=discord.TextStyle.paragraph
    )

    def __init__(self, event_cog):
        super().__init__()
        self.event_cog = event_cog

    async def on_submit(self, interaction: discord.Interaction):
        """Handle manual progress update."""
        if not self.event_cog.event_manager.is_event_active():
            await interaction.response.send_message(
                "no active event to update",
                ephemeral=True
            )
            return

        await interaction.response.defer()

        try:
            # Send progress update
            await self.event_cog._send_progress_update()

            await interaction.followup.send(
                "progress update sent successfully",
                ephemeral=True
            )

        except Exception as e:
            await interaction.followup.send(
                f"error sending progress update: {str(e)}",
                ephemeral=True
            )
