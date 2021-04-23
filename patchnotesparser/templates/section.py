from patchnotesparser.templates.common import *
from patchnotesparser.dragon import Dragon
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from patchnotesparser.templates.border import Border


# TODO: Add support for camps in TOC
ALLOWED_TOC_TYPES: 'list[str]' = ["Champion", "Item", "Summoner", "Rune", "Mastery", "Stat"]

class Section:
    """== {title} =="""
    
    # TODO: Improve on how we detect champions and itens and what not for TOC
    def __init__(self, id: int, title: str) -> None:
        self.id: int = id
        self.title: str = title
        self.borders: 'list[Border]' = []

    def print_toc(self) -> str:
        if any(word in self.title for word in ALLOWED_TOC_TYPES):
            icons: str = ""
            result: str = f"\n|group{self.id}={self.title}\n"
            group_type: str = self.title.split(' ')[0]
            group_type = group_type if not group_type[-1] == "s" else group_type[:-1]
            
            if not any(word in group_type for word in ALLOWED_TOC_TYPES):
                group_type = ""

            result += f"|group{self.id}types={group_type}\n"
            result += f"|group{self.id}images="
            
            for border in self.borders:
                for change in border.changes:
                    if "Champion" in self.title:
                        if any(x["name"] == change.name for x in Dragon.champions):
                            icons += f"{change.name}, "
                    elif "Item" in self.title:
                        if any(x["name"] == change.name for x in Dragon.items):
                            icons += f"{change.name}, "
                        else:
                            for inner_change in change.changes:
                                if any(x["name"] == inner_change.name for x in Dragon.items):
                                    icons += f"{inner_change.name}, "
                    elif "Rune" in self.title:
                        if any(x["name"] == change.name for x in Dragon.runes):
                            icons += f"{change.name}, "
                    elif "Summoner" in self.title:
                        if any(x["name"] == change.name for x in Dragon.spells):
                            icons += f"{change.name}, "
                    #elif "Camp" in self.title:
                    #    if any(x["name"] == change.name for x in Dragon.camps):
                    #        icons += f"{change.name}, "
            if icons and not icons.isspace():
                result += icons[:-2] + NEW_LINE + NEW_LINE
            return result
        else:
            return f"|group{self.id}={self.title}\n"
    
    def print(self) -> str:
        return TITLE.format(self.title)
