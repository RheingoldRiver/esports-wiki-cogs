class Pbc:
    """Champions or items attributes"""
    def __init__(self, name: str) -> None:
        self.name: str = name
        self.before: str = ""
        self.after: str = ""
        self.status: 'str | None' = None

    def print(self) -> str:
        pass
