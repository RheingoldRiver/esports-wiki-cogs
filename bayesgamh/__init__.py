from .bayesgamh import BayesGAMH

__red_end_user_data_statement__ = "This cog stores your subscriptions to specific tags."


def setup(bot):
    bot.add_cog(BayesGAMH(bot))
