"""
Intel cog - News and intelligence gathering commands.
"""
import discord
from discord.ext import commands
import requests

from config.settings import NEWS_API_KEY, logger


class Intel(commands.Cog):
    """Commands for gathering intel and news."""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='intel')
    async def intel(self, ctx):
        """Get latest news as intelligence reports (US)."""
        try:
            params = {
                'apiKey': NEWS_API_KEY,
                'country': 'us',
                'pageSize': 3
            }
            response = requests.get('https://newsapi.org/v2/top-headlines', params=params)
            news = response.json().get('articles', [])
            
            if not news:
                await ctx.send(" No intel available at this time.")
                return

            intel_report = discord.Embed(
                title=" INTEL REPORT ",
                color=discord.Color.red()
            )
            
            for i, article in enumerate(news, 1):
                intel_report.add_field(
                    name=f"Intel #{i}",
                    value=f"```{article['title']}```\n[Read more]({article['url']})",
                    inline=False
                )
                
            await ctx.send(embed=intel_report)
        except Exception as e:
            await ctx.send(" Intel retrieval failed")
            logger.error(f"Intel command error: {e}")


async def setup(bot):
    """Load the Intel cog."""
    await bot.add_cog(Intel(bot))
