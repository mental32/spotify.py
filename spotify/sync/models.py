import inspect
import functools

from .. import SpotifyBase  # noqa
from . import Client as _Client
from .thread import SyncExecution


class SyncMeta(type):
    """Metaclass used for overloading coroutine functions on models."""

    def __new__(cls, name, bases, dct):
        klass = super().__new__(cls, name, bases, dct)

        base = bases[0]
        base_name = base.__name__

        if base_name in ("HTTPClient", "HTTPUserClient"):

            def __init__(self, *args, **kwargs):
                super(type(self), self).__init__(*args, **kwargs)
                self.__client_thread__ = kwargs["loop"]._thread

        elif base_name != "Client":

            def __init__(self, client, *args, **kwargs):
                super(type(self), self).__init__(client, *args, **kwargs)
                self.__client_thread__ = client.__client_thread__

        try:
            setattr(klass, "__init__", __init__)
        except NameError:
            pass

        for name, func in inspect.getmembers(base):

            if inspect.iscoroutinefunction(func):
                _func = getattr(base, name)

                def wrap(f):
                    if isinstance(f, classmethod):

                        @classmethod
                        @functools.wraps(f)
                        def wrapper(cls, client, *args, **kwargs):
                            assert isinstance(
                                client, _Client
                            ), "First argument of classmethod was not a `spotify.Client` instance"
                            client.__client_thread__.run_coro(
                                f, client, *args, **kwargs
                            )

                    else:

                        @functools.wraps(f)
                        def wrapper(self, *args, **kwargs):
                            return self.__client_thread__.run_coro(
                                f(self, *args, **kwargs)
                            )

                    return wrapper

                setattr(klass, name, wrap(_func))
            del name
        return klass


class Client(_Client, metaclass=SyncMeta):
    def __init__(self, *args, **kwargs):
        thread = SyncExecution()
        thread.start()

        kwargs["loop"] = thread._loop

        super().__init__(*args, **kwargs)
        self.__thread = self.__client_thread__ = thread


def _install(_types):
    for name, obj in _types.items():

        class Mock(obj, metaclass=SyncMeta):
            __slots__ = ("__client_thread__",)

        Mock.__name__ = obj.__name__
        Mock.__qualname__ = obj.__qualname__
        Mock.__doc__ = obj.__doc__

        yield name, Mock
