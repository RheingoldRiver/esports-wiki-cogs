import requests as HttpClient
from typing import Any
import json as Json

# links
VERSIONS: str = "https://ddragon.leagueoflegends.com/api/versions.json"
ITEMS: str = "https://ddragon.leagueoflegends.com/cdn/{}/data/en_US/item.json"
CHAMPIONS: str = "https://ddragon.leagueoflegends.com/cdn/{}/data/en_US/champion.json"
RUNES: str = "https://ddragon.leagueoflegends.com/cdn/{}/data/en_US/runesReforged.json"


class DataDragon:
    runes: dict = {}
    items: 'list[dict[str, Any]]' = []
    champions: 'list[dict[str, Any]]' = []
    current_version: 'str | None' = None

    @staticmethod
    def load_data() -> None:
        # check if update is needed
        latest_version: str = DataDragon.__get_latest_version()
        if latest_version == DataDragon.current_version:
            return

        # get champions from data dragon
        response = HttpClient.get(CHAMPIONS.format(f"{latest_version}"))
        data = Json.loads(response.text)["data"]
        DataDragon.champions = []
        for champion in data:
            DataDragon.champions.append(data[champion])

        # get items from data dragon
        response = HttpClient.get(ITEMS.format(f"{latest_version}"))
        data = Json.loads(response.text)["data"]
        DataDragon.items = []
        for item in data:
            DataDragon.items.append(data[item])

        # TODO: fix the remaining lists
        response = HttpClient.get(RUNES.format(f"{latest_version}"))
        DataDragon.runes = Json.loads(response.text)
        DataDragon.current_version = latest_version

    @staticmethod
    def __get_latest_version() -> str:
        response = HttpClient.get(VERSIONS)
        return Json.loads(response.text)[0]
