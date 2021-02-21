import requests as client
import json

# links
VERSIONS: str = "https://ddragon.leagueoflegends.com/api/versions.json"
ITEMS: str = "https://ddragon.leagueoflegends.com/cdn/{}/data/en_US/item.json"
CHAMPIONS: str = "https://ddragon.leagueoflegends.com/cdn/{}/data/en_US/champion.json"
RUNES: str = "https://ddragon.leagueoflegends.com/cdn/{}/data/en_US/runesReforged.json"


class DataDragon:
    current: str = ""
    items: object = None
    runes: object = None
    champions: object = None

    @staticmethod
    async def load_data(ctx: object) -> None:
        # check if update is needed
        latest_version: str = DataDragon.__get_latest_version()
        if latest_version == DataDragon.current:
            return

        response: object = client.get(CHAMPIONS.format(f"{latest_version}"))
        DataDragon.champions = json.loads(response.text)["data"]
        response: object = client.get(ITEMS.format(f"{latest_version}"))
        DataDragon.items = json.loads(response.text)["data"]
        response: object = client.get(RUNES.format(f"{latest_version}"))
        DataDragon.runes = json.loads(response.text)
        DataDragon.current = latest_version
        await ctx.send(f"Updated ddragon to version `{DataDragon.current}`.")

    @staticmethod
    def __get_latest_version() -> str:
        response: object = client.get(VERSIONS)
        return json.loads(response.text)[0]
