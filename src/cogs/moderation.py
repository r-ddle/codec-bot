"""
Moderation cog - Commands for server moderation (kick, ban, clear).
"""
import discord
from discord.ext import commands
from datetime import datetime, timezone
from typing import Optional
import traceback

from config.constants import CONTACT_ADMINS
from config.settings import logger


class Moderation(commands.Cog):
    """Commands for server moderation."""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='kick')
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: Optional[str] = None):
        """Kick a member with MGS-style message and DM."""
        if member is None:
            await ctx.send(" Please specify a member to kick!")
            return
        
        if member == ctx.author:
            await ctx.send(" You cannot kick yourself!")
            return
        
        if member.guild_permissions.administrator:
            await ctx.send(" Cannot kick administrators!")
            return
        
        if member.top_role >= ctx.guild.me.top_role:
            await ctx.send(" Cannot kick this member - they have higher or equal role!")
            return
        
        try:
            # Send DM first
            dm_sent = False
            try:
                dm_embed = discord.Embed(
                    title=" EXTRACTION NOTICE",
                    description=f"```\n> MISSION STATUS: TERMINATED\n> OPERATIVE EXTRACTED FROM MOTHER BASE\n> SERVER: {ctx.guild.name}\n> OPERATOR: {ctx.author.name}\n```",
                    color=discord.Color.red(),
                    timestamp=datetime.now(timezone.utc)
                )
                
                if reason:
                    dm_embed.add_field(
                        name="EXTRACTION REASON",
                        value=f"```\n{reason}\n```",
                        inline=False
                    )
                else:
                    dm_embed.add_field(
                        name="EXTRACTION REASON",
                        value="```\nNo specific reason provided\n```",
                        inline=False
                    )
                
                # Add contact information
                contact_list = "\n".join([f" {admin}" for admin in CONTACT_ADMINS])
                dm_embed.add_field(
                    name=" CONTACT FOR REINSTATEMENT",
                    value=f"```\nIf you believe this extraction was an error,\ncontact any of these Mother Base commanders:\n\n{contact_list}\n```",
                    inline=False
                )
                
                dm_embed.add_field(
                    name="COMMANDER MESSAGE",
                    value="```\nYour mission at Mother Base has been terminated.\nContact command if you believe this is an error.\n```",
                    inline=False
                )
                
                await member.send(embed=dm_embed)
                dm_sent = True
                logger.info(f"DM sent to {member.name}")
                
            except discord.Forbidden:
                logger.warning(f"Cannot send DM to {member.name} - DMs disabled")
                dm_sent = False
            except Exception as e:
                logger.error(f"Error sending DM to {member.name}: {e}")
                dm_sent = False
            
            # Kick the member
            kick_reason = f"Kicked by {ctx.author.name}" + (f" - {reason}" if reason else "")
            await member.kick(reason=kick_reason)
            logger.info(f"Successfully kicked {member.name}")
            
            # Send public embed with GIF
            public_embed = discord.Embed(
                title=" OPERATIVE EXTRACTED",
                description=f"```\n> EXTRACTION COMPLETE\n> TARGET: {member.name}#{member.discriminator}\n> USER ID: {member.id}\n> STATUS: REMOVED FROM MOTHER BASE\n```",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            
            if reason:
                public_embed.add_field(
                    name="EXTRACTION REASON",
                    value=f"```\n{reason}\n```",
                    inline=False
                )
            else:
                public_embed.add_field(
                    name="EXTRACTION REASON",
                    value="```\nNo specific reason provided\n```",
                    inline=False
                )
            
            public_embed.add_field(
                name="OPERATION DETAILS",
                value=f"```\nExtracted by: {ctx.author.display_name}\nDM Notification: {' Sent' if dm_sent else ' Failed'}\nTime: {datetime.now(timezone.utc).strftime('%H:%M:%S')} UTC\n```",
                inline=False
            )
            
            # Add contact info to public message
            contact_list = "  ".join(CONTACT_ADMINS)
            public_embed.add_field(
                name=" REINSTATEMENT CONTACTS",
                value=f"```\nFor appeals or reinstatement:\n{contact_list}\n```",
                inline=False
            )
            
            # Add the kick GIF
            public_embed.set_image(url="https://i.gifer.com/5ZJM.gif")
            public_embed.set_footer(text="Mother Base security protocol executed successfully")
            
            await ctx.send(embed=public_embed)
            logger.info(f"Kick message sent to #{ctx.channel.name}")
            
        except discord.Forbidden:
            await ctx.send(" **OPERATION FAILED**: I don't have permission to kick this member!")
        except discord.HTTPException as e:
            await ctx.send(f" **EXTRACTION FAILED**: {str(e)}")
        except Exception as e:
            await ctx.send(f" **UNEXPECTED ERROR**: {str(e)}")
            logger.error(f"Error in kick command: {e}")
            traceback.print_exc()

    @commands.command(name='ban')
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: Optional[str] = None):
        """Ban a member with MGS-style message."""
        if member is None:
            await ctx.send(" Please specify a member to ban!")
            return
        
        if member == ctx.author:
            await ctx.send(" You cannot ban yourself!")
            return
        
        if member.guild_permissions.administrator:
            await ctx.send(" Cannot ban administrators!")
            return
        
        if member.top_role >= ctx.guild.me.top_role:
            await ctx.send(" Cannot ban this member - they have higher or equal role!")
            return
        
        try:
            # Try to send DM first
            dm_sent = False
            try:
                dm_embed = discord.Embed(
                    title=" TERMINATION NOTICE",
                    description=f"```\n> MISSION STATUS: PERMANENTLY TERMINATED\n> OPERATIVE BANNED FROM MOTHER BASE\n> SERVER: {ctx.guild.name}\n> OPERATOR: {ctx.author.name}\n```",
                    color=discord.Color.dark_red(),
                    timestamp=datetime.now(timezone.utc)
                )
                
                if reason:
                    dm_embed.add_field(
                        name="TERMINATION REASON",
                        value=f"```\n{reason}\n```",
                        inline=False
                    )
                else:
                    dm_embed.add_field(
                        name="TERMINATION REASON",
                        value="```\nNo specific reason provided\n```",
                        inline=False
                    )
                
                dm_embed.add_field(
                    name="FINAL MESSAGE",
                    value="```\nYour access to Mother Base has been permanently revoked.\nThis decision is final.\n```",
                    inline=False
                )
                
                await member.send(embed=dm_embed)
                dm_sent = True
                
            except:
                dm_sent = False
            
            # Ban the member
            ban_reason = f"Banned by {ctx.author.name}" + (f" - {reason}" if reason else "")
            await member.ban(reason=ban_reason)
            
            # Send public embed
            embed = discord.Embed(
                title=" OPERATIVE TERMINATED",
                description=f"```\n> TERMINATION COMPLETE\n> TARGET: {member.name}#{member.discriminator}\n> USER ID: {member.id}\n> STATUS: PERMANENTLY BANNED\n```",
                color=discord.Color.dark_red(),
                timestamp=datetime.now(timezone.utc)
            )
            
            if reason:
                embed.add_field(
                    name="TERMINATION REASON",
                    value=f"```\n{reason}\n```",
                    inline=False
                )
            
            embed.add_field(
                name="OPERATION DETAILS",
                value=f"```\nTerminated by: {ctx.author.display_name}\nDM Notification: {' Sent' if dm_sent else ' Failed'}\nTime: {datetime.now(timezone.utc).strftime('%H:%M:%S')} UTC\n```",
                inline=False
            )
            
            embed.set_footer(text="Mother Base security protocol - permanent termination")
            
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await ctx.send(" **OPERATION FAILED**: I don't have permission to ban this member!")
        except discord.HTTPException as e:
            await ctx.send(f" **TERMINATION FAILED**: {str(e)}")
        except Exception as e:
            await ctx.send(f"❌ **UNEXPECTED ERROR**: {str(e)}")

    @commands.command(name='clear')
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int = 5):
        """Clear messages with MGS-style confirmation."""
        if amount < 1 or amount > 100:
            await ctx.send(" Amount must be between 1 and 100!")
            return
        
        try:
            deleted = await ctx.channel.purge(limit=amount + 1)  # +1 to include the command message
            
            embed = discord.Embed(
                title=" DATA PURGE COMPLETE",
                description=f"```\n> OPERATION: MESSAGE ELIMINATION\n> TARGET CHANNEL: #{ctx.channel.name}\n> RECORDS DELETED: {len(deleted) - 1}\n> OPERATOR: {ctx.author.display_name}\n> STATUS: SUCCESS\n```",
                color=0x00ff00
            )
            
            confirmation = await ctx.send(embed=embed)
            await confirmation.delete(delay=5)
            
        except discord.Forbidden:
            await ctx.send(" **OPERATION FAILED**: I don't have permission to delete messages!")
        except Exception as e:
            await ctx.send(f" **PURGE FAILED**: {str(e)}")


async def setup(bot):
    """Load the Moderation cog."""
    await bot.add_cog(Moderation(bot))
