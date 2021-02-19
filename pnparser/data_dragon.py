import requests as client
import json

# links
DATA_DRAGON_RUNES = "https://ddragon.leagueoflegends.com/cdn/{}/data/en_US/runesReforged.json"
DATA_DRAGON_ITEMS = "https://ddragon.leagueoflegends.com/cdn/{}/data/en_US/item.json"
DATA_DRAGON_CHAMPIONS = "https://ddragon.leagueoflegends.com/cdn/{}/data/en_US/champion.json"


class DataDragon:
    def __init__(self, patch_version):
        self.patch_version = patch_version

    def load_data(self):
        response = client.get(
            DATA_DRAGON_CHAMPIONS.format(f"{self.patch_version}.1"))
        self.champions = json.loads(response.text)["data"]
        response = client.get(
            DATA_DRAGON_ITEMS.format(f"{self.patch_version}.1"))
        self.items = json.loads(response.text)["data"]
        response = client.get(
            DATA_DRAGON_RUNES.format(f"{self.patch_version}.1"))
        self.runes = json.loads(response.text)
        return self
