from .pnparser import PatchNotesParser


def setup(bot: object) -> None:
    bot.add_cog(PatchNotesParser())
