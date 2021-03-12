TEMPLATE: str = "{{pbc"

class Pbc:
    """Champions or items attributes"""
    
    def __init__(self, name: str = "") -> None:
        self.name: str = name
        self.before: str = ""
        self.after: str = ""
        self.status: 'str | None' = None

    def print(self) -> str:
        result: str = TEMPLATE
        
        if self.status:
            result += f"|ch={self.status}"

        if not self.before or self.before.isspace():
            result += f"|{self.name}|{self.after}}}}}\n"
        else:
            result += f"|{self.name}|{self.before}|{self.after}}}}}\n"
        return result
