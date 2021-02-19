from dateutil.parser import parse as datetimeparser
from .data_dragon import DataDragon
from redbot.core import commands
from bs4 import BeautifulSoup
from datetime import datetime
import requests as client
import re as regex

BASE_ADDRESS = "https://na.leagueoflegends.com/en-us/news/game-updates/patch-{}-notes"


class PatchNotesParser(commands.Cog):
    def __init__(self):
        self.errors = ""

    @commands.group()
    async def pnparser(self, ctx):
        """A League of Legends patch notes parser"""

    @pnparser.command()
    async def report(self, ctx, message):
        """Report parser issues"""
        await ctx.send(self.patch_version)
        return  # TODO: Send myself a message

    @pnparser.group()
    async def parse(self, ctx):
        """Commands to parse League of Legends patch notes"""

    @parse.command()
    async def all(self, ctx, patch_version):
        """Parse the entire patch notes"""
        # validate patch notes version number format
        if not self.validate_patch(patch_version):
            return await ctx.send("Incorrect patch number format, "
                                  "use one of the following as the version separator: "
                                  "`. , -`")

        self.patch_url = BASE_ADDRESS.format(
            self.patch_version.replace('.', '-'))
        response = client.get(self.patch_url)

        # something went wrong
        if not response.status_code == 200:
            return await ctx.send("Expected response of type HTTP 200, "
                                  f"but got back {response.status_code}.")

        soup = BeautifulSoup(response.text, "html.parser")
        data_dragon = DataDragon(self.patch_version).load_data()
        self.published_date = datetimeparser(soup.time["datetime"]).date()

        # could not parse datetime
        if not self.published_date:
            self.errors += "WARNING: Could not parse patch notes publishing date.\n"

        # print results
        if not self.errors:
            await ctx.send("Patch notes parsed successfully.\n"
                           "See at: {placeholder}\n"
                           "To report issues with the parser use `^pnparser report <message>`.")
        else:
            await ctx.send(f"```{self.errors}```")

    @parse.command()
    async def midpatch(self, ctx, patch_version):
        """Patch mid-patch section from the specified patch notes"""
        return  # TODO: Parse mid-patch

    def validate_patch(self, patch_version):
        if regex.search(r"^\s*[1-9]{1,2}(\.|,|-)[1-9]{1,2}\s*$", patch_version):
            self.patch_version = patch_version.strip().replace(',', '.').replace('-', '.')
            return True
