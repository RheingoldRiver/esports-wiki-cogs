from .cargocreate import CargoCreate


async def setup(bot):
    n = CargoCreate(bot)
    bot.add_cog(n) if not __import__('asyncio').iscoroutinefunction(bot.add_cog) else await bot.add_cog(n)
