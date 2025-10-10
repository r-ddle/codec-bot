"""
Progression cog - Commands for checking rank, leaderboard, and daily bonuses.
"""
import discord
from discord.ext import commands
from datetime import datetime, timedelta
from typing import Optional
import asyncio
from io import BytesIO

from utils.formatters import format_number, make_progress_bar
from utils.rank_system import get_rank_data_by_name, get_next_rank_info, MGS_RANKS
from utils.role_manager import update_member_roles
from utils.image_gen import generate_rank_card
from utils.daily_supply_gen import generate_daily_supply_card
from utils.leaderboard_gen import generate_leaderboard
from utils.rate_limiter import enforce_rate_limit


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

        embed = discord.Embed(
            title=f"{member_data.get('rank_icon', '')} {ctx.author.display_name}",
            description=f"**Rank:** {member_data['rank']}\n**XP:** {format_number(member_data['xp'])}",
            color=0x599cff
        )

        if ctx.author.avatar:
            embed.set_thumbnail(url=ctx.author.avatar.url)

        embed.add_field(
            name="ACTIVITY STATS",
            value=f"```\nMessages: {format_number(member_data['messages_sent'])}\nVoice: {format_number(member_data['voice_minutes'])} min\n```",
            inline=False
        )

        if next_rank_info:
            xp_progress = member_data["xp"] - next_rank_info["current_rank_xp"]
            xp_total = next_rank_info["next_xp"] - next_rank_info["current_rank_xp"]

            xp_bar = make_progress_bar(xp_progress, xp_total)
            xp_needed = max(0, next_rank_info["next_xp"] - member_data["xp"])

            rank_data = get_rank_data_by_name(next_rank_info["name"])
            role_name = rank_data.get("role_name", next_rank_info["name"])

            progress_text = f"```\nNext Rank: {next_rank_info['name']} {next_rank_info['icon']}\nDiscord Role: {role_name}\n\n"
            progress_text += f"XP: {format_number(member_data['xp'])} / {format_number(next_rank_info['next_xp'])} {xp_bar}\n\n"

            if xp_needed > 0:
                progress_text += f"NEEDED FOR PROMOTION:\nXP: {format_number(xp_needed)}\n"
            else:
                progress_text += " READY FOR PROMOTION!\n"

            progress_text += "```"

            embed.add_field(name="RANK PROGRESS", value=progress_text, inline=False)
        else:
            embed.add_field(name="MAXIMUM RANK", value="```\nFOXHOUND operative - highest rank achieved!\n```", inline=False)

        await ctx.send(embed=embed)

    @commands.command(name='rank')
    @enforce_rate_limit('rank')
    async def rank(self, ctx, member: Optional[discord.Member] = None):
        """Check rank status of yourself or another member."""
        if member is None:
            member = ctx.author

        if member.bot:
            await ctx.send("🤖 Bots don't have ranks.")
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
                for i, rank_info in enumerate(MGS_RANKS):
                    if rank_info.get("name") == current_rank_name:
                        current_rank_index = i
                        break

                # Get next rank if not at max
                next_rank = MGS_RANKS[current_rank_index + 1] if current_rank_index < len(MGS_RANKS) - 1 else None

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
                # Fallback to embed if image generation fails
                embed = discord.Embed(
                    title=f"{member_data.get('rank_icon', '')} {member.display_name}",
                    description=f"**Rank:** {member_data['rank']}\n**XP:** {format_number(member_data['xp'])}",
                    color=0x599cff
                )

                if member.avatar:
                    embed.set_thumbnail(url=member.avatar.url)

                embed.add_field(
                    name="ACTIVITY STATS",
                    value=f"```\nMessages: {format_number(member_data['messages_sent'])}\nVoice: {format_number(member_data['voice_minutes'])} min\n```",
                    inline=False
                )

                await ctx.send(f"⚠️ Image generation failed. Showing text version:\n", embed=embed)
                import traceback
                print(f"Error generating rank card: {e}")
                traceback.print_exc()

    @commands.command(name='leaderboard', aliases=['lb'])
    @enforce_rate_limit('leaderboard')
    async def leaderboard(self, ctx, category: str = "xp"):
        """View server leaderboard with MGS Codec styling."""
        guild_id = ctx.guild.id

        valid_categories = {
            "xp": ("EXPERIENCE POINTS", "XP"),
            "messages": ("MESSAGES SENT", "MSG")
        }

        category_mapping = {
            "xp": "xp",
            "messages": "messages_sent"
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
            await ctx.send("❌ No operatives found in database.")
            return

        # Show typing indicator while generating
        async with ctx.typing():
            try:
                # Format data for image generator
                formatted_data = []
                for i, (member_id, data) in enumerate(leaderboard_data, 1):
                    try:
                        member = ctx.guild.get_member(int(member_id))
                        name = member.display_name if member else f"Unknown"
                        value = data.get(sort_field, 0)
                        rank_icon = data.get("rank_icon", "")

                        formatted_data.append((i, name, value, rank_icon))
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
                await ctx.send(file=file)

            except Exception as e:
                await ctx.send(f"❌ Failed to generate leaderboard: {e}")
                import traceback
                traceback.print_exc()

    @commands.command(name='daily')
    @enforce_rate_limit('daily')
    async def daily(self, ctx):
        """Claim daily bonus."""
        # Rate limiting enforced via decorator

        member_id = ctx.author.id
        guild_id = ctx.guild.id

        success, xp, rank_changed, new_rank = self.bot.member_data.award_daily_bonus(member_id, guild_id)

        if success:
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

            except Exception as e:
                # Fallback to text embed if image fails
                embed = discord.Embed(
                    title="📦 DAILY SUPPLY DROP",
                    description=f"**+{format_number(xp)} XP** received!",
                    color=0x00ff00
                )
                embed.add_field(
                    name="UPDATED STATS",
                    value=f"```\nXP: {format_number(member_data['xp'])}\nRank: {member_data['rank']}\nStreak: {streak_days} days\n```",
                    inline=False
                )
                if rank_changed:
                    embed.add_field(name="🎖️ PROMOTION!", value=f"New rank: **{new_rank}**", inline=False)
                    if role_granted:
                        embed.add_field(name="✓ ROLE ASSIGNED", value=f"Discord role **{role_granted}** granted!", inline=False)

                embed.set_footer(text=f"Error generating image: {e}")
                await ctx.send(embed=embed)

            # Schedule a background save; avoid forcing Neon sync here
            self.bot.member_data.schedule_save()
            asyncio.create_task(self.bot.member_data.save_data_async(force=False))

        else:
            now = datetime.now()
            tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            time_left = tomorrow - now
            hours = time_left.seconds // 3600
            minutes = (time_left.seconds // 60) % 60

            embed = discord.Embed(
                title=" SUPPLY DROP UNAVAILABLE",
                description=f"Already claimed today.\nNext drop in **{hours:02d}:{minutes:02d}**",
                color=0xff0000
            )
            await ctx.send(embed=embed)


async def setup(bot):
    """Load the Progression cog."""
    await bot.add_cog(Progression(bot))
