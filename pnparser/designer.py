import json
import os

ICONS_FILE: str = os.path.join(os.path.dirname(__file__), "designer_icons.json")
TEMPLATE: str = "[[File:{0}|20px|link=]] {1}<br>"


class Designer:
    def __init__(self, name: str) -> None:
        self.__name: str = name
        self.icon: str = ""

    @property
    def name(self) -> str:
        return self.__name

    @name.setter
    def name(self, value: str) -> None:
        self.__name = value.replace('“', '"').replace('”', '"')
        result = regex.search(r'(?:"").*(?:"")', self.__name)
        if result.group[0]:
            self.icon = get_designer_icon(result.group[0])

    def print(self) -> str:
        return TEMPLATE.format(self.icon, self.__name)

    @staticmethod
    def get_designer_icon(username: str) -> str:
        with open(ICONS_FILE, 'r') as file:
            icons: object = json.loads(file.read())
            return icons[username]

    @staticmethod
    def add_designer(username: str, icon: str) -> None:
        # TODO: Add a new designer
        return
