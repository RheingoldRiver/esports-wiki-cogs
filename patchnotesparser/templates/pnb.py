from patchnotesparser.templates.common import *
from patchnotesparser.templates.pbc import Pbc
from patchnotesparser.templates.pai import Pai
from patchnotesparser.dragon import Dragon
from datetime import date as Date
    
    
class ComplexPnb:
    """A more complex way of printing changes"""

    def __init__(self, title: str, context: str) -> None:
        self.title: str = title
        self.context: str = context
        self.text: 'list[str]' = []

    def print(self) -> str:
        result: str = ""
        return result


class Pnb:
    """A champion, item, rune, spell or jungle camp change"""
    
    def __init__(self, name: str = "",
                 new: bool = False,
                 removed: bool = False,
                 date: 'Date | None' = None) -> None:
        self.__name: str = ""
        self.name = name
        self.new: bool = new
        self.context: str = ""
        self.summary: str = ""
        self.removed: bool = removed
        self.changes: 'list[Pnb]' = []
        self.date: 'Date | None' = date
        self.abilities: 'list[Pai]' = []
        self.attributes: 'list[Pbc]' = []
        self.complex_changes: 'list[ComplexPnb] | None' = None

    @property
    def name(self) -> str:
        return self.__name

    @name.setter
    def name(self, value: str) -> None:
        if "(Ornn Upgrade)" in value:
            value = value[:value.index("(Ornn Upgrade)")]
        elif value == "Control Wards":
            value = value[:-1]
        self.__name = value.replace("’", "'")

    def print(self) -> str:
        result: str = "{{pnb"
        
        if self.new:
            result += "|ch=new"
        elif self.removed:
            result += "|ch=removed"
        
        result += "|date=" + (str(self.date or ""))
        
        # TODO: handle printing spells and camps
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

        if self.complex_changes is not None:
            for change in self.complex_changes:
                result += change.print()
            return result

        for attribute in self.attributes:
            result += attribute.print()
        
        if any(x["name"] == self.name for x in Dragon.champions):
            for ability in self.abilities:
                result += ability.print()

                for attribute in ability.attributes:
                    result += attribute.print()
            
            if result[-1] == "=":
                result = result[:-9]
        else:
            for inner_change in self.changes:
                if any(x["name"] == inner_change.name for x in Dragon.champions):

                    if result[-1] == "=":
                        result = result[:-9]

                    result += CI.format(inner_change.name)
                    for ability in inner_change.abilities:
                        result += ability.print()
                else:
                    result += ANCHOR.format(inner_change.name)
                    for attribute in inner_change.attributes:
                        result += attribute.print()
        result += TEMPLATE_END
        return result