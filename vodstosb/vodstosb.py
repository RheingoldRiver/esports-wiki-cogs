import rivercogutils as utils
from redbot.core import commands
from requests.exceptions import ReadTimeout
from tsutils.user_interaction import StatusManager

from vodstosb.vodstosb_main import VodsToSbRunner


class VodsToSb(commands.Cog):
    """Discovers & updates scoreboards on Leaguepedia that are missing vods"""
    
    def __init__(self, bot, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bot = bot
        self.vod_params = ['VodPB', 'VodGameStart', 'Vod', 'VodPostgame']
        self.pages_to_save = {}
    
    @commands.command(pass_context=True)
    async def vodstosb(self, ctx):
        site = await utils.login_if_possible(ctx, self.bot, 'lol')
        
        await ctx.send('Okay, starting now!')
        try:
            async with StatusManager(self.bot):
                VodsToSbRunner(site, self.vod_params).run()
        except ReadTimeout:
            await ctx.send('Whoops, the site is taking too long to respond, try again later')
            return
        await ctx.send('Okay, done!')
