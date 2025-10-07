"""
Progression cog - Commands for checking rank, GMP, leaderboard, and daily bonuses.
"""
import discord
from discord.ext import commands
from datetime import datetime, timedelta
from typing import Optional

from utils.formatters import format_number, make_progress_bar
from utils.rank_system import get_rank_data_by_name, get_next_rank_info
from utils.role_manager import update_member_roles


class Progression(commands.Cog):
    """Commands related to member progression and statistics."""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='gmp')
    async def gmp(self, ctx):
        """Check GMP balance, rank, and stats."""
        member_id = ctx.author.id
        guild_id = ctx.guild.id
        member_data = self.bot.member_data.get_member_data(member_id, guild_id)
        next_rank_info = get_next_rank_info(member_data['xp'], member_data['rank'])
        
        embed = discord.Embed(
            title=f"{member_data.get('rank_icon', '')} {ctx.author.display_name}",
            description=f"**Rank:** {member_data['rank']}\n**GMP:** {format_number(member_data['gmp'])}\n**XP:** {format_number(member_data['xp'])}",
            color=0x599cff
        )
        
        if ctx.author.avatar:
            embed.set_thumbnail(url=ctx.author.avatar.url)
        
        embed.add_field(
            name="ACTIVITY STATS",
            value=f"```\nMessages: {format_number(member_data['messages_sent'])}\nVoice: {format_number(member_data['voice_minutes'])} min\nTactical Words: {format_number(member_data.get('total_tactical_words', 0))}\n```",
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
    async def rank(self, ctx, member: Optional[discord.Member] = None):
        """Check rank status of yourself or another member."""
        if member is None:
            member = ctx.author
        
        if member.bot:
            await ctx.send(" Bots don't have ranks.")
            return
        
        member_id = member.id
        guild_id = ctx.guild.id
        member_data = self.bot.member_data.get_member_data(member_id, guild_id)
        
        embed = discord.Embed(
            title=f"{member_data.get('rank_icon', '')} {member.display_name}",
            description=f"**Rank:** {member_data['rank']}\n**GMP:** {format_number(member_data['gmp'])}\n**XP:** {format_number(member_data['xp'])}",
            color=0x599cff
        )
        
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        
        embed.add_field(
            name="ACTIVITY STATS",
            value=f"```\nMessages: {format_number(member_data['messages_sent'])}\nVoice: {format_number(member_data['voice_minutes'])} min\nTactical Words: {format_number(member_data.get('total_tactical_words', 0))}\n```",
            inline=False
        )
        
        await ctx.send(embed=embed)

    @commands.command(name='leaderboard', aliases=['lb'])
    async def leaderboard(self, ctx, category: str = "xp"):
        """View server leaderboard."""
        guild_id = ctx.guild.id
        
        valid_categories = {
            "gmp": "GMP Ranking",
            "xp": "Experience Points",
            "tactical": "Tactical Words",
            "messages": "Messages Sent"
        }
        
        category_mapping = {
            "gmp": "gmp",
            "xp": "xp", 
            "tactical": "total_tactical_words",
            "messages": "messages_sent"
        }
        
        if category.lower() not in category_mapping:
            category = "xp"
        
        sort_field = category_mapping[category.lower()]
        title = valid_categories[category.lower()]
        
        leaderboard_data = self.bot.member_data.get_leaderboard(guild_id, sort_by=sort_field, limit=10)
        
        embed = discord.Embed(
            title=f" LEADERBOARD: {title.upper()}",
            color=0x599cff
        )
        
        if not leaderboard_data:
            embed.add_field(name="NO DATA", value="No operatives found.", inline=False)
            await ctx.send(embed=embed)
            return
        
        leaderboard_text = ""
        for i, (member_id, data) in enumerate(leaderboard_data, 1):
            try:
                member = ctx.guild.get_member(int(member_id))
                name = member.display_name if member else f"Unknown ({member_id})"
                
                medal = "" if i == 1 else "" if i == 2 else "" if i == 3 else f"{i}."
                value = data.get(sort_field, 0)
                rank_icon = data.get("rank_icon", "")
                
                leaderboard_text += f"{medal} **{name}** - {format_number(value)} {category.upper()} {rank_icon}\n"
            except Exception:
                continue
        
        embed.add_field(name="TOP OPERATIVES", value=leaderboard_text, inline=False)
        
        categories_help = "\n".join([f"`!lb {cat}` - {name}" for cat, name in valid_categories.items()])
        embed.add_field(name="CATEGORIES", value=categories_help, inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name='daily')
    async def daily(self, ctx):
        """Claim daily bonus."""
        member_id = ctx.author.id
        guild_id = ctx.guild.id
        
        success, gmp, xp, rank_changed, new_rank = self.bot.member_data.award_daily_bonus(member_id, guild_id)
        
        if success:
            embed = discord.Embed(
                title=" DAILY SUPPLY DROP",
                description=f"**+{format_number(gmp)} GMP** and **+{format_number(xp)} XP** received!",
                color=0x00ff00
            )
            
            # Get updated member data
            member_data = self.bot.member_data.get_member_data(member_id, guild_id)
            
            embed.add_field(
                name="UPDATED STATS",
                value=f"```\nGMP: {format_number(member_data['gmp'])}\nXP: {format_number(member_data['xp'])}\nRank: {member_data['rank']}\n```",
                inline=False
            )
            
            if rank_changed:
                role_updated = await update_member_roles(ctx.author, new_rank)
                embed.add_field(name=" PROMOTION!", value=f"New rank: **{new_rank}**", inline=False)
                
                if role_updated:
                    rank_data = get_rank_data_by_name(new_rank)
                    role_name = rank_data.get("role_name", new_rank)
                    embed.add_field(name=" ROLE ASSIGNED", value=f"Discord role **{role_name}** granted!", inline=False)
            
            embed.set_footer(text="Come back tomorrow for another supply drop!")
            await ctx.send(embed=embed)
            
            # Force save
            await self.bot.member_data.save_data_async(force=True)
            
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
