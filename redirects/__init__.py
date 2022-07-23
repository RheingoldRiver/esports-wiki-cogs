from .redirects import Redirects


async def setup(bot):
    n = Redirects(bot)
    bot.add_cog(n) if not __import__('asyncio').iscoroutinefunction(bot.add_cog) else await bot.add_cog(n)
