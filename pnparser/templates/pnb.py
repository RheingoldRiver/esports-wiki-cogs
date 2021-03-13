from datetime import date as Date
from ..dragon import Dragon

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .pbc import Pbc
    from .pai import Pai

TEMPLATE: str = "{{pnb"

class Pnb:
    """A champion or item change"""
    
    def __init__(self, name: str = "",
                 new: bool = False,
                 removed: bool = False,
                 date: 'Date | None' = None) -> None:
        self.__name: str = ""
        self.name = name
        self.new: bool = new
        self.removed: bool = removed
        self.context: str = ""
        self.summary: str = ""
        self.date: 'Date | None' = date
        self.changes: 'list[Pnb]' = []
        self.attributes: 'list[Pbc]' = []
        self.abilities: 'list[Pai]' = []

    @property
    def name(self) -> str:
        return self.__name

    @name.setter
    def name(self, value: str) -> None:
        if "(Ornn Upgrade)" in value:
            value = value[:value.index("(Ornn Upgrade)")]
        self.__name = value.replace("’", "'")

    def print(self) -> str:
        result: str = TEMPLATE
        
        if self.new:
            result += "|ch=new"
        elif self.removed:
            result += "|ch=removed"
        
        result += "|date=" + (str(self.date or ""))
        
        if any(x["name"] == self.__name for x in Dragon.champions):
            result += f"|champion={self.__name}\n"
        elif any(x["name"] == self.__name for x in Dragon.items):
            result += f"|item={self.__name}\n"
        elif any(x["name"] == self.__name for x in Dragon.runes):
            result += f"|rune={self.__name}\n"
        elif self.__name and not self.__name.isspace():
            result += f"|title={self.__name}\n"
        
        if self.summary and not self.summary.isspace():
            result += f"|summary={self.summary}\n"
        
        if self.context and not self.context.isspace():
            result += f"|context={self.context}\n"

        result += "|changes="
        return result
