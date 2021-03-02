from dateutil import parser as DatetimeParser
from datetime import datetime as DateTime
from typing import Iterator

from redbot.core.commands import GuildContext
from redbot.core.utils.tunnel import Tunnel
from redbot.core import commands
from redbot.core.bot import Red
from discord.guild import Guild

from bs4 import BeautifulSoup, Tag

import requests as HttpClient
import re as Regex

from .ddragon import DataDragon
from .models import *

BASE_ADDRESS: str = "https://na.leagueoflegends.com/en-us/news/game-updates/patch-{}-notes"
CURRENT_VERSION: str = "0.1.0"


class PatchNotesParser(commands.Cog):

    def __init__(self, bot: Red) -> None:
        self.context: str = ""
        self.patch_version: str = ""
        self.sections: 'list[Section]' = []
        self.patch_url: 'str | None' = None
        self.published_date = DateTime.now()
        self.designers: 'list[Designer]' = []

        # set the bugfix request channel
        guild: 'Guild | None' = bot.get_guild(529775376721903617)
        if isinstance(guild, Guild):
            for channel in guild.text_channels:
                if channel.name == "feature-bug-disc":
                    self.bug_fix_channel = channel
                    break

    def __validate_patch(self, patch_version: str) -> bool:
        if Regex.search(r'^\s*[1-9]{1,2}(\.|,|-)[1-9]{1,2}\s*$', patch_version):
            self.patch_version = patch_version.strip().replace(',', '.').replace('-', '.')
            return True
        return False

    async def __auto_report(self, ctx: GuildContext, message: str) -> None:
        # TODO: remove embeded patch notes info
        await Tunnel.message_forwarder(destination=self.bug_fix_channel,
                                       content="Patch notes parser **auto report** from command "
                                       f"`{ctx.message.system_content}` executed at "
                                       f"*{ctx.guild.name} - #{ctx.channel.name}:*\n"
                                       f"https://discord.com/channels/{ctx.guild.id}/"
                                       f"{ctx.channel.id}/{ctx.message.id}\n"
                                       f"```fix\n{message}\n```"
                                       f"\n**Additional information**\n"
                                       f"Patch notes: {self.patch_url}\n```python\n"
                                       f"Cog version: {CURRENT_VERSION}\n"
                                       f"Data Dragon version: {DataDragon.current_version}\n```")
        await ctx.send("Something went wrong and I could not parse.\n"
                       "An automatic error report was generated and "
                       "someone will look into it.")

    @commands.group()
    async def pnparser(self, ctx: GuildContext) -> None:
        """A League of Legends patch notes parser"""

    @pnparser.command()
    async def version(self, ctx: GuildContext) -> None:
        """Show package information"""
        await ctx.send(f"Current version is {CURRENT_VERSION}.")

    @pnparser.command()
    async def report(self, ctx: GuildContext, *message: str) -> None:
        """Report parser issues"""
        await Tunnel.message_forwarder(destination=self.bug_fix_channel,
                                       content="Patch notes parser error reported by "
                                       f"**{ctx.author.display_name}** in "
                                       f"*{ctx.guild.name} - #{ctx.channel.name}:*\n"
                                       f"https://discord.com/channels/{ctx.guild.id}/"
                                       f"{ctx.channel.id}/{ctx.message.id}\n{' '.join(message)}\n"
                                       f"\n**Additional information**\n"
                                       f"Patch notes: {self.patch_url}\n```python\n"
                                       f"Cog version: {CURRENT_VERSION}\n"
                                       f"Data Dragon version: {DataDragon.current_version}\n```")
        await ctx.send("Thank you for reporting this issue.\n"
                       "Someone will look into it and might get in touch "
                       "to let you know when it is fixed.")

    @pnparser.command()
    async def reparse(self, ctx: GuildContext) -> None:
        """Reparse the last parsed patch notes"""
        if not self.patch_version:
            await ctx.send("Could not reparse. "
                           "Please specify the patch version by calling "
                           "`^pnparser parse all <patch_version>`.")
            return
        await ctx.send(f"Reparsing patch notes version `{self.patch_version}`.")
        await self.all(ctx, self.patch_version)

    @pnparser.group()
    async def designer(self, ctx: GuildContext) -> None:
        """Commands to get information related to patch notes designers"""

    @designer.command()
    async def geticon(self, ctx: GuildContext, designer_name: str) -> None:
        """Get the icon used for the specified designer"""
        await ctx.send(f"`{Designer.get_designer_icon(designer_name)}`")

    @designer.command()
    async def seticon(self, ctx: GuildContext, designer_name: str, designer_icon: str) -> None:
        """Set a new icon for the specified designer"""
        # TODO: Set new icon

    @designer.command()
    async def add(self, ctx: GuildContext, designer_name: str, designer_icon: str) -> None:
        """Add a new designer and icon"""
        Designer.add_designer(designer_name, designer_icon)
        await ctx.send(f"Designer {designer_name} added successfully.")

    @pnparser.group()
    async def ddragon(self, ctx: GuildContext) -> None:
        """Commands to get information related to ddragon"""

    @ddragon.command("version")
    async def ddragon_version(self, ctx: GuildContext) -> None:
        """Get the current version number"""
        await ctx.send(f"Current version of ddragon is `{DataDragon.current_version}`.")

    @ddragon.command()
    async def update(self, ctx: GuildContext) -> None:
        """Get the latest version from Riot"""
        current_version: 'str | None' = DataDragon.current_version
        await DataDragon.load_data(ctx)

        # check if there was an update
        if current_version == DataDragon.current_version:
            await ctx.send(f"Already up to date, latest version is `{current_version}`.")

    @pnparser.group()
    async def parse(self, ctx: GuildContext) -> None:
        """Commands to parse League of Legends patch notes"""

    @parse.command()
    async def all(self, ctx: GuildContext, patch_version: str) -> None:
        """Parse the entire specified patch notes"""

        # validate patch notes version number format
        if not self.__validate_patch(patch_version):
            await ctx.send("Incorrect patch notes version number format.")
            return

        self.patch_url = BASE_ADDRESS.format(
            self.patch_version.replace('.', '-'))
        response = HttpClient.get(self.patch_url)

        # something went wrong
        if not response.status_code == 200:
            # TODO: Try trice and then report
            await ctx.send("Expected response of type `HTTP 200`, "
                           f"but got back `HTTP {response.status_code}`.")
            return

        # assert ddragon is loaded
        await DataDragon.load_data(ctx)

        # load the html contents of the page
        soup = BeautifulSoup(response.text, "html.parser")

        # set the date the patch notes were published
        time: 'Tag | None' = soup.find("time")
        if time is not None:
            self.published_date = DatetimeParser.parse(time["datetime"]).date()
        else:
            return await self.__auto_report(ctx, "Could not get article published date.")

        # patch notes context
        context: 'Tag | None' = soup.find("blockquote", {"class": "context"})
        for line in context.text.strip().split("\n")[:-1]:
            line_text: str = line.strip()
            if line_text and not line_text.isspace():
                self.context += f"{line_text}\n\n"
        self.context = self.context.rstrip()

        # patch notes designers
        designer_elements: 'list[Tag]' = soup.find_all(
            "span", {"class": "context-designer"})
        for designer_span in designer_elements:
            designer = Designer(designer_span.text.strip().title())
            if designer.username is None:
                return await self.__auto_report(ctx, f"Could not extract username from `context-designer`. "
                                                "Please report this issue using "
                                                "`^ pnparser report <message>`.")
            if designer.icon is None:
                # TODO: Somehow try to automate this process
                return await self.__auto_report(ctx, f"Could not parse {designer.username}'s designer icon.\n"
                                                "Use `^pnparser designer seticon <designer_name> <designer_icon>` "
                                                "to add a new designer and icon to my database.")
            self.designers.append(designer)

        # gets the root div where all the patch notes are
        root: 'Tag | None' = soup.find(
            "div", {"class": "style__Content-tkcm0t-1"})
        if root is None:
            return await self.__auto_report(ctx, "Could not locate the main patch notes `<div>`.")

        section_id: int = 1
        border: 'Border | None' = None
        section: 'Section | None' = None
        # https://github.com/microsoft/pylance-release/issues/993
        container: 'list[Tag]' = root.find_all("div", recursive=False)

        if len(container) == 1:
            # everything is under "patch-notes-container"
            # it isn't always like this though
            container = list(filter(lambda tag:
                                    isinstance(tag, Tag) and
                                    tag.has_attr("class"),
                                    container[0].children))
        for tag in container:
            if tag.name == "header" and "header-primary" in tag["class"]:
                section = Section(section_id, tag.text.strip().title())
                self.sections.append(section)
                section_id += 1
                border = None
            elif tag.name == "div" and "content-border" in tag["class"]:
                if section is None:
                    return await self.__auto_report(ctx, 'HTML node with `class="content-border"` '
                                                    'found before the `"header-primary"` was defined.')

                content_list: Iterator[Tag] = filter(lambda tag:
                                                     isinstance(tag, Tag) and
                                                     tag.has_attr("class"),
                                                     tag.div.div.children)

                # handles mid-patch updates
                if section.title == "Mid-Patch Updates":
                    await self.__midpatch(ctx, border, section, content_list)
        await ctx.send("Patch notes parsed successfully.\n"
                       "See at: {placeholder}\n\n"
                       "To report issues with the parser use "
                       "`^pnparser report <message>`.")

    async def __midpatch(self, ctx: GuildContext, border: 'Border | None', section: Section, content_list: Iterator[Tag]) -> None:
        change: 'Pnb | None' = None
        ability: 'Pai | None' = None

        # loop through all the mid-patch updates
        for content in content_list:
            if "change-title" in content["class"]:
                # border is not defined or its title is
                # different from the current border title
                if border is None or border.title != content.text.strip():
                    border = Border(content.text.strip())
                    section.borders.append(border)
                    continue

            # could not find the border title
            if border.title is None or str.isspace(border.title):
                return await self.__auto_report(ctx, "Could not locate an HTML node with class 'change-title'.")

            # border context text
            elif "content" in content["class"]:
                border.contexxt = content.text.strip()
            # attribute is from a champion ability
            elif "ability-title" in content["class"]:
                change = Pnb(content.text.strip())
                border.changes.append(change)

            # handles champion or item attribute change
            elif "attribute-change" in content["class"]:
                attribute: 'Pbc | None' = None

                if change is None:
                    return await self.__auto_report(ctx, 'HTML node with class="attribute-change" '
                                                    'found before the first "ability-title" was defined.')

                # get all the properties of the current attribute
                for attribute_info in content.children:
                    if attribute_info["class"] == "attribute":
                        attribute_name: str = attribute_info.text.strip()
                        await ctx.send(attribute_name)

    @parse.command()
    async def midpatch(self, ctx: GuildContext, patch_version: str) -> None:
        """Parse the mid-patch section from the specified patch notes"""
        # TODO: Parse mid-patch
