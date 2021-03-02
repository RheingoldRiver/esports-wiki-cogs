from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .section import Section


class Border:
    # class="content-border"
    def __init__(self, title: str) -> None:
        self.title: str = title
        self.contexxt: str = ""
        self.changes: 'list[Pnb]' = []
        self.attributes: 'list[Pbc]' = []
        self.skins: 'list[SplashTableEntry]' = []

    def print(self, section: 'Section') -> str:
        pass
