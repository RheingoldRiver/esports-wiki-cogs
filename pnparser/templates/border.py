from typing import TYPE_CHECKING
from .common import *

if TYPE_CHECKING:
    from .pnb import Pnb
    from .pbc import Pbc
    from .section import Section


TEMPLATE: str = "{{{{pnbh|context='''{}'''<br>"


class Border:
    """class=\"content-border\""""
    def __init__(self, title: str = "", context: str = "", simplified: bool = False) -> None:
        self.title: str = title
        self.context: str = context
        self.changes: 'list[Pnb]' = []
        self.attributes: 'list[Pbc]' = []
        self.skins: 'list[SplashTableEntry]' = []
        self.simplified: bool = simplified

    def print(self, section: 'Section') -> str:
        result: str = ""

        if self.title and not self.title.isspace():
            result += SUBTITLE.format(self.title)
        
        if self.simplified:
            if section.title == "ARAM Balance Changes":
                if section.borders.index(self) == 0:
                    result += TEMPLATE.format(self.context)
                else: result += f"\n'''{self.context}'''<br>"

                for attribute in self.attributes:
                    result += attribute.print()

                if section.borders.index(self) == len(section.borders) - 1:
                    result += TEMPLATE_END
            else:
                result += OPEN_BORDER_DIV
                result += self.context[:1]

                for attribute in self.attributes:
                    result += attribute.print()

                result += CLOSE_DIV
        elif self.context and not self.context.isspace():
            result += f"''{self.context}''"
        return result