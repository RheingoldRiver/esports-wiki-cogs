from mwrogue.esports_client import EsportsClient
from rivercogutils import utils
from redbot.core import commands
from asyncio import TimeoutError

from .autorosters_main import AutoRostersRunner


class AutoRosters(commands.Cog):
    """Automatically generates team rosters for Leaguepedia, using scoreboard data"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def autorosters(self, ctx, *, overview_page):
        """Generate team rosters for the specified tournament"""
        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel
        await ctx.send("Tabs `Eg. LEC 2022`:")
        try:
            tabs = await self.bot.wait_for("message", check=check, timeout=60)
        except TimeoutError:
            return
        await ctx.send('Okay, starting now!')
        credentials = await utils.get_credentials(ctx, self.bot)
        site = EsportsClient('lol', credentials=credentials,
                             max_retries_mwc=0,
                             max_retries=2, retry_interval=10)
        AutoRostersRunner(site, overview_page, tabs.content).run()
        await ctx.send('Okay, done!')
