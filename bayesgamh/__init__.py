from .bayesgamh import BayesGAMH

__red_end_user_data_statement__ = "This cog stores your subscriptions to specific tags."


async def setup(bot):
    n = BayesGAMH(bot)
    bot.add_cog(n) if not __import__('asyncio').iscoroutinefunction(bot.add_cog) else await bot.add_cog(n)
