"""
Server event templates with preset configurations.
"""
from typing import Dict, Any
from dataclasses import dataclass
from datetime import timedelta


@dataclass
class EventTemplate:
    """Base class for event templates."""
    name: str
    description: str
    event_type: str
    default_duration_days: int
    goal_multiplier: float  # Multiplier for dynamic goal calculation
    icon: str

    def get_config(self, guild_id: int, event_manager) -> Dict[str, Any]:
        """
        Get event configuration based on template.

        Args:
            guild_id: Guild ID for calculating dynamic goals
            event_manager: ServerEventManager instance

        Returns:
            Event configuration dict
        """
        base_goal = event_manager.calculate_dynamic_event_goal(guild_id)
        adjusted_goal = int(base_goal * self.goal_multiplier)

        return {
            'title': self.name,
            'description': self.description,
            'event_type': self.event_type,
            'goal': adjusted_goal,
            'duration_days': self.default_duration_days,
            'icon': self.icon
        }


class XPRaceTemplate(EventTemplate):
    """XP Race event template - members compete to earn the most XP."""

    def __init__(self):
        super().__init__(
            name="xp race",
            description="compete to earn the most xp through messages, voice chat, and reactions. "
                       "top contributors win bonus rewards",
            event_type="xp",
            default_duration_days=7,
            goal_multiplier=2.0,  # More challenging for XP events
            icon="⚡"
        )


class MessageWarTemplate(EventTemplate):
    """Message War event template - community works together to reach message goal."""

    def __init__(self):
        super().__init__(
            name="message marathon",
            description="work together as a community to reach the message goal. "
                       "every message counts toward our collective target",
            event_type="message",
            default_duration_days=5,
            goal_multiplier=1.5,  # Moderate challenge
            icon="💬"
        )


class ReactionWarTemplate(EventTemplate):
    """Reaction War event template - spread positivity through reactions."""

    def __init__(self):
        super().__init__(
            name="reaction wave",
            description="spread positivity by giving reactions to messages. "
                       "show appreciation and help reach our reaction goal",
            event_type="reaction",
            default_duration_days=3,
            goal_multiplier=3.0,  # Higher multiplier since reactions are easier
            icon="⭐"
        )


class WeekendBlitzTemplate(EventTemplate):
    """Weekend Blitz event template - short intensive event."""

    def __init__(self):
        super().__init__(
            name="weekend blitz",
            description="short and intense weekend event. "
                       "maximize your activity for big rewards",
            event_type="message",
            default_duration_days=2,
            goal_multiplier=0.8,  # Lower goal for short duration
            icon="🔥"
        )


class MonthlyMegaTemplate(EventTemplate):
    """Monthly Mega event template - long-term community challenge."""

    def __init__(self):
        super().__init__(
            name="monthly mega challenge",
            description="month-long community challenge with escalating rewards. "
                       "consistent participation is key",
            event_type="xp",
            default_duration_days=30,
            goal_multiplier=5.0,  # Much higher goal for month-long event
            icon="🏆"
        )


# Template registry
EVENT_TEMPLATES = {
    'xp_race': XPRaceTemplate(),
    'message_war': MessageWarTemplate(),
    'reaction_wave': ReactionWarTemplate(),
    'weekend_blitz': WeekendBlitzTemplate(),
    'monthly_mega': MonthlyMegaTemplate()
}


def get_template(template_name: str) -> EventTemplate:
    """
    Get an event template by name.

    Args:
        template_name: Name of the template

    Returns:
        EventTemplate instance or None if not found
    """
    return EVENT_TEMPLATES.get(template_name.lower().replace(' ', '_'))


def list_templates() -> Dict[str, EventTemplate]:
    """Get all available event templates."""
    return EVENT_TEMPLATES.copy()


def get_template_choices() -> list[tuple[str, str]]:
    """
    Get template choices for Discord UI components.

    Returns:
        List of (display_name, template_key) tuples
    """
    return [
        (f"{template.icon} {template.name}", key)
        for key, template in EVENT_TEMPLATES.items()
    ]
