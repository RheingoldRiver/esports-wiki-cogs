from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .border import Border


class Section:
    # == ==
    def __init__(self, id: int, title: str) -> None:
        self.id: int = id
        self.title: str = title
        self.borders: 'list[Border]' = []
