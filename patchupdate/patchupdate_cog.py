import asyncio
import json
import re
from io import BytesIO
from typing import Optional

import aiohttp
import rivercogutils as utils
from mwrogue.auth_credentials import AuthCredentials
from mwrogue.esports_client import EsportsClient
from redbot.core import commands

from patchupdate.champion_modifier import ChampionModifier
from patchupdate.item_modifier import ItemModifier

DDRAGON_V = "https://ddragon.leagueoflegends.com/api/versions.json"
DDRAGON = "http://ddragon.leagueoflegends.com/cdn/{}/data/en_US/{}.json"

TEMPLATE_MODIFIERS = {
    'champion': ChampionModifier,
    'item': ItemModifier,
}


async def updatestats(site: EsportsClient, section: str, version: Optional[str] = None):
    async with aiohttp.ClientSession() as session:
        if version is None:
            async with session.get(DDRAGON_V) as resp:
                version = json.loads(await resp.text())[0]
        elif not re.match(r'\d+\.\d+\.\d+', version):
            version += ".1"
        async with session.get(DDRAGON.format(version, section)) as resp:
            data = json.loads(await resp.text())['data']

    tm = TEMPLATE_MODIFIERS[section](site, "Infobox " + section.title(), data=data,
                                     summary=section.title() + " Update for " + version)

    await asyncio.get_event_loop().run_in_executor(None, tm.run)
    site.report_all_errors('patchupdate')


class PatchUpdate(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def red_get_data_for_user(self, *, user_id):
        """Get a user's personal data."""
        data = "No data is stored for user with ID {}.\n".format(user_id)
        return {"user_data.txt": BytesIO(data.encode())}

    async def red_delete_data_for_user(self, *, requester, user_id):
        """Delete a user's personal data.

        No personal data is stored in this cog.
        """
        return

    @commands.group()
    async def patchupdate(self, ctx):
        pass

    @patchupdate.command()
    async def championstats(self, ctx, version=None):
        await ctx.send("Okay, starting!")
        site = await utils.login_if_possible(ctx, self.bot, 'lol')
        async with ctx.typing():
            await updatestats(site, "champion", version)
        await ctx.send("Okay, done!")

    @patchupdate.command()
    async def itemstats(self, ctx, version=None):
        await ctx.send("Okay, starting!")
        site = await utils.login_if_possible(ctx, self.bot, 'lol')
        async with ctx.typing():
            await updatestats(site, "item", version)
        await ctx.send("Okay, done!")


if __name__ == "__main__":
    lolsite = EsportsClient('lol', credentials=AuthCredentials(user_file='me'))
    asyncio.run(updatestats(lolsite, "champion"))
    # asyncio.run(updatestats(lolsite, "item"))
