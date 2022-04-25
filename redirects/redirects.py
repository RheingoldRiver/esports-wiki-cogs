from esports_cog_utils.utils import login_if_possible
from mwrogue.esports_client import EsportsClient
from redbot.core import commands


class Redirects(commands.Cog):
    """Fixes double redirects based on the wiki's Special:DoubleRedirects report"""
    
    def __init__(self, bot):
        self.bot = bot
        self.summary = 'Fixing double redirect, requested via Namibot'
    
    @commands.group(pass_context=True)
    async def redirects(self, ctx):
        pass
    
    @redirects.command(pass_context=True)
    async def double(self, ctx, wiki):
        site = await login_if_possible(ctx, self.bot, wiki)
        site: EsportsClient
        if site is None:
            return
        result = site.client.api(action="query", list="querypage", qppage="DoubleRedirects")
        for item in result['query']['querypage']['results']:
            source_page = site.client.pages[item['title']]
            
            # the following code is only used because miser mode is enabled:
            target_title_1 = site.target(source_page.name)
            target_title_2 = site.target(target_title_1)
            
            # the following code would be used if miser mode were not enabled:
            
            # target_title = item['databaseResult']['c_title']
            # target_namespace_number = int(item['databaseResult']['c_namespace'])
            # target_namespace = site.client.namespaces[int(target_namespace_number)]
            # target_page_name = '{}{}'.format(
            #     target_namespace + ':' if target_namespace != '' else '',
            #     target_title
            # )
            
            # site.save(source_page, text='#redirect[[%s]]' % target_title_2, summary=self.summary)
        
        return await ctx.send("Okay, should be done!")