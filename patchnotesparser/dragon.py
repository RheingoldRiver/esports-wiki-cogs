import requests as HttpClient
from typing import Any
import json as Json
import re as Regex

# links
VERSIONS: str = "https://ddragon.leagueoflegends.com/api/versions.json"
ITEMS: str = "https://ddragon.leagueoflegends.com/cdn/{}/data/en_US/item.json"
CHAMPIONS: str = "https://ddragon.leagueoflegends.com/cdn/{}/data/en_US/champion.json"
RUNES: str = "https://ddragon.leagueoflegends.com/cdn/{}/data/en_US/runesReforged.json"
SPELLS: str = "https://ddragon.canisback.com/{}/data/en_US/summoner.json"

# TODO: parallel requests

class Dragon:
    runes: 'list[dict[str, Any]]' = []
    items: 'list[dict[str, Any]]' = []
    # camps: 'list[dict[str, Any]]' = []
    spells: 'list[dict[str, Any]]' = []
    champions: 'list[dict[str, Any]]' = []
    current_version: 'str | None' = None

    @staticmethod
    def load_data() -> None:
        # check if update is needed
        latest_version: str = Dragon._get_latest_version()
        if latest_version == Dragon.current_version:
            return

        # get champions from data dragon
        response = HttpClient.get(CHAMPIONS.format(latest_version))
        data = Json.loads(response.text)["data"]
        Dragon.champions = []
        for champion_key in data:
            Dragon.champions.append(data[champion_key])

        # get items from data dragon
        response = HttpClient.get(ITEMS.format(latest_version))
        data = Json.loads(response.text)["data"]
        Dragon.items = []
        for item_key in data:
            Dragon.items.append(data[item_key])

        # get summoner spells from data dragon
        response = HttpClient.get(SPELLS.format(latest_version))
        data = Json.loads(response.text)["data"]
        Dragon.spells = []
        for spell_key in data:
            Dragon.spells.append(data[spell_key])

        # get runes from data dragon
        response = HttpClient.get(RUNES.format(latest_version))
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
    def _get_latest_version() -> str:
        response = HttpClient.get(VERSIONS)
        return Json.loads(response.text)[0]
