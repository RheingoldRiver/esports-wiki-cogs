from esports_cog_utils.utils import get_credentials
from mwrogue.esports_client import EsportsClient
from requests import ReadTimeout
from redbot.core import commands
from tsutils.user_interaction import StatusManager

from mhtowinners.sbtowinners_main import SbToWinnersRunner
from mhtowinners.vodstosb_main import VodsToSbRunner


class MhToWinners(commands.Cog):
    """Commands to update MatchSchedule & Scoreboards based on each other's data"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def sbtowinners(self, ctx, *, title_list):
        title_list = [title.split() for title in title_list.split(",")]
        await self._do_the_thing(ctx, SbToWinnersRunner, title_list)

    async def _do_the_thing(self, ctx, the_thing, *args):
        await ctx.send('Okay, starting now!')
        credentials = await get_credentials(ctx, self.bot)
        site = EsportsClient('lol', credentials=credentials,
                             max_retries_mwc=0,
                             max_retries=2, retry_interval=10)
        try:
            async with StatusManager(self.bot):
                the_thing(site, *args).run()
        except ReadTimeout:
            return await ctx.send('Whoops, the site is taking too long to respond, try again later')
        await ctx.send('Okay, done!')
