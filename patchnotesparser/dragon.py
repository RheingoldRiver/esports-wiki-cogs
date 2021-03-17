import requests as HttpClient
from typing import Any
import json as Json

# links
VERSIONS: str = "https://ddragon.leagueoflegends.com/api/versions.json"
ITEMS: str = "https://ddragon.leagueoflegends.com/cdn/{}/data/en_US/item.json"
CHAMPIONS: str = "https://ddragon.leagueoflegends.com/cdn/{}/data/en_US/champion.json"
RUNES: str = "https://ddragon.leagueoflegends.com/cdn/{}/data/en_US/runesReforged.json"

# TODO: parallel requests

class Dragon:
    runes: 'list[dict[str, Any]]' = []
    items: 'list[dict[str, Any]]' = []
    champions: 'list[dict[str, Any]]' = []
    current_version: 'str | None' = None

    @staticmethod
    def load_data() -> None:
        # check if update is needed
        latest_version: str = Dragon.__get_latest_version()
        if latest_version == Dragon.current_version:
            return

        # get champions from data dragon
        response = HttpClient.get(CHAMPIONS.format(f"{latest_version}"))
        data = Json.loads(response.text)["data"]
        Dragon.champions = []
        for champion in data:
            Dragon.champions.append(data[champion])

        # get items from data dragon
        response = HttpClient.get(ITEMS.format(f"{latest_version}"))
        data = Json.loads(response.text)["data"]
        Dragon.items = []
        for item in data:
            Dragon.items.append(data[item])

        # get runes from data dragon
        response = HttpClient.get(RUNES.format(f"{latest_version}"))
        data = Json.loads(response.text)
        Dragon.runes = []
        for group in data:
            Dragon.runes.append(group)

            if group["slots"]:
                for slot in group["slots"]:
                    for rune in slot["runes"]:
                        Dragon.runes.append(rune)

        # set dragon current version
        Dragon.current_version = latest_version

    @staticmethod
    def __get_latest_version() -> str:
        response = HttpClient.get(VERSIONS)
        return Json.loads(response.text)[0]
