from redbot.core import commands
from rivercogutils import utils


class CargoCreate(commands.Cog):
    """Creates needed pages for a new Cargo table, and also creates the Cargo table"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(pass_context=True)
    async def cargocreate(self, ctx, wiki, table):
        site = await utils.login_if_possible(ctx, self.bot, wiki)
        await ctx.send('Okay, starting!')
        site.setup_tables(table)
        await ctx.send('Okay, done!')
