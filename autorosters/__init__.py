from .autorosters import AutoRosters


def setup(bot):
    bot.add_cog(AutoRosters(bot))
