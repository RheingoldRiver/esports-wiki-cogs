from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .pbc import Pbc


class Pai:
    def __init__(self) -> None:
        self.name: str = ""
        self.attributes: 'list[Pbc]' = []

    def print(self) -> str:
        pass
