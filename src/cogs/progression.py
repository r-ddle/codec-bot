"""
Progression cog - Commands for checking rank, leaderboard, and daily bonuses.
"""
import discord
from discord.ext import commands
from discord.ui import LayoutView
from datetime import datetime, timedelta
from typing import Optional
import asyncio
from io import BytesIO

from utils.formatters import format_number, make_progress_bar
from utils.rank_system import get_rank_data_by_name, get_next_rank_info
from utils.role_manager import update_member_roles
from utils.image_gen import generate_rank_card
from utils.image_gen_modern import generate_modern_rank_card
from utils.daily_supply_gen import generate_daily_supply_card, generate_promotion_card
from utils.leaderboard_gen import generate_leaderboard
from utils.rate_limiter import enforce_rate_limit
from utils.components_builder import (
    create_status_container,
    create_error_message,
    create_progress_container,
    create_simple_message,
    create_success_message,
    LeaderboardView
)
from config.settings import logger
from config.constants import COZY_RANKS


class Progression(commands.Cog):
    """Commands related to member progression and statistics."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='status')
    @enforce_rate_limit('status')
    async def status(self, ctx):
        """Check your rank, XP, and stats."""
        # Rate limiting enforced via decorator

        member_id = ctx.author.id
        guild_id = ctx.guild.id
        member_data = self.bot.member_data.get_member_data(member_id, guild_id)
        next_rank_info = get_next_rank_info(member_data['xp'], member_data['rank'])

        # Get streak info
        streak_info = self.bot.member_data.get_streak_info(member_id, guild_id)

        # Build fields for the status display
        fields = [
            {
                "name": "current status",
                "value": f"**rank:** {member_data['rank']}\n**xp:** {format_number(member_data['xp'])}"
            }
        ]

        # Add streak info if user has an active streak
        if streak_info['current_streak'] > 0:
            streak_text = f"**current streak:** {streak_info['current_streak']} days\n"
            if streak_info['longest_streak'] > streak_info['current_streak']:
                streak_text += f"**best streak:** {streak_info['longest_streak']} days\n"
            if streak_info['xp_bonus'] > 0:
                streak_text += f"**xp bonus:** +{streak_info['xp_bonus']} per message"

            fields.append({
                "name": "activity streak",
                "value": streak_text
            })

        fields.append({
            "name": "activity stats",
            "value": f"```\nmessages: {format_number(member_data['messages_sent'])}\nvoice: {format_number(member_data['voice_minutes'])} min\n```"
        })

        if next_rank_info:
            xp_progress = member_data["xp"] - next_rank_info["current_rank_xp"]
            xp_total = next_rank_info["next_xp"] - next_rank_info["current_rank_xp"]

            xp_bar = make_progress_bar(xp_progress, xp_total)
            xp_needed = max(0, next_rank_info["next_xp"] - member_data["xp"])

            rank_data = get_rank_data_by_name(next_rank_info["name"])
            role_name = rank_data.get("role_name", next_rank_info["name"])

            progress_text = f"```\nnext rank: {next_rank_info['name']} {next_rank_info['icon']}\ndiscord role: {role_name}\n\n"
            progress_text += f"xp: {format_number(member_data['xp'])} / {format_number(next_rank_info['next_xp'])} {xp_bar}\n\n"

            if xp_needed > 0:
                progress_text += f"needed for promotion:\nxp: {format_number(xp_needed)}\n"
            else:
                progress_text += "ready for promotion\n"

            progress_text += "```"

            fields.append({
                "name": "rank progress",
                "value": progress_text
            })
        else:
            fields.append({
                "name": "maximum rank",
                "value": "```\nfoxhound operative - highest rank achieved\n```"
            })

        container = create_status_container(
            title=f"{member_data.get('rank_icon', '🎖️')} {ctx.author.display_name}",
            fields=fields,
            thumbnail_url=ctx.author.avatar.url if ctx.author.avatar else None
        )

        view = LayoutView()
        view.add_item(container)
        await ctx.send(view=view)

    @commands.command(name='rank')
    @enforce_rate_limit('rank')
    async def rank(self, ctx, member: Optional[discord.Member] = None):
        """Check rank status of yourself or another member."""
        if member is None:
            member = ctx.author

        if member.bot:
            container = create_error_message(
                "Cannot check bot ranks",
                "Bots don't have rank progression."
            )
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)
            return

        member_id = member.id
        guild_id = ctx.guild.id
        member_data = self.bot.member_data.get_member_data(member_id, guild_id)

        # Show typing indicator while generating the image
        async with ctx.typing():
            try:
                current_rank_name = member_data.get('rank', 'Rookie')
                current_rank_icon = member_data.get('rank_icon', '🎖️')
                current_xp = member_data.get('xp', 0)
                messages = member_data.get('messages_sent', 0)
                voice_mins = member_data.get('voice_minutes', 0)

                # Find current rank index
                current_rank_index = 0
                for i, rank_info in enumerate(COZY_RANKS):
                    if rank_info.get("name") == current_rank_name:
                        current_rank_index = i
                        break

                # Get next rank if not at max
                next_rank = COZY_RANKS[current_rank_index + 1] if current_rank_index < len(COZY_RANKS) - 1 else None

                # Calculate XP needed for progress bar
                xp_max = next_rank.get("required_xp", current_xp) if next_rank else current_xp

                # Get avatar URL
                avatar_url = member.avatar.url if member.avatar else None

                # Generate the NEW tactical rank card image off the event loop
                img = await asyncio.to_thread(
                    generate_rank_card,
                    member.display_name,
                    current_rank_icon,
                    current_rank_name,
                    current_xp,
                    xp_max,
                    avatar_url,
                    messages,
                    voice_mins
                )

                # Convert PIL Image to BytesIO in thread
                image_bytes = BytesIO()
                await asyncio.to_thread(img.save, image_bytes, 'PNG')
                image_bytes.seek(0)

                # Create Discord file from the image bytes
                file = discord.File(fp=image_bytes, filename=f"rank_{member_id}.png")

                # Send the image
                await ctx.send(file=file)

            except Exception as e:
                # Fallback to component display if image generation fails
                container = create_status_container(
                    title=f"{member_data.get('rank_icon', '🎖️')} {member.display_name}",
                    fields=[
                        {
                            "name": "RANK INFO",
                            "value": f"**Rank:** {member_data['rank']}\n**XP:** {format_number(member_data['xp'])}"
                        },
                        {
                            "name": "ACTIVITY STATS",
                            "value": f"```\nMessages: {format_number(member_data['messages_sent'])}\nVoice: {format_number(member_data['voice_minutes'])} min\n```"
                        }
                    ],
                    thumbnail_url=member.avatar.url if member.avatar else None,
                    footer=f"⚠️ Image generation failed: {e}"
                )

                view = LayoutView()
                view.add_item(container)
                await ctx.send(view=view)

                import traceback
                print(f"Error generating rank card: {e}")
                traceback.print_exc()

    @commands.command(name='ranknew')
    @enforce_rate_limit('rank')
    async def rank_modern(self, ctx, member: Optional[discord.Member] = None):
        """Check rank status with modern UI design (experimental)."""
        if member is None:
            member = ctx.author

        if member.bot:
            container = create_error_message(
                "Cannot check bot ranks",
                "Bots don't have rank progression."
            )
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)
            return

        member_id = member.id
        guild_id = ctx.guild.id
        member_data = self.bot.member_data.get_member_data(member_id, guild_id)

        # Show typing indicator while generating the image
        async with ctx.typing():
            try:
                current_rank_name = member_data.get('rank', 'New Lifeform')
                current_rank_icon = member_data.get('rank_icon', '🥚')
                current_xp = member_data.get('xp', 0)
                messages = member_data.get('messages_sent', 0)
                voice_mins = member_data.get('voice_minutes', 0)

                # Find current rank index
                current_rank_index = 0
                for i, rank_info in enumerate(COZY_RANKS):
                    if rank_info.get("name") == current_rank_name:
                        current_rank_index = i
                        break

                # Get next rank if not at max
                next_rank = COZY_RANKS[current_rank_index + 1] if current_rank_index < len(COZY_RANKS) - 1 else None

                # Calculate XP needed for progress bar
                xp_max = next_rank.get("required_xp", current_xp) if next_rank else current_xp

                # Get avatar URL
                avatar_url = member.avatar.url if member.avatar else None

                # Get leaderboard position
                guild_data = self.bot.member_data.data.get(str(guild_id), {})
                sorted_members = sorted(
                    [(mid, mdata.get('xp', 0)) for mid, mdata in guild_data.items()],
                    key=lambda x: x[1],
                    reverse=True
                )
                leaderboard_pos = None
                for idx, (mid, _) in enumerate(sorted_members, 1):
                    if int(mid) == member_id:
                        leaderboard_pos = idx
                        break

                # Generate the MODERN rank card image
                img = await asyncio.to_thread(
                    generate_modern_rank_card,
                    member.display_name,
                    current_rank_name,
                    current_xp,
                    xp_max,
                    avatar_url,
                    messages,
                    voice_mins,
                    leaderboard_pos,
                    current_rank_icon
                )

                # Convert PIL Image to BytesIO in thread
                image_bytes = BytesIO()
                await asyncio.to_thread(img.save, image_bytes, 'PNG')
                image_bytes.seek(0)

                # Create Discord file from the image bytes
                file = discord.File(fp=image_bytes, filename=f"rank_modern_{member_id}.png")

                # Send the image
                await ctx.send(file=file)

            except Exception as e:
                # Log the error for debugging
                logger.error(f"Modern rank card generation failed: {e}", exc_info=True)

                # Fallback to simple embed
                embed = discord.Embed(
                    title=f"{member_data.get('rank_icon', '🥚')} {member.display_name}",
                    color=discord.Color.from_rgb(255, 110, 85)
                )

                embed.add_field(
                    name="RANK INFO",
                    value=f"**Rank:** {member_data['rank']}\n**XP:** {format_number(member_data['xp'])}",
                    inline=False
                )

                embed.add_field(
                    name="ACTIVITY STATS",
                    value=f"Messages: {format_number(member_data['messages_sent'])}\nVoice: {format_number(member_data['voice_minutes'])} min",
                    inline=False
                )

                embed.set_footer(text="⚠️ Image generation failed, showing text fallback")
                if member.avatar:
                    embed.set_thumbnail(url=member.avatar.url)

                await ctx.send(embed=embed)

    @commands.command(name='leaderboard', aliases=['lb'])
    @enforce_rate_limit('leaderboard')
    async def leaderboard(self, ctx, category: str = "xp"):
        """View server leaderboard with MGS Codec styling."""
        guild_id = ctx.guild.id

        valid_categories = {
            "xp": ("EXPERIENCE POINTS", "XP"),
            "messages": ("MESSAGES SENT", "MSG"),
            "voice": ("VOICE TIME", "MIN")
        }

        category_mapping = {
            "xp": "xp",
            "messages": "messages_sent",
            "voice": "voice_minutes"
        }

        if category.lower() not in category_mapping:
            category = "xp"

        sort_field = category_mapping[category.lower()]
        category_name, unit_suffix = valid_categories[category.lower()]

        # Fetch leaderboard data
        leaderboard_data = self.bot.member_data.get_leaderboard(
            guild_id, sort_by=sort_field, limit=10
        )

        if not leaderboard_data:
            container = create_error_message(
                "no operatives found in database",
                "there are no members with activity data to display."
            )
            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)
            return

        # Show typing indicator while generating
        async with ctx.typing():
            try:
                # Format data for image generator (skip members who left)
                formatted_data = []
                rank = 1
                for member_id, data in leaderboard_data:
                    try:
                        member = ctx.guild.get_member(int(member_id))
                        # Skip members who have left the server
                        if not member:
                            continue

                        name = member.display_name
                        value = data.get(sort_field, 0)
                        rank_icon = data.get("rank_icon", "")

                        formatted_data.append((rank, name, value, rank_icon))
                        rank += 1
                    except Exception:
                        continue

                # Generate image off the event loop
                img = await asyncio.to_thread(
                    generate_leaderboard,
                    leaderboard_data=formatted_data,
                    category=category_name,
                    unit_suffix=unit_suffix,
                    guild_name=ctx.guild.name
                )

                # Convert to Discord-compatible format
                buffer = BytesIO()
                await asyncio.to_thread(img.save, buffer, 'PNG')
                buffer.seek(0)

                file = discord.File(buffer, filename='leaderboard.png')

                # Create interactive view with category buttons
                view = LeaderboardView(self.bot, ctx, category.lower())
                message = await ctx.send(file=file, view=view)
                view.message = message

            except Exception as e:
                container = create_error_message(
                    "failed to generate leaderboard",
                    f"error details: {str(e)}"
                )
                view = LayoutView()
                view.add_item(container)
                await ctx.send(view=view)

                import traceback
                traceback.print_exc()

    @commands.command(name='daily')
    async def daily(self, ctx):
        """Claim daily bonus."""
        member_id = ctx.author.id
        guild_id = ctx.guild.id

        success, xp, rank_changed, new_rank = self.bot.member_data.award_daily_bonus(member_id, guild_id)

        if not success:
            # Already claimed today - show time remaining
            member_data = self.bot.member_data.get_member_data(member_id, guild_id)
            last_daily = member_data.get("last_daily")

            if last_daily:
                from datetime import datetime, timezone, timedelta
                last_claim_date = datetime.strptime(last_daily, '%Y-%m-%d').replace(tzinfo=timezone.utc)
                next_claim_time = last_claim_date + timedelta(days=1)
                now = datetime.now(timezone.utc)
                time_remaining = next_claim_time - now

                if time_remaining.total_seconds() > 0:
                    hours, remainder = divmod(int(time_remaining.total_seconds()), 3600)
                    minutes, seconds = divmod(remainder, 60)

                    if hours > 0:
                        time_str = f"{hours}h {minutes}m {seconds}s"
                    elif minutes > 0:
                        time_str = f"{minutes}m {seconds}s"
                    else:
                        time_str = f"{seconds}s"
                else:
                    time_str = "a few seconds"
            else:
                time_str = "unknown"

            container = create_status_container(
                title="⏰ Daily Already Claimed",
                fields=[
                    {
                        "name": "Next Claim",
                        "value": f"Available in **{time_str}**"
                    },
                    {
                        "name": "Current Stats",
                        "value": f"```\nXP: {format_number(member_data.get('xp', 0))}\nRank: {member_data.get('rank', 'Rookie')}\nStreak: {member_data.get('daily_streak', 0)} days\n```"
                    }
                ],
                footer="Outer Heaven: Exiled Units"
            )

            view = LayoutView()
            view.add_item(container)
            await ctx.send(view=view)
            return

        # Success - proceed with normal daily claim logic
        # Get updated member data
        member_data = self.bot.member_data.get_member_data(member_id, guild_id)

        # Get streak info
        streak_days = member_data.get('daily_streak', 1)

        # Determine role granted if promoted
        role_granted = None
        if rank_changed:
            role_updated = await update_member_roles(ctx.author, new_rank)
            if role_updated:
                rank_data = get_rank_data_by_name(new_rank)
                role_granted = rank_data.get("role_name", new_rank)

        # Generate MGS Codec-style supply drop image
        try:
            img = generate_daily_supply_card(
                username=ctx.author.display_name,
                xp_reward=xp,
                current_xp=member_data['xp'],
                current_rank=member_data['rank'],
                streak_days=streak_days,
                promoted=rank_changed,
                new_rank=new_rank if rank_changed else None,
                role_granted=role_granted
            )

            # Convert to Discord file
            image_bytes = BytesIO()
            img.save(image_bytes, format='PNG')
            image_bytes.seek(0)

            file = discord.File(fp=image_bytes, filename="daily_supply.png")
            await ctx.send(file=file)

            # Send promotion announcement to specific channel if promoted
            if rank_changed and new_rank:
                try:
                    promo_channel = self.bot.get_channel(1423506534872387584)
                    if promo_channel:
                        # Get old rank for promotion card
                        old_rank = member_data.get('rank', 'Unknown')

                        # Generate promotion card
                        promo_img = generate_promotion_card(
                            username=ctx.author.display_name,
                            old_rank=old_rank,
                            new_rank=new_rank,
                            current_xp=member_data['xp'],
                            role_granted=role_granted
                        )

                        # Convert to Discord file
                        promo_bytes = BytesIO()
                        promo_img.save(promo_bytes, format='PNG')
                        promo_bytes.seek(0)
                        promo_file = discord.File(promo_bytes, filename="promotion.png")

                        # Send promotion message
                        await promo_channel.send(
                            f"{ctx.author.mention} has been promoted to {new_rank}!",
                            file=promo_file
                        )
                except Exception as e:
                    logger.error(f"Error sending promotion announcement: {e}")

        except Exception as e:
            # Log the full error for debugging
            logger.error(f"Image generation error: {e}", exc_info=True)

            # Fallback to simple embed instead of components (avoids character limit issues)
            embed = discord.Embed(
                title="💰 DAILY SUPPLY DROP",
                color=discord.Color.from_rgb(255, 110, 85)
            )

            embed.add_field(
                name="REWARD",
                value=f"**+{format_number(xp)} XP** received!",
                inline=False
            )

            embed.add_field(
                name="UPDATED STATS",
                value=f"XP: {format_number(member_data['xp'])}\nRank: {member_data['rank']}\nStreak: {streak_days} days",
                inline=False
            )

            if rank_changed:
                embed.add_field(
                    name="🎖️ PROMOTION!",
                    value=f"New rank: **{new_rank}**",
                    inline=False
                )
                if role_granted:
                    embed.add_field(
                        name="ROLE ASSIGNED",
                        value=f"Discord role **{role_granted}** granted!",
                        inline=False
                    )

            embed.set_footer(text="⚠️ Image generation failed, showing text fallback")
            await ctx.send(embed=embed)

        # Schedule a background save; avoid forcing Neon sync here
        self.bot.member_data.schedule_save()
        asyncio.create_task(self.bot.member_data.save_data_async(force=False))


async def setup(bot):
    """Load the Progression cog."""
    await bot.add_cog(Progression(bot))
