import logging
from datetime import datetime, timedelta
from io import BytesIO
from typing import Any, Dict, Iterable, List, Literal, Optional, TypedDict, Union

from aiohttp import ClientResponseError, ClientSession
from redbot.core.bot import Red
from tsutils.errors import BadAPIKeyException, NoAPIKeyException

from bayesgamh.errors import BadRequestException

logger = logging.getLogger('red.esports-wiki-cogs.bayesgahm')

GameID = AssetType = Tag = str


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


class BayesAPIWrapper:
    def __init__(self, bot: Red, session: ClientSession):
        self.bot = bot

        self.session = session

        self.access_token = None
        # self.refresh_token = None
        self.expires = datetime.min

    async def ensure_login(self) -> None:
        """Ensure that the access_token is recent and valid"""
        keys = await self.bot.get_shared_api_tokens("bayes")
        if not ("username" in keys and "password" in keys):
            raise NoAPIKeyException((await self.bot.get_valid_prefixes())[0]
                                    + f"set api bayes username <USERNAME> password <PASSWORD>")
        if self.access_token is None or self.expires < datetime.now():
            try:
                data = await self.do_api_call('POST', 'login',
                                              {'username': keys['username'], 'password': keys['password']})
            except ClientResponseError as e:
                if e.status == 500:
                    raise BadAPIKeyException((await self.bot.get_valid_prefixes())[0]
                                             + f"set api bayes username <USERNAME> password <PASSWORD>")
                raise
            self.access_token = data['accessToken']
            # self.refresh_token = data['refreshToken']
            self.expires = datetime.now() + timedelta(seconds=data['expiresIn'] - 30)  # 30 second buffer to be safe
        # # While the documentation mentions a refresh token, it's not actually supplied on an actual login
        # # TODO: Maybe follow up w/ Bayes to see what's up with that ^^?
        # elif self.expires < datetime.now():
        #     data = await self.do_api_call('POST', 'login/refresh_token', {'refreshToken': self.refresh_token})
        #     if not data['success']:
        #         raise RuntimeError(f'Failed to refresh login: {data}')
        #     self.access_token = data['accessToken']
        #     self.expires = datetime.now() + timedelta(seconds=data['expiresIn'] - 30)  # 30 second buffer to be safe

    async def do_api_call(self, method: Literal['GET', 'POST'], service: str, data: Dict[str, Any] = None):
        """Make a single API call to emh-api.bayesesports.com"""
        endpoint = "https://emh-api.bayesesports.com/"
        if data is None:
            data = {}

        if method == "GET":
            async with self.session.get(endpoint + service, headers=await self.get_headers(), params=data) as resp:
                resp.raise_for_status()
                data = await resp.json()
        elif method == "POST":
            async with self.session.post(endpoint + service, json=data) as resp:
                resp.raise_for_status()
                data = await resp.json()
        else:
            raise ValueError("HTTP Method must be GET or POST.")
        return data

    async def get_headers(self) -> Dict[str, str]:
        """Return headers for a GET request to the API"""
        await self.ensure_login()
        return {'Authorization': f'Bearer {self.access_token}'}

    async def get_tags(self) -> List[Tag]:
        """Return a list of tags that can be used to request games"""
        return await self.do_api_call('GET', 'api/v1/tags')

    async def get_games(self, *, tags: Iterable[Tag], page: int = 0, page_size: int = 20,
                        from_timestamp: Union[datetime, str] = datetime.min,
                        to_timestamp: Union[datetime, str] = datetime.max) \
            -> GetGamesResponse:
        """Make an API query to the api/v1/games endpoint"""
        if isinstance(from_timestamp, datetime):
            from_timestamp = from_timestamp.isoformat()
        if isinstance(to_timestamp, datetime):
            to_timestamp = to_timestamp.isoformat()
        tags = ','.join(tags)
        params = {'page': page, 'size': page_size, 'from_timestamp': from_timestamp,
                  'to_timestamp': to_timestamp, 'tags': tags}
        return await self.do_api_call('GET', 'api/v1/games', params)

    async def get_all_games(self, *, tag: Optional[Tag] = None, tags: Optional[List[Tag]] = None,
                            from_timestamp: Union[datetime, str] = datetime.min,
                            to_timestamp: Union[datetime, str] = datetime.max) \
            -> List[Game]:
        """Get all games with a tag within the timestamps"""
        if tags is None:
            tags = []
        if tag is not None:
            tags.append(tag)
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
        return data['games']

    async def get_game(self, game_id: GameID) -> Game:
        """Get a game by its ID"""
        try:
            game = await self.do_api_call('GET', f'api/v1/games/{game_id}')
        except ClientResponseError as e:
            if e.status == 404:
                raise BadRequestException(f'Invalid Game ID: {game_id}')
            raise
        return game

    async def get_asset(self, game_id: GameID, asset: AssetType) -> bytes:
        """Get the bytes for an asset"""
        game = await self.get_game(game_id)
        if asset not in game['assets']:
            raise BadRequestException(f'Invalid asset type for game with ID {game_id}: {asset}')
        data = await self.do_api_call('GET', f'api/v1/games/{game_id}/download', {'type': asset})
        fp = BytesIO()
        async with self.session.get(data['url']) as resp:
            return await resp.read()
