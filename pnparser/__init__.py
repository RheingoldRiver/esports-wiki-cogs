from .pnparser import PatchNotesParser


def setup(bot):
    bot.add_cog(PatchNotesParser())
