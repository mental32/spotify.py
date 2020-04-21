from re import compile as re_compile
from functools import lru_cache
from contextlib import contextmanager
from typing import Iterable, Hashable, TypeVar, Dict, Tuple, Optional

__all__ = ("clean", "filter_items", "to_id")

_URI_RE = re_compile(r"^.*:([a-zA-Z0-9]+)$")
_OPEN_RE = re_compile(r"http[s]?:\/\/open\.spotify\.com\/(.*)\/(.*)")


@contextmanager
def clean(mapping: dict, *keys: Iterable[Hashable]):
    """A helper context manager that defers mutating a mapping."""
    yield
    for key in keys:
        mapping.pop(key)


K = TypeVar("K")  # pylint: disable=invalid-name
V = TypeVar("V")  # pylint: disable=invalid-name


@lru_cache(maxsize=1024)
def _cached_filter_items(data: Tuple[Tuple[K, Optional[V]], ...]) -> Dict[K, V]:
    data_ = {}
    for key, value in data:
        if value is not None:
            data_[key] = value
    return data_


def filter_items(data: Dict[K, Optional[V]]) -> Dict[K, V]:
    """Filter the items of a dict where the value is not None."""
    return _cached_filter_items((*data.items(),))


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
