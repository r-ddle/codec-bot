"""
Intel cog - News and intelligence gathering commands.
"""
import discord
from discord.ext import commands
import aiohttp

from config.settings import NEWS_API_KEY, logger
from utils.rate_limiter import enforce_rate_limit


class Intel(commands.Cog):
    """Commands for gathering intel and news."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='intel')
    @enforce_rate_limit('intel')
    async def intel(self, ctx):
        """Get latest news as intelligence reports (US)."""
        try:
            if not NEWS_API_KEY or NEWS_API_KEY == 'your_news_api_key_here':
                await ctx.send("⚠️ Intel system offline - API key not configured")
                return

            params = {
                'apiKey': NEWS_API_KEY,
                'country': 'us',
                'pageSize': 3
            }

            # Use async HTTP request instead of blocking requests
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get('https://newsapi.org/v2/top-headlines', params=params, timeout=10) as response:
                    if response.status != 200:
                        await ctx.send("❌ Intel retrieval failed - API error")
                        return
                    data = await response.json()
                    news = data.get('articles', [])

                    if not news:
                        await ctx.send("📡 No intel available at this time.")
                        return

                    intel_report = discord.Embed(
                        title="📡 INTEL REPORT",
                        color=discord.Color.red()
                    )

                    for i, article in enumerate(news, 1):
                        intel_report.add_field(
                            name=f"Intel #{i}",
                            value=f"```{article['title']}```\n[Read more]({article['url']})",
                            inline=False
                        )

                    await ctx.send(embed=intel_report)
        except aiohttp.ClientError as e:
            await ctx.send("❌ Intel retrieval failed - Network error")
            logger.error(f"Intel command network error: {e}")
        except Exception as e:
            await ctx.send("❌ Intel retrieval failed - Unexpected error")
            logger.error(f"Intel command error: {e}", exc_info=True)


async def setup(bot):
    """Load the Intel cog."""
    await bot.add_cog(Intel(bot))
