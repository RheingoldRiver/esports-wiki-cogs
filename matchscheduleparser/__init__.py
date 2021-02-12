from .matchscheduleparser import MatchScheduleParser


def setup(bot):
    bot.add_cog(MatchScheduleParser())
