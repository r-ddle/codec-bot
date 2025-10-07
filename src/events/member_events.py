"""
Member events - Handlers for member join and ready events.
"""
import discord
from discord.ext import commands
from datetime import datetime, timezone

from config.settings import WELCOME_CHANNEL_ID, logger


class MemberEvents(commands.Cog):
    """Event handlers for member-related activities."""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """Bot ready event handler."""
        print(f"✅ {self.bot.user} is now online and ready!")
        print(f" Connected to {len(self.bot.guilds)} guilds")
        
        for guild in self.bot.guilds:
            guild_key = str(guild.id)
            if guild_key in self.bot.member_data.data:
                member_count = len(self.bot.member_data.data[guild_key])
                print(f" Guild '{guild.name}' ({guild.id}): {member_count} members loaded")
            else:
                print(f" Guild '{guild.name}' ({guild.id}): New guild, no existing data")
        
        print(" Bot is fully ready and operational!")
        print(" XP-based ranking system active!")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Welcome system for new members."""
        logger.info(f"NEW MEMBER JOINED: {member.name} (ID: {member.id}) in {member.guild.name}")
        
        try:
            self.bot.member_data.get_member_data(member.id, member.guild.id)
            self.bot.member_data.mark_member_verified(member.id, member.guild.id)
            
            welcome_channel = None
            
            if WELCOME_CHANNEL_ID:
                welcome_channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
            
            if not welcome_channel:
                for channel_name in ['welcome', 'general', 'main', 'chat']:
                    welcome_channel = discord.utils.get(member.guild.text_channels, name=channel_name)
                    if welcome_channel:
                        break
            
            if not welcome_channel:
                for channel in member.guild.text_channels:
                    if channel.permissions_for(member.guild.me).send_messages:
                        welcome_channel = channel
                        break
            
            if not welcome_channel:
                logger.warning(f"No suitable welcome channel found in {member.guild.name}")
                return
            
            embed = discord.Embed(
                title=" NEW OPERATIVE DETECTED",
                description=f"**{member.display_name}** has joined Mother Base!",
                color=0x5865F2
            )
            
            embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            
            embed.add_field(
                name="STARTING RESOURCES",
                value="```\n Rank: Rookie\n GMP: 1,000\n XP: 0\n```",
                inline=True
            )
            
            embed.add_field(
                name="QUICK START",
                value="```\n!gmp - Check status\n!daily - Get bonus\n!info - Commands\n```",
                inline=True
            )
            
            embed.add_field(
                name="RANK UP INFO",
                value="**Earn XP to unlock Discord roles!**\nFirst promotion: **Private** role at 100 XP",
                inline=False
            )
            
            embed.set_image(url="https://images-ext-1.discordapp.net/external/znqAGtNjrN09-n-59N5jJGCNJSBIJwYB31d8qzAzXYI/https/media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExdzVqMTFjZXNyZWh6cDA3eGc3YjJuMmUxdjl0Yml6cnhobjlxZzZrMyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/CacxhprRlavR0AveWN/giphy.gif?width=960&height=540")
            
            embed.set_footer(text=f"Joined: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
            
            await welcome_channel.send(f" **Welcome to Mother Base, {member.mention}!**", embed=embed)
            logger.info(f"Welcome sent to #{welcome_channel.name} for {member.name}")
            
            await self.bot.member_data.save_data_async()
            
        except Exception as e:
            logger.error(f"Error in welcome system: {e}", exc_info=True)


async def setup(bot):
    """Load the MemberEvents cog."""
    await bot.add_cog(MemberEvents(bot))
