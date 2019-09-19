import inspect
import functools
import re
from contextlib import contextmanager
from urllib.parse import quote_plus as quote
from typing import Callable

from .errors import SpotifyException

_URI_RE = re.compile(r"^.*:([a-zA-Z0-9]+)$")
_OPEN_RE = re.compile(r"http[s]?:\/\/open\.spotify\.com\/(.*)\/(.*)")


@contextmanager
def clean(l: dict, *names):
    """A helper context manager that defers mutating a set of locals."""
    yield
    for name in names:
        l.pop(name)


def to_id(string: str) -> str:
    """Get a spotify ID from a URI or open.spotify URL.

    Paramters
    ---------
    string : str
        The string to operate on.

    Returns
    -------
    id : str
        The Spotify ID from the string.
    """
    string = string.strip()

    match = _URI_RE.match(string)

    if match is None:
        match = _OPEN_RE.match(string)

        if match is None:
            return string
        else:
            return match.group(2)
    else:
        return match.group(1)


def assert_hasattr(
    attr: str, msg: str, tp: BaseException = SpotifyException
) -> Callable:
    """decorator to assert an object has an attribute when run."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def decorated(self, *args, **kwargs):
            if not hasattr(self, attr):
                raise tp(msg)
            return func(self, *args, **kwargs)

        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def decorated(*args, **kwargs):
                return await decorated(*args, **kwargs)

        return decorated

    return decorator