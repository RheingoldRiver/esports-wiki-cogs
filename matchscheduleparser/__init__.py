from .matchscheduleparser import MatchScheduleParser


async def setup(bot):
    n = MatchScheduleParser(bot)
    bot.add_cog(n) if not __import__('asyncio').iscoroutinefunction(bot.add_cog) else await bot.add_cog(n)