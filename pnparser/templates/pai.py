from typing import TYPE_CHECKING
from ..helpers import Helper

if TYPE_CHECKING:
    from .pbc import Pbc


class Pai:
    """Champion abilities"""
    
    def __init__(self, name: str) -> None:
        self.name: str = Helper.capitalize(name)
        self.attributes: 'list[Pbc]' = []

    def print(self) -> str:
        return f"{{{{pai|{self.name}|}}}}\n"
