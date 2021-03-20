from patchnotesparser.templates.pbc import Pbc
from patchnotesparser.helpers import Helper


class Pai:
    """Champion abilities"""
    
    def __init__(self, name: str) -> None:
        self.name: str = Helper.capitalize(name)
        self.attributes: 'list[Pbc]' = []

    def print(self) -> str:
        return f"{{{{pai|{self.name}|}}}}\n"
