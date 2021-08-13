import logging
from datetime import datetime, timedelta
from io import BytesIO
from typing import Any, BinaryIO, Dict, Iterable, List, Literal, Union

from aiohttp import ClientSession
from redbot.core.bot import Red
from tsutils.errors import NoAPIKeyException

logger = logging.getLogger('red.aradiacogs.bayesgahm')

GameID = AssetType = str


class BayesAPIWrapper:
    def __init__(self, bot: Red, session: ClientSession):
        self.bot = bot

        self.session = session

        self.access_token = None
        self.refresh_token = None
        self.expires = datetime.min

    async def ensure_login(self) -> None:
        """Ensure that the access_token is recent and valid"""
        keys = await self.bot.get_shared_api_tokens("bayes")
        if not ("username" in keys and "password" in keys):
            raise NoAPIKeyException((await self.bot.get_valid_prefixes())[0]
                                    + f"set api bayes username <USERNAME> password <PASSWORD>")
        if self.access_token is None:
            data = await self.do_api_call('POST', 'login',
                                          {'username': keys['username'], 'password': keys['password']})
            if not data['success']:
                raise RuntimeError(f'Failed to login: {data}')
            self.access_token = data['accessToken']
            self.refresh_token = data['refreshToken']
            self.expires = datetime.now() + timedelta(seconds=data['expiresIn'] - 30)  # 30 second buffer to be safe
        elif self.expires < datetime.now():
            data = await self.do_api_call('POST', 'login/refresh_token', {'refreshToken': self.refresh_token})
            if not data['success']:
                raise RuntimeError(f'Failed to refresh login: {data}')
            self.access_token = data['accessToken']
            self.expires = datetime.now() + timedelta(seconds=data['expiresIn'] - 30)  # 30 second buffer to be safe

    async def do_api_call(self, method: Literal['GET', 'POST'], service: str, data: Dict[str, Any] = None):
        """Make a single API call to emh-api.bayesesports.com"""
        endpoint = "https://emh-api.bayesesports.com/"
        if data is None:
            data = {}

        if method == "GET":
            async with self.session.get(endpoint + service, headers=await self.get_headers(), params=data) as resp:
                data = await resp.json()
            return data
        elif method == "POST":
            async with self.session.get(endpoint + service, data=data) as resp:
                data = await resp.json()
            return data
        else:
            raise ValueError("HTTP Method must be GET or POST.")

    async def get_headers(self) -> Dict[str, str]:
        """Return headers for a GET request to the API"""
        await self.ensure_login()
        return {'Authorization': f'Bearer {self.access_token}'}

    async def get_tags(self) -> List[str]:
        """Return a list of tags that can be used to request games"""
        return await self.do_api_call('GET', 'api/v1/tags')

    async def get_games(self, page: int = 0, page_size: int = 20, from_timestamp: Union[datetime, str] = datetime.min,
                        to_timestamp: Union[datetime, str] = datetime.max, tags: Iterable[str] = None) \
            -> Dict[str, Any]:
        if isinstance(from_timestamp, datetime):
            from_timestamp = from_timestamp.isoformat()
        if isinstance(to_timestamp, datetime):
            to_timestamp = to_timestamp.isoformat()
        tags = ','.join(tags or [])
        params = {'page': page, 'size': page_size, 'from_timestamp': from_timestamp,
                  'to_timestamp': to_timestamp, 'tags': tags}
        return await self.do_api_call('GET', 'api/v1/tags', params)

    async def get_all_games(self, from_timestamp: Union[datetime, str] = datetime.min,
                            to_timestamp: Union[datetime, str] = datetime.max, tags: Iterable[str] = None) \
            -> List[Dict[str, Any]]:
        data = await self.get_games(page_size=999, from_timestamp=from_timestamp, to_timestamp=to_timestamp, tags=tags)
        if data['count'] >= 999:
            logger.warning(f"More than 999 games matched with tags {tags}.")
        return data['games']

    async def get_game(self, game_id: GameID) -> Dict[str, Any]:
        return await self.do_api_call('GET', f'api/v1/games/{game_id}')

    async def get_asset(self, game_id: GameID, asset: AssetType) -> BinaryIO:
        data = await self.do_api_call('GET', f'api/v1/games/{game_id}/download', {'type': asset})
        fp = BytesIO()
        async with self.session.get(data['url'], headers=await self.get_headers()) as resp:
            fp.write(await resp.read())
        return fp
