from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .pnb import Pnb
    from .pbc import Pbc
    from .section import Section


class Border:
    # class="content-border"
    def __init__(self, title: str = "", context: str = "", simplified: bool = False) -> None:
        self.title: str = title
        self.context: str = context
        self.changes: 'list[Pnb]' = []
        self.attributes: 'list[Pbc]' = []
        self.skins: 'list[SplashTableEntry]' = []
        self.simplified: bool = simplified

    def print(self, section: 'Section') -> str:
        pass
