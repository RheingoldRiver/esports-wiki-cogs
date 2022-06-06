import json
import logging
import os
from datetime import datetime, timedelta
from io import BytesIO
from typing import Any, Dict, Iterable, List, Literal, Optional, TypedDict, Union

import backoff
from aiofiles import open as aopen
from aiohttp import ClientResponseError, ClientSession
from redbot.core import data_manager
from redbot.core.bot import Red
from tsutils.errors import BadAPIKeyException, NoAPIKeyException

from bayesgamh.errors import BadRequestException

logger = logging.getLogger('red.esports-wiki-cogs.bayesgamh')

GameID = AssetType = str
Tag = Union[str, Literal['NULL', 'ALL']]


class Game(TypedDict):
    platformGameId: GameID
    name: str
    status: str
    createdAt: str  # ISO-8601 Formatted
    assets: List[AssetType]
    tags: List[Tag]


class GetGamesResponse(TypedDict):
    page: int
    size: int
    count: int
    games: List[Game]


class RateLimitException(Exception):
    pass


def _data_file(file_name: str) -> str:
    return os.path.join(str(data_manager.cog_data_path(raw_name='padinfo')), file_name)


class BayesAPIWrapper:
    def __init__(self, bot: Red, session: ClientSession):
        self.bot = bot

        self.session = session

        self.access_token = None
        self.refresh_token = None
        self.expires = datetime.min

    async def _save_login(self):
        async with aopen(_data_file('keys.json'), 'w+') as f:
            await f.write(json.dumps({
                'accessToken': self.access_token,
                'refreshToken': self.refresh_token,
                'expiresIn': self.expires.timestamp()
            }))

    async def _ensure_login(self, force_relogin: bool = False) -> None:
        """Ensure that the access_token is recent and valid"""
        if force_relogin:
            await self._new_login()
        elif self.access_token is None:
            try:
                async with aopen(_data_file('keys.json')) as f:
                    data = json.loads(await f.read())
            except FileNotFoundError:
                return await self._ensure_login(True)
            self.access_token = data['accessToken']
            self.refresh_token = data['refreshToken']
            self.expires = datetime.now() + timedelta(seconds=data['expiresIn'])
            if self.expires <= datetime.now():
                return await self._ensure_login(False)
        elif self.expires <= datetime.now():
            try:
                data = await self._do_api_call('POST', 'login/refresh_token',
                                               {'refreshToken': self.refresh_token})
                self.access_token = data['accessToken']
                self.expires = datetime.now() + timedelta(seconds=data['expiresIn'])
            except ClientResponseError:
                # in case the refresh token endpoint is down or something
                await self._new_login()
        else:
            return
        await self._save_login()

    async def _new_login(self):
        keys = await self.bot.get_shared_api_tokens("bayes")
        if not ("username" in keys and "password" in keys):
            raise NoAPIKeyException((await self.bot.get_valid_prefixes())[0]
                                    + f"set api bayes username <USERNAME> password <PASSWORD>")
        try:
            data = await self._do_api_call('POST', 'login',
                                           {'username': keys['username'], 'password': keys['password']})
        except ClientResponseError as e:
            if e.status == 500:
                raise BadAPIKeyException((await self.bot.get_valid_prefixes())[0]
                                         + f"set api bayes username <USERNAME> password <PASSWORD>")
            raise
        self.access_token = data['accessToken']
        self.refresh_token = data['refreshToken']
        self.expires = datetime.now() + timedelta(seconds=data['expiresIn'])

    @backoff.on_exception(backoff.expo, RateLimitException, logger=None)
    async def _do_api_call(self, method: Literal['GET', 'POST'], service: str,
                           data: Dict[str, Any] = None, *, allow_retry: bool = True):
        """Make a single API call to emh-api.bayesesports.com"""
        endpoint = "https://emh-api.bayesesports.com/"
        if data is None:
            data = {}

        if method == "GET":
            async with self.session.get(endpoint + service, headers=await self._get_headers(), params=data) as resp:
                if resp.status == 401 and allow_retry:
                    await self._ensure_login(force_relogin=True)
                    return await self._do_api_call(method, service, data, allow_retry=False)
                elif resp.status == 429:
                    raise RateLimitException()
                resp.raise_for_status()
                data = await resp.json()
        elif method == "POST":
            async with self.session.post(endpoint + service, json=data) as resp:
                resp.raise_for_status()
                data = await resp.json()
        else:
            raise ValueError("HTTP Method must be GET or POST.")
        return data

    async def _get_headers(self) -> Dict[str, str]:
        """Return headers for a GET request to the API"""
        await self._ensure_login()
        return {'Authorization': f'Bearer {self.access_token}'}

    @staticmethod
    def _clean_game(game: Game) -> Game:
        """Add the NULL tag to a game with no tags."""
        if not game['tags']:
            game['tags'].append('NULL')
        return game

    async def get_tags(self) -> List[Tag]:
        """Return a list of tags that can be used to request games"""
        return ['NULL', 'ALL'] + await self._do_api_call('GET', 'api/v1/tags')

    async def get_games(self, *, page: Optional[int] = None, page_size: Optional[int] = None,
                        from_timestamp: Optional[Union[datetime, str]] = None,
                        to_timestamp: Optional[Union[datetime, str]] = None,
                        tags: Optional[Iterable[Tag]] = None) \
            -> GetGamesResponse:
        """Make an API query to the api/v1/games endpoint"""
        if isinstance(from_timestamp, datetime):
            from_timestamp = from_timestamp.isoformat()
        if isinstance(to_timestamp, datetime):
            to_timestamp = to_timestamp.isoformat()
        tags = ','.join(tags) if tags is not None else None
        params = {'page': page, 'size': page_size, 'from_timestamp': from_timestamp,
                  'to_timestamp': to_timestamp, 'tags': tags}
        params = {k: v for k, v in params.items() if v is not None}
        return await self._do_api_call('GET', 'api/v1/games', params)

    async def get_all_games(self, *, tag: Optional[Tag] = None, tags: Optional[Iterable[Tag]] = None,
                            from_timestamp: Optional[Union[datetime, str]] = None,
                            to_timestamp: Optional[Union[datetime, str]] = None) \
            -> List[Game]:
        """Get all games with the given filters"""
        if tags is None:
            tags = []
        else:
            tags = list(tags)
        only_null = False
        if tag is not None:
            tags.append(tag)
        if not tags or tags == ['ALL']:
            tags = None
        elif tags == ["NULL"]:
            only_null = True
            tags = None
        elif "NULL" in tags or "ALL" in tags:
            raise ValueError("The special tags NULL and ALL must be requested alone.")

        data = await self.get_games(tags=tags, page_size=999,
                                    from_timestamp=from_timestamp,
                                    to_timestamp=to_timestamp)
        if data['count'] >= 999:
            page = 1
            while len(data['games']) < data['count']:
                newpage = await self.get_games(tags=tags, page=page, page_size=999,
                                               from_timestamp=from_timestamp,
                                               to_timestamp=to_timestamp)
                data['games'].extend(newpage['games'])
                if not newpage['games']:
                    break
                page += 1
        return [self._clean_game(game) for game in data['games'] if not (game['tags'] and only_null)]

    async def get_game(self, game_id: GameID) -> Game:
        """Get a game by its ID"""
        try:
            game = await self._do_api_call('GET', f'api/v1/games/{game_id}')
        except ClientResponseError as e:
            if e.status == 404:
                raise BadRequestException(f'Invalid Game ID: {game_id}')
            raise
        return self._clean_game(game)

    async def get_asset(self, game_id: GameID, asset: AssetType) -> bytes:
        """Get the bytes for an asset"""
        game = await self.get_game(game_id)
        if asset not in game['assets']:
            raise BadRequestException(f'Invalid asset type for game with ID {game_id}: {asset}')
        data = await self._do_api_call('GET', f'api/v1/games/{game_id}/download', {'type': asset})
        fp = BytesIO()
        async with self.session.get(data['url']) as resp:
            return await resp.read()
