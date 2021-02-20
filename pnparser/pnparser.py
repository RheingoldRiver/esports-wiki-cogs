from dateutil.parser import parse as datetimeparser
from .data_dragon import DataDragon
from redbot.core import commands
from bs4 import BeautifulSoup
from datetime import datetime
import requests as client
import re as regex

BASE_ADDRESS = "https://na.leagueoflegends.com/en-us/news/game-updates/patch-{}-notes"
CURRENT_VERSION = "0.1.0"


class PatchNotesParser(commands.Cog):

    def __init__(self):
        self.context = ""
        self.patch_url = ""
        self.patch_version = ""
        self.published_date = ""

    @commands.command()
    async def version(self, ctx):
        """Show package information"""
        await ctx.send(f"Current version is {CURRENT_VERSION}")

    @commands.group()
    async def pnparser(self, ctx):
        """A League of Legends patch notes parser"""

    @pnparser.command()
    async def report(self, ctx, message):
        """Report parser issues"""
        return await ctx.send("Thanks, for reporting your issue.")
        # TODO: Send myself a message

    @pnparser.group()
    async def ddragon(self, ctx):
        """Commands to get Data Dragon related information"""

    @ddragon.command()
    async def version(self, ctx):
        """Get the current version of the ddragon"""
        return await ctx.send(f"Current version of ddragon is `{DataDragon.current}`.")

    @ddragon.command()
    async def update(self, ctx):
        """Get the latest version of the Data Dragon from Riot"""
        current_version = DataDragon.current
        await DataDragon.load_data(ctx)

        # check if there was an update
        if current_version == DataDragon.current:
            return await ctx.send(f"Already up to date, latest version is `{current_version}`.")

    @pnparser.group()
    async def parse(self, ctx):
        """Commands to parse League of Legends patch notes"""

    @parse.command()
    async def all(self, ctx, patch_version):
        """Parse the entire patch notes"""

        # validate patch notes version number format
        if not self.__validate_patch(patch_version):
            return await ctx.send("Incorrect patch version number format, "
                                  "use one of the following as the version separator: "
                                  "`. , -`")

        self.patch_url = BASE_ADDRESS.format(
            self.patch_version.replace('.', '-'))
        response = client.get(self.patch_url)

        # something went wrong
        if not response.status_code == 200:
            return await ctx.send("`ERROR: Expected response of type HTTP 200, "
                                  f"but got back HTTP {response.status_code}.`")

        # assert ddragon is loaded
        await DataDragon.load_data(ctx)

        # load the html contents of the page
        soup = BeautifulSoup(response.text, "html.parser")

        # set the date the patch notes were published
        self.published_date = datetimeparser(soup.time["datetime"]).date()

        # gets the root div where all the patch notes are
        container = soup.find("div", {"class": "style__Content-tkcm0t-1"}
                              ).find_all(lambda tag: tag.name == "div")

        # patch notes context
        context = soup.find("blockquote", {"class": "context"}).text.strip()
        for text in context.split("\n")[:-1]:
            content = text.strip()
            if content and not content.isspace():
                self.context += f"{content}\n\n"
        self.context = self.context.rstrip()

        if len(container) == 0:
            return await ctx.send("`ERROR: Couldn't locate the main container.`")

        section = None
        border = None
        section_id = 1

        return await ctx.send("Patch notes parsed successfully.\n"
                              "See at: {placeholder}\n\n"
                              "To report issues with the parser use "
                              "`^pnparser report <message>`.")

    @parse.command()
    async def midpatch(self, ctx, patch_version):
        """Patch mid-patch section from the specified patch notes"""
        # TODO: Parse mid-patch

    def __validate_patch(self, patch_version):
        if regex.search(r"^\s*[1-9]{1,2}(\.|,|-)[1-9]{1,2}\s*$", patch_version):
            self.patch_version = patch_version.strip().replace(',', '.').replace('-', '.')
            return True
