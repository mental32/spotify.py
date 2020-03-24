__all__ = ("SpotifyException", "HTTPException", "Forbidden", "NotFound")


class SpotifyException(Exception):
    """Base exception class for spotify.py."""


class HTTPException(SpotifyException):
    """A generic exception that's thrown when a HTTP operation fails."""

    def __init__(self, response, message):
        self.response = response
        self.status = response.status
        error = message.get("error")

        if isinstance(error, dict):
            self.text = error.get("message", "")
        else:
            self.text = message.get("error_description", "")

        fmt = "{0.reason} (status code: {0.status})"
        if self.text.strip():
            fmt += ": {1}"

        super().__init__(fmt.format(self.response, self.text))


class Forbidden(HTTPException):
    """An exception that's thrown when status code 403 occurs."""


class NotFound(HTTPException):
    """An exception that's thrown when status code 404 occurs."""


class BearerTokenError(HTTPException):
    """An exception that's thrown when Spotify could not provide a valid Bearer Token"""


class RateLimitedException(Exception):
    """An exception that gets thrown when a rate limit is encountered."""
