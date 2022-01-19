import asyncio
import json
import logging
import time
from collections import defaultdict
from datetime import datetime
from io import BytesIO
from typing import Any, List, NoReturn

import aiohttp
import discord
from dateutil.parser import isoparse
from discord import DMChannel, TextChannel, User
from mwrogue.esports_client import EsportsClient
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.commands import UserInputOptional
from redbot.core.utils.chat_formatting import box, inline, pagify, text_to_file
from rivercogutils import login_if_possible
from tsutils.cogs.globaladmin import auth_check, has_perm
from tsutils.helper_functions import repeating_timer
from tsutils.user_interaction import cancellation_message, confirmation_message, get_user_confirmation, \
    send_cancellation_message

from bayesgamh.bayes_api_wrapper import AssetType, BayesAPIWrapper, Game

logger = logging.getLogger('red.esports-wiki-cogs.bayesgamh')


async def is_editor(ctx) -> bool:
    GAMHCOG = ctx.bot.get_cog("BayesGAMH")
    return (ctx.author.id in ctx.bot.owner_ids
            or has_perm('mhadmin', ctx.author, ctx.bot)
            or await GAMHCOG.config.user(ctx.author).allowed_tags())


async def is_dm_or_whitelisted(ctx) -> bool:
    GAMHCOG = ctx.bot.get_cog("BayesGAMH")
    if not (isinstance(ctx.channel, DMChannel)
            or str(ctx.channel.id) in await GAMHCOG.config.allowed_channels()):
        raise commands.UserFeedbackCheckFailure("This command is only available in"
                                                " DMs or whitelisted channels.")
    return True


class BayesGAMH(commands.Cog):
    def __init__(self, bot: Red, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot

        self.session = aiohttp.ClientSession()
        self.config = Config.get_conf(self, identifier=847356477)
        self.config.register_global(seen={}, allowed_channels={})
        self.config.register_user(allowed_tags={}, subscriptions={}, jsononly=True)

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
        await self.config.user_from_id(user_id).subscriptions.set({})

    def cog_unload(self):
        self._loop.cancel()
        self.bot.loop.create_task(self.session.close())

    async def do_loop(self) -> NoReturn:
        try:
            async for _ in repeating_timer(60):
                try:
                    await self.check_subscriptions()
                except asyncio.CancelledError:
                    raise
                except Exception:
                    logger.exception("Error in loop:")
        except asyncio.CancelledError:
            return

    async def check_subscriptions(self) -> None:
        async with self.subscription_lock, self.config.seen() as seen:
            tags_to_uid = defaultdict(set)
            for u_id, data in (await self.config.all_users()).items():
                for sub in data['subscriptions']:
                    tags_to_uid[sub].add(u_id)

            changed_games = []
            for game in await self.api.get_all_games():
                if seen.get(game['platformGameId'], -1) != len(game['assets']):  # Different number of assets
                    changed_games.append(game)
                    seen[game['platformGameId']] = len(game['assets'])

            for u_id, data in (await self.config.all_users()).items():
                if (user := self.bot.get_user(u_id)) is None:
                    logger.warning(f"Failed to find user with ID {u_id} for subscription.")
                    continue
                msg = [await self.format_game_long(game, user)
                       for game in sorted([game for game in changed_games
                                           if any(u_id in tags_to_uid[tag].union(tags_to_uid['ALL'])
                                                  for tag in game['tags'])
                                           and ('GAMH_DETAILS' in game['assets'] or not data['jsononly'])],
                                          key=lambda g: isoparse(g['createdAt']))]
                try:
                    for page in pagify('\n\n'.join(msg)):
                        await user.send(page)
                except discord.Forbidden:
                    logger.warning(f"Unable to send subscription message to user {user}. (Forbidden)")

    @commands.group()
    @commands.check(is_editor)
    @commands.check(is_dm_or_whitelisted)
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
                tags[tag] = {'date': time.time()}
            else:
                return await ctx.send(f"{user} already has access to `{tag}`.")
        await ctx.tick()

    @mh_tag.command(name='remove', aliases=['rm', 'delete', 'del'])
    async def mh_t_remove(self, ctx, user: discord.User, *, tag):
        """Remove an allowed tag from a user"""
        async with self.config.user(user).allowed_tags() as tags:
            if tag in tags:
                tags.pop(tag)
            else:
                return await ctx.send(f"{user} already doesn't have access to `{tag}`.")
        await ctx.tick()

    @mh_tag.group(name='list')
    async def mh_t_list(self, ctx):
        """Listing subcommand"""

    @mh_t_list.command(name='users')
    async def mh_t_l_users(self, ctx, *, tag=None):
        """List all users who are allowed to edit a specific tag

        Leave tag unfilled to get a list of all users who are able to edit any tag
        """
        users = []
        if tag is not None:
            for u_id, data in (await self.config.all_users()).items():
                if (user := self.bot.get_user(u_id)) and tag in data.get('allowed_tags', {}):
                    users.append({'user': user, 'date': data['allowed_tags'][tag].get('date', 0)})

            if not users:
                return await ctx.send("No users have been assigned this tag.")
            users.sort(key=lambda d: d['date'])
            for page in pagify('\n'.join(f"{d['user'].mention}"
                                         f" {datetime.fromtimestamp((d['date'])).strftime('%Y %b %-d')}"
                                         for d in users)):
                await ctx.send(page, allowed_mentions=discord.AllowedMentions(users=False))
        else:
            for u_id, data in (await self.config.all_users()).items():
                if (user := self.bot.get_user(u_id)):
                    for tag, tdata in data.get('allowed_tags', {}).items():
                        users.append({'user': user, 'tag': tag, 'date': tdata.get('date', 0)})

            if not users:
                return await ctx.send("No users have been assigned any tag.")
            users.sort(key=lambda d: (d['user'].mention, d['date']))
            for page in pagify('\n'.join(f"{d['user'].mention} `{d['tag']}`"
                                         f" {datetime.fromtimestamp((d['date'])).strftime('%Y %b %-d')}"
                                         for d in users)):
                await ctx.send(page, allowed_mentions=discord.AllowedMentions(users=False))

    @mh_t_list.command(name='all')
    async def mh_t_l_all(self, ctx):
        """List all available tags sorted alphabetically by length"""
        for page in pagify(', '.join(map(inline, sorted(await self.api.get_tags()))), delims=[', ']):
            await ctx.send(page.strip(', '))

    @mh_t_list.command(name='inuse', aliases=['used'])
    async def mh_t_l_inuse(self, ctx):
        """List all in-use tags"""
        tags = set()
        for user, data in (await self.config.all_users()).items():
            tags.update(data.get('allowed_tags', {}))
        if not tags:
            return await ctx.send("There are no in use tags.")
        for page in pagify(', '.join(map(inline, sorted(tags))), delims=[', ']):
            await ctx.send(page.strip(', '))

    @mh_t_list.command(name='invalid')
    async def mh_t_l_invalid(self, ctx):
        """List all currently invalid tags"""
        tags = set()
        for user, data in (await self.config.all_users()).items():
            tags.update(data.get('allowed_tags', {}))
        tags.difference_update(await self.api.get_tags())
        if not tags:
            return await ctx.send("There are no invalid tags.")
        for page in pagify(', '.join(map(inline, sorted(tags))), delims=[', ']):
            await ctx.send(page.strip(', '))

    @mhtool.group(name='query')
    async def mh_query(self, ctx):
        """Query commands"""

    @mh_query.command(name='all')
    async def mh_q_all(self, ctx, limit: UserInputOptional[int] = 50, *, tag):
        """Get a list of the most recent `limit` games with the provided tag

        If limit is left blank, 50 games are sent.
        """
        allowed_tags = await self.config.user(ctx.author).allowed_tags()
        if not (has_perm('mhadmin', ctx.author, self.bot) or tag in allowed_tags or 'ALL' in allowed_tags):
            return await ctx.send(f"You do not have permission to query the tag `{tag}`.")
        games = sorted(await self.api.get_all_games(tag=tag), key=lambda g: isoparse(g['createdAt']), reverse=True)
        ret = [await self.format_game(game, ctx.author) for game in games[:limit][::-1]]
        if not ret:
            return await ctx.send(f"There are no games with tag `{tag}`."
                                  f" Make sure the tag is valid and correctly cased.")
        for page in pagify('\n\n'.join(ret), delims=['\n\n']):
            await ctx.send(page)

    @mh_query.command(name='new')
    async def mh_q_new(self, ctx, limit: UserInputOptional[int] = 50, *, tag):
        """Get only games that aren't on the wiki yet"""
        allowed_tags = await self.config.user(ctx.author).allowed_tags()
        if not (has_perm('mhadmin', ctx.author, self.bot) or tag in allowed_tags or 'ALL' in allowed_tags):
            return await ctx.send(f"You do not have permission to query the tag `{tag}`.")
        games = sorted(await self.api.get_all_games(tag=tag), key=lambda g: isoparse(g['createdAt']), reverse=True)
        if not games:
            return await ctx.send(f"There are no games with tag `{tag}`."
                                  f" Make sure the tag is valid and correctly cased.")

        site = await login_if_possible(ctx, self.bot, 'lol')
        games = await self.filter_new(site, games)
        ret = [await self.format_game(game, ctx.author) for game in games[:limit][::-1]]

        if not ret:
            return await ctx.send(f"There are no new games with tag `{tag}`.")

        for page in pagify('\n\n'.join(ret), delims=['\n\n']):
            await ctx.send(page)

    @mh_query.command(name='getgame')
    async def mh_q_getgame(self, ctx, game_id):
        """Get a game by its game ID"""
        await ctx.send(await self.format_game_long(await self.api.get_game(game_id), ctx.author))

    @mh_query.command(name='getasset')
    @auth_check('mhadmin')
    async def mh_q_getasset(self, ctx, game_id, asset):
        """Get a match asset by game_id and asset name"""
        await ctx.send(file=discord.File(BytesIO(await self.api.get_asset(game_id, asset)), asset + '.json'))

    @mhtool.group(name='query2')
    @commands.dm_only()
    async def mh_query2(self, ctx):
        """Slow query commands"""

    @mh_query2.command(name='all')
    async def mh_q2_all(self, ctx, limit: UserInputOptional[int] = 50, *, tag):
        """Get a list of the most recent `limit` games with the provided tag

        If limit is left blank, 50 games are sent.
        """
        allowed_tags = await self.config.user(ctx.author).allowed_tags()
        if not (has_perm('mhadmin', ctx.author, self.bot) or tag in allowed_tags or 'ALL' in allowed_tags):
            return await ctx.send(f"You do not have permission to query the tag `{tag}`.")
        games = sorted(await self.api.get_all_games(tag=tag), key=lambda g: isoparse(g['createdAt']), reverse=True)
        ret = [await self.format_game_long(game, ctx.author) for game in games[:limit][::-1]]
        if not ret:
            return await ctx.send(f"There are no games with tag `{tag}`."
                                  f" Make sure the tag is valid and correctly cased.")
        for page in pagify('\n\n'.join(ret), delims=['\n\n']):
            await ctx.send(page)

    @mh_query2.command(name='new')
    async def mh_q2_new(self, ctx, limit: UserInputOptional[int] = 50, *, tag):
        """Get only games that aren't on the wiki yet"""
        allowed_tags = await self.config.user(ctx.author).allowed_tags()
        if not (has_perm('mhadmin', ctx.author, self.bot) or tag in allowed_tags or 'ALL' in allowed_tags):
            return await ctx.send(f"You do not have permission to query the tag `{tag}`.")
        games = sorted(await self.api.get_all_games(tag=tag), key=lambda g: isoparse(g['createdAt']), reverse=True)
        if not games:
            return await ctx.send(f"There are no games with tag `{tag}`."
                                  f" Make sure the tag is valid and correctly cased.")

        site = await login_if_possible(ctx, self.bot, 'lol')
        games = await self.filter_new(site, games)
        ret = [await self.format_game_long(game, ctx.author) for game in games[:limit][::-1]]

        if not ret:
            return await ctx.send(f"There are no new games with tag `{tag}`.")

        for page in pagify('\n\n'.join(ret), delims=['\n\n']):
            await ctx.send(page)

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
            elif not has_perm('mhadmin', ctx.author, self.bot) \
                    and tag not in await self.config.user(ctx.author).allowed_tags() \
                    and 'ALL' not in self.config.user(ctx.author).allowed_tags():
                return await send_cancellation_message(ctx, f"You cannot subscribe to tag `{tag}` as you don't"
                                                            f" have permission to view it. Contact a bot admin"
                                                            f" if you think this is an issue.")
            await self.check_subscriptions()
            async with self.config.seen() as seen:
                for game in await self.api.get_all_games(tag=tag):
                    seen[game['platformGameId']] = len(game['assets'])
            subs[tag] = {'date': time.time()}
        await ctx.tick()

    @mh_subscription.command(name='remove', aliases=['rm', 'delete', 'del'])
    async def mh_s_remove(self, ctx, *, tag):
        """Unsubscribe from a tag"""
        async with self.config.user(ctx.author).subscriptions() as subs:
            if tag not in subs:
                return await ctx.send("You're not subscribed to that tag.")
            subs.pop(tag)
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
        """Clear your current subscriptions"""
        if not await get_user_confirmation(ctx, "Are you sure you want to clear all of your subscriptions?"):
            return await ctx.react_quietly("\N{CROSS MARK}")
        await self.config.user(ctx.author).subscriptions.set({})
        await ctx.tick()

    @mhtool.group(name='prefs', aliases=['pref'])
    async def mh_prefs(self, ctx):
        """Set preferences for your MHTool data"""

    @mh_prefs.command(name='jsononly', aliases=['onlyjson'])
    async def mh_p_jsononly(self, ctx, enable: bool):
        """Only get subscription messages when a game has assets"""
        await self.config.user(ctx.user).jsononly.set(enable)
        await ctx.tick()

    @mhtool.group(name='channels', aliases=['channel'])
    @auth_check('mhadmin')
    async def mh_channels(self, ctx):
        """Set whitelisted channels for the use of this cog"""

    @mh_channels.command(name="add")
    async def mh_c_add(self, ctx, channel: TextChannel):
        """Add a channel"""
        async with self.config.allowed_channels() as channels:
            channels[str(channel.id)] = {'date': time.time()}
        await ctx.tick()

    @mh_channels.command(name='remove', aliases=['rm', 'delete', 'del'])
    async def mh_c_remove(self, ctx, channel: TextChannel):
        """Remove a channel"""
        async with self.config.allowed_channels() as channels:
            if str(channel.id) in channels:
                channels.pop(str(channel.id))
            else:
                return await ctx.send(f"{channel} was not already an allowed channel.")
        await ctx.tick()

    @mh_channels.command(name="list")
    async def mh_c_list(self, ctx):
        """List whitelisted channels"""
        channels = [channel for cid in await self.config.allowed_channels()
                    if (channel := self.bot.get_channel(int(cid)))]
        if not channels:
            return await ctx.send("There are no whitelisted channels.")
        for page in pagify('\n'.join(f"{c.id} ({c.guild.name}/{c.name})" for c in channels)):
            await ctx.send(box(page))

    async def format_game(self, game: Game, user: User) -> str:
        status = f" ({game['status']})" if game['status'] != "FINISHED" else ""

        return (f"`{game['platformGameId']}`{status} {self.get_asset_string(game['assets'])}\n"
                f"\t\tName: {game['name']}\n"
                f"\t\tStart Time: {self.parse_date(game['createdAt'])}\n"
                f"\t\tTags: {', '.join(map(inline, sorted(game['tags'])))}")

    async def format_game_long(self, game: Game, user: User) -> str:
        status = f" ({game['status']})" if game['status'] != "FINISHED" else ""
        teams = winner = 'Unknown'
        if 'GAMH_SUMMARY' in game['assets']:
            summary = json.loads(await self.api.get_asset(game['platformGameId'], 'GAMH_SUMMARY'))
            t1, t2 = summary['participants'][::5]
            teams = (f"{t1['summonerName'].split(' ')[0]} vs {t2['summonerName'].split(' ')[0]}")
            winner = t1['summonerName'].split(' ')[0] if t1['win'] else t2['summonerName'].split(' ')[0]
        return (f"`{game['platformGameId']}`{status} {self.get_asset_string(game['assets'])}\n"
                f"\t\tName: {game['name']}\n"
                f"\t\tTeams: {teams}\n"
                f"\t\tWinner: {winner}\n"
                f"\t\tStart Time: {self.parse_date(game['createdAt'])}\n"
                f"\t\tTags: {', '.join(map(inline, sorted(game['tags'])))}")

    @staticmethod
    def get_asset_string(assets: List[AssetType]):
        if 'GAMH_SUMMARY' in assets and 'GAMH_DETAILS' in assets:
            return confirmation_message("Ready to parse")
        elif 'GAMH_SUMMARY' in assets:
            return confirmation_message("Ready to parse, but no drakes (Possible chronobreak. Please check back later)")
        else:
            return cancellation_message("Not ready to parse")

    @staticmethod
    def parse_date(datestr: str) -> str:
        return f"<t:{int(isoparse(datestr).timestamp())}:F>"

    @staticmethod
    async def filter_new(site: EsportsClient, games: List[Game]) -> List[Game]:
        """Returns only new games from a list of games."""
        if not games:
            return []

        all_ids = [repr(game['platformGameId'].strip()) for game in games]
        where = f"RiotPlatformGameId IN ({','.join(all_ids)})"

        result = site.cargo_client.query(tables="MatchScheduleGame",
                                         fields="RiotPlatformGameId",
                                         where=where)

        old_ids = [row['RiotPlatformGameId'] for row in result]
        return [game for game in games if game['platformGameId'] not in old_ids]
