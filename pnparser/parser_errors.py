class ParserError(Exception):
    """Base class for all non-exit parser exceptions"""
    def __init__(self, message: str) -> None:
        self.message: str = message
        super().__init__(message)

class ParserHttpError(ParserError):
    """Common class for parser HTTP errors"""
    def __init__(self, message: str) -> None:
        self.message: str = message
        super().__init__(message)

class ParserInvalidFormatError(ParserError):
    """Patch number format not allowed"""
    def __init__(self, message: str) -> None:
        self.message: str = message
        super().__init__(message)