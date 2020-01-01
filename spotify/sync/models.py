from functools import wraps
from inspect import getmembers, iscoroutinefunction
from typing import Type, Callable, TYPE_CHECKING

from .. import Client as _Client
from .thread import EventLoopThread

if TYPE_CHECKING:
    import spotify


def _infer_initializer(base: Type, name: str) -> Callable[..., None]:
    """Infer the __init__ to use for a given :class:`typing.Type` base and :class:`str` name."""
    if name in {"HTTPClient", "HTTPUserClient"}:

        def initializer(self: "spotify.HTTPClient", *args, **kwargs) -> None:
            base.__init__(self, *args, **kwargs)
            self.__client_thread__ = kwargs["loop"].__spotify_thread__  # type: ignore

    else:
        assert name != "Client"

        def initializer(self: "spotify.SpotifyBase", client: _Client, *args, **kwargs) -> None:  # type: ignore
            base.__init__(self, client, *args, **kwargs)
            self.__client_thread__ = client.__client_thread__  # type: ignore

    return initializer


def _normalize_coroutine_function(corofunc):
    if isinstance(corofunc, classmethod):

        @classmethod
        @wraps(corofunc)
        def wrapped(cls, client, *args, **kwargs):
            assert isinstance(client, _Client)
            client.__client_thread__.run_coroutine_threadsafe(
                corofunc(cls, client, *args, **kwargs)
            )

    else:

        @wraps(corofunc)
        def wrapped(self, *args, **kwargs):
            return self.__client_thread__.run_coroutine_threadsafe(
                corofunc(self, *args, **kwargs)
            )

    return wrapped


class Synchronous(type):
    """Metaclass used for overloading coroutine functions on models."""

    def __new__(cls, name, bases, dct):
        klass = super().__new__(cls, name, bases, dct)

        base = bases[0]
        name = base.__name__

        if name != "Client":
            # Models and the HTTP classes get their __init__ overloaded.
            initializer = _infer_initializer(base, name)
            setattr(klass, "__init__", initializer)

        for ident, obj in getmembers(base):
            if not iscoroutinefunction(obj):
                continue

            setattr(klass, ident, _normalize_coroutine_function(obj))

        return klass  # type: ignore


class Client(_Client, metaclass=Synchronous):
    def __init__(self, *args, **kwargs):
        thread = EventLoopThread()
        thread.start()

        kwargs["loop"] = thread.loop  # pylint: disable=protected-access

        super().__init__(*args, **kwargs)
        self.__thread = self.__client_thread__ = thread
