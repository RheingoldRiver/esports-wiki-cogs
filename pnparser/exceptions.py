from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .patch_notes import PatchNotes


class ParserError(Exception):
    """Base class for all non-exit parser exceptions"""
    def __init__(self, patch_notes: 'PatchNotes', message: str) -> None:
        self.patch_notes: 'PatchNotes' = patch_notes
        self.message: str = message
        super().__init__(message)

class ParserHttpError(ParserError):
    """Common class for parser HTTP errors"""
    def __init__(self, patch_notes: 'PatchNotes', message: str) -> None:
        super().__init__(patch_notes, message)

class ParserTimeoutError(ParserError):
    """Client connection timed out"""
    def __init__(self, patch_notes: 'PatchNotes', message: str) -> None:
        super().__init__(patch_notes, message)