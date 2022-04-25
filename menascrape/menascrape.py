from esports_cog_utils.utils import login_if_possible
from redbot.core import commands
from toornament_scraper.mena_creator import MenaCreator
from toornament_scraper.ff_checker import FFChecker
from toornament_scraper.mena_updater import MenaUpdater


class MenaScrape(commands.Cog):
    """Scrapes and updates MENA events."""
    
    def __init__(self, bot):
        self.bot = bot
        self.summary = 'Moving page + associated subpages'
    
    @commands.group()
    async def menascrape(self, ctx):
        """Scrapes and updates MENA events from Toornament website. Must add |scrape_link= to Infobox Tournament."""
    
    @menascrape.command()
    async def create(self, ctx, *, title):
        """Creates MatchSchedule code that you can then copy to Data namespace"""
        site = await login_if_possible(ctx, self.bot, 'lol')
        await ctx.send('Okay, starting now!')
        page_updated = MenaCreator(site, title).run()
        await ctx.send('Okay, done! See page <{}>'.format(page_updated))
    
    @menascrape.command()
    async def update(self, ctx, *, title):
        """Updates a live Data namespace page in place"""
        site = await login_if_possible(ctx, self.bot, 'lol')
        await ctx.send('Okay, starting now!')
        page_updated = MenaUpdater(site, title).run()
        await ctx.send('Okay, done! See page <{}>'.format(page_updated))
    
    @menascrape.command()
    async def checkff(self, ctx, *, title):
        """Checks for single-team FFs in place"""
        site = await login_if_possible(ctx, self.bot, 'lol')
        await ctx.send('Okay, starting now!')
        page_updated = FFChecker(site, title).run()
        await ctx.send('Okay, done! See page <{}>'.format(page_updated))
