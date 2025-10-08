"""Shop commands - simplified"""
import discord
from discord.ext import commands
from io import BytesIO
from datetime import datetime, timedelta
import asyncio
from config.shop_config import SHOP_ITEMS
from utils.shop_gen import generate_shop_card
from utils.profile_card_gen import generate_simple_profile_card

class ShopCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='shop')
    async def shop(self, ctx):
        """View the GMP shop"""
        member_data = self.bot.member_data.get_member_data(ctx.author.id, ctx.guild.id)
        async with ctx.typing():
            try:
                img = await asyncio.to_thread(generate_shop_card, member_data.get('gmp', 0), SHOP_ITEMS)
                buffer = BytesIO()
                await asyncio.to_thread(img.save, buffer, 'PNG')
                buffer.seek(0)
                await ctx.send(file=discord.File(buffer, 'shop.png'))
            except Exception as e:
                await ctx.send(f"❌ Error: {e}")

    @commands.command(name='profile')
    async def profile(self, ctx, member: discord.Member = None):
        """View profile card"""
        target = member or ctx.author
        if target.bot:
            await ctx.send("🤖 Bots don't have profiles.")
            return

        async with ctx.typing():
            try:
                member_data = self.bot.member_data.get_member_data(target.id, ctx.guild.id)
                joined_at = target.joined_at
                member_since = joined_at.strftime("%b %Y").upper() if joined_at else "UNKNOWN"
                top_role = next((role.name for role in reversed(target.roles) if role.name != "@everyone"), "NO ROLE")
                bio_text = member_data.get('bio', 'No bio set.')
                voice_hours = member_data.get('voice_minutes', 0) // 60

                img = await asyncio.to_thread(
                    generate_simple_profile_card,
                    username=target.display_name,
                    role_name=top_role,
                    avatar_url=target.avatar.url if target.avatar else None,
                    member_since=member_since,
                    bio_text=bio_text,
                    gmp=member_data.get('gmp', 0),
                    xp=member_data.get('xp', 0),
                    messages=member_data.get('messages_sent', 0),
                    voice_hours=voice_hours,
                    tactical_words=member_data.get('total_tactical_words', 0)
                )

                buffer = BytesIO()
                await asyncio.to_thread(img.save, buffer, 'PNG')
                buffer.seek(0)
                await ctx.send(file=discord.File(buffer, 'profile.png'))
            except Exception as e:
                await ctx.send(f"❌ Error: {e}")

    @commands.command(name='setbio')
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
            await ctx.send("✅ Bio updated! Use `!profile` to see it.")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

    @commands.command(name='buy')
    async def buy(self, ctx, item_number: int):
        """Purchase an item from the shop

        Usage: !buy 1  (for custom role)
               !buy 2  (for extra daily)
               !buy 3  (for 2hr booster)
        """
        # Validate item number
        if item_number < 1 or item_number > len(SHOP_ITEMS):
            await ctx.send(f"❌ Invalid item number! Use `!shop` to see available items (1-{len(SHOP_ITEMS)}).")
            return

        item = SHOP_ITEMS[item_number - 1]
        member_data = self.bot.member_data.get_member_data(ctx.author.id, ctx.guild.id)
        user_gmp = member_data.get('gmp', 0)

        # Check if user can afford
        if user_gmp < item['price']:
            await ctx.send(f"❌ Not enough GMP! You need **{item['price']:,}** GMP but only have **{user_gmp:,}** GMP.")
            return

        # Process purchase based on item type
        if item['item_type'] == 'custom_role':
            # Deduct GMP
            member_data['gmp'] = user_gmp - item['price']
            self.bot.member_data.schedule_save()
            await self.bot.member_data.save_data_async()

            embed = discord.Embed(
                title="✅ CUSTOM ROLE PURCHASED",
                description=f"You've purchased a custom role for **{item['price']:,} GMP**!\n\n"
                           f"**Next Steps:**\n"
                           f"1. Choose your role name\n"
                           f"2. Choose your role color (hex code)\n"
                           f"3. Contact an admin to apply it\n\n"
                           f"Remaining GMP: **{member_data['gmp']:,}**",
                color=0x9B59B6
            )
            await ctx.send(embed=embed)

        elif item['item_type'] == 'extra_daily':
            # Check if user already claimed daily today
            last_daily = member_data.get('last_daily_claim')
            today = datetime.now().date()

            if last_daily:
                last_date = datetime.fromisoformat(last_daily).date()
                if last_date == today:
                    # Already claimed, so give extra daily
                    gmp_reward = 200
                    xp_reward = 100

                    member_data['gmp'] = user_gmp - item['price'] + gmp_reward
                    member_data['xp'] = member_data.get('xp', 0) + xp_reward

                    self.bot.member_data.schedule_save()
                    await self.bot.member_data.save_data_async()

                    embed = discord.Embed(
                        title="✅ EXTRA DAILY CLAIMED",
                        description=f"You've received your extra daily supply drop!\n\n"
                                   f"**Rewards:**\n"
                                   f"• +{gmp_reward} GMP\n"
                                   f"• +{xp_reward} XP\n\n"
                                   f"Remaining GMP: **{member_data['gmp']:,}**",
                        color=0x2ECC71
                    )
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("❌ You haven't claimed your regular daily yet today! Use `!daily` first.")
                    return
            else:
                await ctx.send("❌ You haven't claimed your regular daily yet! Use `!daily` first.")
                return

        elif item['item_type'] == 'xp_boost_2h':
            # Add booster to inventory
            inventory = member_data.get('inventory', {})
            boosters = inventory.get('boosters', [])

            # Check if user already has an active booster
            now = datetime.now()
            active_booster = None
            for booster in boosters:
                if booster.get('active') and datetime.fromisoformat(booster['expires_at']) > now:
                    active_booster = booster
                    break

            if active_booster:
                await ctx.send("❌ You already have an active booster! Wait for it to expire first.")
                return

            # Deduct GMP and add booster
            member_data['gmp'] = user_gmp - item['price']
            expires_at = now + timedelta(hours=item['duration_hours'])

            booster = {
                'item_type': item['item_type'],
                'active': True,
                'purchased_at': now.isoformat(),
                'expires_at': expires_at.isoformat(),
                'xp_multiplier': 2.0,
                'gmp_multiplier': 2.0,
                'cooldown_reduction': 20  # Reduces cooldown from 30s to 10s
            }

            boosters.append(booster)
            inventory['boosters'] = boosters
            member_data['inventory'] = inventory

            self.bot.member_data.schedule_save()
            await self.bot.member_data.save_data_async()

            embed = discord.Embed(
                title="⚡ 2HR BOOSTER ACTIVATED",
                description=f"Your booster is now active for **2 hours**!\n\n"
                           f"**Benefits:**\n"
                           f"• 2x XP from messages\n"
                           f"• 2x GMP from messages\n"
                           f"• Cooldown reduced (30s → 10s)\n\n"
                           f"Expires: <t:{int(expires_at.timestamp())}:R>\n"
                           f"Remaining GMP: **{member_data['gmp']:,}**",
                color=0xFFD700
            )
            await ctx.send(embed=embed)

    @commands.command(name='inventory', aliases=['inv'])
    async def inventory(self, ctx):
        """View your active boosters"""
        member_data = self.bot.member_data.get_member_data(ctx.author.id, ctx.guild.id)
        inventory = member_data.get('inventory', {})
        boosters = inventory.get('boosters', [])

        # Filter active boosters
        now = datetime.now()
        active_boosters = []
        for booster in boosters:
            if booster.get('active') and datetime.fromisoformat(booster['expires_at']) > now:
                active_boosters.append(booster)

        embed = discord.Embed(
            title="📦 YOUR INVENTORY",
            description="Active boosters and items",
            color=0x599cff
        )

        if active_boosters:
            for idx, booster in enumerate(active_boosters, 1):
                expires_at = datetime.fromisoformat(booster['expires_at'])
                time_left = expires_at - now
                hours = int(time_left.total_seconds() // 3600)
                minutes = int((time_left.total_seconds() % 3600) // 60)

                embed.add_field(
                    name=f"⚡ 2HR BOOSTER #{idx}",
                    value=f"```\nTime Left: {hours}h {minutes}m\n"
                          f"XP Boost: 2x\n"
                          f"GMP Boost: 2x\n"
                          f"Cooldown: 10s```",
                    inline=False
                )
        else:
            embed.description = "```\nNo active boosters.\nVisit !shop to purchase items!```"

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ShopCommands(bot))
