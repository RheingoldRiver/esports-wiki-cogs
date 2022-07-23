from .patchupdate_cog import PatchUpdate


async def setup(bot):
    n = PatchUpdate(bot)
    bot.add_cog(n) if not __import__('asyncio').iscoroutinefunction(bot.add_cog) else await bot.add_cog(n)
