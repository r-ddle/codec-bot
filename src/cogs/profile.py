"""Profile commands - view and customize member profiles"""
import discord
from discord.ext import commands
from io import BytesIO
import asyncio
from utils.profile_card_new import (
    generate_profile_new,
    generate_profile_new_bg,
    generate_profile_new_nitro
)
from utils.rate_limiter import enforce_rate_limit

class ProfileCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def calculate_server_avg_messages(self, guild_id: int) -> int:
        """
        Calculate average messages per active member for dynamic goal setting.
        Uses current month's data to set realistic, server-specific goals.

        Returns:
            Average messages per active member, or 0 if no data
        """
        try:
            all_members = self.bot.member_data.data.get(guild_id, {})

            # Filter active members (those with messages this period)
            active_members = [
                data for data in all_members.values()
                if isinstance(data, dict) and data.get('messages_sent', 0) > 0
            ]

            if not active_members:
                return 0

            # Calculate average
            total_messages = sum(m.get('messages_sent', 0) for m in active_members)
            avg = total_messages // len(active_members)

            return avg
        except Exception:
            return 0

    @commands.command(name='profile')
    @enforce_rate_limit('rank')
    async def profile(self, ctx, member: discord.Member = None):
        """View profile card"""
        target = member or ctx.author
        if target.bot:
            await ctx.send("🤖 Bots don't have profiles.")
            return

        async with ctx.typing():
            try:
                member_data = self.bot.member_data.get_member_data(target.id, ctx.guild.id)
                top_role = next((role.name for role in reversed(target.roles) if role.name != "@everyone"), "NO ROLE")
                bio_text = member_data.get('bio', 'No bio set.')
                voice_hours = member_data.get('voice_minutes', 0) // 60

                # Calculate server average for dynamic message goals
                server_avg = self.calculate_server_avg_messages(ctx.guild.id)

                img = await asyncio.to_thread(
                    generate_profile_new,
                    username=target.display_name,
                    role_name=top_role,
                    avatar_url=target.avatar.url if target.avatar else None,
                    bio_text=bio_text,
                    xp=member_data.get('xp', 0),
                    messages=member_data.get('messages_sent', 0),
                    voice_hours=voice_hours,
                    current_rank=member_data.get('rank', 'Rookie'),
                    
                    server_avg_messages=server_avg
                )

                buffer = BytesIO()
                await asyncio.to_thread(img.save, buffer, 'PNG')
                buffer.seek(0)
                await ctx.send(file=discord.File(buffer, 'profile.png'))
            except Exception as e:
                await ctx.send(f"❌ Error: {e}")

    @commands.command(name='setbio')
    @enforce_rate_limit('use')
    async def setbio(self, ctx, *, bio_text: str):
        """Set your bio"""
        if len(bio_text) > 150:
            await ctx.send("❌ Bio too long! Max 150 characters.")
            return

        try:
            member_data = self.bot.member_data.get_member_data(ctx.author.id, ctx.guild.id)
            member_data['bio'] = bio_text
            self.bot.member_data.schedule_save()
            await self.bot.member_data.save_data_async()
            await ctx.send("[OK] Bio updated! Use `!profile` to see it.")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

    @commands.command(name='profilenew')
    @enforce_rate_limit('rank')
    async def profilenew(self, ctx, member: discord.Member = None):
        """View new profile card design - Basic"""
        target = member or ctx.author
        if target.bot:
            await ctx.send("🤖 Bots don't have profiles.")
            return

        async with ctx.typing():
            try:
                member_data = self.bot.member_data.get_member_data(target.id, ctx.guild.id)
                top_role = next((role.name for role in reversed(target.roles) if role.name != "@everyone"), "NO ROLE")
                bio_text = member_data.get('bio', 'No bio set.')
                voice_hours = member_data.get('voice_minutes', 0) // 60

                # Calculate server average for dynamic message goals
                server_avg = self.calculate_server_avg_messages(ctx.guild.id)

                img = await asyncio.to_thread(
                    generate_profile_new,
                    username=target.display_name,
                    role_name=top_role,
                    avatar_url=target.avatar.url if target.avatar else None,
                    bio_text=bio_text,
                    xp=member_data.get('xp', 0),
                    messages=member_data.get('messages_sent', 0),
                    voice_hours=voice_hours,
                    current_rank=member_data.get('rank', 'Rookie'),
                    
                    server_avg_messages=server_avg
                )

                buffer = BytesIO()
                await asyncio.to_thread(img.save, buffer, 'PNG')
                buffer.seek(0)
                await ctx.send(file=discord.File(buffer, 'profile_new.png'))
            except Exception as e:
                await ctx.send(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()

    @commands.command(name='profilenewbg')
    @enforce_rate_limit('rank')
    async def profilenewbg(self, ctx, member: discord.Member = None):
        """View new profile card design - Enhanced Background"""
        target = member or ctx.author
        if target.bot:
            await ctx.send("🤖 Bots don't have profiles.")
            return

        async with ctx.typing():
            try:
                member_data = self.bot.member_data.get_member_data(target.id, ctx.guild.id)
                top_role = next((role.name for role in reversed(target.roles) if role.name != "@everyone"), "NO ROLE")
                bio_text = member_data.get('bio', 'No bio set.')
                voice_hours = member_data.get('voice_minutes', 0) // 60

                # Calculate server average for dynamic message goals
                server_avg = self.calculate_server_avg_messages(ctx.guild.id)

                img = await asyncio.to_thread(
                    generate_profile_new_bg,
                    username=target.display_name,
                    role_name=top_role,
                    avatar_url=target.avatar.url if target.avatar else None,
                    bio_text=bio_text,
                    xp=member_data.get('xp', 0),
                    messages=member_data.get('messages_sent', 0),
                    voice_hours=voice_hours,
                    current_rank=member_data.get('rank', 'Rookie'),
                    
                    server_avg_messages=server_avg
                )

                buffer = BytesIO()
                await asyncio.to_thread(img.save, buffer, 'PNG')
                buffer.seek(0)
                await ctx.send(file=discord.File(buffer, 'profile_new_bg.png'))
            except Exception as e:
                await ctx.send(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()

    @commands.command(name='profilenewbgnitro')
    @enforce_rate_limit('rank')
    async def profilenewbgnitro(self, ctx, member: discord.Member = None):
        """View new profile card design - Nitro Banner"""
        target = member or ctx.author
        if target.bot:
            await ctx.send("🤖 Bots don't have profiles.")
            return

        async with ctx.typing():
            try:
                member_data = self.bot.member_data.get_member_data(target.id, ctx.guild.id)
                top_role = next((role.name for role in reversed(target.roles) if role.name != "@everyone"), "NO ROLE")
                bio_text = member_data.get('bio', 'No bio set.')
                voice_hours = member_data.get('voice_minutes', 0) // 60

                # Calculate server average for dynamic message goals
                server_avg = self.calculate_server_avg_messages(ctx.guild.id)

                img = await asyncio.to_thread(
                    generate_profile_new_nitro,
                    username=target.display_name,
                    role_name=top_role,
                    avatar_url=target.avatar.url if target.avatar else None,
                    bio_text=bio_text,
                    xp=member_data.get('xp', 0),
                    messages=member_data.get('messages_sent', 0),
                    voice_hours=voice_hours,
                    current_rank=member_data.get('rank', 'Rookie'),
                    
                    server_avg_messages=server_avg
                )

                buffer = BytesIO()
                await asyncio.to_thread(img.save, buffer, 'PNG')
                buffer.seek(0)
                await ctx.send(file=discord.File(buffer, 'profile_new_nitro.png'))
            except Exception as e:
                await ctx.send(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()

    @commands.command(name='serveravg')
    @commands.has_permissions(administrator=True)
    async def server_avg_messages(self, ctx):
        """Check server average messages per active member (Admin only)"""
        avg = self.calculate_server_avg_messages(ctx.guild.id)
        await ctx.send(f"{avg}")

async def setup(bot):
    await bot.add_cog(ProfileCommands(bot))
