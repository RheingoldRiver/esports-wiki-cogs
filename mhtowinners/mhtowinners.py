import rivercogutils as utils
from redbot.core import commands
from tsutils.user_interaction import StatusManager

from mhtowinners.mhtowinners_main import MhToWinnersRunner
from mhtowinners.sbtowinners_main import SbToWinnersRunner


class MhToWinners(commands.Cog):
    """Discovers & updates scoreboards on Leaguepedia that are missing vods"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(pass_context=True)
    async def mhtowinners(self, ctx):
        await ctx.send('Okay, starting now!')
        site = await utils.login_if_possible(ctx, self.bot, 'lol')
        try:
            async with StatusManager(self.bot):
                MhToWinnersRunner(site).run()
        except Exception as e:
            await ctx.send('Exception encountered, if Fandom servers are slow please wait a while to retry')
            print(e)
            return
        await ctx.send('Okay, done!')
    
    @commands.command(pass_context=True)
    async def sbtowinners(self, ctx):
        await ctx.send('Okay, starting now!')
        site = await utils.login_if_possible(ctx, self.bot, 'lol')
        try:
            async with StatusManager(self.bot):
                SbToWinnersRunner(site).run()
        except Exception as e:
            await ctx.send('Exception encountered, if Fandom servers are slow please wait a while to retry')
            print(e)
            return
        await ctx.send('Okay, done!')
