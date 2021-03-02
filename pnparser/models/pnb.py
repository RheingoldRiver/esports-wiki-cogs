from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .pbc import Pbc
    from .pai import Pai


class Pnb:
    def __init__(self, name: str) -> None:
        self.__name: str = ""
        self.name = name
        self.new: bool = False
        self.context: str = ""
        self.summary: str = ""
        self.changes: 'list[Pnb]' = []
        self.attributes: 'list[Pbc]' = []
        self.abiliries: 'list[Pai]' = []

    @property
    def name(self) -> str:
        return self.__name

    @name.setter
    def name(self, value: str) -> None:
        if "(Ornn Upgrade)" in value:
            value = value[:value.index("(Ornn Upgrade)")]
        self.__name = value.replace("’", "'")

    def print(self) -> str:
        pass
