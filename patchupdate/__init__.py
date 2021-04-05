from .patchupdate_cog import PatchUpdate


def setup(bot):
    bot.add_cog(PatchUpdate(bot))
