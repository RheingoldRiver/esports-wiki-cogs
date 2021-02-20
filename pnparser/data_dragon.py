import requests as client
import json

# links
VERSIONS = "https://ddragon.leagueoflegends.com/api/versions.json"
ITEMS = "https://ddragon.leagueoflegends.com/cdn/{}/data/en_US/item.json"
CHAMPIONS = "https://ddragon.leagueoflegends.com/cdn/{}/data/en_US/champion.json"
RUNES = "https://ddragon.leagueoflegends.com/cdn/{}/data/en_US/runesReforged.json"


class DataDragon:
    current = "None"
    items = None
    runes = None
    champions = None

    @staticmethod
    async def load_data(ctx):
        # check if update is needed
        latest_version = DataDragon.__get_latest_version()
        if latest_version == DataDragon.current:
            return

        response = client.get(CHAMPIONS.format(f"{latest_version}"))
        DataDragon.champions = json.loads(response.text)["data"]
        response = client.get(ITEMS.format(f"{latest_version}"))
        DataDragon.items = json.loads(response.text)["data"]
        response = client.get(RUNES.format(f"{latest_version}"))
        DataDragon.runes = json.loads(response.text)
        DataDragon.current = latest_version
        await ctx.send(f"Updated ddragon to version `{DataDragon.current}`.")

    @staticmethod
    def __get_latest_version():
        response = client.get(VERSIONS)
        return json.loads(response.text)[0]
