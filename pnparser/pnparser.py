from requests import ReadTimeout
from .parser_errors import ParserError, ParserHttpError
from .patch_notes import PatchNotes
from .templates import Designer
from .dragon import Dragon

from redbot.core.commands import GuildContext
from redbot.core.utils.tunnel import Tunnel
from redbot.core import commands
import rivercogutils as utils
import re as Regex

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from river_mwclient.esports_client import EsportsClient
    from discord.guild import Guild
    from redbot.core.bot import Red


CURRENT_VERSION: str = "0.1.0"
            

class PatchNotesParser(commands.Cog):
    """Parses League of Legends patch notes to Wiki format"""

    def __init__(self, bot: 'Red') -> None:
        self.bot: 'Red' = bot
        self.patch_notes: 'PatchNotes | None' = None
        
        guild: 'Guild | None' = bot.get_guild(529775376721903617)
        if guild is not None:
            for channel in guild.text_channels:
                if channel.name == "feature-bug-disc":
                    self.bug_fix_channel = channel
                    break
    
    async def __auto_report(self, ctx: GuildContext, message: str, patch_notes: PatchNotes) -> None:
        # TODO: remove embeded patch notes info
        await Tunnel.message_forwarder(destination=self.bug_fix_channel,
                                       content="Patch notes parser **auto report** from command "
                                       f"`{ctx.message.system_content}` executed at "
                                       f"*{ctx.guild.name} - #{ctx.channel.name}:*\n"
                                       f"https://discord.com/channels/{ctx.guild.id}/"
                                       f"{ctx.channel.id}/{ctx.message.id}\n"
                                       f"```fix\n{message}\n```"
                                       "\n**Additional information**\n"
                                       f"Patch notes: {patch_notes.patch_url}\n```python\n"
                                       f"Cog version: {CURRENT_VERSION}\n"
                                       f"Data Dragon version: {Dragon.current_version}\n```")
        await ctx.send("Something went wrong and I could not parse.\n"
                       "An automatic error report was generated and "
                       "someone will look into it.")

    def __validate_patch(self, patch_version: str) -> bool:
        if Regex.search(r'^\s*[1-9]{1,2}(\.|,|-)[1-9]{1,2}\s*$', patch_version):
            self.patch_version = patch_version.strip().replace(',', '.').replace('-', '.')
            return True
        return False

    @commands.group()
    async def pnparser(self, ctx: GuildContext) -> None:
        """A League of Legends patch notes parser"""
        pass

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
                                       "\n**Additional information**\n"
                                       f"Patch notes: {self.patch_notes.patch_url}\n```python\n"
                                       f"Cog version: {CURRENT_VERSION}\n"
                                       f"Data Dragon version: {Dragon.current_version}\n```")
        await ctx.send("Thank you for reporting this issue.\n"
                       "Someone will look into it and might get in touch "
                       "to let you know when it is fixed.")

    @pnparser.command()
    async def reparse(self, ctx: GuildContext) -> None:
        """Reparse the last parsed patch notes"""
        if not self.patch_notes.patch_version:
            await ctx.send("Could not reparse. "
                           "Please specify the patch version by calling "
                           "`^pnparser parse all <patch_version>`.")
            return
        await ctx.send(f"Reparsing patch notes version `{self.patch_notes.patch_version}`.")
        await self.all(ctx, self.patch_notes.patch_version)

    @pnparser.group()
    async def designer(self, ctx: GuildContext) -> None:
        """Commands to get information related to patch notes designers"""
        pass

    @designer.command()
    async def geticon(self, ctx: GuildContext, designer_name: str) -> None:
        """Get the icon used for the specified designer"""
        await ctx.send(f"`{Designer.get_designer_icon(designer_name)}`")

    @designer.command()
    async def seticon(self, ctx: GuildContext, designer_name: str, designer_icon: str) -> None:
        """Set a new icon for the specified designer"""
        # TODO: Set new icon
        pass

    @designer.command()
    async def add(self, ctx: GuildContext, designer_name: str, designer_icon: str) -> None:
        """Add a new designer and icon"""
        Designer.add_designer(designer_name, designer_icon)
        await ctx.send(f"Designer {designer_name} added successfully.")

    @pnparser.group()
    async def dragon(self, ctx: GuildContext) -> None:
        """Commands to get information related to ddragon"""
        pass

    @dragon.command("version")
    async def dragon_version(self, ctx: GuildContext) -> None:
        """Get the current version number"""
        await ctx.send(f"Current version of ddragon is `{Dragon.current_version}`.")

    @dragon.command()
    async def update(self, ctx: GuildContext) -> None:
        """Get the latest version from Riot"""
        current_version: 'str | None' = Dragon.current_version
        Dragon.load_data()

        # check if there was an update
        if current_version == Dragon.current_version:
            await ctx.send(f"Already up to date, latest version is `{current_version}`.")
        else: await ctx.send(f"Updated ddragon to version `{current_version}`.")

    @pnparser.group()
    async def parse(self, ctx: GuildContext) -> None:
        """Commands to parse League of Legends patch notes"""
        pass

    @parse.command()
    async def midpatch(self, ctx: GuildContext, patch_version: str) -> None:
        """Parse the mid-patch section from the specified patch notes"""

        # TODO: Parse mid-patch
        # validate patch notes version number format
        if not self.__validate_patch(patch_version):
            await ctx.send("Incorrect patch notes version number format.")
            return

    @parse.command()
    async def all(self, ctx: GuildContext, patch_version: str) -> None:
        """Parse the entire specified patch notes"""
        
        # validate patch notes version number format
        if not self.__validate_patch(patch_version):
            await ctx.send("Incorrect patch notes version number format.")
            return
        
        site: 'EsportsClient' = await utils.login_if_possible(ctx, self.bot, 'lol')

        try:
            # parse
            await ctx.send("Parsing...")
            self.patch_notes = PatchNotes(site).parse_all(patch_version)

            # parsing complete
            await ctx.send("Patch notes parsed successfully.\n"
                        f"See at: https://lol.gamepedia.com/{self.patch_notes.page_url}\n\n"
                        "To report issues with the parser use "
                        "`^pnparser report <message>`.")

        except ParserHttpError as e:
            pass

        # give detailed report to devs
        except ParserError as e:
            await self.__auto_report(ctx, e.message, e.patch_notes)

        except ReadTimeout:
            await ctx.send("Whoops, the site is taking too long to respond, try again later.")