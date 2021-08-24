import asyncio
import logging
from datetime import datetime
from io import BytesIO
from typing import Any, List, NoReturn, Optional

import aiohttp
import discord
import pytz
from dateutil.parser import isoparse
from discord import User
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import inline, pagify, text_to_file
from tsutils.cogs.globaladmin import auth_check, has_perm
from tsutils.helper_functions import repeating_timer
from tsutils.user_interaction import get_user_confirmation, send_cancellation_message

from bayesgamh.bayes_api_wrapper import BayesAPIWrapper, Game

logger = logging.getLogger('red.esports-wiki-cogs.bayesgahm')


async def is_editor(ctx) -> bool:
    GAMHCOG = ctx.bot.get_cog("BayesGAMH")
    return (ctx.author.id in ctx.bot.owner_ids
            or has_perm('mhadmin', ctx.author, ctx.bot)
            or await GAMHCOG.config.user(ctx.author).allowed_tags())


class BayesGAMH(commands.Cog):
    def __init__(self, bot: Red, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot

        self.session = aiohttp.ClientSession()
        self.config = Config.get_conf(self, identifier=847356477)
        self.config.register_global(seen=[])
        self.config.register_user(allowed_tags=[], subscriptions=[])

        self.api = BayesAPIWrapper(bot, self.session)

        self._loop = bot.loop.create_task(self.do_loop())
        self.subscription_lock = asyncio.Lock()

        gadmin: Any = self.bot.get_cog("GlobalAdmin")
        if gadmin:
            gadmin.register_perm('mhadmin')

    async def red_get_data_for_user(self, *, user_id):
        """Get a user's personal data."""
        if (subs := await self.config.user_from_id(user_id).subscriptions()):
            data = f"You are subscribed to the following tags: {', '.join(subs)}"
        else:
            data = "No data is stored for user with ID {}.\n".format(user_id)
        return {"user_data.txt": BytesIO(data.encode())}

    async def red_delete_data_for_user(self, *, requester, user_id):
        """Delete a user's personal data."""
        await self.config.user_from_id(user_id).subscriptions.set([])

    def cog_unload(self):
        self._loop.cancel()
        self.bot.loop.create_task(self.session.close())

    async def do_loop(self) -> NoReturn:
        async for _ in repeating_timer(60):
            try:
                await self.check_subscriptions()
            except Exception:
                logger.exception("Error in loop:")

    async def check_subscriptions(self) -> None:
        async with self.subscription_lock:
            seen = await self.config.seen()
            seeing = set(seen)
            for u_id, data in (await self.config.all_users()).items():
                if (user := self.bot.get_user(u_id)) is None:
                    continue
                if not (subs := data['subscriptions']):
                    continue
                games = await self.api.get_all_games(tags=subs)
                seeing.update(game['platformGameId'] for game in games)
                games = [game for game in games if game['platformGameId'] not in seen]
                msg = [await self.format_game(game, user)
                       for game in sorted(games, key=lambda g: isoparse(g['createdAt']))]
                for page in pagify('\n\n'.join(msg)):
                    await user.send(page)
            await self.config.seen.set(list(seeing))

    @commands.group()
    async def mhtool(self, ctx):
        """A subcommand for all Bayes GAMH commands"""

    @mhtool.group(name='tag', aliases=['tags'])
    @auth_check('mhadmin')
    async def mh_tag(self, ctx):
        """Grant adminstration to specific tags"""

    @mh_tag.command(name='add')
    async def mh_t_add(self, ctx, user: discord.User, *, tag):
        """Add an allowed tag to a user"""
        async with self.config.user(user).allowed_tags() as tags:
            if tag not in tags:
                tags.append(tag)
            else:
                return await ctx.send(f"{user} already has access to `{tag}`.")
        await ctx.tick()

    @mh_tag.command(name='remove', aliases=['rm', 'delete', 'del'])
    async def mh_t_remove(self, ctx, user: discord.User, *, tag):
        """Remove an allowed tag from a user"""
        async with self.config.user(user).allowed_tags() as tags:
            if tag in tags:
                tags.remove(tag)
            else:
                return await ctx.send(f"{user} already doesn't have access to `{tag}`.")
        await ctx.tick()

    @mh_tag.group(name='list')
    async def mh_t_list(self, ctx):
        """Listing subcommand"""

    @mh_t_list.command(name='users')
    async def mh_t_l_users(self, ctx, *, tag):
        """List all users who are allowed to edit a tag"""
        users = []
        for u_id, data in await self.config.all_users():
            if (user := self.bot.get_user(u_id)) and tag in data.get('tags', []):
                users.append(user)
        await ctx.send('\n'.join(users))

    @mh_t_list.command(name='all')
    async def mh_t_l_all(self, ctx):
        """List all available tags sorted alphabetically by length"""
        await ctx.send(', '.join(map(inline, sorted(await self.api.get_tags()))))

    @mh_t_list.command(name='inuse', aliases=['used'])
    async def mh_t_l_inuse(self, ctx):
        """List all in-use tags"""
        tags = {}
        for user, data in await self.config.all_users():
            tags.update(data.get('allowed_tags', []))
        await ctx.send(', '.join(map(inline, sorted(tags))))

    @mhtool.group(name='query')
    @commands.dm_only()
    @commands.check(is_editor)
    async def mh_query(self, ctx):
        """Query commands"""

    @mh_query.command(name='all')
    async def mh_q_all(self, ctx, limit: Optional[int], *, tag):
        """Get a list of the most recent `limit` games containing any of the listed tags

        If limit is left blank, all games are sent.
        """
        allowed_tags = await self.config.user(ctx.author).allowed_tags()
        if not (has_perm('mhadmin', ctx.author, self.bot) or tag in allowed_tags):
            return await ctx.send(f"You aren't allowed to use the tags: {tag}")
        games = sorted(await self.api.get_all_games(tag=tag), key=lambda g: isoparse(g['createdAt']), reverse=True)
        ret = [await self.format_game(game, ctx.author) for game in games[:limit][::-1]]
        if not ret:
            await ctx.send("There are no available games.  Check to make sure your tags are valid.")
        for page in pagify('\n\n'.join(ret)):
            await ctx.send(page)

    @mh_query.command(name='new')
    async def mh_q_new(self, ctx, limit: Optional[int], *, tag):
        """Something something new games maybe?"""
        allowed_tags = await self.config.user(ctx.author).allowed_tags()
        if not (has_perm('mhadmin', ctx.author, self.bot) or tag in allowed_tags):
            return await ctx.send(f"You aren't allowed to use the tags: {tag}")
        games = sorted(await self.api.get_all_games(tag=tag), key=lambda g: isoparse(g['createdAt']), reverse=True)
        games = await self.filter_new(games)
        ret = [await self.format_game(game, ctx.author) for game in games[:limit][::-1]]
        if not ret:
            await ctx.send("There are no available games.  Check to make sure your tags are valid.")
        for page in pagify('\n\n'.join(ret)):
            await ctx.send(page)

    @mh_query.command(name='getgame')
    async def mh_q_getgame(self, ctx, game_id):
        """Get a game by its game ID"""
        await ctx.send(await self.format_game(await self.api.get_game(game_id), ctx.author))

    @mh_query.command(name='getasset')
    async def mh_q_getasset(self, ctx, game_id, asset):
        """Get a match asset by game_id and asset name"""
        await ctx.send(file=text_to_file(
            (await self.api.get_asset(game_id, asset)).decode('utf-8'),  # TODO: Send PR to red to allow bytes
            filename=asset + '.json'))

    @mhtool.group(name='subscription', aliases=['subscriptions', 'subscribe'])
    async def mh_subscription(self, ctx):
        """Subscribe to a tag"""

    @mh_subscription.command(name='add')
    async def mh_s_add(self, ctx, *, tag):
        """Subscribe to a tag"""
        async with self.config.user(ctx.author).subscriptions() as subs:
            if tag in subs:
                return await ctx.send("You're already subscribed to that tag.")
            if has_perm('mhadmin', ctx.author, self.bot) and tag not in await self.api.get_tags():
                if not await get_user_confirmation(ctx, f"Are you sure you want to subscribe"
                                                        f" to currently non-existant tag `{tag}`?"):
                    return await ctx.react_quietly("\N{CROSS MARK}")
            elif not has_perm('mhadmin', ctx.author, self.bot) and tag not in await self.config.user(
                    ctx.author).allowed_tags():
                return await send_cancellation_message(ctx, f"You cannot subscribe to tag `{tag}` as you don't"
                                                            f" have permission to view it.  Contact a bot admin"
                                                            f" if you think this is an issue.")
            await self.check_subscriptions()
            seen = {game['platformGameId'] for game in await self.api.get_all_games(tag=tag)}
            await self.config.seen.set(list(seen.union(await self.config.seen())))
            subs.append(tag)
        await ctx.tick()

    @mh_subscription.command(name='remove', aliases=['rm', 'delete', 'del'])
    async def mh_s_remove(self, ctx, *, tag):
        """Unsubscribe yourself from a tag"""
        async with self.config.user(ctx.author).subscriptions() as subs:
            if tag not in subs:
                return await ctx.send("You're not subscribed to that tag.")
            subs.remove(tag)
        await ctx.tick()

    @mh_subscription.command(name='list')
    async def mh_s_list(self, ctx):
        """List your subscribed tags"""
        subs = await self.config.user(ctx.author).subscriptions()
        if not subs:
            return await ctx.send("You are not subscribed to any tags.")
        await ctx.send(f"You are subscribed to the following tags: {', '.join(map(inline, subs))}")

    @mh_subscription.command(name='clear', aliases=['purge'])
    async def mh_s_clear(self, ctx):
        if not await get_user_confirmation(ctx, "Are you sure you want to clear all of your subscriptions?"):
            return await ctx.react_quietly("\N{CROSS MARK}")
        await self.config.user(ctx.author).subscriptions.set([])
        await ctx.tick()

    async def format_game(self, game: Game, user: User) -> str:
        return (f"`{game['platformGameId']}` - Name: {game['name']} ({game['status']})\n"
                f"\tStart Time: {(await self.parse_date(game['createdAt'], user)).strftime('%X %Z on %A %B %d, %Y')}\n"
                f"\tTags: {', '.join(map(inline, sorted(game['tags'])))}\n"
                f"\tAvailable Assets:{', '.join(map(inline, game['assets']))}")

    async def parse_date(self, datestr: str, user: User) -> datetime:
        date = isoparse(datestr)
        cog: Any = self.bot.get_cog("UserPreferences")
        if cog is None:
            return date
        return date.astimezone(await cog.get_user_timezone(user) or pytz.UTC)

    async def filter_new(self, games: List[Game]) -> List[Game]:
        """Returns only 'new' games from a list of games."""
        return games  # TODO: River needs to write this
