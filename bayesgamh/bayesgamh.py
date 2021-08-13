import logging
from io import BytesIO
from typing import Any

import aiohttp
import discord
from dateutil.parser import isoparse
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import inline, pagify
from tsutils import auth_check

from bayesgamh.bayes_api_wrapper import BayesAPIWrapper

logger = logging.getLogger('red.aradiacogs.bayesgahm')


class BayesGAMH(commands.Cog):
    def __init__(self, bot: Red, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot

        self.session = aiohttp.ClientSession()
        self.config = Config.get_conf(self, identifier=847356477)
        self.config.register_user(admin=False, allowed_tags=[])

        self.api = BayesAPIWrapper(bot, self.session)

        GACOG: Any = self.bot.get_cog("GlobalAdmin")
        if GACOG:
            GACOG.register_perm("mhtoolgrant")

    async def red_get_data_for_user(self, *, user_id):
        """Get a user's personal data."""
        data = "No data is stored for user with ID {}.\n".format(user_id)
        return {"user_data.txt": BytesIO(data.encode())}

    async def red_delete_data_for_user(self, *, requester, user_id):
        """Delete a user's personal data.

        No personal data is stored in this cog.
        """
        return

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    @commands.group()
    async def mhtool(self, ctx):
        """A subcommand for all Bayes GAMH commands"""

    @auth_check("mhtoolgrant")
    @mhtool.group()
    async def admin(self, ctx):
        """Administration commands"""

    @admin.command(name='add')
    async def mh_a_add(self, ctx, user: discord.User):
        """Grant GAMH admin priveleges to a user"""
        await self.config.user(user).admin.set(True)
        await ctx.tick()

    @admin.command(name='remove', aliases=['rm', 'delete', 'del'])
    async def mh_a_remove(self, ctx, user: discord.User):
        """Remove GAMH admin priveleges from a user"""
        await self.config.user(user).admin.set(False)
        await ctx.tick()

    @admin.group(name='tag')
    async def mh_a_tag(self, ctx):
        """Grant adminstration to specific tags"""

    @mh_a_tag.command(name='add')
    async def mh_a_t_add(self, ctx, tag, user: discord.User):
        """Add an allowed tag to a user"""
        async with self.config.user(user).allowed_tags as tags:
            if tag not in tags:
                tags.append(tag)
            else:
                return await ctx.send(f"{user} already has access to `{tag}`.")
        await ctx.tick()

    @mh_a_tag.command(name='remove', aliases=['rm', 'delete', 'del'])
    async def mh_a_t_remove(self, ctx, tag, user: discord.User):
        """Remove an allowed tag from a user"""
        async with self.config.user(user).allowed_tags as tags:
            if tag in tags:
                tags.remove(tag)
            else:
                return await ctx.send(f"{user} already doesn't have access to `{tag}`.")
        await ctx.tick()

    @mh_a_tag.group(name='list')
    async def mh_a_t_list(self, ctx):
        """Listing subcommand"""

    @mh_a_t_list.command(name='users')
    async def mh_a_t_l_users(self, ctx, tag):
        """List all users who are allowed to edit a tag"""
        users = []
        for u_id, data in await self.config.all_users():
            if (user := self.bot.get_user(u_id)) and tag in data.get('tags', []):
                users.append(user)
        await ctx.send('\n'.join(users))

    @mh_a_t_list.command(name='valid')
    async def mh_a_t_l_valid(self, ctx):
        """List all available tags sorted alphabetically by length"""
        await ctx.send(', '.join(map(inline, await self.sort_tags(await self.api.get_tags()))))

    @mh_a_t_list.command(name='invalid')
    async def mh_a_t_l_invalid(self, ctx):
        """List all invalid tags caught by the tag filter"""
        all_tags = await self.api.get_tags()
        valid_tags = await self.sort_tags(all_tags)
        sorted_invalid_tags = sorted(set(all_tags).difference(valid_tags), key=lambda tag: (len(tag), tag))
        await ctx.send(', '.join(map(inline, sorted_invalid_tags)))

    @mh_a_t_list.command(name='inuse', aliases=['used'])
    async def mh_a_t_l_inuse(self, ctx):
        """List all in-use tags"""
        tags = {}
        for user, data in await self.config.all_users():
            tags.update(data.get('allowed_tags', []))
        await ctx.send(', '.join(map(inline, await self.sort_tags(tags))))

    @mhtool.group(name='query')
    @commands.dm_only()
    async def mh_query(self, ctx):
        """Query commands"""

    @mh_query.command(name='all')
    async def mh_q_all(self, ctx, *tags: str):
        """Get a list of all games containing any of the listed tags"""
        full_admin = self.config.user(ctx.author).admin()
        allowed_tags = await self.config.user(ctx.author).allowed_tags()
        if not (await self.is_admin(ctx) or all(tag in allowed_tags for tag in tags)):
            return await ctx.send("You aren't allowed to use the following tags: "
                                  + ", ".join(map(inline, set(tags).difference(allowed_tags))))
        games = await self.api.get_all_games(tags=tags)
        ret = [f"{game['name']} - ID: {game['platformGameId']} ({game['status']})\n"
               f"\tStart Time: {isoparse(game['createdAt']).strftime('%X %Z on %A %B %d, %Y')}\n"
               f"\tTags: {', '.join(map(inline, game['tags']))}\n"
               f"\tAvailable Assets:{', '.join(map(inline, game['assets']))}"
               for game in games]
        if not ret:
            await ctx.send("There are no available games.  Something is probably wrong.")
        for page in pagify('\n\n'.join(ret)):
            await ctx.send(page)

    @mh_query.command(name='new')
    async def mh_q_new(self, ctx, *tags: str):
        """Something something new games maybe?"""
        allowed_tags = await self.config.user(ctx.author).allowed_tags()
        if not (await self.is_admin(ctx) or all(tag in allowed_tags for tag in tags)):
            return await ctx.send("You aren't allowed to use the following tags: "
                                  + ", ".join(map(inline, set(tags).difference(allowed_tags))))
        games = await self.api.get_all_games(tags=tags)
        games = [game for game in games if True]  # TODO: Add some sort of validation.  Wiki API or smth?
        ret = [f"{game['name']} - ID: {game['platformGameId']} ({game['status']})\n"
               f"\tStart Time: {isoparse(game['createdAt']).strftime('%X %Z on %A %B %d, %Y')}\n"
               f"\tTags: {', '.join(map(inline, game['tags']))}\n"
               f"\tAvailable Assets:{', '.join(map(inline, game['assets']))}"
               for game in games]
        if not ret:
            await ctx.send("There are no available games.  Something is probably wrong.")
        for page in pagify('\n\n'.join(ret)):
            await ctx.send(page)

    @mh_query.command(name='getasset')
    async def mh_q_getasset(self, ctx, game_id, asset):
        """Get a match asset by game_id and asset name"""
        await ctx.send(file=discord.File(await self.api.get_asset(game_id, asset), filename=asset + '.json'))

    async def sort_tags(self, tags):
        return sorted(tags, key=lambda t: (len(t), t))  # TODO: Filter tags somehow

    async def is_admin(self, user) -> bool:
        GACOG: Any = self.bot.get_cog("GlobalAdmin")
        is_gadmin = False
        if GACOG:
            is_gadmin = GACOG.settings.get_perm(user.id, "mhtoolgrant")
        return user.id in self.bot.owner_ids or is_gadmin or await self.config.user(user).admin()
