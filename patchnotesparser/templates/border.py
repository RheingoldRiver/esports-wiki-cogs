from patchnotesparser.templates.splash import SplashTableEntry
from patchnotesparser.templates.section import Section
from patchnotesparser.templates.common import *
from patchnotesparser.templates.pnb import Pnb
from patchnotesparser.templates.pbc import Pbc


class Border:
    """The <div> border used by Riot in the patch notes for each change"""
    
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
            # TODO: think of a better way to check for this
            # don't want to keep section title here
            if section.title == "ARAM Balance Changes" or section.title == "Mid-Patch Updates":
                if section.borders.index(self) == 0:
                    result += f"{{{{pnbh|context='''{self.context}'''<br>\n"
                else: result += f"\n'''{self.context}'''<br>\n"

                for attribute in self.attributes:
                    result += attribute.print()

                # in case the next border is not simplified or
                # this is the last one then we should close the template
                if section.borders.index(self) == len(section.borders) - 1 or \
                not section.borders[section.borders.index(self) + 1].simplified:
                    result += TEMPLATE_END

                else:
                    result += "<br><hr><br>"
            else:
                result += OPEN_BORDER_DIV
                result += self.context

                for attribute in self.attributes:
                    result += attribute.print()

                result += CLOSE_DIV
        elif self.context and not self.context.isspace():
            result += OPEN_BORDER_DIV
            result += f":''{self.context}''\n"
            result += CLOSE_DIV
        return result
