from redbot.core import commands
import rivercogutils as utils
from .fncheckresults_main import check_results


class FnCheckResults(commands.Cog):
    """
    Checks results for the Fortnite esports wiki
    """
    
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(pass_context=True)
    async def fncheckresults(self, ctx, *, title):
        site = await utils.login_if_possible(ctx, self.bot, 'fortnite')
        await ctx.send('Okay, starting!')
        result = check_results(site, title)
        if len(result) == 0:
            await ctx.send('Everything looks good!')
            return
        await ctx.send('Uhoh, there\'s some problems, printing...')
        for item in result:
            await ctx.send('Player: {} Team: {}'.format(
                item['Player'],
                item['Team']
            ))
        await ctx.send('Done')
