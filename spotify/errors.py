__all__ = ('SpotifyException', 'HTTPException', 'Forbidden', 'NotFound')


class SpotifyException(Exception):
    """base exception class for spotify.py."""
    pass


class HTTPException(SpotifyException):
    """exception that's thrown when a HTTP operation fails."""

    def __init__(self, response, message):
        self.response = response
        self.status = response.status
        error = message.get('error')

        if isinstance(error, dict):
            self.text = error.get('message')
        else:
            self.text = message.get('error_description')

        fmt = '{0.reason} (status code: {0.status})'
        if self.text.strip():
            fmt += ': {1}'

        super().__init__(fmt.format(self.response, self.text))


class Forbidden(HTTPException):
    """exception that's thrown when status code 403 occurs."""
    pass


class NotFound(HTTPException):
    """exception that's thrown when status code 404 occurs."""
    pass
