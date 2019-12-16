import inspect
from functools import wraps
from inspect import getmembers, iscoroutinefunction
from contextlib import suppress
from typing import Type, Callable, Optional

from .. import Client as _Client
from .thread import EventLoopThread


def _infer_initializer(base: Type, name: str) -> Callable[..., None]:
    """Infer the __init__ to use for a given :class:`typing.Type` base and :class:`str` name."""
    if name in {"HTTPClient", "HTTPUserClient"}:

        def initializer(self: "HTTPClient", *args, **kwargs) -> None:
            base.__init__(self, *args, **kwargs)
            self.__client_thread__ = kwargs["loop"].__spotify_thread__

    else:
        assert name != "Client"

        def initializer(self: "SpotifyBase", client: _Client, *args, **kwargs) -> None:
            base.__init__(self, client, *args, **kwargs)
            self.__client_thread__ = client.__client_thread__

    return initializer


def _coroutine_function_decorator(corofunc):
    if isinstance(corofunc, classmethod):

        @classmethod
        @wraps(corofunc)
        def wrapped(_, client, *args, **kwargs):
            assert isinstance(client, _Client)
            client.__client_thread__.run_coroutine_threadsafe(
                corofunc(klass, client, *args, **kwargs)
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

    def __new__(cls, name, bases, dct) -> type:
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

            setattr(klass, ident, _coroutine_function_decorator(obj))

        return klass


class Client(_Client, metaclass=Synchronous):
    def __init__(self, *args, **kwargs):
        thread = EventLoopThread()
        thread.start()

        kwargs["loop"] = thread.loop  # pylint: disable=protected-access

        super().__init__(*args, **kwargs)
        self.__thread = self.__client_thread__ = thread


def _install(types):
    for name, obj in types.items():

        class Mock(
            obj, metaclass=Synchronous
        ):  # pylint: disable=too-few-public-methods
            __slots__ = {"__client_thread__"}

        Mock.__name__ = obj.__name__
        Mock.__qualname__ = obj.__qualname__
        Mock.__doc__ = obj.__doc__

        yield name, Mock
