from tsutils.errors import ClientInlineTextException


class BadRequestException(ClientInlineTextException):
    def __init__(self, reason, *args):
        super().__init__(*args)
        self.reason = reason
