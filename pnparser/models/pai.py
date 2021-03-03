from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .pbc import Pbc


class Pai:
    """Champion abilities"""
    def __init__(self, name: str) -> None:
        self.name: str = name
        self.attributes: 'list[Pbc]' = []

    def print(self) -> str:
        pass
