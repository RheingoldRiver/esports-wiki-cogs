import os.path as Path
import json as Json
import re as Regex

ICONS_DB: str = Path.join(Path.dirname(__file__), "designer_icons.json")
TEMPLATE: str = "[[File:{0}|20px|link=]] {1}<br>"


class Designer:
    def __init__(self, name: str) -> None:
        self.username: str = None
        self.__name: str = ""
        self.icon: str = None
        self.name = name

    @staticmethod
    def get_designer_icon(username: str) -> str:
        # returns the designer's icon name
        with open(ICONS_DB, 'r') as file:
            icons: dict = Json.loads(file.read())
            return icons[username]

    @staticmethod
    def add_designer(username: str, icon: str) -> None:
        # TODO: Add a new designer
        return

    @property
    def name(self) -> str:
        return self.__name

    @name.setter
    def name(self, value: str) -> None:
        # standardize text and get the user icon
        self.__name = value.replace('“', '"').replace('”', '"')
        result = Regex.search(r'(?:").*(?:")', self.__name)
        if result is not None:
            self.username = result.group(0)[1:-1]
            self.icon = Designer.get_designer_icon(self.username)

    def print(self) -> str:
        # print the designer template
        return TEMPLATE.format(self.icon, self.__name)
