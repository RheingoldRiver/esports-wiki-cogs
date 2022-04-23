from mwrogue.esports_client import EsportsClient
from rivercogutils import utils
from redbot.core import commands

from .autorosters_main import AutoRostersRunner


async def is_lol_staff(ctx) -> bool:
    staff_role = None
    if not ctx.guild:
        raise commands.UserFeedbackCheckFailure("You must be in a server to run this command!")
    for role in ctx.message.guild.roles:
        if role.name == "LoL-Staff":
            staff_role = role
            break
    if staff_role not in ctx.author.roles:
        raise commands.UserFeedbackCheckFailure("You don't have enough permissions to run this command!")
    return True


class AutoRosters(commands.Cog):
    """Automatically generates team rosters for Leaguepedia, using scoreboard data"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    @commands.check(is_lol_staff)
    async def autorosters(self, ctx, *, overview_page):
        """Generate team rosters for the specified tournament"""
        await ctx.send('Okay, starting now!')
        credentials = await utils.get_credentials(ctx, self.bot)
        site = EsportsClient('lol', credentials=credentials,
                             max_retries_mwc=0,
                             max_retries=2, retry_interval=10)
        overview_page = site.cache.get_target(overview_page)
        if not site.client.pages[overview_page].exists:
            return await ctx.send('The tournament page does not exist!')
        warnings = AutoRostersRunner(site, overview_page).run()
        username = site.credentials.username
        username = username.split('@')[0] if "@" in username else username
        sandbox_page = f"\nhttps://lol.fandom.com/wiki/User:{username}/Team_Rosters_Sandbox".replace(" ", "_")
        rosters_page = f"\nhttps://lol.fandom.com/wiki/{overview_page}/Team_Rosters".replace(" ", "_")
        await ctx.send('Okay, done! **Remember the generated content has no coaches!**')
        await ctx.send(f'Here is the sandbox page with the new content: {sandbox_page}')
        await ctx.send(f'Here is where you should copy it: {rosters_page}')
        if warnings:
            for warning in warnings:
                await ctx.send(f"**{warning}**")
