from patchnotesparser.exceptions import ParserError, ParserHttpError, ParserTimeoutError
from patchnotesparser.templates.designer import Designer
from patchnotesparser.patch_notes import PatchNotes
from patchnotesparser.dragon import Dragon

from redbot.core.commands import GuildContext
from redbot.core.utils.tunnel import Tunnel
from redbot.core import commands, Config
from redbot.core.bot import Red

from discord.guild import Guild, TextChannel
import rivercogutils as RiverCogUtils
import re as Regex

CURRENT_VERSION: str = "0.8.0"
            

class PatchNotesParser(commands.Cog):
    """Parses League of Legends patch notes to Wiki format"""

    def __init__(self, bot: 'Red') -> None:
        self.bot: 'Red' = bot
        self.patch_notes: 'PatchNotes | None' = None
        self.bug_fix_channel: 'TextChannel | None' = None
        self.config: Config = Config.get_conf(self, identifier=5527993091442, force_registration=True)
        self._register_config()

    # register all the config variables
    def _register_config(self) -> None:
        self.config.register_global(bug_fix_channel = None)
        self.config.register_global(patch_notes = None)

    # try to set the bug report channel
    async def _try_set_bug_report_channel(self, guild: Guild) -> bool:
        for channel in guild.text_channels:
            if channel.id == await self.config.bug_fix_channel():
                self.bug_fix_channel = channel
                return True
        return False
        
    async def _auto_report(self, ctx: GuildContext, message: str, patch_notes: PatchNotes) -> None:
        # TODO: remove embeded patch notes info
        content: str = "Patch notes parser **auto report** from command " \
                    f"`{ctx.message.system_content}` executed at " \
                    f"*{ctx.guild.name} - #{ctx.channel.name}:*\n" \
                    f"https://discord.com/channels/{ctx.guild.id}/" \
                    f"{ctx.channel.id}/{ctx.message.id}\n" \
                    f"```fix\n{message}\n```" \
                    "\n**Additional information**\n" \
                    f"Patch notes: {patch_notes.patch_url}\n```python\n" \
                    f"Cog version: {CURRENT_VERSION}\n" \
                    f"Data Dragon version: {Dragon.current_version}\n```"
        
        # check if the channel is loaded from the configuration
        if await self._try_set_bug_report_channel(ctx.guild) and self.bug_fix_channel is not None:
            await Tunnel.message_forwarder(destination=self.bug_fix_channel, content=content)
            await ctx.send("Something went wrong and I could not parse.\n"
                           "An automatic error report was generated and "
                           "someone will look into it.")
        else:
            await ctx.send("Could not send auto generated report to the default bug fix channel.\n"
                           "Please verify that you have set the default channel by running `^pnparser get bugreportchannel`.\n"
                           f"\n\nThe error report is as follows: \n {content}")


    def _validate_patch(self, patch_version: str) -> bool:
        if Regex.search(r'^\s*[1-9]{1,2}(\.|,|-)[1-9]{1,2}\s*$', patch_version):
            self.patch_version = patch_version.strip().replace(',', '.').replace('-', '.')
            return True
        return False

    @commands.group()
    async def pnparser(self, ctx: GuildContext) -> None:
        """A League of Legends patch notes parser"""
        pass

    @pnparser.group()
    async def set(self, ctx: GuildContext) -> None:
        """Set COG settings"""
        pass

    @set.command(name="bugreportchannel")
    async def set_bug_report_channel(self, ctx: GuildContext, channel_id: int) -> None:
        """Sets the default bug fix channel for error reports"""

        if channel_id > 0:
            await self.config.bug_fix_channel.set(channel_id)
            if await self._try_set_bug_report_channel(ctx.guild):
                await ctx.send("Channel set for auto generated bug reports.")
            else:
                await ctx.send("Could not set the default bug report channel. Please verify the provided id.")
                await self.config.bug_fix_channel.set(None)
        else:
            await ctx.send("Invalid channel guild id.")

    @pnparser.group()
    async def get(self, ctx:GuildContext) -> None:
        """Get COG settings"""
        pass

    @get.command(name="bugreportchannel")
    async def get_bug_report_channel(self, ctx: GuildContext) -> None:
        """Gets the default bug fix channel for error reports"""
        await ctx.send(f"Current bug report channel id is `{await self.config.bug_fix_channel()}`.")

    @pnparser.command()
    async def version(self, ctx: GuildContext) -> None:
        """Show package information"""
        await ctx.send(f"Current version is {CURRENT_VERSION}.")

    @pnparser.command()
    async def report(self, ctx: GuildContext, *message: str) -> None:
        """Report parser issues"""
        # TODO: remove embeded patch notes info
        content: str = "Patch notes parser error reported by " \
                    f"**{ctx.author.display_name}** in " \
                    f"*{ctx.guild.name} - #{ctx.channel.name}:*\n" \
                    f"https://discord.com/channels/{ctx.guild.id}/" \
                    f"{ctx.channel.id}/{ctx.message.id}\n{' '.join(message)}\n" \
                    "\n**Additional information**\n" \
                    f"Patch notes: {self.patch_notes.patch_url}\n```python\n" \
                    f"Cog version: {CURRENT_VERSION}\n" \
                    f"Data Dragon version: {Dragon.current_version}\n```"
                    
        if await self._try_set_bug_report_channel(ctx.guild) and self.bug_fix_channel is not None:
            await Tunnel.message_forwarder(destination=self.bug_fix_channel, content=content)
            await ctx.send("Thank you for reporting this issue.\n"
                            "Someone will look into it and might get in touch "
                            "to let you know when it is fixed.")
        else:
            await ctx.send("Could not send report to the default bug fix channel.\n"
                           "Please verify that you have set the default channel by running `^pnparser get bugreportchannel`.\n"
                           f"\n\nThe error report is as follows: \n {content}")

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
    async def geticon(self, ctx: GuildContext, *designer_name: str) -> None:
        """Get the icon used for the specified designer"""
        try:
            await ctx.send(f"`{Designer.get_designer_icon(' '.join(designer_name))}`")
        except KeyError:
            await ctx.send("Designer not found.")

    #@designer.command()
    #async def seticon(self, ctx: GuildContext, designer_name: str, designer_icon: str) -> None:
    #    """Set a new icon for the specified designer"""
    #    # TODO: Set new icon
    #    pass

    #@designer.command()
    #async def add(self, ctx: GuildContext, designer_name: str, designer_icon: str) -> None:
    #    """Add a new designer and icon"""
    #    Designer.add_designer(designer_name, designer_icon)
    #    await ctx.send(f"Designer {designer_name} added successfully.")

    @pnparser.group()
    async def dragon(self, ctx: GuildContext) -> None:
        """Commands to get information related to dragon"""
        pass

    @dragon.command("version")
    async def dragon_version(self, ctx: GuildContext) -> None:
        """Get the current version number"""
        await ctx.send(f"Current version of dragon is `{Dragon.current_version}`.")

    @dragon.command()
    async def update(self, ctx: GuildContext) -> None:
        """Get the latest version from Riot"""
        current_version: 'str | None' = Dragon.current_version
        Dragon.load_data()

        # check if there was an update
        if current_version == Dragon.current_version:
            await ctx.send(f"Already up to date, latest version is `{current_version}`.")
        else: await ctx.send(f"Updated dragon to version `{Dragon.current_version}`.")

    @pnparser.group()
    async def parse(self, ctx: GuildContext) -> None:
        """Commands to parse League of Legends patch notes"""
        pass

    #@parse.command()
    #async def midpatch(self, ctx: GuildContext, patch_version: str) -> None:
    #    """Parse the mid-patch section from the specified patch notes"""

    #    # TODO: Parse mid-patch
    #    # validate patch notes version number format
    #    if not self._validate_patch(patch_version):
    #        await ctx.send("Incorrect patch notes version number format.")
    #        return

    @parse.command()
    async def all(self, ctx: GuildContext, patch_version: str) -> None:
        """Parse the entire specified patch notes"""
        
        # validate patch notes version number format
        if not self._validate_patch(patch_version):
            await ctx.send("Incorrect patch notes version number format.")
            return
        
        site = await RiverCogUtils.login_if_possible(ctx, self.bot, 'lol')

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

        except ParserTimeoutError as e:
            self.patch_notes = e.patch_notes
            await ctx.send(e.message)

        # give detailed report to devs
        except ParserError as e:
            await self._auto_report(ctx, e.message, e.patch_notes)
