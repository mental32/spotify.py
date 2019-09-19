import re
from contextlib import contextmanager
from typing import Iterable, Hashable

_URI_RE = re.compile(r"^.*:([a-zA-Z0-9]+)$")
_OPEN_RE = re.compile(r"http[s]?:\/\/open\.spotify\.com\/(.*)\/(.*)")


@contextmanager
def clean(mapping: dict, *keys: Iterable[Hashable]):
    """A helper context manager that defers mutating a mapping."""
    yield
    for key in keys:
        mapping.pop(key)


def to_id(value: str) -> str:
    """Get a spotify ID from a URI or open.spotify URL.

    Paramters
    ---------
    value : :class:`str`
        The value to operate on.

    Returns
    -------
    id : :class:`str`
        The Spotify ID from the value.
    """
    value = value.strip()
    match = _URI_RE.match(value)

    if match is None:
        match = _OPEN_RE.match(value)

        if match is None:
            return value
        return match.group(2)
    return match.group(1)
