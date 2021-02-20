import json
import os

ICONS_FILE = os.path.join(os.path.dirname(__file__), "designer_icons.json")
TEMPLATE = "[[File:{0}|20px|link=]] {1}<br>"


class Designer:
    def __init__(self, name):
        self.__name = name
        self.icon = ""

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, value):
        self.__name = value.replace('“', '"').replace('”', '"')
        result = regex.search(r'(?:"").*(?:"")', self.__name)
        if result.group[0]:
            self.icon = get_designer_icon(result.group[0])

    def print(self):
        return TEMPLATE.format(self.icon, self.__name)

    @staticmethod
    def get_designer_icon(username):
        with open(ICONS_FILE, 'r') as file:
            icons = json.loads(file.read())
            return icons[username]

    @staticmethod
    def add_designer(username, icon):
        # TODO: Add a new designer
        return
