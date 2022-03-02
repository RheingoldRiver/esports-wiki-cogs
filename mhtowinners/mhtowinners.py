from mwrogue.esports_client import EsportsClient
from requests import ReadTimeout
from rivercogutils import utils
from redbot.core import commands
from tsutils.user_interaction import StatusManager

from mhtowinners.mhtowinners_main import MhToWinnersRunner
from mhtowinners.sbtowinners_main import SbToWinnersRunner
from mhtowinners.vodstosb_main import VodsToSbRunner


class MhToWinners(commands.Cog):
    """Commands to update MatchSchedule & Scoreboards based on each other's data"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(pass_context=True)
    async def mhtowinners(self, ctx):
        self._do_the_thing(ctx, MhToWinnersRunner)
    
    @commands.command(pass_context=True)
    async def sbtowinners(self, ctx):
        self._do_the_thing(ctx, SbToWinnersRunner)
    
    @commands.command(pass_context=True)
    async def vodstosb(self, ctx):
        vod_params = ['VodPB', 'VodGameStart', 'Vod', 'VodPostgame']
        self._do_the_thing(ctx, VodsToSbRunner, vod_params)

    def _do_the_thing(self, ctx, the_thing, *args):
        await ctx.send('Okay, starting now!')
        credentials = await utils.get_credentials(ctx, self.bot)
        site = EsportsClient('lol', credentials=credentials,
                             max_retries=1, retry_interval=1)
        try:
            async with StatusManager(self.bot):
                the_thing(site, *args).run()
        except ReadTimeout:
            return await ctx.send('Whoops, the site is taking too long to respond, try again later')
        await ctx.send('Okay, done!')
